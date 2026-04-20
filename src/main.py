import logging
import traceback
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from helpers.config import get_settings
from helpers.exceptions import CustomAPIException
from helpers.logger import setup_logging
from models import AssetModel, ProjectModel, ResponseSignal
from routes import base, data, nlp, settings, wiki_search
from services.llm import LLMFactory
from services.ranker import RankerFactory
from services.vectordb import VectorDBFactory

# Set up the logger
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting Mini Rag System API...")

    try:
        # 1. Initialize MongoDB client
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)

        # 2. ACTUALLY check the connection by forcing a ping
        await mongo_client.admin.command("ping")
        logger.info("✅ Successfully connected to MongoDB!")

        # 3. Store in app state inside the try block
        app.state.mongo_client = mongo_client
        app.state.db_client = mongo_client[settings.MONGODB_DB_NAME]

    except Exception as e:
        logger.error(f"❌ CRITICAL: Failed to connect to MongoDB: {e}")
        # 4. Stop the server from starting if the DB is down!
        raise e

    # 5. INITIALIZE INDEXES HERE!
    logger.info("Verifying database indexes...")

    project_model = ProjectModel(db_client=app.state.db_client)
    asset_model = AssetModel(db_client=app.state.db_client)

    await project_model.init_collection()
    await asset_model.init_collection()

    try:
        # Initialize GENERATION, EMBEDDING, and SPARSE backends
        logger.info("Initializing LLM backends...")
        app.state.generation_client = LLMFactory.get_generation_client(settings)
        app.state.embedding_client = LLMFactory.get_embedding_client(settings)
        app.state.sparse_embedding_client = LLMFactory.get_sparse_embedding_client(settings)
        logger.info("✅ LLM backends initialized.")
    except Exception as e:
        logger.exception("❌ CRITICAL: Failed to initialize LLM backend")
        raise e

    try:
        # Initialize VECTOR_DB_BACKEND
        logger.info("Initializing Vector Database backend...")
        app.state.vector_db_client = VectorDBFactory.get_vector_db_client(
            settings,
            client_backend=settings.VECTOR_DB_BACKEND,
            existing_mongo_db=mongo_client[settings.MONGODB_DB_NAME],
        )
        await app.state.vector_db_client.connect()
        logger.info("✅ Vector Database backend initialized.")
    except Exception as e:
        logger.exception("❌ CRITICAL: Failed to initialize Vector Database backend")
        raise e

    try:
        # Initialize RANKER_BACKEND
        logger.info("Initializing Ranker backend...")
        app.state.ranker_client = RankerFactory.get_ranker_client(settings)
        logger.info("✅ Ranker backend initialized.")
    except Exception as e:
        logger.exception("❌ CRITICAL: Failed to initialize Ranker backend")
        raise e

    # 6. Initialize mutable runtime settings for live UI tuning
    app.state.runtime_settings = {
        "temperature": settings.GENERATION_TEMPERATURE,
        "retrieval_limit": 5,
        "max_output_tokens": settings.GENERATION_MAX_OUTPUT_TOKENS,
    }

    # 7. Initialize provider state for runtime hot-swapping
    app.state.active_providers = {
        "generation_backend": settings.GENERATION_BACKEND,
        "generation_model": settings.GENERATION_MODEL_ID,
        "embedding_backend": settings.EMBEDDING_BACKEND,
        "embedding_model": settings.EMBEDDING_MODEL_ID,
    }
    app.state.api_keys = {
        "openai": settings.OPENAI_API_KEY,
        "cohere": settings.COHERE_API_KEY,
        "gemini": settings.GEMINI_API_KEY,
    }
    app.state.connection_urls = {
        "openai_base_url": settings.OPENAI_BASE_URL or "",
        "qdrant_url": settings.QDRANT_URL,
        "mongodb_uri": settings.MONGODB_URI,
    }
    logger.info("✅ Runtime settings and provider state initialized.")

    yield

    # 6. Safely close the clients when the application shuts down
    logger.info("Shutting down: Closing connections...")
    if hasattr(app.state, "mongo_client"):
        app.state.mongo_client.close()
        logger.info("✅ MongoDB connection closed.")

    if hasattr(app.state, "vector_db_client"):
        await app.state.vector_db_client.disconnect()
        logger.info("✅ Vector DB connection closed.")


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

# This automatically generates a unique UUID for every single web request
app.add_middleware(CorrelationIdMiddleware)

# Integrate CORSMiddleware locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Grab the unique ID for this specific web request
    req_id = correlation_id.get()

    method = request.method
    url = request.url.path
    error_trace = traceback.format_exc()

    # The logger automatically formats this beautifully based on logger.py!
    logger.error(f"🚨 CRITICAL UNHANDLED ERROR on {method} {url}")
    logger.error(f"Details: {exc}\n{error_trace}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "signal": ResponseSignal.INTERNAL_SERVER_ERROR.signal,
            "message": ResponseSignal.INTERNAL_SERVER_ERROR.message,
            # 2. Give the ID to the frontend so they can report it!
            "request_id": req_id,
            "dev_detail": str(exc),
        },
    )


@app.exception_handler(CustomAPIException)
async def custom_api_exception_handler(request: Request, exc: CustomAPIException):
    """
    Catches the CustomAPIException and formats it into a clean JSON response for the frontend,
    while logging the exact business context to the terminal.
    """
    # Grab the unique ID for this specific web request
    req_id = correlation_id.get()

    method = request.method
    url = request.url.path

    # Log the specific business logic failure (exc_info=exc prints the chained traceback!)
    logger.error(
        f"⚠️ Custom API Error [{exc.status_code}] on {method} {url} | "
        f"Signal: {exc.signal.value if hasattr(exc.signal, 'value') else exc.signal} | "
        f"Detail: {exc.dev_detail}",
        exc_info=exc,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "signal": exc.signal.value if hasattr(exc.signal, "value") else str(exc.signal),
            "message": exc.message,
            "request_id": req_id,
            "dev_detail": exc.dev_detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 1. Grab the unique ID
    req_id = correlation_id.get()

    raw_errors = exc.errors()
    simplified_errors = [{"field": err["loc"][-1], "message": err["msg"]} for err in raw_errors]

    logger.warning(f"⚠️ Validation Error on {request.method} {request.url.path}: {simplified_errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "signal": ResponseSignal.VALIDATION_FAILED.signal,
            "message": ResponseSignal.VALIDATION_FAILED.message,
            # 2. Give the ID to the frontend here too!
            "request_id": req_id,
            "details": simplified_errors,
        },
    )


app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(wiki_search.wiki_search_router)
app.include_router(nlp.nlp_router)
app.include_router(settings.settings_router)

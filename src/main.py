import logging
import traceback
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from helpers.config import get_settings
from helpers.logger import setup_logging
from models import AssetModel, ChunkModel, ProjectModel, ResponseSignal
from routes import base, data, wiki_search
from services.llm import LLMFactory

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

    # 5. INITIALIZE INDEXES HERE! This ensures indexes are always created before any requests hit the server.
    logger.info("Verifying database indexes...")

    project_model = ProjectModel(db_client=app.state.db_client)
    chunk_model = ChunkModel(db_client=app.state.db_client)
    asset_model = AssetModel(db_client=app.state.db_client)

    await project_model.init_collection()
    await chunk_model.init_collection()
    await asset_model.init_collection()

    try:
        # Initialize GENERATION_BACKEND and EMBEDDING_BACKEND
        logger.info("Initializing LLM backends...")
        app.state.generation_client = LLMFactory.get_generation_client(settings)
        app.state.embedding_client = LLMFactory.get_embedding_client(settings)
        logger.info("✅ LLM backends initialized.")
    except Exception:
        logger.exception("❌ CRITICAL: Failed to initialize LLM backend")

    yield

    # 6. Safely close the MongoDB client when the application shuts down
    logger.info("Shutting down: Closing MongoDB connection...")
    if hasattr(app.state, "mongo_client"):
        app.state.mongo_client.close()
        logger.info("✅ MongoDB connection closed.")


app = FastAPI(lifespan=lifespan)

# This automatically generates a unique UUID for every single web request
app.add_middleware(CorrelationIdMiddleware)


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
            "signal": ResponseSignal.INTERNAL_SERVER_ERROR.value,
            "message": ResponseSignal.INTERNAL_SERVER_ERROR_MESSAGE.value,
            # 2. Give the ID to the frontend so they can report it!
            "request_id": req_id,
            "dev_detail": str(exc),
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
            "signal": ResponseSignal.VALIDATION_FAILED.value,
            "message": ResponseSignal.VALIDATION_FAILED_MESSAGE.value,
            # 2. Give the ID to the frontend here too!
            "request_id": req_id,
            "details": simplified_errors,
        },
    )


app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(wiki_search.wiki_search_router)

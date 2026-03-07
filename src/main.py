import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from helpers.config import get_settings
from routes import base, data, wiki_search


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        # Initialize MongoDB client and check the connection
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
    except Exception as e:
        logging.getLogger("uvicorn.error").error(f"Failed to connect to MongoDB: {e}")

    # store MongoDB client in the app state
    app.state.mongo_client = mongo_client
    # Access the specific database and store it in the app state for easy access in controllers
    app.state.db_client = app.state.mongo_client[settings.MONGODB_DB_NAME]
    yield
    # Close the MongoDB client when the application shuts down
    app.state.mongo_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(wiki_search.wiki_search_router)

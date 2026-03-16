import logging
from typing import Optional

from Clients import MongoDBClient, QdrantClient

from controllers.BaseController import BaseController

from .VectorDBEnums import VectorDBBackendEnum
from .VectorDBInterface import VectorDBInterface

logger = logging.getLogger(__name__)


class VectorDBFactory:
    """
    A Factory class to instantiate the correct Vector Database client
    based on environment variables.
    """

    @staticmethod
    def get_vector_db_client(
        settings, client_backend: Optional[str] = None, existing_mongo_db=None
    ) -> VectorDBInterface:
        """
        Initializes and returns the configured VectorDB client.

        Args:
            settings (Settings): The application settings object.
            client_backend (Optional[str]): Override the .env setting if needed.
            existing_mongo_db (Optional[AsyncIOMotorDatabase]): Inherited MongoDB connection pool.

        Returns:
            VectorDBInterface: The instantiated database client.
        """
        # Default to the .env setting if no override is provided
        target_backend = client_backend if client_backend else settings.VECTOR_DB_BACKEND
        baseController = BaseController()
        if target_backend == VectorDBBackendEnum.QDRANT.value:
            logger.info("Factory routing: Initializing Qdrant Client...")

            # Safely handle the API key (pass None if it's an empty string)
            qdrant_key = (
                settings.QDRANT_API_KEY if hasattr(settings, "QDRANT_API_KEY") and settings.QDRANT_API_KEY else None
            )
            qdrant_url = settings.QDRANT_URL if hasattr(settings, "QDRANT_URL") and settings.QDRANT_URL else None
            qdrant_path = settings.QDRANT_PATH if hasattr(settings, "QDRANT_PATH") and settings.QDRANT_PATH else None

            if qdrant_path:
                qdrant_path = baseController.get_database_path(database_name=qdrant_path)

            return QdrantClient(
                url=qdrant_url,
                api_key=qdrant_key,
                path=qdrant_path,
            )

        elif target_backend == VectorDBBackendEnum.MONGODB.value:
            logger.info("Factory routing: Initializing MongoDB Atlas Client...")

            return MongoDBClient(
                uri=settings.MONGODB_URI, db_name=settings.MONGODB_DB_NAME, existing_mongo_db=existing_mongo_db
            )

        else:
            error_msg = f"CRITICAL: Unsupported Vector DB backend configured: '{target_backend}'"
            logger.error(error_msg)
            raise ValueError(error_msg)

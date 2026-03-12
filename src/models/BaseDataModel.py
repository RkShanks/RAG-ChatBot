import logging

from helpers.config import Settings, get_settings

logger = logging.getLogger(__name__)


class BaseDataModel:
    def __init__(self, db_client):
        self.db_client = db_client
        self.app_settings: Settings = get_settings()

        # We define these as None here so IDEs know they exist.
        # The child classes will overwrite them!
        self.collection = None
        self.document_class = None

    async def init_collection(self):
        # Safety check: ensure the child class actually set these up
        if self.collection is None or self.document_class is None:
            logger.warning("Collection or document_class not set. Skipping index creation.")
            return

        logger.debug(f"Initializing indexes for collection: {self.collection.name}...")

        try:
            # Safely check if the Pydantic model has the get_indexes method
            if hasattr(self.document_class, "get_indexes"):
                indexes = self.document_class.get_indexes()

                for index in indexes:
                    await self.collection.create_index(
                        index["key"],
                        name=index["name"],
                        unique=index.get("unique", False),  # Defaults to False safely
                    )
                logger.info(f"Indexes verified for {self.collection.name}.")
            else:
                logger.debug(f"No indexes defined in schema for {self.document_class.__name__}.")

        except Exception:
            logger.exception(f"Failed to create indexes for {self.collection.name}.")
            raise

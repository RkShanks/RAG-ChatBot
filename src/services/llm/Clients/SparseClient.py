import asyncio
import logging
from typing import Dict, List

from fastembed import SparseTextEmbedding

logger = logging.getLogger(__name__)


class SparseClient:
    def __init__(self, model_name: str = "prithivida/Splade_PP_en_v1"):
        logger.info(f"Loading Local Sparse Model: {model_name}...")
        # This downloads the small model to your local machine on first run
        self.model = SparseTextEmbedding(model_name=model_name)
        logger.info("Sparse Model loaded successfully.")

    async def generate_sparse_embedding(self, text: str) -> Dict[str, List]:
        """
        Converts text into a dictionary of indices and values for Hybrid Search.
        Runs in a background thread to prevent blocking the async event loop.
        """
        try:
            # fastembed returns a generator, so we wrap it in a list
            result = await asyncio.to_thread(lambda: list(self.model.embed([text]))[0])

            # Extract the indices and values required by Qdrant/MongoDB
            return {"indices": result.indices.tolist(), "values": result.values.tolist()}
        except Exception:
            logger.exception("Failed to generate sparse embedding.")
            raise

import asyncio
import logging
from pathlib import Path
from typing import Dict, List

from fastembed import SparseTextEmbedding

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal

logger = logging.getLogger(__name__)


class SparseClient:
    def __init__(self, model_name: str = "prithivida/Splade_PP_en_v1"):
        logger.info(f"Loading Local Sparse Model: {model_name}...")
        # 1. Dynamically calculate the path to src/assets/local_models
        # .parent (Clients) -> .parent (llm) -> .parent (services) -> .parent (src)
        src_dir = Path(__file__).resolve().parent.parent.parent.parent

        # 2. Build the final path: src/assets/local_models
        cache_dir = src_dir / "assets" / "local_models"

        try:
            # 3. Create the folder if it doesn't exist yet
            cache_dir.mkdir(parents=True, exist_ok=True)

            # 4. Pass the string version of the path to fastembed and downloads the small model to your local machine
            self.model = SparseTextEmbedding(model_name=model_name, cache_dir=str(cache_dir))
            logger.info("Sparse Model loaded successfully.")
        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.MODEL_LOADING_FAILED,
                status_code=500,
                dev_detail=f"Failed to load local sparse model '{model_name}' into {cache_dir}.",
            ) from e

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

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.EMBEDDING_FAILED,
                status_code=500,  # 500 because it crashed locally, not a 502 upstream error
                dev_detail="Local Sparse model failed to execute mathematical embedding in background thread.",
            ) from e

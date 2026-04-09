import asyncio
import logging
from pathlib import Path
from typing import List

from sentence_transformers import CrossEncoder

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal
from models.db_schemes import RetrievedDocument

from ..RankerInterface import RankerInterface

logger = logging.getLogger(__name__)


class LocalRankerClient(RankerInterface):
    def __init__(self, model_id: str = "Alibaba-NLP/gte-multilingual-reranker-base"):
        logger.info(f"Loading Local Cross-Encoder Ranker: {model_id}...")
        # 1. Dynamically calculate the path to src/assets/local_models
        # .parent (Clients) -> .parent (ranker) -> .parent (services) -> .parent (src)
        src_dir = Path(__file__).resolve().parent.parent.parent.parent

        # 2. Build the final path: src/assets/local_models
        cache_dir = src_dir / "assets" / "local_models"

        try:
            # 3. Create the folder if it doesn't exist yet
            cache_dir.mkdir(parents=True, exist_ok=True)

            # This downloads to your HuggingFace cache on first run
            self.model = CrossEncoder(
                model_id,
                cache_folder=str(cache_dir),
                trust_remote_code=True,
            )
            logger.info("Local Ranker loaded successfully.")
        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.MODEL_LOADING_FAILED,
                status_code=500,
                dev_detail=f"Failed to load local cross-encoder model '{model_id}' into cache {cache_dir}.",
            ) from e

    async def rerank(self, query: str, documents: List[RetrievedDocument], top_k: int = 5) -> List[RetrievedDocument]:
        if not documents:
            return []
        logger.debug(f"Reranking {len(documents)} documents with query: {query}")

        # Create pairs of (Query, Document_Text) for the Cross-Encoder
        sentence_pairs = [[query, doc.text] for doc in documents]

        try:
            logger.debug(f"Calling Local Cross-Encoder predict with {len(sentence_pairs)} sentence pairs.")
            # Run the ML math in a background thread to prevent blocking FastAPI
            scores = await asyncio.to_thread(self.model.predict, sentence_pairs)

            # Attach the new scores to the documents
            for i, doc in enumerate(documents):
                doc.relevance_score = float(scores[i])

            # Sort the documents by highest score first
            sorted_docs = sorted(documents, key=lambda x: x.relevance_score, reverse=True)

            # Return only the top_k
            best_docs = sorted_docs[:top_k]

            logger.debug(f"Local Cross-Encoder reranked {len(documents)} docs down to {len(best_docs)}")
            return best_docs

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.RERANKING_FAILED,
                status_code=500,
                dev_detail=f"Local Cross-Encoder math failed on {len(sentence_pairs)} sentence pairs.",
            ) from e

import logging
from typing import List

import cohere

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal
from models.db_schemes import RetrievedDocument

from ..RankerInterface import RankerInterface

logger = logging.getLogger(__name__)


class CohereRankerClient(RankerInterface):
    def __init__(self, api_key: str, model_id: str = "rerank-v4.0-fast"):
        if not api_key:
            raise CustomAPIException(
                signal_enum=ResponseSignal.API_KEY_MISSING,
                status_code=500,
                dev_detail="Cohere API key missing during CohereRankerClient initialization.",
            )

        # Note: Cohere V2 Async Client
        self.client = cohere.AsyncClientV2(api_key=api_key)
        self.model_id = model_id
        logger.info(f"Cohere Ranker initialized with model: {self.model_id}")

    async def rerank(self, query: str, documents: List[RetrievedDocument], top_k: int = 5) -> List[RetrievedDocument]:
        logger.debug(f"Reranking {len(documents)} documents with query: {query}")
        if not documents:
            return []

        # Extract just the text for Cohere
        texts = [doc.text for doc in documents]

        try:
            logger.debug(f"Calling Cohere Rerank API with model: {self.model_id}, query: {query}, top_n: {top_k}")
            # Call the API
            results = await self.client.rerank(
                model=self.model_id,
                query=query,
                documents=texts,
                top_n=top_k,
            )

            # Re-map the results back to RetrievedDocument objects with updated scores
            reranked_docs = []
            for result in results.results:
                original_doc = documents[result.index]
                reranked_docs.append(
                    RetrievedDocument(
                        text=original_doc.text,
                        relevance_score=result.relevance_score,
                        metadata=original_doc.metadata,
                    )
                )

            logger.debug(f"Cohere successfully reranked {len(documents)} docs down to {len(reranked_docs)}")
            return reranked_docs

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.RERANKING_FAILED,
                status_code=502,
                dev_detail=f"Cohere API failed to rerank {len(documents)} chunks using model '{self.model_id}'.",
            ) from e

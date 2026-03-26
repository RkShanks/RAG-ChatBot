import logging
from typing import Any, Dict, List, Optional

from controllers.BaseController import BaseController
from services.llm import InputTypeEnum, LLMInterface
from services.vectordb import VectorDBInterface

logger = logging.getLogger(__name__)


class NLPController(BaseController):
    def __init__(
        self,
        vector_client: VectorDBInterface,
        generation_client: LLMInterface,
        embedding_client: LLMInterface,
        sparse_embedding_client: Optional[LLMInterface] = None,
        reranker_client: Optional[Any] = None,
    ):
        super().__init__()
        self.vector_client = vector_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.sparse_client = sparse_embedding_client
        self.reranker_client = reranker_client

    async def search_and_rerank(
        self,
        project_id: str,
        query: str,
        retrieval_limit: int = 20,
        final_limit: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Reranking Step: Fetches a broad set of results (top 20 by default),
        then cross-encodes them to strictly judge relevance, returning the top 5.
        """
        collection_name = self.get_collection_name(project_id)

        logger.debug(f"Generating query embeddings for search in '{collection_name}'...")
        try:
            dense_query_vector = await self.embedding_client.generate_embedding(
                texts=[query],
                input_type=InputTypeEnum.Query.value,
            )
        except Exception:
            return
        sparse_query_vector = None
        if self.vector_client.is_sparse_needed() and self.sparse_client:
            sparse_query_vector = await self.sparse_client.generate_sparse_embedding(query)

        logger.debug(f"Executing broad vector search with retrieval_limit={retrieval_limit}...")
        initial_results = await self.vector_client.search_by_vector(
            collection_name=collection_name,
            query_vector=dense_query_vector[0],
            limit=retrieval_limit,
            filter_criteria=filter_criteria,
            sparse_query_vector=sparse_query_vector,
        )

        # The Cross-Encoder Reranking
        if self.reranker_client and initial_results:
            logger.debug(f"Reranking top {retrieval_limit} chunks to find the absolute best {final_limit}...")
            reranked_results = await self.reranker_client.rerank(
                query=query, documents=initial_results, top_n=final_limit
            )
            return reranked_results

        # Fallback if no reranker is configured
        return initial_results[:final_limit]

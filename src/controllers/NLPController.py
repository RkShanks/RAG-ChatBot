import logging
from typing import Any, Dict, List, Optional

from controllers.BaseController import BaseController
from models.db_schemes import RetrievedDocument
from services.llm import InputTypeEnum, LLMInterface
from services.vectordb import VectorDBInterface

logger = logging.getLogger(__name__)


class NLPController(BaseController):
    SYSTEM_PROMPT_TEMPLATE = """You are an expert, objective AI assistant with name Nimo.
Your sole task is to answer the user's question based strictly on the provided context.

CONSTRAINTS:
1. NO HALLUCINATIONS: If the answer cannot be deduced from the context, you MUST state: "I cannot answer this based on the provided documents."
2. NO EXTERNAL KNOWLEDGE: Do not supplement your answer with outside information.
3. LANGUAGE: You MUST generate your entire response in the following language/locale: {target_locale}
4. CONCISENESS: Answer directly based on the context. If the text implies an answer but does not explicitly state it, you may infer the answer but must briefly mention the inference.
--- START CONTEXT ---
{context_string}
--- END CONTEXT ---
"""

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
        format_results = self.format_search_results(initial_results)

        # The Cross-Encoder Reranking
        if self.reranker_client and format_results:
            logger.debug(f"Reranking top {retrieval_limit} chunks to find the absolute best {final_limit}...")
            reranked_results = await self.reranker_client.rerank(
                query=query, documents=format_results, top_k=final_limit
            )
            return reranked_results

        # Fallback if no reranker is configured
        return format_results[:final_limit]

    def format_search_results(self, search_results: List[Dict[str, Any]]) -> List[RetrievedDocument]:
        formatted_results = []
        for result in search_results:
            formatted_results.append(
                RetrievedDocument(
                    text=result.get("text"),
                    relevance_score=float(result.get("score")),
                    metadata=result.get("metadata"),
                )
            )
        return formatted_results

    def format_context(self, search_results: List[RetrievedDocument]) -> str:
        if not search_results:
            return "No relevant context found."

        context_parts = []
        for i, result in enumerate(search_results):
            text = result.text
            metadata = result.metadata
            source = metadata.get("source", "Unknown Source")
            page = metadata.get("page_number", "N/A")

            context_parts.append(f"[Source {i + 1}: {source} (Page {page})]\n{text}\n")

        return "\n".join(context_parts)

    def _manage_token_window(
        self, system_prompt: str, query: str, chat_history: List[Dict[str, str]], max_tokens: int = 6000
    ) -> List[Dict[str, str]]:

        if not chat_history:
            return []

        def estimate_tokens(text: str) -> int:
            # For strict production, replace this block with: `return len(encoding.encode(text))`
            return len(text) // 4

        base_tokens = estimate_tokens(system_prompt) + estimate_tokens(query)

        valid_history = chat_history.copy()
        while valid_history:
            history_tokens = sum(estimate_tokens(msg.get("content", "")) for msg in valid_history)
            if base_tokens + history_tokens <= max_tokens:
                break
            # Drop the oldest message from the front
            valid_history.pop(0)

        if len(valid_history) < len(chat_history):
            logger.warning(f"Context window tight! Trimmed {len(chat_history) - len(valid_history)} older messages.")

        return valid_history

    async def ask_question(
        self,
        project_id: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        limit: int = 5,
        target_locale: str = "Based in Query language",
        max_output_tokens: Optional[int] = None,
    ):
        chat_history = chat_history or []

        # Step A: Retrieve & Rerank
        search_results = await self.search_and_rerank(project_id, query, retrieval_limit=20, final_limit=limit)
        context_string = self.format_context(search_results)

        # Step B: Build system prompt
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(context_string=context_string, target_locale=target_locale)

        # Step C: Token Trimming
        trimmed_history = self._manage_token_window(system_prompt, query, chat_history)

        # Step D: Inject the System Prompt as the FIRST message in the history list
        final_payload_history = [{"role": "system", "content": system_prompt}] + trimmed_history

        # Step E: Generate the final response
        logger.info(f"Starting LLM response for project {project_id}...")
        response = await self.generation_client.generate_text(
            prompt=query, chat_history=final_payload_history, max_output_tokens=max_output_tokens
        )
        return response, final_payload_history

    async def ask_question_stream(
        self,
        project_id: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        limit: int = 5,
        target_locale: str = "Based in Query language",
        max_output_tokens: int = None,
    ):

        chat_history = chat_history or []

        # Step A: Retrieve & Rerank
        search_results = await self.search_and_rerank(project_id, query, retrieval_limit=20, final_limit=limit)
        context_string = self.format_context(search_results)

        # Step B: Build system prompt
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(context_string=context_string, target_locale=target_locale)

        # Step C: Token Trimming
        trimmed_history = self._manage_token_window(system_prompt, query, chat_history)

        # Step D: Inject the System Prompt as the FIRST message in the history list
        final_payload_history = [{"role": "system", "content": system_prompt}] + trimmed_history

        # Step E: Generate the final response
        logger.info(f"Starting streaming LLM response for project {project_id}...")
        stream = self.generation_client.generate_text_stream(
            prompt=query, chat_history=final_payload_history, max_output_tokens=max_output_tokens
        )
        return stream, final_payload_history

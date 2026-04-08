import logging
from typing import Dict, List

import cohere

from helpers.decorators import validate_llm_client

from ..LLMEnums import CohereEnum, InputTypeEnum
from ..LLMInterface import LLMInterface

logger = logging.getLogger(__name__)


class CohereClient(LLMInterface):
    def __init__(
        self,
        api_key: str,
        default_max_input_characters: int = 2048,
        default_max_output_tokens: int = 2048,
        default_temperature: float = 0.1,
    ):
        if not api_key:
            logger.error("A Cohere API key must be provided.")
            raise ValueError("A Cohere API key must be provided.")

        # Initialize the async Cohere client
        self.client = cohere.AsyncClientV2(api_key=api_key)

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.DEFAULT_DIMENSIONS = CohereEnum.DEFAULT_DIMENSIONS.value

        # Store your excellent RAG defaults

        self.default_max_input_characters = default_max_input_characters
        self.default_max_tokens = default_max_output_tokens
        self.default_temperature = default_temperature

        self.INPUT_TYPE_MAP = CohereEnum.INPUT_TYPE_MAP.value

        logger.info("Cohere client initialized.")

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
        logger.debug(f"Cohere generation model set to: {model_id}")

    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size or self.DEFAULT_DIMENSIONS.get(model_id)
        logger.debug(f"Cohere embedding model set to: {model_id} (Size: {self.embedding_size})")

    async def construct_prompt(self, prompt: str, role: str) -> dict:
        return {
            "role": role,
            "content": await self.process_text(prompt),
        }

    async def process_text(self, prompt: str) -> str:
        return prompt[: self.default_max_input_characters].strip()

    @validate_llm_client
    async def generate_text(
        self, prompt: str, chat_history: List[Dict[str, str]] = None, max_output_tokens: int = None, **kwargs
    ) -> str:
        """
        Calls the Cohere Chat API using the explicit max_output_tokens.
        """
        cohere_history = chat_history.copy() if chat_history else []
        cohere_history.append(await self.construct_prompt(prompt, CohereEnum.USER.value))

        # Merge defaults, explicitly preferring max_output_tokens if provided
        call_params = {
            "temperature": self.default_temperature,
            "max_tokens": max_output_tokens or self.default_max_tokens,
            **kwargs,
        }

        try:
            response = await self.client.chat(
                model=self.generation_model_id,
                messages=cohere_history,
                **call_params,
            )

            # --- OUTPUT VALIDATION ---
            content = response.message.content[0].text

            if not content or not isinstance(content, str) or not content.strip():
                logger.error(f"Cohere returned an empty response for model '{self.generation_model_id}'")
                raise ValueError("Received empty text response from LLM.")

            return content.strip()

        except Exception:
            logger.exception(f"Cohere text generation failed using model '{self.generation_model_id}'")
            raise

    @validate_llm_client
    async def generate_text_stream(
        self, prompt: str, chat_history: List[Dict[str, str]] = None, max_output_tokens: int = None, **kwargs
    ):
        """
        Calls the Cohere Chat API with streaming enabled.
        """
        cohere_history = chat_history.copy() if chat_history else []
        cohere_history.append(await self.construct_prompt(prompt, CohereEnum.USER.value))

        # Merge defaults, explicitly preferring max_output_tokens if provided
        call_params = {
            "temperature": self.default_temperature,
            "max_tokens": max_output_tokens or self.default_max_tokens,
            **kwargs,
        }

        try:
            response = await self.client.chat_stream(
                model=self.generation_model_id,
                messages=cohere_history,
                **call_params,
            )

            async for event in response:
                if event and event.type == "content-delta":
                    if event.delta and event.delta.message and event.delta.message.content:
                        yield {"type": "answer", "text": event.delta.message.content.text}

        except Exception:
            logger.exception(f"Cohere text stream generation failed using model '{self.generation_model_id}'")
            raise

    @validate_llm_client
    async def generate_embedding(
        self, texts: list[str], input_type: str = InputTypeEnum.Document.value, **kwargs
    ) -> list[List[float]]:
        """
        Calls the Cohere Embed API.
        """
        cohere_task_type = self.INPUT_TYPE_MAP.get(input_type, "RETRIEVAL_DOCUMENT")

        try:
            response = await self.client.embed(
                texts=texts,
                model=self.embedding_model_id,
                input_type=cohere_task_type,
                embedding_types=["float"],
                **kwargs,
            )

            # --- OUTPUT VALIDATION ---
            if not response.embeddings.float or not isinstance(response.embeddings.float, list):
                logger.error("Cohere returned an invalid embedding format.")
                raise ValueError("Received invalid embedding format from LLM.")

            embedding = response.embeddings.float

            if self.embedding_size and len(embedding[0]) != self.embedding_size:
                logger.error(f"Dimensionality mismatch! Expected {self.embedding_size}, got {len(embedding[0])}.")
                raise ValueError(f"Embedding dimension mismatch. Expected {self.embedding_size}.")

            return embedding

        except Exception:
            logger.exception(f"Cohere embedding generation failed using model '{self.embedding_model_id}'")
            raise

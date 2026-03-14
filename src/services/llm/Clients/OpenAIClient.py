import logging
from typing import Dict, List

from openai import AsyncOpenAI

from helpers.decorators import validate_llm_client

from ..LLMEnums import OPENAIEnum
from ..LLMInterface import LLMInterface

logger = logging.getLogger(__name__)


class OpenAIClient(LLMInterface):
    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        default_max_input_characters: int = 2048,
        default_max_output_tokens: int = 2048,
        default_temperature: float = 0.1,
    ):
        """
        Initialize the async OpenAI client with system-wide defaults.
        """
        if not api_key and not base_url:
            logger.error("An OPENAI_API key or a local base_url must be provided.")
            raise ValueError("An API key or a local base_url must be provided.")

        # If base_url is provided, it will point to your local open-source server!
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None

        # Store your excellent RAG defaults
        self.default_max_input_characters = default_max_input_characters
        self.default_max_output_tokens = default_max_output_tokens
        self.default_temperature = default_temperature

        logger.info("OpenAI client initialized")

    def set_generation_model(self, model_id: str):
        logger.debug(f"OpenAI generation model set to: {model_id}")
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        logger.debug(f"OpenAI embedding model set to: {model_id} (Size: {embedding_size})")
        self.embedding_model_id = model_id
        self.embedding_size = (
            embedding_size or OPENAIEnum.DEFAULT_DIMENSIONS[model_id].value or OPENAIEnum.DEFAULT_EMBEDDING_SIZE.value
        )

    @validate_llm_client
    async def generate_text(
        self,
        prompt: str,
        chat_history: List[Dict[str, str]] = None,
        temperature: float = None,
        max_output_tokens: int = None,
        **kwargs,
    ) -> str:
        """
        Calls the OpenAI Chat Completions API.
        """
        # 1. Format the messages array correctly for OpenAI
        messages = chat_history.copy() if chat_history else []
        messages.append(await self.construct_prompt(prompt, OPENAIEnum.USER.value))

        call_params = {
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_output_tokens or self.default_max_tokens,
            **kwargs,
        }
        try:
            # 2. Call the async client, passing in any extra kwargs (like temperature)
            response = await self.client.chat.completions.create(
                model=self.generation_model_id,
                messages=messages,
                **call_params,
            )

            # 3. Extract the content
            content = response.choices[0].message.content

            # 5. Verify it is a valid string and not empty
            if not content or not isinstance(content, str) or not content.strip():
                logger.error(f"OpenAI returned an empty or invalid response for model '{self.generation_model_id}'")
                raise ValueError("Received empty text response from LLM.")

            #  Return the clean guaranteed string
            return content.strip()

        except Exception:
            logger.exception(f"OpenAI text generation failed using model '{self.generation_model_id}'")
            raise

    @validate_llm_client
    async def generate_embedding(self, text: str, input_type: str = None, **kwargs) -> List[float]:
        """
        Calls the OpenAI Embeddings API to convert text to a vector.
        """
        try:
            # Generate the embedding
            response = await self.client.embeddings.create(
                input=text,
                model=self.embedding_model_id,
                dimensions=self.embedding_size,
                **kwargs,
            )

            # Verify the response
            # 1. Extract the raw float array from the response object
            embedding = response.data[0].embedding

            # 2. Verify it is actually a list
            if not embedding or not isinstance(embedding, list):
                logger.error("OpenAI returned an invalid embedding format.")
                raise ValueError("Received invalid embedding format from LLM.")

            # 3. Verify the dimensions match your database requirements exactly!
            if self.embedding_size and len(embedding) != self.embedding_size:
                logger.error(f"Dimensionality mismatch! Expected {self.embedding_size}, got {len(embedding)}.")
                raise ValueError(f"Embedding dimension mismatch. Expected {self.embedding_size}.")

            # 4. Return the guaranteed, perfectly sized vector
            return embedding

        except Exception:
            logger.exception(
                f"OpenAI embedding generation failed using model '{self.embedding_model_id}' and size '{self.embedding_size}'"
            )
            raise

    async def construct_prompt(self, prompt: str, role: str) -> dict:
        return {
            "role": role,
            "content": await self.process_text(prompt),
        }

    async def process_text(self, prompt: str) -> str:
        return prompt[: self.default_max_input_characters].strip()

import logging
from typing import Dict, List

from google import genai
from google.genai import types

from helpers.decorators import validate_llm_client

from ..LLMEnums import GeminiEnum, InputTypeEnum
from ..LLMInterface import LLMInterface

logger = logging.getLogger(__name__)


class GeminiClient(LLMInterface):
    def __init__(
        self,
        api_key: str,
        default_max_input_characters: int = 8192,
        default_max_output_tokens: int = int(GeminiEnum.DEFAULT_MAX_OUTPUT_TOKENS.value),
        default_temperature: float = float(GeminiEnum.DEFAULT_TEMPERATURE.value),
    ):
        if not api_key:
            raise ValueError("A Gemini API key must be provided.")

        # Initialize the new unified Async Client
        self.client = genai.Client(api_key=api_key).aio

        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        self.DEFAULT_DIMENSIONS = GeminiEnum.DEFAULT_DIMENSIONS.value
        self.task_type_map = GeminiEnum.INPUT_TYPE_MAP.value

        self.default_max_input_characters = default_max_input_characters
        self.default_max_tokens = default_max_output_tokens
        self.default_temperature = default_temperature

        logger.info("Gemini Async Client initialized.")

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
        logger.debug(f"Gemini generation model set to: {model_id}")

    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size or self.DEFAULT_DIMENSIONS.get(model_id)
        logger.debug(f"Gemini embedding model set to: {model_id} (Size: {self.embedding_size})")

    async def construct_prompt(self, prompt: str, role: str) -> dict:
        """
        Maps standard roles to Gemini's 'user' and 'model' requirements.
        """
        role_normalized = role.strip().lower()

        if role_normalized in ["user", "human"]:
            gemini_role = GeminiEnum.USER.value
        elif role_normalized == "system":
            gemini_role = GeminiEnum.SYSTEM.value
        else:
            gemini_role = GeminiEnum.ASSISTANT.value  # 'model'

        return {
            "role": gemini_role,
            "parts": [{"text": await self.process_text(prompt)}],
        }

    async def process_text(self, prompt: str) -> str:
        return prompt[: self.default_max_input_characters].strip()

    @validate_llm_client
    async def generate_text(
        self, prompt: str, chat_history: List[Dict[str, str]] = None, max_output_tokens: int = None, **kwargs
    ) -> str:
        """
        Calls the Gemini Text Generation API.
        """
        gemini_history = []
        system_instruction = None

        if chat_history:
            for msg in chat_history:
                role = msg.get("role", GeminiEnum.USER.value)

                # Gemini handles system prompts via config, not in the standard message array
                if role.lower() == "system":
                    system_instruction = await self.process_text(msg.get("content", ""))
                    continue

                formatted_msg = await self.construct_prompt(msg.get("content", ""), role)
                gemini_history.append(formatted_msg)

        # Append the current prompt
        gemini_history.append(await self.construct_prompt(prompt, GeminiEnum.USER.value))

        # Pack everything cleanly into Gemini's GenerateContentConfig
        call_params = {
            "temperature": self.default_temperature,
            "max_output_tokens": max_output_tokens or self.default_max_tokens,
            **kwargs,
        }
        if system_instruction:
            call_params["system_instruction"] = system_instruction

        try:
            response = await self.client.models.generate_content(
                model=self.generation_model_id,
                contents=gemini_history,
                config=types.GenerateContentConfig(**call_params),
            )

            # --- OUTPUT VALIDATION ---
            content = response.text

            if not content or not isinstance(content, str) or not content.strip():
                logger.error(f"Gemini returned an empty response for model '{self.generation_model_id}'")
                raise ValueError("Received empty text response from LLM.")

            return content.strip()

        except Exception:
            logger.exception(f"Gemini text generation failed using model '{self.generation_model_id}'")
            raise

    @validate_llm_client
    async def generate_text_stream(
        self, prompt: str, chat_history: List[Dict[str, str]] = None, max_output_tokens: int = None, **kwargs
    ):
        """
        Calls the Gemini Text Generation API with streaming enabled.
        """
        gemini_history = []
        system_instruction = None

        if chat_history:
            for msg in chat_history:
                role = msg.get("role", GeminiEnum.USER.value)

                # Gemini handles system prompts via config, not in the standard message array
                if role.lower() == "system":
                    system_instruction = await self.process_text(msg.get("content", ""))
                    continue

                formatted_msg = await self.construct_prompt(msg.get("content", ""), role)
                gemini_history.append(formatted_msg)

        # Append the current prompt
        gemini_history.append(await self.construct_prompt(prompt, GeminiEnum.USER.value))

        # Pack everything cleanly into Gemini's GenerateContentConfig
        call_params = {
            "temperature": self.default_temperature,
            "max_output_tokens": max_output_tokens or self.default_max_tokens,
            **kwargs,
        }
        if system_instruction:
            call_params["system_instruction"] = system_instruction

        try:
            response = await self.client.models.generate_content_stream(
                model=self.generation_model_id,
                contents=gemini_history,
                config=types.GenerateContentConfig(**call_params),
            )

            async for chunk in response:
                if chunk.text:
                    yield {"type": "answer", "text": chunk.text}

        except Exception:
            logger.exception(f"Gemini text stream generation failed using model '{self.generation_model_id}'")
            raise

    @validate_llm_client
    async def generate_embedding(
        self, texts: list[str], input_type: str = InputTypeEnum.Document.value, **kwargs
    ) -> list[List[float]]:
        """
        Calls the Gemini Embedding API.
        """
        # Map your generic app input types to Gemini's specific TaskTypes

        gemini_task_type = self.task_type_map.get(input_type, "RETRIEVAL_DOCUMENT")

        try:
            config_params = {"task_type": gemini_task_type}
            if self.embedding_size:
                config_params["output_dimensionality"] = self.embedding_size

            response = await self.client.models.embed_content(
                model=self.embedding_model_id, contents=texts, config=types.EmbedContentConfig(**config_params)
            )

            # --- OUTPUT VALIDATION ---
            if not response.embeddings or not isinstance(response.embeddings, list):
                logger.error("Gemini returned an invalid embedding format.")
                raise ValueError("Received invalid embedding format from LLM.")

            embeddings = [embedding.values for embedding in response.embeddings]

            if self.embedding_size and len(embeddings[0]) != self.embedding_size:
                logger.error(f"Dimensionality mismatch! Expected {self.embedding_size}, got {len(embeddings[0])}.")
                raise ValueError(f"Embedding dimension mismatch. Expected {self.embedding_size}.")

            return embeddings

        except Exception:
            logger.exception(f"Gemini embedding generation failed using model '{self.embedding_model_id}'")
            raise

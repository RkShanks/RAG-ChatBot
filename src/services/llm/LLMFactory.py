import logging

from .Clients import CohereClient, GeminiClient, OpenAIClient, SparseClient
from .LLMEnums import LLMEnums
from .LLMInterface import LLMInterface

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    A Factory class to dynamically instantiate the correct LLM provider
    based on the current environment configuration.
    """

    @staticmethod
    def get_generation_client(settings) -> LLMInterface:
        """
        Reads the GENERATION_BACKEND from settings and returns the fully configured client.
        """
        backend = settings.GENERATION_BACKEND.strip().upper()
        logger.info(f"Factory initializing Generation Backend: {backend}")

        if backend == LLMEnums.OPENAI.value:
            client = OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
                default_max_input_characters=settings.GENERATION_MAX_INPUT_CHARACTERS,
                default_max_output_tokens=settings.GENERATION_MAX_OUTPUT_TOKENS,
                default_temperature=settings.GENERATION_TEMPERATURE,
            )
            client.set_generation_model(settings.GENERATION_MODEL_ID)
            return client

        elif backend == LLMEnums.COHERE.value:
            client = CohereClient(
                api_key=settings.COHERE_API_KEY,
                default_max_input_characters=settings.GENERATION_MAX_INPUT_CHARACTERS,
                default_max_output_tokens=settings.GENERATION_MAX_OUTPUT_TOKENS,
                default_temperature=settings.GENERATION_TEMPERATURE,
            )
            client.set_generation_model(settings.GENERATION_MODEL_ID)
            return client

        elif backend == LLMEnums.GEMINI.value:
            client = GeminiClient(
                api_key=settings.GEMINI_API_KEY,
                default_max_input_characters=settings.GENERATION_MAX_INPUT_CHARACTERS,
                default_max_output_tokens=settings.GENERATION_MAX_OUTPUT_TOKENS,
                default_temperature=settings.GENERATION_TEMPERATURE,
            )
            client.set_generation_model(settings.GENERATION_MODEL_ID)
            return client

        else:
            logger.critical(f"Unsupported GENERATION_BACKEND specified: {backend}")
            raise ValueError(f"Unsupported generation backend: {backend}")

    @staticmethod
    def get_embedding_client(settings) -> LLMInterface:
        """
        Reads the EMBEDDING_BACKEND from settings and returns the fully configured client.
        """
        backend = settings.EMBEDDING_BACKEND.strip().upper()
        logger.info(f"Factory initializing Embedding Backend: {backend}")

        if backend == LLMEnums.OPENAI.value:
            client = OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
            )
            client.set_embedding_model(settings.EMBEDDING_MODEL_ID)
            return client

        elif backend == LLMEnums.COHERE.value:
            client = CohereClient(
                api_key=settings.COHERE_API_KEY,
            )
            client.set_embedding_model(settings.EMBEDDING_MODEL_ID)
            return client

        elif backend == LLMEnums.GEMINI.value:
            client = GeminiClient(
                api_key=settings.GEMINI_API_KEY,
            )
            client.set_embedding_model(settings.EMBEDDING_MODEL_ID)
            return client

        else:
            logger.critical(f"Unsupported EMBEDDING_BACKEND specified: {backend}")
            raise ValueError(f"Unsupported embedding backend: {backend}")

    @staticmethod
    def get_sparse_embedding_client(settings) -> LLMInterface:
        if settings.SPARSE_CLIENT_MODEL_ID != "":
            client = SparseClient(model_name=settings.SPARSE_CLIENT_MODEL_ID)
            return client
        else:
            return SparseClient()

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

    @staticmethod
    def hot_swap_generation_client(
        backend: str,
        model_id: str,
        api_key: str,
        base_url: str = None,
        runtime_settings: dict = None,
    ) -> LLMInterface:
        """
        Create a new generation client with the provided overrides.
        Returns the new client on success, raises on failure.
        The caller is responsible for swapping app.state.generation_client.
        """
        rt = runtime_settings or {}
        max_input = rt.get("max_input_characters", 32768)
        max_output = rt.get("max_output_tokens", 32768)
        temperature = rt.get("temperature", 0.1)

        logger.info(f"Hot-swap: Creating new generation client for {backend}/{model_id}")

        if backend == LLMEnums.OPENAI.value:
            client = OpenAIClient(
                api_key=api_key,
                base_url=base_url if base_url else None,
                default_max_input_characters=max_input,
                default_max_output_tokens=max_output,
                default_temperature=temperature,
            )
            client.set_generation_model(model_id)
            return client
        elif backend == LLMEnums.COHERE.value:
            client = CohereClient(
                api_key=api_key,
                default_max_input_characters=max_input,
                default_max_output_tokens=max_output,
                default_temperature=temperature,
            )
            client.set_generation_model(model_id)
            return client
        elif backend == LLMEnums.GEMINI.value:
            client = GeminiClient(
                api_key=api_key,
                default_max_input_characters=max_input,
                default_max_output_tokens=max_output,
                default_temperature=temperature,
            )
            client.set_generation_model(model_id)
            return client
        else:
            raise ValueError(f"Unsupported generation backend: {backend}")

    @staticmethod
    def hot_swap_embedding_client(
        backend: str,
        model_id: str,
        api_key: str,
        base_url: str = None,
    ) -> LLMInterface:
        """
        Create a new embedding client with the provided overrides.
        Returns the new client on success, raises on failure.
        """
        logger.info(f"Hot-swap: Creating new embedding client for {backend}/{model_id}")

        if backend == LLMEnums.OPENAI.value:
            client = OpenAIClient(
                api_key=api_key,
                base_url=base_url if base_url else None,
            )
            client.set_embedding_model(model_id)
            return client
        elif backend == LLMEnums.COHERE.value:
            client = CohereClient(
                api_key=api_key,
            )
            client.set_embedding_model(model_id)
            return client
        elif backend == LLMEnums.GEMINI.value:
            client = GeminiClient(
                api_key=api_key,
            )
            client.set_embedding_model(model_id)
            return client
        else:
            raise ValueError(f"Unsupported embedding backend: {backend}")

import logging
import inspect
from functools import wraps

logger = logging.getLogger(__name__)


def validate_llm_client(func):
    """
    Smart decorator to ensure the LLM client and the appropriate
    model IDs are initialized before running generation methods.
    """

    if inspect.isasyncgenfunction(func):
        @wraps(func)
        async def async_gen_wrapper(self, *args, **kwargs):
            # 1. Core Validation: Check if the client exists
            if getattr(self, "client", None) is None:
                logger.critical(f"Validation Failed: Cannot run '{func.__name__}' because self.client is None.")
                raise ValueError("LLM Client is not initialized.")

            # 2. Contextual Validation: Text Generation
            if func.__name__ in ("generate_text", "generate_text_stream"):
                if not getattr(self, "generation_model_id", None):
                    logger.critical(
                        f"Validation Failed: Cannot run '{func.__name__}' because generation_model_id is missing."
                    )
                    raise ValueError("Text generation model ID is not configured.")

            # 3. Contextual Validation: Embedding Generation
            elif func.__name__ == "generate_embedding":
                if not getattr(self, "embedding_model_id", None):
                    logger.critical(
                        f"Validation Failed: Cannot run '{func.__name__}' because embedding_model_id is missing."
                    )
                    raise ValueError("Embedding model ID is not configured.")

            # Execute the actual async generator
            async for chunk in func(self, *args, **kwargs):
                yield chunk

        return async_gen_wrapper

    else:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 1. Core Validation: Check if the client exists
            if getattr(self, "client", None) is None:
                logger.critical(f"Validation Failed: Cannot run '{func.__name__}' because self.client is None.")
                raise ValueError("LLM Client is not initialized.")

            # 2. Contextual Validation: Text Generation
            if func.__name__ in ("generate_text", "generate_text_stream"):
                if not getattr(self, "generation_model_id", None):
                    logger.critical(
                        f"Validation Failed: Cannot run '{func.__name__}' because generation_model_id is missing."
                    )
                    raise ValueError("Text generation model ID is not configured.")

            # 3. Contextual Validation: Embedding Generation
            elif func.__name__ == "generate_embedding":
                if not getattr(self, "embedding_model_id", None):
                    logger.critical(
                        f"Validation Failed: Cannot run '{func.__name__}' because embedding_model_id is missing."
                    )
                    raise ValueError("Embedding model ID is not configured.")

            # If all security checks pass, execute the actual function!
            return await func(self, *args, **kwargs)

        return wrapper

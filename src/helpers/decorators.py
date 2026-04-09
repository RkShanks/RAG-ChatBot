import inspect
import logging
from functools import wraps

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal

logger = logging.getLogger(__name__)


def _run_validation_checks(instance, func_name: str):
    """
    Internal helper to DRY up the validation logic.
    Throws a CustomAPIException if the LLM client is missing required configuration.
    """
    # 1. Core Validation: Check if the client exists
    if getattr(instance, "client", None) is None:
        raise CustomAPIException(
            signal_enum=ResponseSignal.LLM_CONFIGURATION_ERROR,
            status_code=500,
            dev_detail=f"Validation Failed: Cannot run '{func_name}' because self.client is None.",
        )

    # 2. Contextual Validation: Text Generation
    if func_name in ("generate_text", "generate_text_stream"):
        if not getattr(instance, "generation_model_id", None):
            raise CustomAPIException(
                signal_enum=ResponseSignal.LLM_CONFIGURATION_ERROR,
                status_code=500,
                dev_detail=f"Validation Failed: Cannot run '{func_name}' because generation_model_id is missing.",
            )

    # 3. Contextual Validation: Embedding Generation
    elif func_name == "generate_embedding":
        if not getattr(instance, "embedding_model_id", None):
            raise CustomAPIException(
                signal_enum=ResponseSignal.LLM_CONFIGURATION_ERROR,
                status_code=500,
                dev_detail=f"Validation Failed: Cannot run '{func_name}' because embedding_model_id is missing.",
            )


def validate_llm_client(func):
    """
    Smart decorator to ensure the LLM client and the appropriate
    model IDs are initialized before running generation methods.
    """

    if inspect.isasyncgenfunction(func):

        @wraps(func)
        async def async_gen_wrapper(self, *args, **kwargs):
            # Run the unified validation checks
            _run_validation_checks(self, func.__name__)

            # Execute the actual async generator
            async for chunk in func(self, *args, **kwargs):
                yield chunk

        return async_gen_wrapper

    else:

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Run the unified validation checks
            _run_validation_checks(self, func.__name__)

            # If all security checks pass, execute the actual function!
            return await func(self, *args, **kwargs)

        return wrapper

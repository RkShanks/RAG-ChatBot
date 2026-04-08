import logging

from .Clients import CohereRankerClient, LocalRankerClient
from .RankerEnums import CohereEnum, LocalEnum, RankerEnums
from .RankerInterface import RankerInterface

logger = logging.getLogger(__name__)


class RankerFactory:
    @staticmethod
    def get_ranker_client(settings) -> RankerInterface:
        backend = getattr(settings, "RERANKER_BACKEND", "").strip().upper()
        logger.info(f"Factory initializing Reranker Backend: '{backend}'")

        if backend == RankerEnums.COHERE.value:
            return CohereRankerClient(
                api_key=settings.COHERE_API_KEY,
                model_id=getattr(settings, "RERANKER_MODEL_ID", None) or CohereEnum.DEFAULT_MODEL_ID.value,
            )

        elif backend == RankerEnums.LOCAL.value:
            return LocalRankerClient(
                model_id=getattr(settings, "RERANKER_MODEL_ID", None) or LocalEnum.DEFAULT_MODEL_ID.value
            )

        elif backend == "" or backend is None:
            logger.warning("RERANKER_BACKEND is not set. No reranker will be used.")
            return None
        else:
            logger.error(f"Unsupported RERANKER_BACKEND: {backend}")
            raise ValueError(f"Unsupported reranker backend: {backend}")

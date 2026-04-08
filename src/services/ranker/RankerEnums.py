from enum import Enum


class RankerEnums(Enum):
    COHERE = "COHERE"
    LOCAL = "LOCAL"


class CohereEnum(Enum):
    DEFAULT_MODEL_ID = "rerank-v4.0-fast"


class LocalEnum(Enum):
    DEFAULT_MODEL_ID = "Alibaba-NLP/gte-multilingual-reranker-base"

from enum import Enum


class LLMEnums(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"


class OPENAIEnum(Enum):
    DEFAULT_MODEL_ID = "gpt-4o"
    DEFAULT_MAX_TOKENS = 2048
    DEFAULT_TEMPERATURE = 0.1

    DEFAULT_EMBEDDING_MODEL_ID = "text-embedding-3-small"
    DEFAULT_EMBEDDING_SIZE = 1536

    DEFAULT_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

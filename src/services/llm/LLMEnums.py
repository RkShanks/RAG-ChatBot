from enum import Enum


class LLMEnums(Enum):
    OPENAI = "OPENAI"
    GEMINI = "GEMINI"
    COHERE = "COHERE"
    LOCAL = "LOCAL"


class OPENAIEnum(Enum):
    GENERATION_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
    ]

    EMBEDDING_MODELS = [
        "text-embedding-3-small",
        "text-embedding-3-large",
        "text-embedding-ada-002",
    ]

    DEFAULT_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class CohereEnum(Enum):
    GENERATION_MODELS = [
        "command-r-plus",
        "command-r",
        "command-light",
    ]

    EMBEDDING_MODELS = [
        "embed-english-v3.0",
        "embed-multilingual-v3.0",
        "embed-english-light-v3.0",
        "embed-multilingual-light-v3.0",
    ]

    DEFAULT_DIMENSIONS = {
        "embed-english-v3.0": 1024,
        "embed-multilingual-v3.0": 1024,
        "embed-english-light-v3.0": 384,
        "embed-multilingual-light-v3.0": 384,
    }

    INPUT_TYPE_MAP = {
        "document": "search_document",
        "query": "search_query",
    }
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class GeminiEnum(Enum):
    GENERATION_MODELS = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ]

    EMBEDDING_MODELS = [
        "gemini-embedding-001",
        "text-embedding-004",
        "gemini-embedding-2-preview",
    ]

    DEFAULT_MODEL_ID = "gemini-2.5-flash"
    DEFAULT_MAX_OUTPUT_TOKENS = 2048
    DEFAULT_TEMPERATURE = 0.1

    DEFAULT_EMBEDDING_MODEL_ID = "gemini-embedding-2-preview"
    DEFAULT_EMBEDDING_SIZE = 768

    # Gemini 2 embeddings natively output 3072 dimensions, but use MRL
    # (Matryoshka Representation Learning) to safely truncate down to 768 or 256.
    DEFAULT_DIMENSIONS = {
        "gemini-embedding-001": 768,
        "text-embedding-004": 768,
        "gemini-embedding-2-preview": 3072,
    }

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "model"  # Gemini's required keyword for the AI

    INPUT_TYPE_MAP = {
        "document": "RETRIEVAL_DOCUMENT",
        "query": "RETRIEVAL_QUERY",
        "classification": "CLASSIFICATION",
        "clustering": "CLUSTERING",
    }


class InputTypeEnum(Enum):
    Document = "document"
    Query = "query"
    Classification = "classification"
    Clustering = "clustering"

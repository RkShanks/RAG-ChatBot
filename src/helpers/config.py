from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    WIKI_USER_AGENT: str
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str
    FILE_EXTENSIONS: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int
    MONGODB_URI: str
    MONGODB_DB_NAME: str

    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    # 2. Provider Secrets
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = None
    COHERE_API_KEY: str
    GEMINI_API_KEY: str

    # 3. Generation Tuning Parameters  # or "command-r"
    GENERATION_MODEL_ID: str
    GENERATION_MAX_INPUT_CHARACTERS: int
    GENERATION_MAX_OUTPUT_TOKENS: int
    GENERATION_TEMPERATURE: float

    # 4. Embedding Tuning Parameters
    EMBEDDING_MODEL_ID: str
    EMBEDDING_MODEL_SIZE: int
    EMBEDDING_MODEL_MAX_TOKEN: int

    VECTOR_DB_BACKEND: str
    SPARSE_CLIENT_MODEL_ID: str

    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_PATH: str

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()

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

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()

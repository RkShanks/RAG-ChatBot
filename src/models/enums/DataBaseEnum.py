from enum import Enum


class DataBaseEnum(str, Enum):
    COLLECTION_PROJECT_NAME = "projects"
    COLLECTION_DATA_CHUNKS_NAME = "data_chunks"

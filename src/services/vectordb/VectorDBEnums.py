from enum import Enum


class VectorDBEnums(Enum):
    QDRANT = "QDRANT"
    MONGODB = "MONGODB"


class DistanceMetricEnum(Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"

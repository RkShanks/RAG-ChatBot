from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from models.db_schemes import DocumentChunk


class VectorDBInterface(ABC):
    """
    The strict contract for any Vector Database provider in the RAG system.
    Whether using MongoDB Atlas or Qdrant, the client must implement these methods.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish a connection to the database.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Safely close the database connection to prevent memory leaks.
        """
        pass

    @abstractmethod
    async def is_collection_exist(self, collection_name: str) -> bool:
        """
        Check if a collection exists in the database.
        """
        pass

    @abstractmethod
    async def list_all_collections(self) -> List:
        """
        List all collections in the database.
        """
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> Dict:
        """
        Get information about a specific collection.

        Args:
            collection_name (str): The name of the collection/index.

        Returns:
            Dict: Information about the collection.
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from the database.

        Args:
            collection_name (str): The name of the collection/index.
        """
        pass

    @abstractmethod
    async def create_collection(
        self, collection_name: str, vector_size: int, distance_metric: str = "cosine", do_reset: bool = False
    ) -> bool:
        """
        Create a new collection (or index) to store vector embeddings.

        Args:
            collection_name (str): The name of the collection/index.
            vector_size (int): The dimensionality of the vectors (e.g., 768 or 1024).
            distance_metric (str): The metric used to calculate similarity (cosine, dot, euclidean).
            do_reset (bool): Whether to reset the collection if it already exists.

        Returns:
            bool: True if the collection was successfully created, False otherwise.

        """
        pass

    @abstractmethod
    async def insert_one(self, collection_name: str, document: DocumentChunk) -> bool:
        """
        Insert chunked document and its vector embeddings into the database.

        Args:
            collection_name (str): The name of the collection/index.
            document (DocumentChunk): The strictly validated Pydantic document object.

        Returns:
            bool: True if the document was successfully inserted, False otherwise.
        """
        pass

    @abstractmethod
    async def insert_many(self, collection_name: str, documents: List[DocumentChunk], batch_size: int = 100) -> int:
        """
        Insert chunked documents and their vector embeddings into the database.

        Args:
            collection_name (str): The name of the collection/index.
            documents (List[DocumentChunk]): A list of DocumentChunk to be inserted.
            batch_size (int): The number of documents to insert in each batch.

        Returns:
            int: The total number of documents failed to be inserted.

        """
        pass

    @abstractmethod
    async def search_by_vector(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None,
        sparse_query_vector: Optional[Dict[str, List]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform a semantic vector search to retrieve the most relevant document chunks.

        Args:
            collection_name (str): The collection to search inside.
            query_vector (List[float]): The embedded user prompt.
            limit (int): The maximum number of chunks to return (K).
            filter_criteria (dict): Optional metadata filters (e.g., {"source": "math.pdf"}).
            sparse_query_vector (dict): Optional sparse vector filter (e.g., {"indices": [1, 2, 3], "values": [0.1, 0.2, 0.3]})

        Returns:
            A list of dictionaries containing the retrieved chunks, scores, and metadata.
        """
        pass

    def is_sparse_needed(self) -> bool:
        """ "

        Indicates whether the vector database implementation requires sparse vectors for hybrid search.

        Returns:
            bool: True if sparse vectors are needed, False otherwise.
        """
        pass

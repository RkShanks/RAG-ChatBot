import logging
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient, models

from models.db_schemes import DocumentChunk

from ..VectorDBEnums import DistanceMetricEnum
from ..VectorDBInterface import VectorDBInterface

logger = logging.getLogger(__name__)


class QdrantClient(VectorDBInterface):
    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str = None,
        path: Optional[str] = None,
    ):
        self.url = url
        self.api_key = api_key
        self.path = path
        self.client: Optional[AsyncQdrantClient] = None
        self.qdrant_metric_map = {
            "cosine": models.Distance.COSINE,
            "dot": models.Distance.DOT,
            "euclidean": models.Distance.EUCLID,
        }

    async def connect(self) -> None:
        try:
            # 1. Connect via Local File Path (No Docker needed!)
            if self.path:
                self.client = AsyncQdrantClient(path=self.path)
                logger.info(f"Successfully connected to local Qdrant at path: {self.path}")

            # 2. Connect via Cloud/Docker URL
            elif self.url:
                self.client = AsyncQdrantClient(url=self.url, api_key=self.api_key)
                logger.info(f"Successfully connected to Qdrant at URL: {self.url}")

            # 3. Fallback: Connect entirely In-Memory (Great for unit tests)
            else:
                self.client = AsyncQdrantClient(location=":memory:")
                logger.warning("Connected to Qdrant IN-MEMORY. Data will be lost on restart.")

        except Exception:
            logger.exception("Failed to connect to Qdrant")
            raise

    async def disconnect(self) -> None:
        try:
            await self.client.close()
            self.client = None
            logger.info("Successfully disconnected from Qdrant")
        except Exception:
            logger.exception("Failed to disconnect from Qdrant")
            raise

    async def is_collection_exist(self, collection_name: str) -> bool:
        try:
            collection = await self.client.collection_exists(collection_name=collection_name)
            return collection
        except Exception:
            logger.exception(f"Failed to check if collection '{collection_name}' exists")
            raise

    async def list_all_collections(self) -> List:
        try:
            response = await self.client.get_collections()
            logger.info("Successfully listed all collections")
            return response

        except Exception:
            logger.exception("Failed to list all collections")
            raise

    async def get_collection_info(self, collection_name: str) -> Dict:
        try:
            info = await self.client.get_collection(collection_name=collection_name)
            logger.info(f"Successfully retrieved collection info for collection '{collection_name}'")
            return info.model_dump()
        except Exception:
            logger.exception(f"Failed to retrieve collection info for collection '{collection_name}'")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        try:
            if await self.is_collection_exist(collection_name):
                await self.client.delete_collection(collection_name=collection_name)
                logger.info(f"Deleted collection: {collection_name}")
                return True
            logger.info(f"Collection: {collection_name} does not exist")
            return False
        except Exception:
            logger.exception(f"Failed to delete collection: {collection_name}")
            raise

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = DistanceMetricEnum.COSINE.value,
        do_reset: bool = False,
    ) -> bool:
        logger.debug(f"Creating collection: {collection_name}")
        if await self.is_collection_exist(collection_name):
            if do_reset:
                logger.warning(f"Resetting collection '{collection_name}'...")
                await self.delete_collection(collection_name)
            else:
                logger.info(f"Collection '{collection_name}' already exists.")
                return True

        # Map string metrics to Qdrant Enums
        qdrant_metric = self.qdrant_metric_map.get(distance_metric.lower(), models.Distance.COSINE)

        # ------------------------------------------------------------------
        # THE HYBRID SEARCH CONFIGURATION
        # We define multiple vectors: 'dense' (LLM) and 'sparse' (Keywords)
        # ------------------------------------------------------------------
        vectors_config = {
            "dense": models.VectorParams(
                size=vector_size,
                distance=qdrant_metric,
            ),
        }
        sparse_vectors_config = {
            "sparse": models.SparseVectorParams(
                modifier=models.Modifier.IDF,  # Standard configuration for keyword sparse vectors
            )
        }
        try:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
            )
            logger.info(f"Created Hybrid-ready collection: {collection_name} (Size: {vector_size})")
            return True

        except Exception:
            logger.exception(f"Failed to create collection: {collection_name}")
            raise

    async def insert_one(self, collection_name: str, document: DocumentChunk) -> bool:
        return await self.insert_many(collection_name, [document])

    async def insert_many(self, collection_name: str, documents: List[DocumentChunk], batch_size: int = 100) -> bool:
        logger.debug(f"Inserting {len(documents)} documents into collection: {collection_name}")

        if not await self.is_collection_exist(collection_name):
            logger.warning(f"Collection {collection_name} does not exist.")
            return False

        points = self.documents_to_points(documents)
        failed_inserts = 0
        # Batch insert to protect memory and network
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            try:
                await self.client.upsert(
                    collection_name=collection_name,
                    points=batch,
                )
            except Exception:
                failed_inserts += len(batch)
                logger.exception(f"Failed to insert batch number {i // batch_size} into {collection_name}.")
                continue

        logger.info(f"Inserted {len(documents)} chunks into {collection_name} with failed inserts: {failed_inserts}")
        return True

    def documents_to_points(self, documents: List[DocumentChunk]) -> List[models.PointStruct]:

        points = []
        for doc in documents:
            # Pydantic guarantees the ID exists!
            point_id = doc.id

            payload = doc.metadata.copy()
            payload["text"] = doc.text

            # Grab the dense vector
            vector_payload = {"dense": doc.vector}

            # If the optional sparse vector exists, attach it
            if doc.sparse_vector:
                vector_payload["sparse"] = models.SparseVector(
                    indices=doc.sparse_vector["indices"],
                    values=doc.sparse_vector["values"],
                )

            points.append(
                models.PointStruct(
                    id=point_id,
                    payload=payload,
                    vector=vector_payload,
                )
            )

        return points

    async def search_by_vector(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None,
        sparse_query_vector: Optional[Dict[str, List]] = None,
    ) -> List[Dict[str, Any]]:

        # 1. Handle Metadata Filters
        query_filter = self.create_query_filter(filter_criteria)
        # 2. HYBRID SEARCH ROUTING (Dense Only vs. Dense + Sparse)
        if sparse_query_vector:
            # Create a Fusion Query using RRF (Reciprocal Rank Fusion)
            prefetch = [
                models.Prefetch(
                    query=query_vector,
                    using="dense",
                    limit=limit * 2,  # Fetch more for better fusion ranking
                    filter=query_filter,
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_query_vector["indices"],
                        values=sparse_query_vector["values"],
                    ),
                    using="sparse",
                    limit=limit * 2,
                    filter=query_filter,
                ),
            ]

            # The new Qdrant Query API merges the prefetch lists
            try:
                logger.debug(f"Performing hybrid search for collection: {collection_name}")
                results = await self.client.query_points(
                    collection_name=collection_name,
                    prefetch=prefetch,
                    query=models.FusionQuery(fusion=models.Fusion.RRF),
                    limit=limit,
                )
            except Exception:
                logger.exception(f"Failed to perform hybrid search for collection: {collection_name}")
                raise

        else:
            # Standard Dense Search (If no sparse keywords were provided)
            try:
                logger.debug(f"Performing dense search for collection: {collection_name}")
                results = await self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    using="dense",
                    query_filter=query_filter,
                    limit=limit,
                )
            except Exception:
                logger.exception(f"Failed to perform dense search for collection: {collection_name}")
                raise

        # 3. Standardize Output format for your application
        formatted_results = []
        for point in results.points:
            formatted_results.append(
                {
                    "id": str(point.id),
                    "score": point.score,
                    "text": point.payload.get("text", ""),
                    "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                }
            )

        return formatted_results

    def create_query_filter(self, filter_criteria: Optional[Dict[str, Any]]) -> Optional[models.Filter]:
        query_filter = None
        if filter_criteria:
            must_conditions = []
            for key, value in filter_criteria.items():
                must_conditions.append(models.FieldCondition(key=key, match=models.MatchValue(value=value)))
            query_filter = models.Filter(must=must_conditions)

        return query_filter

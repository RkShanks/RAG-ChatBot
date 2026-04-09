import logging
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.operations import SearchIndexModel

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal
from models.db_schemes import DocumentChunk

from ..VectorDBEnums import DistanceMetricEnum
from ..VectorDBInterface import VectorDBInterface

logger = logging.getLogger(__name__)


class MongoDBClient(VectorDBInterface):
    def __init__(self, uri: str, db_name: str, existing_mongo_db=None):
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = existing_mongo_db
        self.metric_map = {
            "cosine": "cosine",
            "dot": "dotProduct",
            "euclidean": "euclidean",
        }

    async def connect(self) -> None:
        if self.db:
            return
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            logger.info(f"Successfully connected to MongoDB Atlas: Database '{self.db_name}'")

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.DB_CONNECTION_FAILED,
                status_code=503,
                dev_detail=f"Failed to connect to MongoDB Atlas at URI: {self.uri}",
            ) from e

    async def disconnect(self) -> None:
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.db = None
                logger.info("Successfully disconnected from MongoDB Atlas")

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.INTERNAL_SERVER_ERROR,
                status_code=500,
                dev_detail="Failed to gracefully disconnect from MongoDB Atlas.",
            ) from e

    async def is_collection_exist(self, collection_name: str) -> bool:
        try:
            collections = await self.db.list_collection_names()
            return collection_name in collections

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.DB_CONNECTION_FAILED,
                status_code=503,
                dev_detail=f"Failed to fetch collection names to check if '{collection_name}' exists.",
            ) from e

    async def list_all_collections(self) -> List[str]:
        try:
            response = await self.db.list_collection_names()
            logger.info("Successfully listed all collections")
            return response

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.COLLECTION_INFO_FAILED,
                status_code=503,
                dev_detail="Failed to list all collections in MongoDB.",
            ) from e

    async def get_collection_info(self, collection_name: str) -> Dict:
        try:
            collection = self.db[collection_name]
            count = await collection.count_documents({})
            logger.info(f"Successfully retrieved info for collection '{collection_name}'")
            return {"collection_name": collection_name, "document_count": count}

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.COLLECTION_INFO_FAILED,
                status_code=500,
                dev_detail=f"Failed to retrieve collection info for '{collection_name}'.",
            ) from e

    async def delete_collection(self, collection_name: str) -> bool:
        try:
            if await self.is_collection_exist(collection_name):
                await self.db.drop_collection(collection_name)
                logger.info(f"Deleted MongoDB collection: {collection_name}")
                return True
            logger.info(f"Collection: {collection_name} does not exist")
            return False

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.COLLECTION_DELETION_FAILED,
                status_code=500,
                dev_detail=f"Failed to delete MongoDB collection: {collection_name}",
            ) from e

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

        try:
            await self.db.create_collection(collection_name)
            mongo_metric = self.metric_map.get(distance_metric.lower(), "cosine")

            index_name = f"{collection_name}_vector_index"
            search_index_model = SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "path": "vector",
                            "numDimensions": vector_size,
                            "similarity": mongo_metric,
                        },
                        {"type": "filter", "path": "metadata"},
                    ]
                },
                name=index_name,
                type="vectorSearch",
            )
            await self.db[collection_name].create_search_index(model=search_index_model)
            logger.info(f"Created collection '{collection_name}' and Vector Index '{index_name}'.")
            return True

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.COLLECTION_CREATION_FAILED,
                status_code=500,
                dev_detail=f"Failed to create collection or vector index for '{collection_name}'.",
            ) from e

    async def insert_one(self, collection_name: str, document: DocumentChunk) -> bool:
        return await self.insert_many(collection_name, [document])

    async def insert_many(self, collection_name: str, documents: List[DocumentChunk], batch_size: int = 100) -> bool:
        logger.debug(f"Inserting {len(documents)} documents into collection: {collection_name}")

        if not await self.is_collection_exist(collection_name):
            logger.warning(f"Collection {collection_name} does not exist.")
            return False

        collection = self.db[collection_name]
        mongo_docs = self.documents_to_mongo_docs(documents)
        failed_inserts = 0

        # Batch insert to protect memory and network
        for i in range(0, len(mongo_docs), batch_size):
            batch = mongo_docs[i : i + batch_size]
            try:
                await collection.insert_many(batch)

            except Exception as e:
                failed_inserts += len(batch)
                # Replaced logger.exception with logger.error to avoid spamming stack traces
                logger.error(f"Failed to insert batch {i // batch_size} into {collection_name}. Error: {str(e)}")
                continue

        logger.info(
            f"Inserted {len(documents) - failed_inserts} chunks into {collection_name}. Failed: {failed_inserts}"
        )
        return True

    def documents_to_mongo_docs(self, documents: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """Sync helper to convert strictly validated Pydantic models into MongoDB dictionaries."""
        mongo_docs = []
        for doc in documents:
            doc_dict = doc.model_dump(exclude_none=True)
            # MongoDB strictly requires '_id' instead of 'id'
            doc_dict["_id"] = doc_dict.pop("id")
            mongo_docs.append(doc_dict)
        return mongo_docs

    def create_query_filter(self, filter_criteria: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Sync helper to translate standard app filters into MongoDB specific filters."""
        if not filter_criteria:
            return None

        filter_dict = {}
        for key, value in filter_criteria.items():
            filter_dict[f"metadata.{key}"] = {"$eq": value}
        return filter_dict

    async def search_by_vector(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None,
        sparse_query_vector: Optional[Dict[str, List]] = None,
    ) -> List[Dict[str, Any]]:

        try:
            collection = self.db[collection_name]
            index_name = f"{collection_name}_vector_index"
            query_filter = self.create_query_filter(filter_criteria)

            vector_search_stage = {
                "$vectorSearch": {
                    "index": index_name,
                    "path": "vector",
                    "queryVector": query_vector,
                    "numCandidates": limit * 10,
                    "limit": limit,
                }
            }

            if query_filter:
                vector_search_stage["$vectorSearch"]["filter"] = query_filter

            pipeline = [
                vector_search_stage,
                {
                    "$project": {
                        "vector": 0,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]

            # MongoDB handles hybrid search via native text indexing, not sparse math arrays.
            if sparse_query_vector:
                logger.debug(
                    "sparse_query_vector passed to MongoDB. Ignoring, as Atlas uses native Lucene text search."
                )

            logger.debug(f"Performing vector search for collection: {collection_name}")
            cursor = collection.aggregate(pipeline)
            results = []

            async for doc in cursor:
                # Revert '_id' back to 'id' to match the GenZ School app standards
                doc["id"] = doc.pop("_id")
                results.append(doc)

            return results

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.NLP_SEARCH_FAILED,
                status_code=503,
                dev_detail=f"Vector aggregation pipeline failed on collection '{collection_name}'.",
            ) from e

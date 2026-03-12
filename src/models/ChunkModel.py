import logging
from typing import Any, List

from bson import ObjectId
from pymongo.errors import BulkWriteError

from .BaseDataModel import BaseDataModel
from .db_schemes import Asset, DataChunk, Project
from .enums.DataBaseEnum import DataBaseEnum

logger = logging.getLogger(__name__)


class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_DATA_CHUNKS_NAME.value]
        self.document_class = DataChunk

    async def create_data_chunk(self, chunk_data: DataChunk) -> DataChunk:
        logger.debug(
            f"Creating data chunk for project_id: {chunk_data.chunk_project_id} with index: {chunk_data.chunk_index}"
        )

        # Convert the Pydantic model to a dictionary, excluding None values and using aliases
        chunk = chunk_data.model_dump(by_alias=True, exclude_none=True)
        try:
            result = await self.collection.insert_one(chunk)
            chunk_data.id = str(result.inserted_id)
            logger.info(f"Chunk created for project {chunk_data.chunk_project_id} (MongoDB ID: {result.inserted_id})")
            return chunk_data

        except Exception:
            logger.exception(f"Error creating data chunk for project_id: {chunk_data.chunk_project_id}")
            raise

    async def get_chunk(self, chunk_id: str) -> List[DataChunk]:
        logger.debug(f"Retrieving chunk with ID: {chunk_id}")

        try:
            cursor = self.collection.find({"_id": ObjectId(chunk_id)})
            raw_chunks = await cursor.to_list(length=None)
            chunks = [DataChunk.model_validate(doc) for doc in raw_chunks]
            logger.info(f"Retrieved {len(chunks)} chunks for chunk_id: {chunk_id}")
            return chunks
        except Exception:
            logger.exception(f"Error retrieving chunk with ID: {chunk_id}")
            raise

    async def clean_chunks(self, chunks: List[Any], project: Project, asset: Asset) -> List[DataChunk]:
        logger.debug(f"Cleaning {len(chunks)} chunks for project_id: {project.id}")
        chunks_record = []

        for index, chunk in enumerate(chunks):
            # Safely peek into dl_meta strictly for the headings
            dl_meta = chunk.metadata.get("dl_meta", {})

            # Docling sometimes puts headings at the top level, sometimes inside dl_meta.
            # This safely checks both places.
            raw_headings = chunk.metadata.get("headings", dl_meta.get("headings", []))

            # Format headings into a clean string for the LLM (e.g., "Chapter 1 > Introduction")
            heading_str = " > ".join(raw_headings) if isinstance(raw_headings, list) else str(raw_headings)

            #  Build a strictly controlled, 100% safe metadata dictionary
            safe_metadata = {
                "source": chunk.metadata.get("source", "unknown"),
                # LangChain sometimes uses "page", Docling sometimes uses "page_no".
                # This safely checks both and defaults to 0.
                "page_number": chunk.metadata.get("page_no", chunk.metadata.get("page", 0)),
                "heading": heading_str,
                "title": chunk.metadata.get("title", ""),
            }

            # Create the Pydantic model and append it to the list
            chunks_record.append(
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=safe_metadata,
                    chunk_index=index + 1,
                    chunk_project_id=project.id,
                    chunk_asset_id=asset.id,
                )
            )
        logger.info(f"Cleaned {len(chunks_record)} chunks for project_id: {project.id}")
        return chunks_record

    async def insert_chunks(self, chunks: List[DataChunk], batch_size: int = 100) -> int:
        logger.debug(f"Inserting {len(chunks)} chunks into the database with batch size: {batch_size}")

        total_inserted = 0
        for i in range(0, len(chunks), batch_size):
            chunk_dicts = [
                chunks[j].model_dump(by_alias=True, exclude_none=True)
                for j in range(i, min(i + batch_size, len(chunks)))
            ]

            if chunk_dicts:
                try:
                    # Try to insert the batch
                    result = await self.collection.insert_many(chunk_dicts)
                    total_inserted += len(result.inserted_ids)

                except BulkWriteError as bwe:
                    # This catches specific MongoDB batch errors (like duplicate IDs) and contains the exact chunk that caused the crash
                    logger.error(f"BulkWriteError on batch {i}: {bwe.details}")
                    raise

                except Exception:
                    # Catch any network drops or unexpected crashes
                    logger.exception(f"Unexpected database error on batch {i}")
                    raise

        logger.info(f"Successfully inserted {total_inserted} total chunks.")
        return total_inserted

    async def delete_chunks_by_project_id(self, project_id: ObjectId) -> int:
        logger.debug(f"Deleting chunks for project_id: {project_id}")
        try:
            result = await self.collection.delete_many({"chunk_project_id": project_id})
            logger.info(f"Deleted {result.deleted_count} chunks for project_id: {project_id}")
            return result.deleted_count
        except Exception:
            logger.exception(f"Error deleting chunks for project_id: {project_id}")
            raise

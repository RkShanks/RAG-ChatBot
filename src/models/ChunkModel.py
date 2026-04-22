import logging
from typing import Any, Dict, List, Optional

from .db_schemes import Asset, DataChunk, DocumentChunk, Project

logger = logging.getLogger(__name__)


class ChunkModel:
    def __init__(self, vector_db_client):
        self.vector_db_client = vector_db_client
        self.document_class = DataChunk

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

            # Page lives at: dl_meta → doc_items[0] → prov[0] → page_no (1-indexed)
            try:
                page_number = dl_meta["doc_items"][0]["prov"][0]["page_no"]
            except (KeyError, IndexError, TypeError):
                page_number = 0  # absent for non-paginated formats (MD, TXT, HTML)

            #  Build a strictly controlled, 100% safe metadata dictionary
            safe_metadata = {
                "source": chunk.metadata.get("source", "unknown"),
                "page_number": page_number,
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

    async def insert_chunks(
        self,
        collection_name: str,
        chunks: List[DocumentChunk],
        batch_size: int = 100,
    ) -> int:
        """
        Inserts a list of chunks into the vector database in batches.
        :param collection_name: The name of the collection to insert chunks into.
        :param chunks: A list of DocumentChunk objects to be inserted.
        :param batch_size: The number of chunks to insert in each batch.
        :return: The total number of chunks successfully inserted.

        """
        logger.debug(f"Inserting {len(chunks)} chunks into the database with batch size: {batch_size}")

        total_failed_inserts = await self.vector_db_client.insert_many(
            collection_name=collection_name, documents=chunks, batch_size=batch_size
        )
        total_inserted = len(chunks) - total_failed_inserts

        logger.info(f"Successfully inserted {total_inserted} chunks. {total_failed_inserts} chunks failed to insert.")
        return total_inserted

    async def delete_chunks_by_collection_name(self, collection_name: str) -> bool:
        """
        Deletes all chunks associated with a given collection name from the vector database.
        :param collection_name: The name of the collection to delete chunks from.
        :return: True if the collection_name was exist, False otherwise.
        """
        logger.debug(f"Deleting chunks for collection_name: {collection_name}")

        result = await self.vector_db_client.delete_collection(collection_name=collection_name)

        logger.info(f"Deleted collection: {collection_name}")
        return result

    async def delete_chunks_by_asset_id(self, collection_name: str, asset_id: str) -> bool:
        """
        Deletes securely all chunks associated with a specific file (asset) inside the Vector DB.
        """
        logger.debug(f"Deleting all chunks for asset '{asset_id}' inside collection '{collection_name}'")
        filter_criteria = {"chunk_asset_id": asset_id}
        result = await self.vector_db_client.delete_points_by_filter(
            collection_name=collection_name, 
            filter_criteria=filter_criteria
        )
        logger.info(f"Deletion signals routed for asset_id: {asset_id} in {collection_name}")
        return result

    async def create_document_chunks(
        self,
        chunk: DataChunk,
        vectors: List[float],
        sparse_vectors: Optional[Dict[str, List]] = None,
    ) -> DocumentChunk:
        """
        Converts DataChunk objects into DocumentChunk objects for vector database insertion.
        :param chunk: The DataChunk object to be converted.
        :param vectors: The dense vector embedding for the chunk.
        :param sparse_vectors: The optional sparse vector embedding for the chunk.
        :return: A DocumentChunk object ready for the vector database.

        """
        meta_data = chunk.chunk_metadata
        meta_data["chunk_index"] = chunk.chunk_index
        meta_data["chunk_project_id"] = str(chunk.chunk_project_id)
        meta_data["chunk_asset_id"] = str(chunk.chunk_asset_id)
        return DocumentChunk(
            text=chunk.chunk_text,
            vector=vectors,
            sparse_vector=sparse_vectors if sparse_vectors else None,
            metadata=meta_data,
        )

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = "cosine",
        do_reset: bool = False,
    ) -> bool:
        """
        Creates a new collection in the vector database.
        :param collection_name: The name of the collection to create.
        :param vector_size: The size of the dense
        :param distance_metric: The distance metric to use for the collection.
        :param do_reset: Whether to reset the collection if it already exists.
        :return: True if the collection was successfully created, False otherwise.
        """
        logger.debug(f"Creating collection: {collection_name}")

        result = await self.vector_db_client.create_collection(
            collection_name=collection_name,
            vector_size=vector_size,
            distance_metric=distance_metric,
            do_reset=do_reset,
        )

        logger.info(f"Created collection: {collection_name}")
        return result

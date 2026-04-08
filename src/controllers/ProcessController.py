import asyncio
import logging
import os
from typing import List

from docling.chunking import HybridChunker
from fastapi import status
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType

from models import AssetModel, AssetTypeEnum, ChunkModel, ProjectModel, ResponseSignal
from models.db_schemes import DataChunk, DocumentChunk
from services.llm import InputTypeEnum, LLMInterface
from services.vectordb import VectorDBEnums, VectorDBInterface

from .BaseController import BaseController
from .ProjectController import ProjectController

logger = logging.getLogger(__name__)


class ProcessController(BaseController):
    def __init__(
        self,
        project_id: str,
        db_client,
        vector_client: VectorDBInterface,
        embedding_client: LLMInterface,
        sparse_embedding_client: LLMInterface,
        embedding_max_tken: int = 512,
    ):
        super().__init__()
        self.project_id = project_id
        self.project_dir = ProjectController().get_project_path(project_id=project_id)

        # Inject the active database connections
        self.db_client = db_client
        self.vector_client = vector_client
        self.embedding_client = embedding_client
        self.sparse_client = sparse_embedding_client
        self.embedding_max_token = embedding_max_tken

        # Instantiate Models using the injected connections
        self.asset_model = AssetModel(db_client=self.db_client)
        self.chunk_model = ChunkModel(vector_db_client=self.vector_client)
        self.project_model = ProjectModel(db_client=self.db_client)

        # Will hold the actual database object for the project once fetched
        self.project_obj = None

    def _get_docling_tokenizer(self):
        """
        Dynamically returns the correct tokenizer wrapper for Docling's HybridChunker
        based on the active embedding client.
        """
        client_type = self.embedding_client.__class__.__name__
        model_id = self.embedding_client.embedding_model_id

        try:
            if client_type == "OpenAIClient":
                import tiktoken
                from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

                try:
                    encoding = tiktoken.encoding_for_model(model_id)
                    logger.debug(f"Loading native OpenAI tokenizer for model: {model_id}")
                except KeyError:
                    logger.debug(f"Open-source model '{model_id}' detected. Approximating with cl100k_base.")
                    encoding = tiktoken.get_encoding("cl100k_base")

                return OpenAITokenizer(tokenizer=encoding, max_tokens=self.embedding_max_token)

            elif client_type in ["CohereClient", "GeminiClient"]:
                import tiktoken
                from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

                # Docling's HF wrapper requires specific Sentence-BERT configs.
                # To avoid network crashes, we use the local industry-standard cl100k_base
                # to flawlessly approximate multilingual chunk sizes offline.
                logger.debug(f"Approximating {client_type} tokens using local cl100k_base tokenizer.")
                return OpenAITokenizer(
                    tokenizer=tiktoken.get_encoding("cl100k_base"), max_tokens=self.embedding_max_token
                )

        except ImportError as e:
            logger.warning(f"Missing tokenizer library: {e}. Falling back to Docling default.")
            return None
        except Exception:
            logger.exception(f"Could not load tokenizer for {model_id}. Falling back to default.")
            return None

        return None

    async def get_file_chunks(self, file_id: str):
        file_path = os.path.join(self.project_dir, file_id)

        if not os.path.exists(file_path):
            logger.warning(f"File not found at path: {file_path}")
            return None

        logger.debug(f"Initializing DoclingLoader for {file_id}...")
        # Grab the specific mathematical dictionary for the active AI
        active_tokenizer = self._get_docling_tokenizer()

        # Configure the Chunker
        chunker_config = HybridChunker(tokenizer=active_tokenizer) if active_tokenizer else HybridChunker()
        try:
            loader = DoclingLoader(
                file_path=file_path,
                export_type=ExportType.DOC_CHUNKS,
                chunker=chunker_config,
            )
            chunks = await asyncio.to_thread(loader.load)

            logger.info(f"Successfully chunked file '{file_id}' into {len(chunks)} chunks.")
            return chunks

        except Exception:
            logger.exception(f"Error during chunking of file '{file_id}'")
            raise

    async def get_assets_to_process(self, file_id: str = None) -> list:
        """Helper to fetch the exact assets requested by the user."""
        # Ensure the project exists and cache the object for the chunker
        self.project_obj = await self.project_model.get_project_or_create(project_id=self.project_id)

        if file_id:
            logger.debug(f"Fetching specific file_id: '{file_id}'")
            asset = await self.asset_model.get_asset_record(
                asset_project_id=str(self.project_obj.id),
                asset_name=file_id,
            )
            return [asset] if asset else []
        else:
            logger.debug(f"Fetching all files for project '{self.project_id}'")
            return await self.asset_model.get_all_project_assets(
                asset_project_id=str(self.project_obj.id),
                asset_type=AssetTypeEnum.FILE.value,
            )

    async def embed_and_package_chunks(
        self,
        cleaned_chunks: List[DataChunk],
        batch_size: int = 50,
    ) -> List[DocumentChunk]:
        """
        Takes cleaned dictionaries, generates dense vectors CONCURRENTLY via the LLM,
        and packages them into strict DocumentChunk models. Uses a Semaphore to protect API limits.
        """
        logger.debug(f"Generating embeddings concurrently for {len(cleaned_chunks)} chunks...")
        needs_sparse = self.vector_client.is_sparse_needed()
        packaged_chunks = []
        # Loop through the chunks in groups of 90
        for i in range(0, len(cleaned_chunks), batch_size):
            batch = cleaned_chunks[i : i + batch_size]

            # Extract just the raw text strings from your chunk objects
            # (Adjust 'chunk.page_content' to whatever property your chunk object uses for text)
            texts = [chunk.chunk_text for chunk in batch]

            try:
                # 1. Generate Dense Embeddings (External API - Batched)
                dense_embeddings = await self.embedding_client.generate_embedding(
                    texts=texts,
                    input_type=InputTypeEnum.Document.value,
                )

                # 2. Generate Sparse Embeddings (Local Splade Model - No rate limits)
                if needs_sparse:
                    sparse_tasks = [self.sparse_client.generate_sparse_embedding(text) for text in texts]
                    sparse_embeddings = await asyncio.gather(*sparse_tasks)

                # 3. Package the vectors back into the chunk objects
                for j, chunk in enumerate(batch):
                    document_chunk = await self.chunk_model.create_document_chunks(
                        chunk=chunk,
                        vectors=dense_embeddings[j],
                        sparse_vectors=sparse_embeddings[j] if needs_sparse else None,
                    )
                    packaged_chunks.append(document_chunk)

                # 4. Respect the Trial Key: Pause for 2 seconds between batches
                # This ensures you never hit the 100 calls per minute limit
                if i + batch_size < len(cleaned_chunks):
                    logger.debug("Sleeping for 2 seconds to respect API rate limits...")
                    await asyncio.sleep(2)
            except Exception:
                logger.error(f"Critical error processing batch {i} to {i + batch_size}")
                # Depending on your pipeline, you can raise the error here or continue to the next batch
                raise

        logger.info(f"Successfully embedded and packaged {len(packaged_chunks)} chunks.")
        return packaged_chunks

    async def run_ingestion_pipeline(
        self,
        file_id: str = None,
        distance_metric: str = VectorDBEnums.DistanceMetricEnum.COSINE.value,
        batch_size: int = 100,
        do_reset: int = 0,
    ) -> dict:
        """
        The Master Orchestrator.
        Executes the business rules for ingestion and returns a Result Dictionary to the Route.
        """
        collection_name = self.get_collection_name(project_id=self.project_id)
        operation_name = "Reset" if do_reset else "Create"

        # STEP 1: Create or Reset Collection
        try:
            logger.debug(f"Attempting to {operation_name} collection '{collection_name}' (do_reset={do_reset})")
            await self.chunk_model.create_collection(
                collection_name=collection_name,
                vector_size=self.embedding_client.embedding_size,
                distance_metric=distance_metric,
                do_reset=do_reset,
            )
            logger.info(f"Successfully {operation_name} collection '{collection_name}'")
        except Exception:
            logger.exception(f"Failed to {operation_name} collection '{collection_name}'")
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "content": {
                    "signal": ResponseSignal.COLLECTION_CREATION_FAILED.value,
                },
            }

        # STEP 2: Fetch Target Assets
        project_assets = await self.get_assets_to_process(file_id)
        if not project_assets:
            logger.warning(f"No assets found to process for project '{self.project_id}'.")
            return {
                "status": status.HTTP_404_NOT_FOUND,
                "content": {
                    "signal": ResponseSignal.FILE_NOT_FOUND.value,
                },
            }

        total_inserted_count = 0
        total_failed_inserted_count = 0
        failed_files = []

        # STEP 3: Process Each Asset
        for asset in project_assets:
            file_name = asset.asset_name
            logger.debug(f"Pipeline started for file: '{file_name}'")

            try:
                # A. Parse PDF
                raw_chunks = await self.get_file_chunks(file_id=file_name)
                if raw_chunks is None:
                    failed_files.append(file_name)
                    continue

                # B. Clean Metadata
                cleaned_chunks = await self.chunk_model.clean_chunks(
                    chunks=raw_chunks, project=self.project_obj, asset=asset
                )

                # C. Generate vectors & Package to DocumentChunk
                document_chunks = await self.embed_and_package_chunks(
                    cleaned_chunks=cleaned_chunks,
                    batch_size=batch_size,
                )

                # D. Store in VectorDB
                if document_chunks:
                    inserted = await self.chunk_model.insert_chunks(
                        collection_name=collection_name,
                        chunks=document_chunks,
                        batch_size=batch_size,
                    )
                    if inserted:
                        total_inserted_count += inserted
                        failed_inserted_count = len(document_chunks) - inserted
                        total_failed_inserted_count += failed_inserted_count
                        if failed_inserted_count > 0:
                            failed_files.append(file_name)
                            logger.warning(
                                f"Inserted {len(document_chunks)} chunks for '{file_name}' with {failed_inserted_count} failed inserts."
                            )
                        else:
                            logger.info(
                                f"Inserted {len(document_chunks)} chunks for '{file_name}' with {failed_inserted_count} failed inserts."
                            )

                    else:
                        failed_files.append(file_name)
                        logger.warning(f"Failed to insert any chunks for '{file_name}'")
                else:
                    logger.warning(f"No valid embedded chunks generated for '{file_name}'.")
                    failed_files.append(file_name)

            except Exception:
                logger.exception(f"Critical pipeline failure for file: {file_name}")
                failed_files.append(file_name)
                continue

        # STEP 4: Return Final State to the Route
        return {
            "status": status.HTTP_200_OK,
            "content": {
                "signal": ResponseSignal.CHUNK_INSERTION_SUCCESSFUL.value
                if not failed_files
                else ResponseSignal.CHUNK_INSERTION_FAILED.value,
                "inserted": total_inserted_count,
                "processed_files": len(project_assets) - len(failed_files),
                "failed_files": failed_files,
                "total_failed_inserts": total_failed_inserted_count,
            },
        }

    async def get_vector_db_collection_info(self, project_id: str):
        collection_name = self.get_collection_name(project_id=project_id)
        logger.debug(f"Attempting to retrieve collection info for '{collection_name}'")
        try:
            info = await self.vector_client.get_collection_info(collection_name=collection_name)
            logger.info(f"Successfully retrieved collection info for '{collection_name}'")
            return {
                "status": status.HTTP_200_OK,
                "content": {
                    "signal": ResponseSignal.COLLECTION_INFO_SUCCESSFUL.value,
                    "info": info,
                },
            }
        except Exception:
            logger.exception(f"Failed to get collection info for '{collection_name}'")
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "content": {"signal": ResponseSignal.COLLECTION_INFO_FAILED.value},
            }

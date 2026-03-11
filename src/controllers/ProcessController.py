import asyncio
import logging
import os

from docling.chunking import HybridChunker
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType

from models import ResponseSignal

from .BaseController import BaseController
from .ProjectController import ProjectController

logger = logging.getLogger(__name__)


class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_dir = ProjectController().get_project_path(project_id=project_id)

    async def get_file_chunks(self, file_id: str):
        file_path = os.path.join(self.project_dir, file_id)

        if not os.path.exists(file_path):
            logger.warning(f"File not found at path: {file_path}")
            return None, ResponseSignal.FILE_NOT_FOUND.value

        logger.debug(f"Initializing DoclingLoader for {file_id}...")

        try:
            loader = DoclingLoader(
                file_path=file_path,
                export_type=ExportType.DOC_CHUNKS,
                chunker=HybridChunker(),
            )
            chunks = await asyncio.to_thread(loader.load)

            logger.info(f"Successfully chunked file '{file_id}' into {len(chunks)} chunks.")
            return chunks

        except Exception:
            logger.exception(f"Error during chunking of file '{file_id}'")
            raise

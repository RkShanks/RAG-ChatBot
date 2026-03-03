import os

from docling.chunking import HybridChunker
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType

from models import ResponseSignal

from .BaseController import BaseController
from .ProjectController import ProjectController


class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_dir = ProjectController().get_project_path(project_id=project_id)

    def get_file_chunks(self, file_id: str):
        file_path = os.path.join(self.project_dir, file_id)
        if not os.path.exists(file_path):
            return None, ResponseSignal.FILE_NOT_FOUND.value

        loader = DoclingLoader(
            file_path=file_path,
            export_type=ExportType.DOC_CHUNKS,
            chunker=HybridChunker(),
        )
        chunks = loader.load()
        cleaned_chunks = self.clean_up_chunks(chunks=chunks)
        return cleaned_chunks, ResponseSignal.CHUNKING_SUCCESS.value

    def clean_up_chunks(self, chunks):
        cleaned_chunks = [
            {
                "page_content": chunk.page_content,
                "metadata": {
                    "source": chunk.metadata.get("source", "unknown"),
                },
            }
            for chunk in chunks
        ]

        return cleaned_chunks

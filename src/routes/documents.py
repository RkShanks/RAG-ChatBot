import logging
import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from controllers.ProjectController import ProjectController
from helpers.dependencies import get_session_id
from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal
from models import AssetModel

logger = logging.getLogger(__name__)

documents_router = APIRouter(
    prefix="/api/v1/documents",
    tags=["api_v1_documents"],
)

# Text-based formats: safe to read as raw UTF-8
TEXT_FORMATS = {".txt", ".md", ".markdown", ".html", ".htm"}


@documents_router.get("/preview/{project_id}/{asset_id}")
async def preview_document(
    project_id: str,
    asset_id: str,
    request: Request,
    session_id: str = Depends(get_session_id),
):
    """
    Returns the first 3000 characters of a stored document for in-app preview.
    - Text formats (.txt, .md, .html): read directly as UTF-8.
    - Binary formats (.pdf, .docx, .pptx, .xlsx): converted to Markdown via Docling.
    """
    asset_model = AssetModel(db_client=request.app.state.db_client)
    asset = await asset_model.get_asset_by_id(asset_id=asset_id)

    if not asset or str(asset.asset_project_id) != project_id:
        raise CustomAPIException(
            signal_enum=ResponseSignal.FILE_NOT_FOUND,
            status_code=404,
            dev_detail=f"Asset '{asset_id}' not found or does not belong to project '{project_id}'",
        )

    file_path = os.path.join(
        ProjectController().get_project_path(project_id), asset.asset_name
    )

    if not os.path.exists(file_path):
        raise CustomAPIException(
            signal_enum=ResponseSignal.FILE_NOT_FOUND,
            status_code=404,
            dev_detail=f"Physical file not found on disk: {file_path}",
        )

    ext = os.path.splitext(asset.asset_name)[1].lower()

    if ext in TEXT_FORMATS:
        # Safe to read as plain text
        with open(file_path, "r", errors="replace") as f:
            preview = f.read(3000)
    else:
        # Binary format — use Docling to extract readable Markdown text
        logger.debug(f"Converting binary file '{asset.asset_name}' to text via Docling for preview...")
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(file_path)
        preview = result.document.export_to_markdown()[:3000]

    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "file_name": asset.asset_name,
            "preview": preview,
        },
    )

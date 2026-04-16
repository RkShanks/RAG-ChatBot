import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from controllers import BaseController
from helpers.config import get_settings
from helpers.dependencies import get_session_id
from models import AssetModel, ChunkModel, ProjectModel

logger = logging.getLogger(__name__)
settings_router = APIRouter(
    prefix="/api/v1/settings",
    tags=["api_v1_settings"],
)


class TuningUpdate(BaseModel):
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    retrieval_limit: Optional[int] = Field(default=None, ge=1, le=20)
    max_output_tokens: Optional[int] = Field(default=None, ge=64, le=65536)


@settings_router.get("/info")
async def get_system_info(request: Request):
    """Returns read-only system diagnostics for the Settings panel."""
    settings = get_settings()

    # Mask the MongoDB URI to hide credentials
    raw_uri = settings.MONGODB_URI
    if "@" in raw_uri:
        host_part = raw_uri.split("@")[-1]
        masked_uri = f"mongodb://••••:••••@{host_part}"
    else:
        masked_uri = raw_uri

    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "info": {
                "generation_backend": settings.GENERATION_BACKEND,
                "generation_model": settings.GENERATION_MODEL_ID,
                "embedding_backend": settings.EMBEDDING_BACKEND,
                "embedding_model": settings.EMBEDDING_MODEL_ID,
                "vector_db_backend": settings.VECTOR_DB_BACKEND,
                "reranker_backend": settings.RERANKER_BACKEND or "None",
                "database_uri": masked_uri,
                "database_name": settings.MONGODB_DB_NAME,
            },
        },
    )


@settings_router.get("/tuning")
async def get_tuning(request: Request):
    """Returns current mutable runtime tuning values."""
    rt = request.app.state.runtime_settings
    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "tuning": {
                "temperature": rt["temperature"],
                "retrieval_limit": rt["retrieval_limit"],
                "max_output_tokens": rt["max_output_tokens"],
            },
        },
    )


@settings_router.put("/tuning")
async def update_tuning(request: Request, update: TuningUpdate):
    """Live-updates runtime LLM tuning values. No server restart required."""
    rt = request.app.state.runtime_settings

    if update.temperature is not None:
        rt["temperature"] = update.temperature
    if update.retrieval_limit is not None:
        rt["retrieval_limit"] = update.retrieval_limit
    if update.max_output_tokens is not None:
        rt["max_output_tokens"] = update.max_output_tokens

    logger.info(f"✅ Runtime settings updated: {rt}")

    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "tuning": rt,
        },
    )


@settings_router.post("/reset")
async def nuclear_reset(
    request: Request,
    session_id: str = Depends(get_session_id),
):
    """Session-scoped nuclear reset: destroys ALL workspaces, vectors, chat history, and disk files for this session."""
    from controllers import ProjectController

    project_model = ProjectModel(db_client=request.app.state.db_client)
    asset_model = AssetModel(db_client=request.app.state.db_client)
    chunk_model = ChunkModel(vector_db_client=request.app.state.vector_db_client)
    base_controller = BaseController()
    project_controller = ProjectController()

    # Fetch all projects for this session
    projects, _ = await project_model.get_all_projects(page=1, page_size=1000, session_id=session_id)
    destroyed_count = 0

    for project in projects:
        try:
            # 1. Delete vector collection
            collection_name = base_controller.get_collection_name(project.project_id, session_id)
            try:
                await chunk_model.delete_chunks_by_collection_name(collection_name)
            except Exception:
                pass

            # 2. Delete MongoDB assets
            await asset_model.delete_project_assets(asset_project_id=str(project.id))

            # 3. Delete MongoDB project
            await project_model.delete_project(project_id=project.project_id, session_id=session_id)

            # 4. Delete disk files
            try:
                project_controller.delete_project_path(project_id=project.project_id)
            except Exception:
                pass

            destroyed_count += 1
        except Exception as e:
            logger.warning(f"Failed to fully destroy project {project.project_id}: {e}")

    logger.info(f"🔥 Nuclear Reset complete: {destroyed_count} workspaces destroyed for session {session_id}")

    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "destroyed_count": destroyed_count,
        },
    )

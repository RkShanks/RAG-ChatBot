import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from controllers import BaseController
from helpers.config import get_settings
from helpers.dependencies import get_session_id
from models import AssetModel, ChunkModel, ProjectModel, UserModel
from services.llm.LLMEnums import LLMEnums, OPENAIEnum, CohereEnum, GeminiEnum
from services.llm import LLMFactory

logger = logging.getLogger(__name__)
settings_router = APIRouter(
    prefix="/api/v1/settings",
    tags=["api_v1_settings"],
)


class TuningUpdate(BaseModel):
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    retrieval_limit: Optional[int] = Field(default=None, ge=1, le=20)
    max_output_tokens: Optional[int] = Field(default=None, ge=64, le=65536)


class ProviderUpdate(BaseModel):
    generation_backend: Optional[str] = None
    generation_model: Optional[str] = None
    generation_api_key: Optional[str] = None
    embedding_backend: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None


def mask_key(key: str) -> str:
    """Mask an API key showing only the last 4 characters."""
    if not key or len(key) < 4:
        return "Not Set"
    return "••••••••" + key[-4:]


def mask_uri(uri: str) -> str:
    """Mask a MongoDB URI hiding credentials."""
    if not uri:
        return "Not Set"
    if "@" in uri:
        host_part = uri.split("@")[-1]
        return f"mongodb://••••:••••@{host_part}"
    return uri


@settings_router.get("/info")
async def get_system_info(request: Request):
    """Returns system diagnostics reflecting runtime provider state."""
    settings = get_settings()
    providers = request.app.state.active_providers
    urls = request.app.state.connection_urls

    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "info": {
                "generation_backend": providers["generation_backend"],
                "generation_model": providers["generation_model"],
                "embedding_backend": providers["embedding_backend"],
                "embedding_model": providers["embedding_model"],
                "vector_db_backend": settings.VECTOR_DB_BACKEND,
                "reranker_backend": settings.RERANKER_BACKEND or "None",
                "database_uri": mask_uri(urls.get("mongodb_uri", "")),
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


@settings_router.get("/providers")
async def get_providers():
    """Returns available provider enums and their model catalogs."""
    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "generation_providers": [e.value for e in LLMEnums],
            "generation_models": {
                "OPENAI": OPENAIEnum.GENERATION_MODELS.value,
                "COHERE": CohereEnum.GENERATION_MODELS.value,
                "GEMINI": GeminiEnum.GENERATION_MODELS.value,
            },
            "embedding_providers": [e.value for e in LLMEnums],
            "embedding_models": {
                "OPENAI": OPENAIEnum.EMBEDDING_MODELS.value,
                "COHERE": CohereEnum.EMBEDDING_MODELS.value,
                "GEMINI": GeminiEnum.EMBEDDING_MODELS.value,
            },
        },
    )


@settings_router.get("/keys")
async def get_keys(request: Request):
    """Returns masked API keys and connection URLs."""
    keys = request.app.state.api_keys
    urls = request.app.state.connection_urls
    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "keys": {
                "openai": mask_key(keys.get("openai", "")),
                "cohere": mask_key(keys.get("cohere", "")),
                "gemini": mask_key(keys.get("gemini", "")),
            },
            "urls": {
                "openai_base_url": urls.get("openai_base_url", ""),
                "qdrant_url": urls.get("qdrant_url", ""),
                "mongodb_uri": mask_uri(urls.get("mongodb_uri", "")),
            },
        },
    )


@settings_router.put("/provider")
async def update_provider(request: Request, update: ProviderUpdate):
    """Hot-swap LLM provider at runtime with graceful fallback on failure."""
    providers = request.app.state.active_providers
    keys = request.app.state.api_keys
    urls = request.app.state.connection_urls

    # 1. Update API keys if new ones are provided
    if update.generation_api_key:
        backend = (update.generation_backend or providers["generation_backend"]).upper()
        if backend == "OPENAI":
            keys["openai"] = update.generation_api_key
        elif backend == "COHERE":
            keys["cohere"] = update.generation_api_key
        elif backend == "GEMINI":
            keys["gemini"] = update.generation_api_key

    if update.embedding_api_key:
        backend = (update.embedding_backend or providers["embedding_backend"]).upper()
        if backend == "OPENAI":
            keys["openai"] = update.embedding_api_key
        elif backend == "COHERE":
            keys["cohere"] = update.embedding_api_key
        elif backend == "GEMINI":
            keys["gemini"] = update.embedding_api_key

    # 2. Update connection URLs
    if update.openai_base_url is not None:
        urls["openai_base_url"] = update.openai_base_url

    # 3. Attempt generation client hot-swap
    if update.generation_backend or update.generation_model:
        new_backend = (update.generation_backend or providers["generation_backend"]).upper()
        new_model = update.generation_model or providers["generation_model"]
        try:
            new_client = LLMFactory.hot_swap_generation_client(
                backend=new_backend,
                model_id=new_model,
                api_key=keys.get(new_backend.lower(), ""),
                base_url=urls.get("openai_base_url", "") if new_backend == "OPENAI" else None,
                runtime_settings=request.app.state.runtime_settings,
            )
            request.app.state.generation_client = new_client
            providers["generation_backend"] = new_backend
            providers["generation_model"] = new_model
            logger.info(f"✅ Generation client swapped to {new_backend} / {new_model}")
        except Exception as e:
            logger.error(f"❌ Generation hot-swap failed: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "signal": "provider_swap_failed",
                    "detail": f"Generation swap failed: {str(e)}. Previous client preserved.",
                },
            )

    # 4. Attempt embedding client hot-swap
    if update.embedding_backend or update.embedding_model:
        new_backend = (update.embedding_backend or providers["embedding_backend"]).upper()
        new_model = update.embedding_model or providers["embedding_model"]
        try:
            new_client = LLMFactory.hot_swap_embedding_client(
                backend=new_backend,
                model_id=new_model,
                api_key=keys.get(new_backend.lower(), ""),
                base_url=urls.get("openai_base_url", "") if new_backend == "OPENAI" else None,
            )
            request.app.state.embedding_client = new_client
            providers["embedding_backend"] = new_backend
            providers["embedding_model"] = new_model
            logger.info(f"✅ Embedding client swapped to {new_backend} / {new_model}")
        except Exception as e:
            logger.error(f"❌ Embedding hot-swap failed: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "signal": "provider_swap_failed",
                    "detail": f"Embedding swap failed: {str(e)}. Previous client preserved.",
                },
            )

    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "active_providers": providers,
        },
    )


@settings_router.get("/profile")
async def get_profile(request: Request, session_id: str = Depends(get_session_id)):
    """Returns the user profile for the current session, creating one if it doesn't exist."""
    user_model = UserModel(db_client=request.app.state.db_client)
    user = await user_model.get_or_create_user(session_id)
    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "profile": user,
        },
    )


@settings_router.put("/profile")
async def update_profile(request: Request, session_id: str = Depends(get_session_id)):
    """Updates the display name for the current user profile."""
    body = await request.json()
    display_name = body.get("display_name", "")

    user_model = UserModel(db_client=request.app.state.db_client)
    updated = await user_model.update_display_name(session_id, display_name)

    if updated:
        logger.info(f"✅ Profile updated for session {session_id[:8]}...")

    # Return the updated profile
    user = await user_model.get_or_create_user(session_id)
    return JSONResponse(
        status_code=200,
        content={
            "signal": "success",
            "profile": user,
        },
    )

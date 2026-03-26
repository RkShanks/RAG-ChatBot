import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from controllers import NLPController
from helpers.config import Settings, get_settings
from models import ResponseSignal
from routes.schemes.nlp import SearchRequest

logger = logging.getLogger(__name__)
nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1_nlp"],
)


@nlp_router.post("/search/{project_id}")
async def search_data(
    request: Request,
    project_id: str,
    search_request: SearchRequest,
    app_settings: Settings = Depends(get_settings),
):
    logger.debug(f"Search request started for project '{project_id}' with parameters: {search_request}")

    nlp_controller = NLPController(
        vector_client=request.app.state.vector_db_client,
        generation_client=request.app.state.generation_client,
        embedding_client=request.app.state.embedding_client,
        sparse_embedding_client=request.app.state.sparse_embedding_client,
        reranker_client=request.app.state.ranker_client,
    )

    result = await nlp_controller.search_and_rerank(
        project_id=project_id,
        query=search_request.query,
        retrieval_limit=search_request.limit * 2,
        final_limit=search_request.limit,
        filter_criteria=search_request.filter_criteria,
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.NLP_SEARCH_SUCCESSFUL.value,
            "results": [doc.model_dump() for doc in result],
        },
    )

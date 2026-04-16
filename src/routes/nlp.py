import json
import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from controllers import NLPController
from helpers.config import Settings, get_settings
from helpers.dependencies import get_session_id
from helpers.exceptions import CustomAPIException
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
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Search request started for project '{project_id}' with parameters: {search_request}")

    nlp_controller = NLPController(
        vector_client=request.app.state.vector_db_client,
        generation_client=request.app.state.generation_client,
        embedding_client=request.app.state.embedding_client,
        sparse_embedding_client=request.app.state.sparse_embedding_client,
        reranker_client=request.app.state.ranker_client,
        project_id=project_id,
        session_id=session_id,
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


@nlp_router.post("/ask/stream/{project_id}")
async def chat_with_project(
    request: Request,
    project_id: str,
    search_request: SearchRequest,
    app_settings: Settings = Depends(get_settings),
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Chat request started for project '{project_id}' with query: {search_request.query}")

    nlp_controller = NLPController(
        vector_client=request.app.state.vector_db_client,
        generation_client=request.app.state.generation_client,
        embedding_client=request.app.state.embedding_client,
        sparse_embedding_client=request.app.state.sparse_embedding_client,
        reranker_client=request.app.state.ranker_client,
        project_id=project_id,
        session_id=session_id,
    )

    # 1. The Generator Wrapper
    async def raw_generator():
        try:
            stream, history = await nlp_controller.ask_question_stream(
                project_id=project_id,
                query=search_request.query,
                chat_history=search_request.chat_history,
                limit=search_request.limit,
                target_locale=search_request.target_locale,
            )

            async for chunk in stream:
                # 'chunk' is the dictionary we created in the client e.g., {"type": "answer", "text": "مرحبا"}
                safe_data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {safe_data}\n\n"

        except CustomAPIException as e:
            # SSE Error Handling: We catch our clean custom exception and send it as an SSE error event
            # so the frontend UI can display the precise dev_detail without breaking the chat window!
            error_payload = {"type": "error", "text": e.dev_detail, "signal": e.signal_enum.value}
            safe_data = json.dumps(error_payload, ensure_ascii=False)
            yield f"data: {safe_data}\n\n"

        except Exception:
            # Catch-all for unexpected Python crashes mid-stream
            logger.exception(f"Unexpected stream crash for project {project_id}")
            error_payload = {"type": "error", "text": "An unexpected internal server error occurred during streaming."}
            safe_data = json.dumps(error_payload, ensure_ascii=False)
            yield f"data: {safe_data}\n\n"

    return StreamingResponse(
        raw_generator(),
        media_type="text/event-stream",
    )


@nlp_router.post("/ask/generate/{project_id}")
async def ask_project(
    request: Request,
    project_id: str,
    search_request: SearchRequest,
    app_settings: Settings = Depends(get_settings),
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Ask request started for project '{project_id}' with query: {search_request.query}")

    nlp_controller = NLPController(
        vector_client=request.app.state.vector_db_client,
        generation_client=request.app.state.generation_client,
        embedding_client=request.app.state.embedding_client,
        sparse_embedding_client=request.app.state.sparse_embedding_client,
        reranker_client=request.app.state.ranker_client,
        project_id=project_id,
        session_id=session_id,
    )

    response, history = await nlp_controller.ask_question(
        project_id=project_id,
        query=search_request.query,
        chat_history=search_request.chat_history,
        limit=search_request.limit,
        target_locale=search_request.target_locale,
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.NLP_CHAT_SUCCESSFUL.value,
            "response": response,
            "chat_history": history,
        },
    )

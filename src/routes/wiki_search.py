import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from controllers import DataController, Wiki_SearchController
from helpers.config import Settings, get_settings
from models import AssetModel, ProjectModel, ResponseSignal

logger = logging.getLogger(__name__)
wiki_search_router = APIRouter(
    prefix="/api/v1/wiki",
    tags=["api_v1_wiki_search"],
)


@wiki_search_router.post("/wiki-search/{project_id}")
async def wiki_search(
    request: Request,
    project_id: str,
    query: str,
    app_settings: Settings = Depends(get_settings),
):
    logger.debug(f"Received wiki search request for project '{project_id}' with query '{query}'")
    # Implement the logic to perform a wiki search based on the query and project_id
    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_project_or_create(project_id=project_id)

    # You can use the DataController to handle any necessary data operations
    data_controller = DataController()
    wiki_search_controller = Wiki_SearchController()

    # search for the query and return the results
    try:
        page = wiki_search_controller.search_wikipedia(query=query)
    except Exception:
        logger.exception(f"Exception occurred while searching Wikipedia for query '{query}' in project '{project_id}'")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"search_status": ResponseSignal.WIKI_SEARCH_ERROR.value},
        )

    if page is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"search_status": ResponseSignal.WIKI_SEARCH_NO_RESULTS.value},
        )

    # get the UploadFile object for the page
    upload_file = wiki_search_controller.get_UploadFile(page)

    # save the file using the DataController
    file_dir_path, file_id = data_controller.generate_unique_file_path(
        file_name=upload_file.filename,
        project_id=project_id,
    )
    try:
        _ = await data_controller.save_file(
            file=upload_file,
            file_path=file_dir_path,
            project_id=project_id,
            app_settings=app_settings,
        )
    except Exception:
        logger.exception(
            f"Exception occurred while saving wiki search result for query '{query}' in project '{project_id}'"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "search_status": ResponseSignal.WIKI_SEARCH_RESULTS_FOUND.value,
                "signal": ResponseSignal.WIKI_FILE_UPLOAD_FAILED.value,
            },
        )

    logger.info(
        f"Wiki search result for query '{query}' uploaded successfully as file '{file_id}' in project '{project_id}'"
    )

    asset_model = AssetModel(db_client=request.app.state.db_client)
    try:
        asset_record = await asset_model.create_from_file(
            project_id=str(project.id),
            file_id=file_id,
            file_path=file_dir_path,
        )
        logger.info(
            "Successfully processed: Creating asset record for file '{upload_file.filename}' in project '{project_id}'"
        )
        return JSONResponse(
            content={
                "search_status": ResponseSignal.WIKI_SEARCH_RESULTS_FOUND.value,
                "signal": ResponseSignal.WIKI_FILE_UPLOADED_SUCCESSFULLY.value,
                "file_id": str(asset_record.id),
            }
        )

    except Exception:
        logger.exception(
            f"Exception occurred while creating asset record for file '{upload_file.filename}' in project '{project_id}'"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.ASSET_CREATION_FAILED.value,
            },
        )

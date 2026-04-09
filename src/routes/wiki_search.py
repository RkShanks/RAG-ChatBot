import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from controllers import DataController, Wiki_SearchController
from helpers.config import Settings, get_settings
from models import AssetModel, ProjectModel, ResponseSignal
from routes.schemes.wiki import SearchWikiRequest

logger = logging.getLogger(__name__)
wiki_search_router = APIRouter(
    prefix="/api/v1/wiki",
    tags=["api_v1_wiki_search"],
)


@wiki_search_router.post("/wiki-search/{project_id}")
async def wiki_search(
    request: Request,
    project_id: str,
    wiki_search_request: SearchWikiRequest,
    app_settings: Settings = Depends(get_settings),
):
    logger.debug(f"Received wiki search request for project '{project_id}' with query '{wiki_search_request.query}'")

    # 1. Get or Create Project (Let It Crash if MongoDB fails)
    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_project_or_create(project_id=project_id)

    data_controller = DataController()
    wiki_search_controller = Wiki_SearchController()

    # 2. Search Wikipedia (Let It Crash if the Wiki API goes down)
    page = wiki_search_controller.search_wikipedia(query=wiki_search_request.query, language=wiki_search_request.lang)
    if page is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"search_status": ResponseSignal.WIKI_SEARCH_NO_RESULTS.value},
        )

    # 3. Convert page to UploadFile
    upload_file = wiki_search_controller.get_UploadFile(page)

    # 4. Save the file to disk
    file_dir_path, file_id = data_controller.generate_unique_file_path(
        file_name=upload_file.filename,
        project_id=project_id,
    )

    await data_controller.save_file(
        file=upload_file,
        file_path=file_dir_path,
        project_id=project_id,
        app_settings=app_settings,
    )
    logger.info(f"Wiki search result for '{wiki_search_request.query}' uploaded successfully as file '{file_id}'.")

    # 5. Create Asset Record
    asset_model = AssetModel(db_client=request.app.state.db_client)
    asset_record = await asset_model.create_from_file(
        project_id=str(project.id),
        file_id=file_id,
        file_path=file_dir_path,
    )
    logger.info(f"Successfully created asset record for file '{upload_file.filename}' in project '{project_id}'")

    # 6. Return Success
    return JSONResponse(
        content={
            "search_status": ResponseSignal.WIKI_SEARCH_RESULTS_FOUND.value,
            "signal": ResponseSignal.WIKI_FILE_UPLOADED_SUCCESSFULLY.value,
            "file_id": str(asset_record.id),
        }
    )

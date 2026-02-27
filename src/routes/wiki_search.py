import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from controllers import DataController, Wiki_SearchController
from helpers.config import Settings, get_settings
from models import ResponseSignal

logger = logging.getLogger("uvicorn.error")
wiki_search_router = APIRouter(
    prefix="/api/v1/wiki",
    tags=["api_v1_wiki_search"],
)


@wiki_search_router.post("/wiki-search/{project_id}")
async def wiki_search(
    project_id: str, query: str, app_settings: Settings = Depends(get_settings)
):
    # Implement the logic to perform a wiki search based on the query and project_id
    # You can use the DataController to handle any necessary data operations
    data_controller = DataController()
    wiki_search_controller = Wiki_SearchController()

    # search for the query and return the results
    page = wiki_search_controller.search_wikipedia(query=query)
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
    is_saved = await data_controller.save_file(
        file=upload_file,
        file_path=file_dir_path,
        project_id=project_id,
        app_settings=app_settings,
    )
    if not is_saved:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "search_status": ResponseSignal.WIKI_SEARCH_RESULTS_FOUND.value,
                "signal": ResponseSignal.WIKI_FILE_UPLOAD_FAILED.value,
            },
        )

    return JSONResponse(
        content={
            "search_status": ResponseSignal.WIKI_SEARCH_RESULTS_FOUND.value,
            "signal": ResponseSignal.WIKI_FILE_UPLOADED_SUCCESSFULLY.value,
            "file_id": file_id,
        },
    )

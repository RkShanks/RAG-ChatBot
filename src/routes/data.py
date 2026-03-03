import logging

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse

from controllers import DataController, ProcessController
from helpers.config import Settings, get_settings
from models import ResponseSignal
from routes.schemes.data import ProcessRequest

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1_data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(
    project_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)
):
    # validate file type
    data_controller = DataController()
    is_valid, signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": signal},
        )

    file_dir_path, file_id = data_controller.generate_unique_file_path(
        file_name=file.filename,
        project_id=project_id,
    )
    is_saved = await data_controller.save_file(
        file=file,
        file_path=file_dir_path,
        project_id=project_id,
        app_settings=app_settings,
    )
    if not is_saved:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.FILE_UPLOADED_FAILED.value,
            },
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOADED_SUCCESSFULLY.value,
            "file_id": file_id,
        },
    )


@data_router.post("/process/{project_id}")
async def process_data(
    project_id: str,
    request: ProcessRequest,
    app_settings: Settings = Depends(get_settings),
):
    process_controller = ProcessController(project_id=project_id)
    chunks, signal = process_controller.get_file_chunks(file_id=request.file_id)

    if chunks is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": signal},
        )
    return chunks

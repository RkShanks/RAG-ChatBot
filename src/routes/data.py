import logging

from fastapi import APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import JSONResponse

from controllers import DataController, ProcessController
from helpers.config import Settings, get_settings
from models import ChunkModel, ResponseSignal
from models.ProjectModel import ProjectModel
from routes.schemes.data import ProcessRequest

logger = logging.getLogger(__name__)
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1_data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: str,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
):
    logger.debug(f"Received upload request for project '{project_id}' with file '{file.filename}'")
    project_model = ProjectModel(db_client=request.app.state.db_client)
    _ = await project_model.get_project_or_create(project_id=project_id)
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
    try:
        _ = await data_controller.save_file(
            file=file,
            file_path=file_dir_path,
            project_id=project_id,
            app_settings=app_settings,
        )
    except Exception:
        logger.exception(f"Exception occurred while saving file '{file.filename}' for project '{project_id}'")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.FILE_UPLOADED_FAILED.value,
            },
        )
    logger.info(f"File uploaded successfully: {file_id}")
    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOADED_SUCCESSFULLY.value,
            "file_id": file_id,
        },
    )


@data_router.post("/process/{project_id}")
async def process_data(
    request: Request,
    project_id: str,
    process_request: ProcessRequest,
    app_settings: Settings = Depends(get_settings),
):
    logger.debug(f"Process request started for project '{project_id}' on file '{process_request.file_id}'")
    # Instantiate controllers and models
    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_project_or_create(project_id=project_id)

    chunk_model = ChunkModel(db_client=request.app.state.db_client)
    process_controller = ProcessController(project_id=project_id)

    if process_request.do_reset == 1:
        try:
            deleted_count = await chunk_model.delete_chunks_by_project_id(project_id=project.id)
            logger.info(f"Reset requested: Deleted {deleted_count} existing chunks for project '{project_id}'")
        except Exception as e:
            logger.exception(f"Exception occurred while deleting chunks for project '{project_id}': {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"signal": ResponseSignal.CHUNK_DELETION_FAILED.value},
            )
    try:
        chunks = await process_controller.get_file_chunks(file_id=process_request.file_id)
        logger.debug(f"Chunking completed for file '{process_request.file_id}' with {len(chunks)} chunks generated.")

    except Exception:
        logger.exception(f"Docling failed to parse the document for file_id '{process_request.file_id}'")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.CHUNKING_FAILED.value},
        )

    chunks_record = await chunk_model.clean_chunks(chunks=chunks, project=project)

    try:
        inserted_count = await chunk_model.insert_chunks(chunks=chunks_record)
        logger.info(f"Successfully processed: Inserted {inserted_count} chunks for file_id: {process_request.file_id}")

        return JSONResponse(
            content={
                "signal": ResponseSignal.CHUNK_INSERTION_SUCCESSFUL.value,
                "inserted_chunks": inserted_count,
            },
        )
    except Exception:
        logger.exception(f"Error inserting chunks for file_id: {process_request.file_id}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.CHUNK_INSERTION_FAILED.value},
        )

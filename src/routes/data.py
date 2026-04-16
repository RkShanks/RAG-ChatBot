import logging

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import JSONResponse

from controllers import DataController, ProcessController
from helpers.config import Settings, get_settings
from helpers.dependencies import get_session_id
from models import AssetModel, ProjectModel, ResponseSignal
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
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Received upload request for project '{project_id}' with file '{file.filename}'")

    # 1. Get or Create Project
    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_project_or_create(project_id=project_id, session_id=session_id)

    # 2. Validate File
    data_controller = DataController()
    data_controller.validate_uploaded_file(file=file)

    # 3. Generate Path
    file_dir_path, file_id = data_controller.generate_unique_file_path(
        file_name=file.filename,
        project_id=project_id,
    )

    # 4. Save File to Disk
    await data_controller.save_file(
        file=file,
        file_path=file_dir_path,
        project_id=project_id,
        app_settings=app_settings,
    )
    logger.info(f"File uploaded successfully to disk: {file_id}")

    # 5. Save Asset to Database
    asset_model = AssetModel(db_client=request.app.state.db_client)
    asset_record = await asset_model.create_from_file(
        project_id=str(project.id),
        file_id=file_id,
        file_path=file_dir_path,
    )

    # 6. Return Success
    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOADED_SUCCESSFULLY.value,
            "file_id": str(asset_record.id),
        },
    )


@data_router.post("/process/{project_id}")
async def process_data(
    request: Request,
    project_id: str,
    process_request: ProcessRequest,
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Process request started for project '{project_id}' with parameters: {process_request}")
    # Instantiate controller
    controller = ProcessController(
        project_id=project_id,
        session_id=session_id,
        db_client=request.app.state.db_client,
        vector_client=request.app.state.vector_db_client,
        embedding_client=request.app.state.embedding_client,
        sparse_embedding_client=request.app.state.sparse_embedding_client,
    )
    # Run Pipeline
    result = await controller.run_ingestion_pipeline(
        file_id=process_request.file_id,
        do_reset=process_request.do_reset,
    )

    return JSONResponse(
        status_code=result["status"],
        content=result["content"],
    )


@data_router.get("/info/{project_id}")
async def get_collection_info(
    request: Request,
    project_id: str,
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Get process info request started for project '{project_id}'")
    controller = ProcessController(
        project_id=project_id,
        session_id=session_id,
        db_client=request.app.state.db_client,
        vector_client=request.app.state.vector_db_client,
        embedding_client=request.app.state.embedding_client,
        sparse_embedding_client=request.app.state.sparse_embedding_client,
    )
    result = await controller.get_vector_db_collection_info(project_id=project_id)
    return JSONResponse(
        status_code=result["status"],
        content=result["content"],
    )

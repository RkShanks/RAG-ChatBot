import logging

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import JSONResponse

from controllers import BaseController, DataController, ProcessController, ProjectController
from helpers.config import Settings, get_settings
from helpers.dependencies import get_session_id
from models import AssetModel, ChunkModel, ProjectModel, ResponseSignal, AssetTypeEnum
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

    # 1.5. Workspace Auto-Naming
    if project.project_name == "Untitled Workspace" or not project.project_name:
        # Strip the file extension to generate a clean title
        clean_name = file.filename.rsplit(".", 1)[0]
        project.project_name = clean_name
        await project_model.update_project(project)

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

@data_router.get("/files/{project_id}")
async def get_project_files(
    request: Request,
    project_id: str,
    session_id: str = Depends(get_session_id),
):
    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_project(project_id=project_id, session_id=session_id)
    if not project:
        return JSONResponse(status_code=404, content={"signal": ResponseSignal.PROJECT_NOT_FOUND.value})

    asset_model = AssetModel(db_client=request.app.state.db_client)
    assets = await asset_model.get_all_project_assets(
        asset_project_id=str(project.id),
        asset_type=AssetTypeEnum.FILE.value,
    )
    
    return JSONResponse(
        content={
            "signal": "success",
            "files": [{"id": str(a.id), "name": a.asset_name} for a in assets]
        }
    )


@data_router.delete("/project/{project_id}")
async def delete_project(
    request: Request,
    project_id: str,
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Received delete request for project '{project_id}'")

    project_model = ProjectModel(db_client=request.app.state.db_client)

    # 1. Verify Ownership & Retrieve Project
    project = await project_model.get_project(project_id=project_id, session_id=session_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND.value}
        )

    # 2. Delete Qdrant Vector Collection Physically
    base_controller = BaseController()
    collection_name = base_controller.get_collection_name(project_id, session_id)
    chunk_model = ChunkModel(vector_db_client=request.app.state.vector_db_client)
    # The VectorDB might throw CustomAPIException if collection doesn't exist, we can ignore or let global handler catch.
    # Usually it's fine to pass through.
    try:
        await chunk_model.delete_chunks_by_collection_name(collection_name)
    except Exception as e:
        logger.warning(f"Vector DB collection might not exist, skipping... Detail: {e}")

    # 3. Delete MongoDB Assets
    asset_model = AssetModel(db_client=request.app.state.db_client)
    await asset_model.delete_project_assets(asset_project_id=str(project.id))

    # 4. Delete MongoDB Project Config
    await project_model.delete_project(project_id=project_id, session_id=session_id)

    # 5. Physically eradicate the disk directory
    project_controller = ProjectController()
    project_controller.delete_project_path(project_id=project_id)

    logger.info(f"Successfully eradicated project '{project_id}' and all associated physical data.")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.PROJECT_DELETED_SUCCESSFULLY.value}
    )

@data_router.delete("/project/{project_id}/file/{file_id}")
async def delete_project_file(
    request: Request,
    project_id: str,
    file_id: str,
    session_id: str = Depends(get_session_id),
):
    logger.debug(f"Received delete request for file '{file_id}' in project '{project_id}'")

    project_model = ProjectModel(db_client=request.app.state.db_client)

    # 1. Verify Ownership & Retrieve Project
    project = await project_model.get_project(project_id=project_id, session_id=session_id)
    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND.value}
        )

    # 2. Retrieve the Specific Asset from MongoDB
    asset_model = AssetModel(db_client=request.app.state.db_client)
    asset = await asset_model.get_asset_by_id(asset_id=file_id)
    if not asset or str(asset.asset_project_id) != str(project.id):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseSignal.FILE_NOT_FOUND.value}
        )

    # 3. Delete VectorDB Data Associated with the File
    base_controller = BaseController()
    collection_name = base_controller.get_collection_name(project_id, session_id)
    chunk_model = ChunkModel(vector_db_client=request.app.state.vector_db_client)
    try:
        await chunk_model.delete_chunks_by_asset_id(collection_name=collection_name, asset_id=file_id)
    except Exception as e:
        logger.warning(f"Vector DB point deletion failed or collection might not exist, skipping... Detail: {e}")

    # 4. Physically eradicate the disk file
    project_controller = ProjectController()
    project_controller.delete_file_path(project_id=project_id, file_name=asset.asset_name)

    # 5. Delete the MongoDB Asset config
    await asset_model.delete_asset_by_id(asset_id=file_id)

    logger.info(f"Successfully eradicated file '{file_id}' and all associated physical data.")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.FILE_DELETED_SUCCESSFULLY.value}
    )

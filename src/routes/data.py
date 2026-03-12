import logging

from fastapi import APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import JSONResponse

from controllers import DataController, ProcessController
from helpers.config import Settings, get_settings
from models import AssetModel, ChunkModel, ProjectModel, ResponseSignal
from models.enums.AssetTypeEnum import AssetTypeEnum
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
    project = await project_model.get_project_or_create(project_id=project_id)
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

    asset_model = AssetModel(db_client=request.app.state.db_client)
    try:
        asset_record = await asset_model.create_from_file(
            project_id=str(project.id),
            file_id=file_id,
            file_path=file_dir_path,
        )
        return JSONResponse(
            content={
                "signal": ResponseSignal.FILE_UPLOADED_SUCCESSFULLY.value,
                "file_id": str(asset_record.id),
            },
        )
    except Exception:
        logger.exception(
            f"Exception occurred while creating asset record for file '{file.filename}' in project '{project_id}'"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.ASSET_CREATION_FAILED.value,
            },
        )


@data_router.post("/process/{project_id}")
async def process_data(
    request: Request,
    project_id: str,
    process_request: ProcessRequest,
    app_settings: Settings = Depends(get_settings),
):
    logger.debug(f"Process request started for project '{project_id}' with parameters: {process_request}")
    # Instantiate controllers and models
    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_project_or_create(project_id=project_id)

    chunk_model = ChunkModel(db_client=request.app.state.db_client)
    process_controller = ProcessController(project_id=project_id)

    asset_model = AssetModel(db_client=request.app.state.db_client)

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

    project_assets = []
    if process_request.file_id:
        logger.debug(f"Specific file_id provided for processing: '{process_request.file_id}'")
        asset = await asset_model.get_asset_record(
            asset_project_id=str(project.id),
            asset_name=process_request.file_id,
        )
        if not asset:
            logger.warning(f"File not found for file_id '{process_request.file_id}' during processing.")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"signal": ResponseSignal.FILE_NOT_FOUND.value},
            )
        project_assets.append(asset)
    else:
        # If no specific file_id provided, process all files for the project
        try:
            project_assets = await asset_model.get_all_project_assets(
                asset_project_id=str(project.id),
                asset_type=AssetTypeEnum.FILE.value,
            )
            logger.debug(
                f"No specific file_id provided. Found {len(project_assets)} files to process for project '{project_id}'"
            )
        except Exception:
            logger.exception(f"Exception occurred while retrieving assets for project '{project_id}'")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"signal": ResponseSignal.ASSET_RETRIEVAL_FAILED.value},
            )

    total_inserted_count = 0
    asset_names = [asset.asset_name for asset in project_assets]
    failed_files = []
    logger.info(f"Starting processing for project '{project_id}' with file_ids: {asset_names}")

    for asset in project_assets:
        logger.debug(f"Starting processing for file_id: '{asset.asset_name}' in project '{project_id}'")

        try:
            file_id = asset.asset_name

            chunks = await process_controller.get_file_chunks(file_id=file_id)
            if chunks is None:
                logger.warning(f"File not found for file_id '{file_id}' during processing.")
                failed_files.append(file_id)
                continue

            logger.debug(f"Chunking completed for file '{file_id}' with {len(chunks)} chunks generated.")

        except Exception:
            logger.exception(f"Docling failed to parse the document for file_id '{file_id}'")
            failed_files.append(file_id)
            continue

        chunks_record = await chunk_model.clean_chunks(chunks=chunks, project=project, asset=asset)

        try:
            inserted_count = await chunk_model.insert_chunks(chunks=chunks_record)
            total_inserted_count += inserted_count
            logger.info(
                f"Successfully processed: Inserted {inserted_count} chunks for project '{project_id}' with file_ids: {file_id}"
            )

        except Exception:
            logger.exception(f"Error inserting chunks for file_id: {file_id}")
            failed_files.append(file_id)
            continue

    return JSONResponse(
        content={
            "signal": ResponseSignal.CHUNK_INSERTION_SUCCESSFUL.value,
            "total_inserted_chunks": total_inserted_count,
            "total_files_processed": len(project_assets) - len(failed_files),
            "failed_files": failed_files,
        },
    )

import logging
import os
import re

import aiofiles
from fastapi import UploadFile

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal
from models import ProcessingEnums

from .BaseController import BaseController
from .ProjectController import ProjectController

logger = logging.getLogger(__name__)


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.file_scalar = 1024 * 1024  # 1 MB in bytes

    def validate_uploaded_file(self, file: UploadFile):
        logger.debug(f"Validating uploaded file: {file.filename} (type: {file.content_type}, size: {file.size} bytes)")

        # Implement file validation logic based on self.app_settings.FILE_EXTENSIONS and self.app_settings.FILE_SIZE_LIMIT
        if file.content_type not in self.app_settings.FILE_EXTENSIONS:
            raise CustomAPIException(
                signal_enum=ResponseSignal.FILE_TYPE_NOT_SUPPORTED,
                status_code=415,  # 415 Unsupported Media Type
                dev_detail=f"Rejected '{file.filename}'. MIME type '{file.content_type}' is not allowed.",
            )

        if file.size > self.app_settings.FILE_MAX_SIZE * self.file_scalar:
            raise CustomAPIException(
                signal_enum=ResponseSignal.FILE_SIZE_EXCEEDED,
                status_code=413,  # 413 Payload Too Large
                dev_detail=f"Rejected '{file.filename}'. Size {file.size} exceeds the {self.app_settings.FILE_MAX_SIZE}MB limit.",
            )

        logger.info(f"File '{file.filename}' passed validation checks.")
        return True

    def generate_unique_file_path(self, file_name: str, project_id: str):
        logger.debug(f"Generating unique file path for file: '{file_name}' in project: '{project_id}'")

        random_file_name = self.generate_random_string()
        project_dir = ProjectController().get_project_path(project_id=project_id)

        # Clean the file name to remove any unwanted characters
        clean_file_name = self.get_clean_file_name(file_name=file_name)

        # Combine the random name with the cleaned file name
        new_file_path = os.path.join(
            project_dir,
            random_file_name + "_" + clean_file_name,
        )

        # Ensure the generated file path is unique
        while os.path.exists(new_file_path):
            random_file_name = self.generate_random_string()
            new_file_path = os.path.join(
                project_dir,
                random_file_name + "_" + clean_file_name,
            )
        logger.debug(f"Unique file path generated: {new_file_path}")
        return new_file_path, random_file_name + "_" + clean_file_name

    def get_clean_file_name(self, file_name: str):

        base_name = os.path.basename(file_name)
        # Clean the file name to remove any unwanted characters
        clean_name = base_name.strip().replace(" ", "_")
        clean_file_name = re.sub(r"[^\w\-.\ ]", "", clean_name)

        # Change txt to md for Docling compatibility
        if clean_file_name.lower().endswith(ProcessingEnums.TXT.value):
            clean_file_name = clean_file_name[:-4] + ProcessingEnums.MD.value
        return clean_file_name

    async def save_file(self, file: UploadFile, file_path: str, project_id: str, app_settings):
        logger.debug(f"Saving file: '{file.filename}' to '{file_path}'")

        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await out_file.write(chunk)

            logger.info(f"Successfully saved file '{file.filename}' to project {project_id}.")
            return True

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.FILE_UPLOADED_FAILED,
                status_code=500,
                dev_detail=f"Disk IO Error while saving '{file.filename}' to path: '{file_path}'",
            ) from e

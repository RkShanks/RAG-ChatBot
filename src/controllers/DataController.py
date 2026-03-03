import logging
import os
import re

import aiofiles
from fastapi import UploadFile

from model import ResponseSignal

from .BaseController import BaseController
from .ProjectController import ProjectController


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.file_scalar = 1024 * 1024  # 1 MB in bytes
        self.logger = logging.getLogger("uvicorn.error")

    def validate_uploaded_file(self, file):

        # Implement file validation logic based on self.app_settings.FILE_EXTENSIONS and self.app_settings.FILE_SIZE_LIMIT
        if file.content_type not in self.app_settings.FILE_EXTENSIONS:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE * self.file_scalar:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        return True, ResponseSignal.FILE_VALIDATION_SUCCESS.value

    def generate_unique_file_path(self, file_name: str, project_id: str):
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
        return new_file_path, random_file_name + "_" + clean_file_name

    def get_clean_file_name(self, file_name: str):
        # Clean the file name to remove any unwanted characters
        clean_name = file_name.strip().replace(" ", "_")
        clean_file_name = re.sub(r"[^\w\-.\ ]", "", clean_name)
        return clean_file_name

    async def save_file(
        self, file: UploadFile, file_path: str, project_id: str, app_settings
    ):
        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await out_file.write(chunk)
            return True
        except Exception as e:
            self.logger.error(
                f"Error uploading file: {file.filename} to project: {project_id} - {str(e)}"
            )
            return False

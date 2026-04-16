import logging
import os

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal

from .BaseController import BaseController

logger = logging.getLogger(__name__)


class ProjectController(BaseController):
    def __init__(self):
        super().__init__()

    def get_project_path(self, project_id: str):
        projects_dir = os.path.join(
            self.files_dir,
            project_id,
        )

        # Create a directory for the project if it doesn't exist
        if not os.path.exists(projects_dir):
            try:
                os.makedirs(projects_dir)
            except Exception as e:
                raise CustomAPIException(
                    signal_enum=ResponseSignal.INTERNAL_SERVER_ERROR,
                    status_code=500,
                    dev_detail=f"OS failed to create project directory at path: {projects_dir}.",
                ) from e

        return projects_dir

    def delete_project_path(self, project_id: str):
        import shutil
        projects_dir = self.get_project_path(project_id)
        if os.path.exists(projects_dir):
            try:
                shutil.rmtree(projects_dir)
                logger.info(f"Physically deleted project directory: {projects_dir}")
            except Exception as e:
                raise CustomAPIException(
                    signal_enum=ResponseSignal.INTERNAL_SERVER_ERROR,
                    status_code=500,
                    dev_detail=f"OS failed to recursively delete project directory at path: {projects_dir}.",
                ) from e

import os

from .BaseController import BaseController


class ProjectController(BaseController):
    def __init__(self):
        super().__init__()

    def get_project_path(self, project_id: str):
        porjects_dir = os.path.join(
            self.files_dir,
            project_id,
        )

        # Create a directory for the project if it doesn't exist
        if not os.path.exists(porjects_dir):
            os.makedirs(porjects_dir)
        return porjects_dir

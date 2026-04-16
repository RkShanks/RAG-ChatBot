import os
import random
import string

from helpers.config import get_settings
from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal


class BaseController:
    def __init__(self):
        self.app_settings = get_settings()
        self.main_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(
            self.main_dir,
            "assets",
            "files",
        )
        self.database_dir = os.path.join(
            self.main_dir,
            "assets",
            "local_database",
        )

    def generate_random_string(self, length: int = 12):
        # Generate a random string of fixed length.
        letters = string.ascii_lowercase + string.digits
        return "".join(random.choice(letters) for _ in range(length))

    def get_database_path(self, database_name: str):
        database_path = os.path.join(
            self.database_dir,
            database_name,
        )

        if not os.path.exists(database_path):
            try:
                os.makedirs(database_path)
            except Exception as e:
                raise CustomAPIException(
                    signal_enum=ResponseSignal.INTERNAL_SERVER_ERROR,
                    status_code=500,
                    dev_detail=f"OS failed to create local database directory at path: {database_path}.",
                ) from e

        return database_path

    def get_collection_name(self, project_id: str, session_id: str) -> str:
        return f"collection_{session_id}_{project_id}".replace("-", "_").strip()

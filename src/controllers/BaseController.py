import os
import random
import string

from helpers.config import get_settings


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
            os.makedirs(database_path)
        return database_path

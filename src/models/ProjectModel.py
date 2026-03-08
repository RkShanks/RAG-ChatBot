import math
from typing import List, Tuple

from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum


class ProjectModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    async def create_project(self, project_data: Project) -> Project:

        # Convert the Pydantic model to a dictionary, excluding None values and using aliases
        project = project_data.model_dump(by_alias=True, exclude_none=True)
        result = await self.collection.insert_one(project)

        project_data._id = result.inserted_id
        return project_data

    async def get_project_or_create(self, project_id: str) -> Project:
        # Try to find the project by its ID
        record = await self.collection.find_one(
            {
                "project_id": project_id,
            }
        )
        if not record:
            # If the project doesn't exist, create a new one
            new_project = Project(project_id=project_id)
            record = await self.create_project(new_project)
        return Project.model_validate(record)

    async def get_all_projects(
        self, page: int, page_size: int
    ) -> Tuple[List[Project], int]:

        # 1. Count total documents
        total_documents = await self.collection.count_documents({})

        # 2. Calculate total pages cleanly using math.ceil
        total_pages = (
            math.ceil(total_documents / page_size) if total_documents > 0 else 0
        )

        # 3. Fetch the data for the requested page
        skip_amount = (page - 1) * page_size
        cursor = self.collection.find({}).skip(skip_amount).limit(page_size)
        raw_documents = await cursor.to_list(length=page_size)

        # 4. Parse the raw documents into Pydantic models
        projects = [Project.model_validate(doc) for doc in raw_documents]

        return projects, total_pages

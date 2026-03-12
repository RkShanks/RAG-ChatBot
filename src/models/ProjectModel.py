import logging
import math
from typing import List, Tuple

from pymongo import ReturnDocument

from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

logger = logging.getLogger(__name__)


class ProjectModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
        self.document_class = Project

    async def create_project(self, project_data: Project) -> Project:
        logger.debug(f"Creating project with ID: {project_data.project_id}")

        # Convert the Pydantic model to a dictionary, excluding None values and using aliases
        project = project_data.model_dump(by_alias=True, exclude_none=True)
        try:
            result = await self.collection.insert_one(project)
            logger.info(f"Project created with ID: {project_data.project_id} (MongoDB ID: {result.inserted_id})")
            project_data.id = str(result.inserted_id)

        except Exception:
            logger.exception(f"Error creating project with ID: {project_data.project_id}")
            raise

        return project_data

    async def get_project_or_create(self, project_id: str) -> Project:
        logger.debug(f"Retrieving or creating project with ID: {project_id}")
        # Try to find the project by its ID
        try:
            # This finds the project. If it doesn't exist, it creates it instantly.
            # ReturnDocument.AFTER ensures it returns the newly created document.
            record = await self.collection.find_one_and_update(
                {"project_id": project_id},
                {"$setOnInsert": {"project_id": project_id}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            logger.info(f"Project retrieved or created with ID: {project_id} (MongoDB ID: {record['_id']})")
            return Project.model_validate(record)

        except Exception:
            logger.exception(f"Error in get_project_or_create for ID {project_id}")
            raise

    async def get_all_projects(self, page: int, page_size: int) -> Tuple[List[Project], int]:
        logger.debug(f"Retrieving all projects with pagination - Page: {page}, Page Size: {page_size}")

        # 1. Count total documents
        try:
            total_documents = await self.collection.count_documents({})
            logger.info(f"Total projects in database: {total_documents}")
        except Exception:
            logger.exception("Error counting documents")
            raise

        # 2. Calculate total pages cleanly using math.ceil
        total_pages = math.ceil(total_documents / page_size) if total_documents > 0 else 0

        # 3. Fetch the data for the requested page
        skip_amount = (page - 1) * page_size
        try:
            cursor = self.collection.find({}).skip(skip_amount).limit(page_size)
            raw_documents = await cursor.to_list(length=page_size)
            logger.info(f"Fetched {len(raw_documents)} projects for page {page} with page size {page_size}")

        except Exception:
            logger.exception("Error fetching projects")
            raise

        # 4. Parse the raw documents into Pydantic models
        projects = [Project.model_validate(doc) for doc in raw_documents]

        return projects, total_pages

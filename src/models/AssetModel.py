import asyncio
import logging
import os
from typing import List

from bson import ObjectId

from helpers.exceptions import CustomAPIException
from helpers.ResponseEnums import ResponseSignal

from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums import AssetTypeEnum, DataBaseEnum

logger = logging.getLogger(__name__)


class AssetModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSETS_NAME.value]
        self.document_class = Asset

    async def delete_project_assets(self, asset_project_id: str) -> bool:
        logger.debug(f"Deleting all assets for project DB ID: {asset_project_id}")
        try:
            result = await self.collection.delete_many({"asset_project_id": ObjectId(asset_project_id)})
            logger.info(f"Deleted {result.deleted_count} assets for project DB ID: {asset_project_id}")
            return True
        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.INTERNAL_SERVER_ERROR,
                status_code=500,
                dev_detail=f"MongoDB failed to delete assets for project DB ID '{asset_project_id}'.",
            ) from e

    async def get_asset_by_id(self, asset_id: str) -> Asset:
        logger.debug(f"Retrieving asset by DB ID: {asset_id}")
        try:
            doc = await self.collection.find_one({"_id": ObjectId(asset_id)})
            if not doc:
                return None
            return Asset.model_validate(doc)
        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.ASSET_RETRIEVAL_FAILED,
                status_code=500,
                dev_detail=f"MongoDB query failed for asset ID '{asset_id}'.",
            ) from e

    async def delete_asset_by_id(self, asset_id: str) -> bool:
        logger.debug(f"Deleting asset by DB ID: {asset_id}")
        try:
            result = await self.collection.delete_one({"_id": ObjectId(asset_id)})
            return result.deleted_count > 0
        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.INTERNAL_SERVER_ERROR,
                status_code=500,
                dev_detail=f"MongoDB failed to delete asset ID '{asset_id}'.",
            ) from e

    async def create_asset(self, asset: Asset) -> Asset:
        logger.debug(f"Creating asset with name: {asset.asset_name}")

        # Convert the Pydantic model to a dictionary, excluding None values and using aliases
        asset_dict = asset.model_dump(by_alias=True, exclude_none=True)
        try:
            result = await self.collection.insert_one(asset_dict)
            logger.info(f"Asset created with name: {asset.asset_name} (MongoDB ID: {result.inserted_id})")
            asset.id = result.inserted_id

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.ASSET_CREATION_FAILED,
                status_code=500,
                dev_detail=f"MongoDB failed to insert asset '{asset.asset_name}'.",
            ) from e

        return asset

    async def get_all_project_assets(self, asset_project_id: str, asset_type: str) -> List[Asset]:
        logger.debug(f"Retrieving all assets for project_id: {asset_project_id}")

        try:
            cursor = self.collection.find(
                {
                    "asset_project_id": ObjectId(asset_project_id),
                    "asset_type": asset_type,
                },
            )
            raw_assets = await cursor.to_list(length=None)
            assets = [Asset.model_validate(doc) for doc in raw_assets]
            logger.info(f"Retrieved {len(assets)} assets for project_id: {asset_project_id}")
            return assets

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.ASSET_RETRIEVAL_FAILED,
                status_code=500,
                dev_detail=f"Failed to retrieve assets of type '{asset_type}' for project '{asset_project_id}'.",
            ) from e

    async def create_from_file(self, project_id: str, file_id: str, file_path: str):
        logger.debug(
            f"Attempting to create Asset record from disk file '{file_id}' (Path: '{file_path}') for project ID: '{project_id}'"
        )

        # 1. get file size in a non-blocking way
        try:
            file_size_bytes = await asyncio.to_thread(os.path.getsize, file_path)
            file_size_kb = file_size_bytes / 1024

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.FILE_NOT_FOUND,
                status_code=404,
                dev_detail=f"Disk IO failure calculating size for '{file_path}'.",
            ) from e

        # 2. Build the strict Pydantic model internally
        asset_resource = Asset(
            asset_project_id=ObjectId(project_id),
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=file_size_bytes,
        )

        # 3. Insert the new Asset record into MongoDB
        try:
            # We call the core insertion method with await!
            result = await self.create_asset(asset=asset_resource)
            logger.info(f"Asset record created effectively for file '{file_id}' ({file_size_kb:.2f} KB)")
            return result

        except CustomAPIException:
            # The Pass-Through: Prevent double-wrapping if create_asset fails!
            raise

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.ASSET_CREATION_FAILED,
                status_code=500,
                dev_detail=f"Database insertion failed during asset creation for '{file_id}'",
            ) from e

    async def get_asset_record(self, asset_project_id: str, asset_name: str) -> Asset:
        logger.debug(f"Retrieving asset record for project_id: {asset_project_id} and asset_name: {asset_name}")

        try:
            doc = await self.collection.find_one(
                {
                    "asset_project_id": ObjectId(asset_project_id),
                    "asset_name": asset_name,
                },
            )
            if doc is None:
                logger.warning(f"No asset found for project_id: {asset_project_id} and asset_name: {asset_name}")
                return None

            asset = Asset.model_validate(doc)
            logger.info(f"Asset record retrieved for asset_name: {asset_name} in project_id: {asset_project_id}")
            return asset

        except Exception as e:
            raise CustomAPIException(
                signal_enum=ResponseSignal.ASSET_RETRIEVAL_FAILED,
                status_code=500,
                dev_detail=f"MongoDB query crashed while fetching '{asset_name}' for project '{asset_project_id}'.",
            ) from e

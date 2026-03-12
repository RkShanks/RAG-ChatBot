from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class Asset(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    asset_project_id: ObjectId
    asset_name: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    asset_size: Optional[int] = Field(gt=0, default=None)
    asset_config: dict = Field(default_factory=dict)
    asset_pushed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("asset_project_id", 1),
                    ("asset_name", 1),
                ],
                "name": "asset_project_id_name_index_1",
                "unique": True,
            },
        ]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

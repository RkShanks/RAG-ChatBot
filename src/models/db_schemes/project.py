from typing import Any, Optional, List, Dict

from bson import ObjectId
from pydantic import BaseModel, Field, validator


class Project(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    project_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    project_name: Optional[str] = Field(default="Untitled Workspace")
    chat_history: List[Dict[str, Any]] = Field(default_factory=list)

    @validator("project_id")
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError("Project ID must be alphanumeric")
        return value

    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [("project_id", 1), ("session_id", 1)],
                "name": "project_id_session_id_index_1",
                "unique": True,
            }
        ]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

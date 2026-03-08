from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, validator


class Project(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    project_id: str = Field(..., min_length=1)

    @validator("project_id")
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError("Project ID must be alphanumeric")
        return value

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True

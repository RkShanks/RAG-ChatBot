from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class DataChunk(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_index: int = Field(..., gt=0)
    chunk_project_id: ObjectId

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True

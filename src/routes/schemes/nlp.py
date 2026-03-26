from typing import Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    filter_criteria: Optional[dict] = None

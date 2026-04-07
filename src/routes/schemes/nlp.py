from typing import Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    filter_criteria: Optional[dict] = None
    target_locale: Optional[str] = "based in last user Query"
    chat_history: Optional[list] = None

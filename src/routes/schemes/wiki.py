from typing import Optional

from pydantic import BaseModel


class SearchWikiRequest(BaseModel):
    query: str
    lang: Optional[str] = "en"

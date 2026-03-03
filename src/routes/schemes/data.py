from typing import Optional

from pydantic import BaseModel


class ProcessRequest(BaseModel):
    file_id: str
    do_reset: Optional[int] = 0

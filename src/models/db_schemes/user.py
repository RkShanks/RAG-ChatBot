from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    """Pydantic schema for anonymous user profile data."""

    session_id: str
    display_name: Optional[str] = Field(default="", max_length=50)
    avatar_color: Optional[str] = Field(default="hsl(220, 70%, 50%)")

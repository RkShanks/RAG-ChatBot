import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    # Auto-generate a UUID if the user doesn't provide one
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    # The dense mathematical meaning (from Cohere/Gemini/OpenAI)
    vector: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Optional keyword math for Hybrid Search (e.g., Fastembed)
    sparse_vector: Optional[Dict[str, List[float]]] = None

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class HistorySchema(BaseModel):
    user_id: str = Field(..., description="The ID of the user who owns this history item")
    title: str = Field(..., max_length=100, description="Short title/snippet of the summary")
    original_text: str = Field(..., description="The original text input")
    summary_result: Dict[str, Any] = Field(..., description="The full JSON result from the summarizer")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_favorite: bool = Field(default=False)

    class Config:
        schema_extra = {
            "example": {
                "user_id": "60d5ec...",
                "title": "Quantum Computing Basics...",
                "original_text": "Full text here...",
                "summary_result": {"basic_summary": "...", "ai_summary": "..."},
                "created_at": "2023-10-27T10:00:00",
                "is_favorite": False
            }
        }

class HistoryResponseSchema(BaseModel):
    id: str
    title: str
    created_at: datetime
    is_favorite: bool

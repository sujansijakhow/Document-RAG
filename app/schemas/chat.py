from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Stable ID for one multi-turn conversation.")
    message: str = Field(..., min_length=1)


class RetrievedSource(BaseModel):
    document_id: str
    chunk_index: int
    score: float
    text: str


class BookingStatus(BaseModel):
    active: bool = False
    collected: dict[str, str] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    completed: bool = False


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[RetrievedSource] = Field(default_factory=list)
    booking_status: BookingStatus

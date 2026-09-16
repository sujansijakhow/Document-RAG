from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ChunkingStrategy(str, Enum):
    fixed_size = "fixed_size"
    recursive_paragraph = "recursive_paragraph"


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    chunking_strategy: str
    num_chunks: int
    char_count: int
    uploaded_at: datetime


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    chunking_strategy: str
    num_chunks: int
    uploaded_at: datetime

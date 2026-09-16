from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookingRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    name: str
    email: str
    date: str
    time: str
    created_at: datetime

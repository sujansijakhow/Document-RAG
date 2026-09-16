from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.schemas.booking import BookingRecord

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingRecord])
def list_bookings(db: Session = Depends(get_db)) -> list[Booking]:
    return list(db.execute(select(Booking).order_by(Booking.created_at.desc())).scalars())

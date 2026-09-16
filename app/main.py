from __future__ import annotations

from fastapi import FastAPI

from app.database import init_db
from app.routers.bookings import router as bookings_router
from app.routers.chat import router as chat_router
from app.routers.ingestion import router as ingestion_router

app = FastAPI(title="Palm Mind AI Backend", version="0.1.0")
app.include_router(ingestion_router)
app.include_router(chat_router)
app.include_router(bookings_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}

from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.booking import BookingService
from app.services.embeddings import get_embedding_service
from app.services.llm import get_llm_provider
from app.services.memory import get_chat_memory
from app.services.rag import RagService
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@lru_cache
def get_rag_service() -> RagService:
    settings = get_settings()
    llm = get_llm_provider()
    return RagService(
        embeddings=get_embedding_service(),
        vector_store=get_vector_store(),
        llm=llm,
        memory=get_chat_memory(),
        booking_service=BookingService(llm),
        top_k=settings.top_k,
    )


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    rag: RagService = Depends(get_rag_service),
) -> ChatResponse:
    answer, sources, booking_status = await rag.handle_message(
        db=db, session_id=payload.session_id, message=payload.message
    )
    return ChatResponse(
        session_id=payload.session_id,
        answer=answer,
        sources=sources,
        booking_status=booking_status,
    )

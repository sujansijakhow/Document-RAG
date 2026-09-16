from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.chat import BookingStatus, RetrievedSource
from app.services.booking import BookingService
from app.services.embeddings import EmbeddingService
from app.services.llm import LLMProvider
from app.services.memory import ChatMemory
from app.services.vector_store import VectorStore

_RAG_SYSTEM_PROMPT = """You are a helpful assistant answering questions using ONLY the provided \
context excerpts from the user's uploaded documents. If the context does not contain the answer, \
say you don't have enough information in the documents rather than guessing. Be concise.

You can also help the user book an interview (name, email, date, time) if they ask to - a \
separate part of the system handles collecting those details, so if the user is mid-booking you \
can acknowledge that naturally instead of answering from the documents."""


class RagService:
    def __init__(
        self,
        embeddings: EmbeddingService,
        vector_store: VectorStore,
        llm: LLMProvider,
        memory: ChatMemory,
        booking_service: BookingService,
        top_k: int,
    ) -> None:
        self._embeddings = embeddings
        self._vector_store = vector_store
        self._llm = llm
        self._memory = memory
        self._booking_service = booking_service
        self._top_k = top_k

    async def handle_message(
        self, db: Session, session_id: str, message: str
    ) -> tuple[str, list[RetrievedSource], BookingStatus]:
        history = await self._memory.get_history(session_id)
        pending_slots = await self._memory.get_pending_booking(session_id)

        booking_result, new_pending = await self._booking_service.process_turn(
            db=db,
            session_id=session_id,
            user_message=message,
            history=history,
            pending_slots=pending_slots,
        )
        await self._memory.set_pending_booking(session_id, new_pending)

        if booking_result.completed:
            answer = booking_result.confirmation_message or "Your booking is confirmed."
            sources: list[RetrievedSource] = []
        elif booking_result.active:
            answer = self._ask_for_missing_fields(booking_result.missing_fields)
            sources = []
        else:
            answer, sources = await self._answer_from_documents(message, history)

        await self._memory.append_turn(session_id, "user", message)
        await self._memory.append_turn(session_id, "assistant", answer)

        status = BookingStatus(
            active=booking_result.active,
            collected=booking_result.collected,
            missing_fields=booking_result.missing_fields,
            completed=booking_result.completed,
        )
        return answer, sources, status

    async def _answer_from_documents(
        self, message: str, history: list[dict[str, str]]
    ) -> tuple[str, list[RetrievedSource]]:
        query_vector = self._embeddings.embed_one(message)
        matches = self._vector_store.search(query_vector, top_k=self._top_k)

        context_block = "\n\n".join(
            f"[Source {i + 1}] {m.text}" for i, m in enumerate(matches)
        ) or "(no relevant documents found)"

        history_block = "\n".join(f"{t['role']}: {t['content']}" for t in history[-6:])
        user_prompt = (
            f"Conversation history:\n{history_block}\n\n"
            f"Context from documents:\n{context_block}\n\n"
            f"Question: {message}"
        )

        answer = await self._llm.complete(_RAG_SYSTEM_PROMPT, user_prompt)
        sources = [
            RetrievedSource(
                document_id=m.document_id,
                chunk_index=m.chunk_index,
                score=m.score,
                text=m.text,
            )
            for m in matches
        ]
        return answer, sources

    @staticmethod
    def _ask_for_missing_fields(missing_fields: list[str]) -> str:
        field_prompts = {
            "name": "your full name",
            "email": "your email address",
            "date": "your preferred interview date",
            "time": "your preferred interview time",
        }
        asks = ", ".join(field_prompts[f] for f in missing_fields)
        return f"Happy to set up your interview - could you share {asks}?"

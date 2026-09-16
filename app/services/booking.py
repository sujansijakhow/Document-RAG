from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.services.llm import LLMProvider

REQUIRED_FIELDS = ("name", "email", "date", "time")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_EXTRACTION_SYSTEM_PROMPT = """You are a slot-extraction module for an interview scheduling \
assistant. Given the conversation so far and the latest user message, decide whether the user \
wants to book an interview, and extract any of these fields present in the LATEST message only: \
name, email, date (YYYY-MM-DD if you can resolve it, otherwise as stated), time (HH:MM 24h if \
you can resolve it, otherwise as stated).

Respond with ONLY a JSON object, no other text, in this exact shape:
{"wants_booking": true|false, "fields": {"name": "...", "email": "...", "date": "...", "time": "..."}}

Omit a key from "fields" if that field was not mentioned in the latest message."""


@dataclass
class BookingTurnResult:
    active: bool
    collected: dict[str, str] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    completed: bool = False
    confirmation_message: str | None = None


class BookingService:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def process_turn(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        history: list[dict[str, str]],
        pending_slots: dict[str, str],
    ) -> tuple[BookingTurnResult, dict[str, str]]:
        was_active = bool(pending_slots)

        transcript = "\n".join(f"{t['role']}: {t['content']}" for t in history[-6:])
        user_prompt = f"Conversation so far:\n{transcript}\n\nLatest user message: {user_message}"

        extraction = await self._llm.complete_json(_EXTRACTION_SYSTEM_PROMPT, user_prompt)
        wants_booking = bool(extraction.get("wants_booking")) or was_active
        extracted_fields = extraction.get("fields") or {}

        if not wants_booking:
            return BookingTurnResult(active=False), pending_slots

        merged = {**pending_slots, **_clean_fields(extracted_fields)}
        missing = [f for f in REQUIRED_FIELDS if not merged.get(f)]

        if not missing:
            record = Booking(
                session_id=session_id,
                name=merged["name"],
                email=merged["email"],
                date=merged["date"],
                time=merged["time"],
            )
            db.add(record)
            db.commit()
            result = BookingTurnResult(
                active=True,
                collected=merged,
                missing_fields=[],
                completed=True,
                confirmation_message=(
                    f"You're booked in, {merged['name']}! Interview confirmed for "
                    f"{merged['date']} at {merged['time']}. A confirmation will be sent to "
                    f"{merged['email']}."
                ),
            )
            return result, {}

        result = BookingTurnResult(active=True, collected=merged, missing_fields=missing)
        return result, merged


def _clean_fields(fields: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key in REQUIRED_FIELDS:
        value = fields.get(key)
        if not value or not isinstance(value, str):
            continue
        value = value.strip()
        if key == "email" and not _EMAIL_RE.match(value):
            continue
        if value:
            cleaned[key] = value
    return cleaned

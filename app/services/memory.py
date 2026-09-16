from __future__ import annotations

import json
from functools import lru_cache

import redis.asyncio as redis

from app.config import get_settings

CHAT_KEY_PREFIX = "chat:"
BOOKING_KEY_PREFIX = "booking:"


class ChatMemory:
    def __init__(self, client: redis.Redis, ttl_seconds: int, max_turns: int) -> None:
        self._client = client
        self._ttl = ttl_seconds
        self._max_turns = max_turns

    async def append_turn(self, session_id: str, role: str, content: str) -> None:
        key = f"{CHAT_KEY_PREFIX}{session_id}"
        await self._client.rpush(key, json.dumps({"role": role, "content": content}))
        await self._client.ltrim(key, -self._max_turns, -1)
        await self._client.expire(key, self._ttl)

    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        key = f"{CHAT_KEY_PREFIX}{session_id}"
        raw_turns = await self._client.lrange(key, 0, -1)
        return [json.loads(turn) for turn in raw_turns]

    async def get_pending_booking(self, session_id: str) -> dict[str, str]:
        key = f"{BOOKING_KEY_PREFIX}{session_id}"
        raw = await self._client.get(key)
        return json.loads(raw) if raw else {}

    async def set_pending_booking(self, session_id: str, slots: dict[str, str]) -> None:
        key = f"{BOOKING_KEY_PREFIX}{session_id}"
        await self._client.set(key, json.dumps(slots), ex=self._ttl)

    async def clear_pending_booking(self, session_id: str) -> None:
        await self._client.delete(f"{BOOKING_KEY_PREFIX}{session_id}")


@lru_cache
def get_chat_memory() -> ChatMemory:
    settings = get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)
    return ChatMemory(client, settings.chat_history_ttl_seconds, settings.chat_history_max_turns)

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.schemas.document import ChunkingStrategy


class Chunker(ABC):
    @abstractmethod
    def split(self, text: str) -> list[str]:
        ...


class FixedSizeChunker(Chunker):
    def __init__(self, chunk_size: int = 800, overlap: int = 100) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        chunks: list[str] = []
        step = self.chunk_size - self.overlap
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size].strip()
            if chunk:
                chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class RecursiveParagraphChunker(Chunker):
    _SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_chunk_size: int = 800, min_chunk_size: int = 200) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def split(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        units: list[str] = []
        for para in paragraphs:
            if len(para) <= self.max_chunk_size:
                units.append(para)
            else:
                units.extend(s for s in self._SENTENCE_RE.split(para) if s.strip())

        chunks: list[str] = []
        buffer = ""
        for unit in units:
            candidate = f"{buffer} {unit}".strip() if buffer else unit
            if len(candidate) <= self.max_chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = unit
        if buffer:
            chunks.append(buffer)

        if len(chunks) > 1 and len(chunks[-1]) < self.min_chunk_size:
            chunks[-2] = f"{chunks[-2]} {chunks.pop()}".strip()

        return chunks


_STRATEGIES: dict[ChunkingStrategy, type[Chunker]] = {
    ChunkingStrategy.fixed_size: FixedSizeChunker,
    ChunkingStrategy.recursive_paragraph: RecursiveParagraphChunker,
}


def get_chunker(strategy: ChunkingStrategy) -> Chunker:
    return _STRATEGIES[strategy]()

from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import get_settings


@dataclass(frozen=True)
class ScoredChunk:
    vector_id: str
    document_id: str
    chunk_index: int
    text: str
    score: float


class VectorStore:
    def __init__(self, path: str, collection: str, vector_size: int) -> None:
        self._client = QdrantClient(path=path)
        self._collection = collection
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(
                    size=vector_size, distance=qmodels.Distance.COSINE
                ),
            )

    def upsert_chunks(
        self,
        document_id: str,
        chunks: list[str],
        vectors: list[list[float]],
    ) -> list[str]:
        vector_ids = [str(uuid.uuid4()) for _ in chunks]
        points = [
            qmodels.PointStruct(
                id=vector_id,
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_index": index,
                    "text": chunk,
                },
            )
            for index, (vector_id, chunk, vector) in enumerate(zip(vector_ids, chunks, vectors))
        ]
        self._client.upsert(collection_name=self._collection, points=points)
        return vector_ids

    def search(self, query_vector: list[float], top_k: int) -> list[ScoredChunk]:
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
        )
        return [
            ScoredChunk(
                vector_id=str(r.id),
                document_id=r.payload["document_id"],
                chunk_index=r.payload["chunk_index"],
                text=r.payload["text"],
                score=r.score,
            )
            for r in results
        ]


@lru_cache
def get_vector_store() -> VectorStore:
    from app.services.embeddings import get_embedding_service

    settings = get_settings()
    settings.ensure_data_dirs()
    dimension = get_embedding_service().dimension
    return VectorStore(settings.qdrant_path, settings.qdrant_collection, dimension)

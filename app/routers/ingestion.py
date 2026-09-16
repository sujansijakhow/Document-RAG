from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.schemas.document import ChunkingStrategy, DocumentUploadResponse
from app.services.chunking import get_chunker
from app.services.embeddings import EmbeddingService, get_embedding_service
from app.services.text_extraction import extract_text
from app.services.vector_store import VectorStore, get_vector_store

router = APIRouter(prefix="/api/v1/documents", tags=["ingestion"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    chunking_strategy: ChunkingStrategy = Form(default=ChunkingStrategy.recursive_paragraph),
    db: Session = Depends(get_db),
    embeddings: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store),
) -> Document:
    text = await extract_text(file)

    chunker = get_chunker(chunking_strategy)
    chunks = chunker.split(text)

    document = Document(
        filename=file.filename or "unknown",
        content_type=file.content_type or "unknown",
        chunking_strategy=chunking_strategy.value,
        num_chunks=len(chunks),
        char_count=len(text),
    )
    db.add(document)
    db.flush()

    if chunks:
        vectors = embeddings.embed(chunks)
        vector_ids = vector_store.upsert_chunks(document.id, chunks, vectors)
        for index, (vector_id, chunk) in enumerate(zip(vector_ids, chunks)):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    vector_id=vector_id,
                    chunk_index=index,
                    char_count=len(chunk),
                )
            )

    db.commit()
    db.refresh(document)
    logger.info("Ingested document %s (%d chunks, strategy=%s)", document.id, len(chunks), chunking_strategy)
    return document

from __future__ import annotations

import io

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

SUPPORTED_CONTENT_TYPES = {"application/pdf", "text/plain"}


async def extract_text(file: UploadFile) -> str:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = (file.filename or "").lower()
    content_type = file.content_type or ""

    is_pdf = filename.endswith(".pdf") or content_type == "application/pdf"
    is_txt = filename.endswith(".txt") or content_type == "text/plain"

    if is_pdf:
        return _extract_pdf(raw)
    if is_txt:
        return _extract_txt(raw)

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Only .pdf and .txt files are accepted.",
    )


def _extract_pdf(raw: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(raw))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not parse PDF: {exc}") from exc

    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in PDF (it may be a scanned/image-only PDF).",
        )
    return text


def _extract_txt(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="Could not decode text file.")

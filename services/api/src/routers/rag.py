"""Developlus API — RAG Router (Document Upload & Management)"""
import os
from typing import List
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.dependencies import CurrentUser, DBSession
from src.schemas import DocumentResponse, SuccessResponse
from src.services import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])

ALLOWED_TYPES = {"application/pdf", "text/plain", "text/markdown"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(current_user: CurrentUser, db: DBSession):
    """Kullanıcının yüklediği belgeleri listeler."""
    docs = await rag_service.get_documents(db, current_user.id)
    return docs


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    current_user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
):
    """
    Belge yükler ve arka planda Celery task ile indexler.
    Desteklenen formatlar: PDF, TXT, MD
    """
    # Boyut kontrolü
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya boyutu 10 MB'ı aşamaz",
        )

    # Tip kontrolü
    file_type = file.content_type or "application/octet-stream"
    ext = os.path.splitext(file.filename or "")[1].lower()
    if file_type not in ALLOWED_TYPES and ext not in {".pdf", ".txt", ".md"}:
        raise HTTPException(
            status_code=415,
            detail="Desteklenmeyen dosya türü. PDF, TXT veya MD yükleyebilirsiniz.",
        )

    # Veritabanına kaydet
    doc = await rag_service.create_document_record(
        db=db,
        user_id=current_user.id,
        filename=file.filename or "untitled",
        file_type=file_type,
        file_size=len(content),
    )

    # Celery task ile arka planda indexle
    try:
        from src.celery_client import index_document_task
        index_document_task.delay(str(doc.id), content.decode("utf-8", errors="ignore")
                                  if ext != ".pdf" else None,
                                  content.hex() if ext == ".pdf" else None)
    except Exception:
        # Celery bağlantısı yoksa basit metin çıkarımı yap
        if ext == ".pdf":
            text = rag_service.extract_text_from_pdf(content)
        else:
            text = content.decode("utf-8", errors="ignore")

        # Senkron indexleme (fallback)
        await _index_document_sync(db, doc, text)

    return doc


async def _index_document_sync(db, doc, text: str):
    """Celery olmadan senkron indexleme (dev/fallback)."""
    from src.models import DocumentChunk
    from src.services.llm_service import create_embedding

    chunks = rag_service.chunk_text(text)
    doc.status = "processing"
    await db.flush()

    indexed = 0
    for i, chunk_text in enumerate(chunks):
        try:
            embedding = await create_embedding(chunk_text)
            chunk = DocumentChunk(
                document_id=doc.id,
                user_id=doc.user_id,
                chunk_index=i,
                chunk_text=chunk_text,
                embedding=embedding,
                token_count=len(chunk_text.split()),
            )
            db.add(chunk)
            indexed += 1
        except Exception:
            continue

    doc.chunk_count = indexed
    doc.status = "ready" if indexed > 0 else "failed"
    await db.flush()


@router.delete("/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(document_id: UUID, current_user: CurrentUser, db: DBSession):
    """Belgeyi ve tüm chunk'larını siler."""
    from sqlalchemy import select
    from src.models import Document

    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")

    await rag_service.delete_document(db, doc)
    return SuccessResponse(message="Belge silindi")

"""Developlus API — RAG Service (pgvector similarity search)"""
import io
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Document, DocumentChunk
from src.services import llm_service


async def get_documents(db: AsyncSession, user_id: UUID) -> List[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def create_document_record(
    db: AsyncSession, user_id: UUID, filename: str,
    file_type: str, file_size: int
) -> Document:
    doc = Document(
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        status="pending",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def delete_document(db: AsyncSession, document: Document) -> None:
    await db.delete(document)


async def similarity_search(
    db: AsyncSession,
    query: str,
    user_id: UUID,
    top_k: int = 5,
    threshold: float = 0.7,
) -> List[str]:
    """Kullanıcının belgelerinde pgvector cosine similarity araması yapar."""
    try:
        query_embedding = await llm_service.create_embedding(query)
    except Exception:
        return []

    # pgvector cosine distance sorgusu
    sql = text("""
        SELECT chunk_text,
               1 - (embedding <=> :embedding::vector) AS similarity
        FROM document_chunks
        WHERE user_id = :user_id
          AND 1 - (embedding <=> :embedding::vector) >= :threshold
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "embedding": str(query_embedding),
        "user_id": str(user_id),
        "threshold": threshold,
        "top_k": top_k,
    })

    rows = result.fetchall()
    return [row.chunk_text for row in rows]


async def build_rag_context(chunks: List[str]) -> Optional[str]:
    if not chunks:
        return None
    context_parts = [f"[Kaynak {i+1}]\n{chunk}" for i, chunk in enumerate(chunks)]
    return "\n\n".join(context_parts)


def extract_text_from_pdf(content: bytes) -> str:
    """PDF içeriğini metin olarak çıkarır."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        texts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                texts.append(text.strip())
        return "\n\n".join(texts)
    except Exception:
        return ""


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Metni örtüşen chunk'lara böler."""
    if not text.strip():
        return []

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks

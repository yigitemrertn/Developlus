"""Developlus Worker — Document Indexing Tasks"""
import asyncio
import os
from typing import Optional

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")


def get_async_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
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


async def _create_embedding(text: str):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=os.getenv("LITELLM_MASTER_KEY", ""),
        base_url=f"{os.getenv('LITELLM_PROXY_URL', 'http://litellm:4000')}/v1",
    )
    response = await client.embeddings.create(model="qwen-embedding", input=text)
    return response.data[0].embedding


async def _index_document(document_id: str, text: str):
    """Metni chunk'lar, embedding oluşturur, veritabanına kaydeder."""
    from sqlalchemy import select, update
    # Import models inline to avoid circular deps
    import sys, importlib
    sys.path.insert(0, "/app")

    AsyncSession = get_async_session()

    async with AsyncSession() as db:
        # Document kaydını bul
        from sqlalchemy.sql import text as sql_text
        result = await db.execute(
            sql_text("SELECT id, user_id FROM documents WHERE id = :id"),
            {"id": document_id}
        )
        doc_row = result.fetchone()
        if not doc_row:
            return

        # Durumu güncelle
        await db.execute(
            sql_text("UPDATE documents SET status = 'processing' WHERE id = :id"),
            {"id": document_id}
        )
        await db.commit()

        # Chunk'la ve indexle
        chunks = chunk_text(text)
        indexed = 0

        for i, chunk in enumerate(chunks):
            try:
                embedding = await _create_embedding(chunk)
                embedding_str = f"[{','.join(map(str, embedding))}]"
                await db.execute(sql_text("""
                    INSERT INTO document_chunks
                        (document_id, user_id, chunk_index, chunk_text, embedding, token_count)
                    VALUES (:doc_id, :user_id, :idx, :text, :emb::vector, :tokens)
                """), {
                    "doc_id": document_id,
                    "user_id": str(doc_row.user_id),
                    "idx": i,
                    "text": chunk,
                    "emb": embedding_str,
                    "tokens": len(chunk.split()),
                })
                await db.commit()
                indexed += 1
            except Exception as e:
                print(f"Chunk {i} indexlenemedi: {e}")
                continue

        # Sonucu güncelle
        status = "ready" if indexed > 0 else "failed"
        await db.execute(sql_text("""
            UPDATE documents SET status = :status, chunk_count = :count WHERE id = :id
        """), {"status": status, "count": indexed, "id": document_id})
        await db.commit()
        print(f"Belge indexlendi: {document_id} — {indexed}/{len(chunks)} chunk")


@shared_task(
    bind=True,
    name="src.tasks.document_tasks.index_document",
    max_retries=3,
    default_retry_delay=60,
    queue="documents",
)
def index_document(self, document_id: str, text: Optional[str] = None, pdf_hex: Optional[str] = None):
    """Belgeyi indexler. PDF veya düz metin alır."""
    try:
        if pdf_hex:
            import io, pypdf
            content = bytes.fromhex(pdf_hex)
            reader = pypdf.PdfReader(io.BytesIO(content))
            text = "\n\n".join(
                page.extract_text() for page in reader.pages if page.extract_text()
            )

        if not text:
            raise ValueError("İşlenecek metin yok")

        asyncio.run(_index_document(document_id, text))

    except Exception as exc:
        raise self.retry(exc=exc)

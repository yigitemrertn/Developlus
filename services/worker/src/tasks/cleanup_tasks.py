"""Developlus Worker — Cleanup Tasks"""
import asyncio
import os
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _cleanup_expired_tokens():
    SessionLocal = get_session()
    async with SessionLocal() as db:
        result = await db.execute(text("""
            DELETE FROM refresh_tokens
            WHERE expires_at < NOW()
            RETURNING id
        """))
        deleted = result.rowcount
        await db.commit()
        print(f"Süresi dolmuş {deleted} refresh token silindi")


async def _cleanup_failed_documents():
    SessionLocal = get_session()
    async with SessionLocal() as db:
        result = await db.execute(text("""
            DELETE FROM documents
            WHERE status = 'failed'
              AND created_at < NOW() - INTERVAL '7 days'
            RETURNING id
        """))
        deleted = result.rowcount
        await db.commit()
        print(f"Başarısız {deleted} belge kaydı temizlendi")


@shared_task(name="src.tasks.cleanup_tasks.cleanup_expired_tokens", queue="default")
def cleanup_expired_tokens():
    asyncio.run(_cleanup_expired_tokens())


@shared_task(name="src.tasks.cleanup_tasks.cleanup_failed_documents", queue="default")
def cleanup_failed_documents():
    asyncio.run(_cleanup_failed_documents())

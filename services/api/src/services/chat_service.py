"""Developlus API — Chat Service"""
import time
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ChatSession, Message
from src.schemas import SessionCreate, SessionUpdate
from src.services import cache_service, llm_service


async def get_sessions(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 50) -> List[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_session(db: AsyncSession, user_id: UUID, data: SessionCreate) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        title=data.title,
        model_used=data.model_used,
        system_prompt=data.system_prompt,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        use_rag=data.use_rag,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID, user_id: UUID) -> Optional[ChatSession]:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_session(db: AsyncSession, session: ChatSession, data: SessionUpdate) -> ChatSession:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(session, field, value)
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await cache_service.cache_delete(cache_service.session_history_key(str(session.id)))


async def get_messages(db: AsyncSession, session_id: UUID) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


async def get_message_count(db: AsyncSession, session_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).where(Message.session_id == session_id)
    )
    return result.scalar() or 0


async def _get_session_history(db: AsyncSession, session_id: UUID) -> List[dict]:
    """Redis önbellekli konuşma geçmişi."""
    cache_key = cache_service.session_history_key(str(session_id))
    cached = await cache_service.cache_get(cache_key)
    if cached:
        return cached

    messages = await get_messages(db, session_id)
    history = [{"role": m.role, "content": m.content} for m in messages]
    await cache_service.cache_set(cache_key, history, ttl=86400)
    return history


async def stream_chat(
    db: AsyncSession,
    session: ChatSession,
    user_message: str,
    rag_context: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """SSE streaming: mesajı kaydeder, LLM'den token token yanıt alır."""

    # Kullanıcı mesajını kaydet
    user_msg = Message(
        session_id=session.id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # Geçmişi al
    history = await _get_session_history(db, session.id)

    # LLM mesajlarını oluştur
    llm_messages = await llm_service.build_messages(
        session_history=history[:-1] if history else [],
        user_message=user_message,
        system_prompt=session.system_prompt,
        rag_context=rag_context,
    )

    # Streaming
    full_response = ""
    start = time.monotonic()

    async for token in llm_service.chat_completion_stream(
        messages=llm_messages,
        model=session.model_used,
        temperature=session.temperature,
        max_tokens=session.max_tokens,
    ):
        full_response += token
        yield token

    latency_ms = int((time.monotonic() - start) * 1000)

    # Asistan yanıtını kaydet
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=full_response,
        latency_ms=latency_ms,
        model=session.model_used,
    )
    db.add(assistant_msg)

    # Oturum başlığını ilk mesajdan güncelle
    if session.title == "Yeni Sohbet":
        session.title = user_message[:60] + ("..." if len(user_message) > 60 else "")

    await db.flush()

    # Cache'i geçersiz kıl → bir sonraki istekte yeniden yüklenecek
    await cache_service.cache_delete(cache_service.session_history_key(str(session.id)))

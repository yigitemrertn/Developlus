"""Developlus API — Chat Router (Sessions + SSE Streaming)"""
import asyncio
import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import CurrentUser, DBSession
from src.schemas import (
    ChatRequest, MessageResponse, SessionCreate,
    SessionResponse, SessionUpdate, SuccessResponse
)
from src.services import chat_service, rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])


# ─────────────────────────────────────────────────────────────────────────────
#  SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(current_user: CurrentUser, db: DBSession, skip: int = 0, limit: int = 50):
    """Kullanıcının tüm oturumlarını listeler."""
    sessions = await chat_service.get_sessions(db, current_user.id, skip, limit)
    result = []
    for session in sessions:
        count = await chat_service.get_message_count(db, session.id)
        response = SessionResponse(
            id=session.id,
            title=session.title,
            model_used=session.model_used,
            system_prompt=session.system_prompt,
            temperature=session.temperature,
            max_tokens=session.max_tokens,
            use_rag=session.use_rag,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=count,
        )
        result.append(response)
    return result


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(data: SessionCreate, current_user: CurrentUser, db: DBSession):
    """Yeni chat oturumu oluşturur."""
    session = await chat_service.create_session(db, current_user.id, data)
    return SessionResponse(
        id=session.id,
        title=session.title,
        model_used=session.model_used,
        system_prompt=session.system_prompt,
        temperature=session.temperature,
        max_tokens=session.max_tokens,
        use_rag=session.use_rag,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID, data: SessionUpdate, current_user: CurrentUser, db: DBSession
):
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")
    updated = await chat_service.update_session(db, session, data)
    count = await chat_service.get_message_count(db, updated.id)
    return SessionResponse(
        id=updated.id, title=updated.title, model_used=updated.model_used,
        system_prompt=updated.system_prompt, temperature=updated.temperature,
        max_tokens=updated.max_tokens, use_rag=updated.use_rag,
        created_at=updated.created_at, updated_at=updated.updated_at,
        message_count=count,
    )


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def delete_session(session_id: UUID, current_user: CurrentUser, db: DBSession):
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")
    await chat_service.delete_session(db, session)
    return SuccessResponse(message="Oturum silindi")


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(session_id: UUID, current_user: CurrentUser, db: DBSession):
    """Oturuma ait tüm mesajları döner."""
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")
    messages = await chat_service.get_messages(db, session_id)
    return messages


# ─────────────────────────────────────────────────────────────────────────────
#  SSE STREAMING CHAT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/stream")
async def stream_chat(request: ChatRequest, current_user: CurrentUser, db: DBSession):
    """
    Server-Sent Events ile streaming chat.
    Frontend EventSource API veya fetch ile tüketilir.
    """
    session = await chat_service.get_session(db, request.session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")

    # RAG context oluştur (oturum RAG modundaysa)
    rag_context = None
    if session.use_rag:
        chunks = await rag_service.similarity_search(db, request.message, current_user.id)
        rag_context = await rag_service.build_rag_context(chunks)

    async def event_generator():
        try:
            async for token in chat_service.stream_chat(
                db=db,
                session=session,
                user_message=request.message,
                rag_context=rag_context,
            ):
                # SSE formatı: data: <payload>\n\n
                payload = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            # Stream bitti sinyali
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx buffering'i devre dışı bırak
        },
    )

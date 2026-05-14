"""Developlus API — Chat Service"""
import json
import time
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ChatSession, Message, ChatHistory, Project
from src.schemas import SessionCreate, SessionUpdate
from src.services import cache_service, llm_service, tavily_service


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
    """SSE streaming: mesajı kaydeder, LLM'den token token yanıt alır (Agentic Loop dahil)."""

    # Kullanıcı mesajını kaydet
    user_msg = Message(
        session_id=session.id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # Geçmişi al
    history = await _get_session_history(db, session.id) # type: ignore

    # LLM mesajlarını oluştur
    llm_messages = await llm_service.build_messages(
        session_history=history[:-1] if history else [],
        user_message=user_message,
        system_prompt=session.system_prompt, # type: ignore
        rag_context=rag_context, # type: ignore
    )

    tavily_tool = {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Tavily kullanarak internette arama yapar. Yeni teknolojiler, güncel versiyonlar veya bilinmeyen kütüphaneler hakkında bilgi almak için kullan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Arama sorgusu. Örn: 'React 19 features'"}
                },
                "required": ["query"]
            }
        }
    }
    tools = [tavily_tool]

    # Agentic Loop: 1. Adım (Araç Kullanımı Kontrolü)
    first_response = await llm_service.chat_completion(
        messages=llm_messages,
        model=session.model_used, # type: ignore
        temperature=session.temperature, # type: ignore
        max_tokens=1000, # type: ignore
        tools=tools,
    )

    search_sources = ""

    # Eğer LLM araç kullanmak istediyse
    if first_response.get("tool_calls"):
        tool_call = first_response["tool_calls"][0]
        if tool_call.function.name == "search_web":
            try:
                args = json.loads(tool_call.function.arguments)
                query = args.get("query")
                
                # Kullanıcıya UI'da arama yapıldığını göstermek için yield
                yield f"\n\n🔍 **Ajan İnternette Arıyor:** `{query}`\n\n"
                
                search_result = await tavily_service.search_web(query)
                
                # Araç çağrısını ve sonucunu mesajlara ekle
                llm_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": first_response["tool_calls"]
                })
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "search_web",
                    "content": search_result
                })
                
                search_sources = f"\n\n---\n**🔍 Agentic RAG Arama Kaynakları:**\n*Sorgu: {query}*\n*(Sonuçlar otonom olarak Tavily üzerinden çekilmiştir.)*"
            except Exception as e:
                pass # Hata durumunda devam et, LLM normal cevap versin

    # Streaming (Nihai Cevap)
    full_response = ""
    start = time.monotonic()

    async for token in llm_service.chat_completion_stream(
        messages=llm_messages,
        model=session.model_used, # type: ignore
        temperature=session.temperature, # type: ignore
        max_tokens=session.max_tokens, # type: ignore
    ):
        full_response += token
        yield token

    # Eğer arama yapıldıysa makale gereği açıklanabilirliği (explainability) artırmak için URL bilgisini ekle
    if search_sources:
        full_response += search_sources
        yield search_sources

    latency_ms = int((time.monotonic() - start) * 1000)

    # Asistan yanıtını kaydet
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=full_response,
        latency_ms=latency_ms,
        model=session.model_used, # type: ignore
    )
    db.add(assistant_msg)

    # Oturum başlığını ilk mesajdan güncelle
    if session.title == "Yeni Sohbet":
        setattr(session, "title", user_message[:60] + ("..." if len(user_message) > 60 else ""))

    await db.flush()

    # Cache'i geçersiz kıl → bir sonraki istekte yeniden yüklenecek
    await cache_service.cache_delete(cache_service.session_history_key(str(session.id))) # type: ignore


async def get_project_messages(db: AsyncSession, project_id: UUID) -> List[ChatHistory]:
    """Proje bazlı mesaj geçmişini döner."""
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.project_id == project_id)
        .order_by(ChatHistory.created_at)
    )
    return list(result.scalars().all())


async def stream_project_chat(
    db: AsyncSession,
    project_id: UUID,
    user_message: str,
    extra_context: str = "",
) -> AsyncGenerator[str, None]:
    """SSE streaming for Project-specific chat history with Agentic RAG."""
    import time
    print(f"DEBUG: stream_project_chat started for project_id: {project_id}")
    
    # 1. Kullanıcı mesajını kaydet
    user_msg = ChatHistory(
        project_id=project_id,
        role="user",
        message_content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # 2. Geçmişi al
    messages = await get_project_messages(db, project_id)
    history = [{"role": m.role, "content": m.message_content} for m in messages]

    # 3. LLM mesajlarını oluştur (Survey context dahil)
    llm_messages = await llm_service.build_messages(
        session_history=history[:-1] if history else [],
        user_message=user_message,
        system_prompt=f"Sen bir yazılım mimarı ve teknik danışmansın. Kullanıcının projesine özel teknoloji yığını (stack) önerileri veriyorsun. {extra_context}",
    )

    tavily_tool = {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Tavily kullanarak internette arama yapar. Yeni teknolojiler, kütüphaneler veya best-practice'ler hakkında güncel bilgi almak için kullan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Arama sorgusu."}
                },
                "required": ["query"]
            }
        }
    }

    # Agentic Loop
    first_response = await llm_service.chat_completion(
        messages=llm_messages,
        tools=[tavily_tool],
    )

    search_sources = ""
    if first_response.get("tool_calls"):
        tool_call = first_response["tool_calls"][0]
        # Dict veya Object erişimini garantiye alalım
        tc_name = tool_call.get("function", {}).get("name") if isinstance(tool_call, dict) else tool_call.function.name
        
        if tc_name == "search_web":
            try:
                tc_args_str = tool_call.get("function", {}).get("arguments") if isinstance(tool_call, dict) else tool_call.function.arguments
                args = json.loads(tc_args_str)
                query = args.get("query")
                yield f"\n\n🔍 **Arama Yapılıyor:** `{query}`\n\n"
                
                search_result = await tavily_service.search_web(query)
                llm_messages.append({"role": "assistant", "content": None, "tool_calls": first_response["tool_calls"]})
                
                tc_id = tool_call.get("id") if isinstance(tool_call, dict) else tool_call.id
                llm_messages.append({"role": "tool", "tool_call_id": tc_id, "name": "search_web", "content": search_result})
                search_sources = f"\n\n---\n**Kaynak:** Tavily Search (`{query}`)"
            except Exception as e:
                print(f"Tool call error: {e}")

    # Streaming Final Response
    full_response = ""
    start = time.monotonic()
    async for token in llm_service.chat_completion_stream(messages=llm_messages):
        full_response += token
        yield token

    if search_sources:
        full_response += search_sources
        yield search_sources

    # 4. Asistan yanıtını kaydet
    assistant_msg = ChatHistory(
        project_id=project_id,
        role="assistant",
        message_content=full_response,
        latency_ms=int((time.monotonic() - start) * 1000),
        model_used="qwen-turbo"
    )
    db.add(assistant_msg)
    await db.commit()

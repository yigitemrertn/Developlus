"""Developlus API - Chat Service (Agentic RAG)

Mimari:
  1. Kullanici mesaji + anket verileri alinir
  2. Dataset RAG: yerel TSDS + TDS veritabanindan ilgili sirket/arac profilleri cekilir
  3. Yeterliyse LLM e zengin context ile gonderilir
  4. Yetersizse Tavily Agentic RAG ile internetten arama yapilir
  5. Chat gecmisi her yanita context olarak dahil edilir
"""
import json
import time
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ChatHistory
from src.services import dataset_service, llm_service, tavily_service


# ─── Public API ──────────────────────────────────────────────────────────────

async def get_project_messages(
    db: AsyncSession,
    project_id: UUID,
) -> List[dict]:
    """Projeye ait tum mesajlari kronolojik sirayla doner."""
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.project_id == project_id)
        .order_by(ChatHistory.created_at.asc())
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "project_id": str(r.project_id),
            "role": r.role,
            "message_content": r.message_content,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "latency_ms": r.latency_ms,
            "model_used": getattr(r, "model_used", None),
        }
        for r in rows
    ]


async def stream_project_chat(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    user_message: str,
    survey_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Agentic RAG tabanli SSE streaming chat.
    """

    # ── 1. Kullanici mesajini kaydet ──────────────────────────────────────────
    user_msg = ChatHistory(
        project_id=project_id,
        role="user",
        message_content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # ── 2. Chat gecmisini yukle ───────────────────────────────────────────────
    all_messages = await get_project_messages(db, project_id)
    history = [
        {"role": m["role"], "content": m["message_content"]}
        for m in all_messages[:-1]
    ]

    # ── 3. Dataset RAG ────────────────────────────────────────────────────────
    rag_context: Optional[str] = None
    search_sources: str = ""
    rag_method: str = "none"

    is_greeting = _check_if_greeting(user_message)
    
    if not is_greeting:
        dataset_context = dataset_service.build_dataset_context(
            query=user_message,
            survey_context=survey_context,
        )

        if dataset_context:
            rag_context = dataset_context
            rag_method = "dataset"
            yield _sse_status("Bilgi tabani taraniyor...")
        else:
            search_query = _build_search_query(user_message, survey_context)
            yield _sse_status(f"Ajan internette arastiriyor: {search_query}")

            try:
                web_result = await tavily_service.search_web(search_query)
                if web_result and len(web_result.strip()) > 50:
                    rag_context = f"## Internetten Bulunan Guncel Kaynaklar\n\n{web_result}"
                    search_sources = "\n\n---\n**Kaynak:** Tavily Web Search"
                    rag_method = "tavily"
            except Exception as e:
                print(f"[chat_service] Tavily error: {e}")

    system_prompt = _build_system_prompt(survey_context, rag_method, is_greeting)

    llm_messages = llm_service.build_messages(
        session_history=history,
        user_message=user_message,
        system_prompt=system_prompt,
        rag_context=rag_context,
    )

    full_response = ""
    start = time.monotonic()

    async for token in llm_service.chat_completion_stream(messages=llm_messages):
        full_response += token
        yield token

    if search_sources:
        full_response += search_sources
        yield search_sources

    latency_ms = int((time.monotonic() - start) * 1000)
    assistant_msg = ChatHistory(
        project_id=project_id,
        role="assistant",
        message_content=full_response,
        latency_ms=latency_ms,
        model_used="qwen-turbo",
    )
    db.add(assistant_msg)
    await db.commit()


# ─── Yardimci Fonksiyonlar ────────────────────────────────────────────────────

def _sse_status(message: str) -> str:
    """Kullaniciya gorunen durum mesaji."""
    return f"\n\n*{message}*\n\n"

def _check_if_greeting(text: str) -> bool:
    """Basit greeting tespiti."""
    greetings = {"selam", "merhaba", "hi", "hello", "hey", "nasil gidiyor", "gunaydin", "iyi aksamlar"}
    text_clean = text.lower().strip().replace("!", "").replace(".", "")
    return text_clean in greetings or len(text_clean) < 3

def _build_search_query(user_message: str, survey_context: str) -> str:
    """Tavily icin optimize edilmis arama sorgusu olusturur."""
    base = user_message.strip()
    project_keywords = []
    survey_lower = survey_context.lower()
    for keyword in ["startup", "enterprise", "saas", "mobile", "e-commerce", "fintech",
                     "gaming", "streaming", "healthcare", "ai", "realtime"]:
        if keyword in survey_lower:
            project_keywords.append(keyword)

    if project_keywords:
        return f"tech stack recommendation {' '.join(project_keywords[:2])} {base}"
    return f"best tech stack for {base} 2024"


def _build_system_prompt(survey_context: str, rag_method: str, is_greeting: bool) -> str:
    """
    LLM icin kapsamli sistem promptu olusturur.
    """
    prompt = (
        "Sen Developlus platformunun kıdemli yazılım mimarı AI danışmanısın. "
        "Görevin: kullanıcının projesine özel, uygulanabilir, GERÇEKÇİ ve minimalist bir teknoloji yığını önermek.\n\n"
        "## KRİTİK KURALLAR\n"
        "- DİL: Sadece TÜRKÇE yanıt ver. Asla İngilizce veya Çince karakterler/açıklamalar kullanma.\n"
        "- ÖLÇEKLENEBİLİRLİK: Eğer proje 'basit' veya 'küçük' ise, devasa frameworkler (Java Spring Boot, .NET Enterprise vb.) önerme.\n"
        "- BASİT PROJELER İÇİN: Python (Flask/FastAPI), Node.js (Express) veya hatta sadece HTML/JS + Firebase/SQLite gibi hafif çözümlere odaklan.\n"
        "- HALÜSİNASYON: Bilmediğin şirketlerin (Spotify, Twitch vb.) teknolojileri hakkında uydurma yapma.\n"
        "- ANKET VERİSİ: Kullanıcının bütçesi ve ekibi kısıtlıysa Azure/AWS gibi pahalı servisler yerine ücretsiz/ucuz alternatifleri (Heroku free tier, Render, Vercel) öner.\n"
    )

    if is_greeting:
        prompt += (
            "\n## Greeting Modu\n"
            "Kullanıcı sadece selam verdi. Ona nazikçe hoşgeldin de, "
            "Developlus'un nasıl yardımcı olabileceğini anlat ve projesini sormasını iste. "
            "Hemen tech stack önermeye başlama!\n"
        )
    elif rag_method == "dataset":
        prompt += (
            "\n## Bilgi Tabani Kullanimi\n"
            "Saglanan sirket stack ornekleri gercek dunya verisinden geliyordur. "
            "Sadece burada yazan şirketleri referans göster.\n"
        )
    elif rag_method == "tavily":
        prompt += (
            "\n## Web Arastirmasi Kullanimi\n"
            "Internetten guncel bilgi cekildi. Bu bilgileri sentezle.\n"
        )

    if survey_context and survey_context.strip():
        prompt += f"\n\n## Kullanicinin Proje Kisitlari (Anket Yanitlari)\n{survey_context}"

    return prompt

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

from src.models import ChatHistory, StackRecommendation, Project
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
            "total_tokens": getattr(r, "total_tokens", None),
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
        dataset_context = await dataset_service.build_dataset_context(
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

    buffer = ""
    hide_output = False

    async for token in llm_service.chat_completion_stream(messages=llm_messages):
        full_response += token
        buffer += token
        
        while True:
            if not hide_output:
                start_idx = buffer.find("<stack_update>")
                if start_idx != -1:
                    if start_idx > 0:
                        yield buffer[:start_idx]
                    buffer = buffer[start_idx + len("<stack_update>"):]
                    hide_output = True
                    continue
                else:
                    tag = "<stack_update>"
                    safe_to_yield_idx = len(buffer)
                    for i in range(1, len(tag)):
                        if buffer.endswith(tag[:i]):
                            safe_to_yield_idx = len(buffer) - i
                            break
                    if safe_to_yield_idx > 0:
                        yield buffer[:safe_to_yield_idx]
                        buffer = buffer[safe_to_yield_idx:]
                    break
            else:
                end_idx = buffer.find("</stack_update>")
                if end_idx != -1:
                    buffer = buffer[end_idx + len("</stack_update>"):]
                    hide_output = False
                    continue
                else:
                    tag = "</stack_update>"
                    safe_to_discard_idx = len(buffer)
                    for i in range(1, len(tag)):
                        if buffer.endswith(tag[:i]):
                            safe_to_discard_idx = len(buffer) - i
                            break
                    if safe_to_discard_idx > 0:
                        buffer = buffer[safe_to_discard_idx:]
                    break

    if buffer and not hide_output:
        yield buffer

    if search_sources:
        full_response += search_sources
        yield search_sources

    # ── 4. Stack Recommendation Guncelleme Kontrolu ─────────────────────────
    # Eğer yanıtta <stack_update> etiketi varsa, veritabanını güncelle
    if "<stack_update>" in full_response:
        try:
            # Tag içindeki JSON'u parse et
            import re
            match = re.search(r"<stack_update>(.*?)</stack_update>", full_response, re.DOTALL)
            if match:
                stack_text = match.group(1).strip()
                
                # Sadece JSON kısmını almak için ilk '{' ve son '}' arasını bul
                start_idx = stack_text.find('{')
                end_idx = stack_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    stack_text = stack_text[start_idx:end_idx+1]
                
                stack_json = json.loads(stack_text)
                
                # Mevcut versiyonu bul
                v_res = await db.execute(
                    select(StackRecommendation.version)
                    .where(StackRecommendation.project_id == project_id)
                    .order_by(StackRecommendation.version.desc())
                    .limit(1)
                )
                last_version = v_res.scalar() or 0
                
                new_stack = StackRecommendation(
                    project_id=project_id,
                    version=last_version + 1,
                    layers=stack_json,
                    generated_from={"user_query": user_message}
                )
                db.add(new_stack)
                
                # Yanıt metninden etiketi temizle (kullanıcıya ham JSON gösterme)
                full_response = re.sub(r"<stack_update>.*?</stack_update>", "", full_response, flags=re.DOTALL).strip()
        except Exception as e:
            print(f"[chat_service] Stack update error: {e}")

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
    prompt = """
    # ROLE: SENIOR SOLUTIONS ARCHITECT (DEVELOPLUS AI)
Sen Developlus platformunun kıdemli yazılım mimarı AI danışmanısın. Görevin, kullanıcının girdilerine göre minimalist, gerçekçi ve uygulanabilir teknoloji yığınları (tech stack) önermek ve mevcut stack durumunu yönetmektir.

# OPERATIONAL LOGIC:
Her kullanıcı girdisinde şu 4 adımlı iç mekanizmayı çalıştır:
1. SCAN: Kullanıcının mesajını, bütçesini, ekip seviyesini ve proje ölçeğini analiz et.
2. EVALUATE: Küçük projeler için devasa frameworkler (Java Spring, .NET Enterprise, AWS/Azure) önerme. Hafif çözümlere (Python FastAPI/Flask, Node.js, Firebase, Supabase, Render, Vercel) odaklan.
3. UPDATE: Teknik durumu her zaman arka planda güncelle.
4. RESPOND: Sadece TÜRKÇE yanıt ver. Yanıtın net, doğrudan ve lafı uzatmayan (no-bullshit) bir üslupta olsun. Asla gerçek yazılım kodu (python, js satırları) üretme.

# OUTPUT FORMAT (STRICT):
SADECE kullanıcı doğrudan bir mimari veya teknoloji kararı sorduğunda, stack'i güncellemeni istediğinde veya yeni bir stack oluşturduğunda yanıtın EN SONUNA mutlaka şu formatta bir blok ekle. Normal sohbetlerde, genel teknik sorularda veya selamlaşmalarda bu bloğu ASLA KULLANMA. Bu bloğu eklediğinde, projeye en uygun katman (layer) başlıklarını KENDİN BELİRLE. Standart Frontend/Backend başlıklarına bağlı kalmak zorunda değilsin. Örneğin bir veri bilimi projesi için "Data Ingestion", "Model Training", "Serving" gibi başlıklar kullanabilirsin. Bir mobil oyun için "Client", "Game Server", "Matchmaking" kullanabilirsin. Sadece anahtar-değer (STRING-STRING) içeren DÜZ (nested olmayan) bir JSON üret:

---CONVERSATION---
[Buraya kullanıcıya vereceğin doğal, net ve uzman mimari yanıtı yaz.]

<stack_update>
{
  "Senin_Belirledigin_Katman_Adı_1": "Seçilen teknoloji ve kısa açıklama",
  "Senin_Belirledigin_Katman_Adı_2": "Seçilen teknoloji ve kısa açıklama",
  "Senin_Belirledigin_Katman_Adı_3": "Seçilen teknoloji ve kısa açıklama"
}
</stack_update>
    """

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

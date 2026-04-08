"""Developlus API — LLM Service (Qwen via LiteLLM Proxy)"""
import time
from typing import AsyncGenerator, List, Optional

import httpx
from openai import AsyncOpenAI

from src.config import settings


def get_llm_client() -> AsyncOpenAI:
    """LiteLLM Proxy üzerinden OpenAI uyumlu istemci."""
    return AsyncOpenAI(
        api_key=settings.litellm_master_key,
        base_url=f"{settings.litellm_proxy_url}/v1",
        timeout=120.0,
    )


async def chat_completion(
    messages: List[dict],
    model: str = None,
    temperature: float = None,
    max_tokens: int = None,
) -> dict:
    """Tek seferlik (non-streaming) chat completion."""
    client = get_llm_client()
    start = time.monotonic()

    response = await client.chat.completions.create(
        model=model or settings.default_model,
        messages=messages,
        temperature=temperature or settings.default_temperature,
        max_tokens=max_tokens or settings.default_max_tokens,
        stream=False,
    )

    latency_ms = int((time.monotonic() - start) * 1000)
    choice = response.choices[0]

    return {
        "content": choice.message.content,
        "model": response.model,
        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
        "completion_tokens": response.usage.completion_tokens if response.usage else None,
        "total_tokens": response.usage.total_tokens if response.usage else None,
        "latency_ms": latency_ms,
        "finish_reason": choice.finish_reason,
    }


async def chat_completion_stream(
    messages: List[dict],
    model: str = None,
    temperature: float = None,
    max_tokens: int = None,
) -> AsyncGenerator[str, None]:
    """SSE streaming chat completion. Token token yield eder."""
    client = get_llm_client()

    stream = await client.chat.completions.create(
        model=model or settings.default_model,
        messages=messages,
        temperature=temperature or settings.default_temperature,
        max_tokens=max_tokens or settings.default_max_tokens,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def create_embedding(text: str) -> List[float]:
    """RAG için metin embedding'i oluşturur."""
    client = get_llm_client()
    response = await client.embeddings.create(
        model="qwen-embedding",
        input=text,
    )
    return response.data[0].embedding


async def build_messages(
    session_history: List[dict],
    user_message: str,
    system_prompt: Optional[str] = None,
    rag_context: Optional[str] = None,
) -> List[dict]:
    """Konuşma geçmişinden LLM mesaj listesi oluşturur."""
    messages = []

    # System prompt
    if system_prompt or rag_context:
        system_content = system_prompt or "Sen Developlus AI asistanısın."
        if rag_context:
            system_content += f"\n\n## Bilgi Tabanı\nAşağıdaki bilgileri kullanarak soruyu yanıtla:\n\n{rag_context}"
        messages.append({"role": "system", "content": system_content})
    else:
        messages.append({
            "role": "system",
            "content": "Sen Developlus AI asistanısın. Yardımcı, nazik ve bilgili bir yapay zeka asistanısın."
        })

    # Geçmiş mesajlar (son 20 mesaj)
    for msg in session_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Yeni kullanıcı mesajı
    messages.append({"role": "user", "content": user_message})

    return messages

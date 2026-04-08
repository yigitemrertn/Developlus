"""
Developlus API — Analyze & Simple Chat Endpoints
Frontend (React + Vite) ile uyumlu: auth gerektirmez.

POST /analyze  → Proje açıklamasını analiz et, tech stack öner
POST /chat     → Basit tek-seferlik LLM chat
"""
import json
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.services.llm_service import chat_completion

router = APIRouter(tags=["Analyze"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    prompt: str


class TechResult(BaseModel):
    category: str
    icon: str
    cls: str
    tech: str
    desc: str


class AnalyzeResponse(BaseModel):
    results: List[TechResult]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ─── Sabit kategori metadata ───────────────────────────────────────────────────

CATEGORIES = [
    {"id": "frontend",  "name": "Frontend",     "icon": "Monitor",    "cls": "cat-frontend"},
    {"id": "backend",   "name": "Backend",       "icon": "Server",     "cls": "cat-backend"},
    {"id": "database",  "name": "Veritabanı",    "icon": "Database",   "cls": "cat-database"},
    {"id": "arch",      "name": "Mimari",        "icon": "GitBranch",  "cls": "cat-arch"},
    {"id": "auth",      "name": "Auth",          "icon": "Shield",     "cls": "cat-auth"},
    {"id": "deploy",    "name": "Deployment",    "icon": "Cloud",      "cls": "cat-deploy"},
    {"id": "cicd",      "name": "CI/CD",         "icon": "RefreshCw",  "cls": "cat-cicd"},
    {"id": "test",      "name": "Test",          "icon": "CheckCircle","cls": "cat-test"},
    {"id": "security",  "name": "Güvenlik",      "icon": "Lock",       "cls": "cat-security"},
    {"id": "api",       "name": "API Tasarımı",  "icon": "Globe",      "cls": "cat-api"},
]

ANALYZE_SYSTEM_PROMPT = """Sen Developlus AI teknoloji danışmanısın. 
Kullanıcı bir proje fikri veya açıklaması yazacak. 
Sen bu projeye en uygun teknoloji stack'ini 10 kategori için önereceksin.

Yanıtını SADECE geçerli JSON formatında ver. Başka hiçbir şey yazma.
JSON formatı şu şekilde olmalı:

{
  "results": [
    {
      "category": "Frontend",
      "icon": "Monitor",
      "cls": "cat-frontend",
      "tech": "React + Vite",
      "desc": "Neden bu teknoloji seçildi (1-2 cümle Türkçe)"
    },
    ...
  ]
}

10 kategori sırasıyla: Frontend, Veritabanı, Backend, Mimari, Auth, Deployment, CI/CD, Test, Güvenlik, API Tasarımı
Her kategori için gerçekten projeye uygun bir teknoloji öner ve kısa Türkçe açıklama yaz.
cls değerleri sırasıyla: cat-frontend, cat-database, cat-backend, cat-arch, cat-auth, cat-deploy, cat-cicd, cat-test, cat-security, cat-api
icon değerleri sırasıyla: Monitor, Database, Server, GitBranch, Shield, Cloud, RefreshCw, CheckCircle, Lock, Globe"""


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_project(request: AnalyzeRequest):
    """
    Proje açıklamasını LLM ile analiz eder ve teknoloji önerileri döner.
    Frontend'in beklediği format: { results: [{category, icon, cls, tech, desc}] }
    """
    messages = [
        {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Proje açıklaması:\n{request.prompt}"},
    ]

    try:
        response = await chat_completion(
            messages=messages,
            model="qwen-turbo",
            temperature=0.7,
            max_tokens=2000,
        )
        content = response["content"].strip()

        # JSON bloğu varsa temizle
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        results = parsed.get("results", [])

        # cls ve icon eksikse varsayılan ata
        cat_meta = {c["name"]: c for c in CATEGORIES}
        for r in results:
            meta = cat_meta.get(r.get("category"), {})
            if not r.get("cls") and meta:
                r["cls"] = meta["cls"]
            if not r.get("icon") and meta:
                r["icon"] = meta["icon"]

        return AnalyzeResponse(results=[TechResult(**r) for r in results])

    except (json.JSONDecodeError, Exception):
        # LLM yanıtı parse edilemezse akıllı fallback döndür
        return _smart_fallback(request.prompt)


@router.post("/chat", response_model=ChatResponse)
async def simple_chat(request: ChatRequest):
    """
    Basit tek-seferlik chat. Frontend ChatPanel'in beklediği format:
    { reply: "..." }
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Sen Developlus AI asistanısın. Yazılım projeleri, teknoloji seçimleri, "
                "mimari kararlar ve geliştirme süreçleri konusunda uzman bir danışmansın. "
                "Kısa, net ve yardımcı yanıtlar ver. Türkçe konuş."
            ),
        },
        {"role": "user", "content": request.message},
    ]

    try:
        response = await chat_completion(
            messages=messages,
            model="qwen-turbo",
            temperature=0.8,
            max_tokens=1024,
        )
        return ChatResponse(reply=response["content"])

    except Exception as e:
        return ChatResponse(
            reply="Şu an AI servisine bağlanamıyorum. Lütfen biraz sonra tekrar dene. 🙏"
        )


# ─── Fallback ─────────────────────────────────────────────────────────────────

def _smart_fallback(prompt: str) -> AnalyzeResponse:
    """LLM yanıtı başarısız olursa prompt'a göre akıllı varsayılan döndürür."""
    lower = prompt.lower()

    frontend = ("Next.js", "SSR ve SEO dostu, full-stack React framework") \
        if any(w in lower for w in ["web", "e-ticaret", "blog", "portal"]) \
        else ("React + Vite", "Hızlı SPA geliştirme için ideal modern framework")

    backend = ("FastAPI", "Python ekosistemi ile yüksek performanslı async API") \
        if "python" in lower \
        else ("NestJS", "TypeScript ile yapılandırılmış, ölçeklenebilir backend")

    db = ("PostgreSQL", "ACID garantili, güvenilir ilişkisel veritabanı") \
        if any(w in lower for w in ["ilişkisel", "güvenli", "kurumsal"]) \
        else ("MongoDB", "Esnek şema ile hızlı prototipleme")

    fallback_data = [
        {"category": "Frontend",    "icon": "Monitor",     "cls": "cat-frontend",  "tech": frontend[0],           "desc": frontend[1]},
        {"category": "Backend",     "icon": "Server",      "cls": "cat-backend",   "tech": backend[0],            "desc": backend[1]},
        {"category": "Veritabanı",  "icon": "Database",    "cls": "cat-database",  "tech": db[0],                 "desc": db[1]},
        {"category": "Mimari",      "icon": "GitBranch",   "cls": "cat-arch",      "tech": "Modular Monolith",    "desc": "Monolith avantajlarıyla modüler, bakımı kolay yapı"},
        {"category": "Auth",        "icon": "Shield",      "cls": "cat-auth",      "tech": "JWT + Refresh Token", "desc": "Güvenli ve stateless kimlik doğrulama"},
        {"category": "Deployment",  "icon": "Cloud",       "cls": "cat-deploy",    "tech": "Docker + K8s",        "desc": "Container tabanlı taşınabilir deployment"},
        {"category": "CI/CD",       "icon": "RefreshCw",   "cls": "cat-cicd",      "tech": "GitHub Actions",      "desc": "GitHub entegreli otomatik build ve deploy"},
        {"category": "Test",        "icon": "CheckCircle", "cls": "cat-test",      "tech": "Vitest + Playwright", "desc": "Unit ve E2E test kapsamı"},
        {"category": "Güvenlik",    "icon": "Lock",        "cls": "cat-security",  "tech": "Rate Limiting",       "desc": "API kötüye kullanım ve brute force koruması"},
        {"category": "API Tasarımı","icon": "Globe",       "cls": "cat-api",       "tech": "REST + OpenAPI",      "desc": "Standart REST API, Swagger ile dokümantasyon"},
    ]

    return AnalyzeResponse(results=[TechResult(**r) for r in fallback_data])

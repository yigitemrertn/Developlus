"""Developlus API — Main Application Entry Point"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.config import settings
from src.routers import analyze, auth, chat, health, rag, projects, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatma ve kapanma işlemleri."""
    print(f"🚀 Developlus API başlatılıyor — {settings.environment}")
    yield
    print("🛑 Developlus API kapatılıyor...")


# ─── FastAPI uygulaması ────────────────────────────────────────────────────
app = FastAPI(
    title="Developlus API",
    description="LLM tabanlı chatbot platformu — Qwen + RAG + PostgreSQL + Redis",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(analyze.router)  # Frontend uyumlu: /analyze ve /chat
app.include_router(projects.router)
app.include_router(users.router)


@app.get("/")
async def root():
    return {
        "name": "Developlus API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }

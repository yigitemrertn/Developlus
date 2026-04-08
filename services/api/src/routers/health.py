"""Developlus API — Health Check Router"""
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from src.database import AsyncSessionLocal
from src.services.cache_service import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Sistemin genel sağlık durumunu kontrol eder."""
    checks = {}

    # PostgreSQL kontrolü
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    # Redis kontrolü
    try:
        redis = await get_redis()
        await redis.ping()
        checks["cache"] = "healthy"
    except Exception as e:
        checks["cache"] = f"unhealthy: {e}"

    overall = "healthy" if all("healthy" == v for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "services": checks,
    }

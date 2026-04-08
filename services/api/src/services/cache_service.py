"""Developlus API — Cache Service (Redis)"""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from src.config import settings

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def cache_get(key: str) -> Optional[Any]:
    redis = await get_redis()
    value = await redis.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    redis = await get_redis()
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    await redis.setex(key, ttl, value)


async def cache_delete(key: str) -> None:
    redis = await get_redis()
    await redis.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    redis = await get_redis()
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)


# Key builder fonksiyonları
def session_history_key(session_id: str) -> str:
    return f"developlus:session:{session_id}:history"


def user_profile_key(user_id: str) -> str:
    return f"developlus:user:{user_id}:profile"


def rate_limit_key(user_id: str) -> str:
    return f"developlus:ratelimit:{user_id}"


async def check_rate_limit(user_id: str, limit: int = 50, window: int = 60) -> bool:
    """Dakikada limit kadar istek kontrolü. True = izin verildi."""
    redis = await get_redis()
    key = rate_limit_key(user_id)
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window)
    return current <= limit

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.analytics_cache import AnalyticsCache
from app.redis_client import get_redis_client


class AICacheService:
    def make_cache_key(self, payload: dict) -> str:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return f"ai:cache:{digest}"

    async def get(self, cache_key: str) -> dict | None:
        redis = await get_redis_client()
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AnalyticsCache).where(AnalyticsCache.cache_key == cache_key))
            row = result.scalar_one_or_none()
            if row is None or row.expires_at < datetime.now(UTC):
                return None
            await redis.set(cache_key, json.dumps(row.data), ex=int((row.expires_at - datetime.now(UTC)).total_seconds()))
            return row.data

    async def set(self, cache_key: str, value: dict, ttl_seconds: int = 60 * 60 * 24) -> None:
        redis = await get_redis_client()
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        await redis.set(cache_key, json.dumps(value), ex=ttl_seconds)

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AnalyticsCache).where(AnalyticsCache.cache_key == cache_key))
            row = result.scalar_one_or_none()
            if row is None:
                session.add(AnalyticsCache(cache_key=cache_key, data=value, expires_at=expires_at))
            else:
                row.data = value
                row.expires_at = expires_at
            await session.commit()


ai_cache_service = AICacheService()

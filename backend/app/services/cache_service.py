from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, Callable

from app.redis_client import get_redis_client

_MISSING = object()


def _make_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    digest = hashlib.md5(raw.encode()).hexdigest()  # noqa: S324
    return f"analytics:{prefix}:{digest}"


async def cache_get(key: str) -> Any | None:
    try:
        redis = await get_redis_client()
        raw = await redis.get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    try:
        redis = await get_redis_client()
        await redis.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:
        pass


async def cache_delete_pattern(pattern: str) -> int:
    try:
        redis = await get_redis_client()
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
    except Exception:
        pass
    return 0


async def invalidate_all_analytics() -> int:
    return await cache_delete_pattern("analytics:*")


def cached(ttl: int = 300, prefix: str | None = None) -> Callable:
    """Decorator: cache async function results in Redis."""

    def decorator(func: Callable) -> Callable:
        key_prefix = prefix or func.__qualname__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_key(key_prefix, *args, **kwargs)
            cached_val = await cache_get(key)
            if cached_val is not None:
                return cached_val
            result = await func(*args, **kwargs)
            if result is not None:
                serialisable = result if isinstance(result, (dict, list)) else result
                try:
                    await cache_set(key, serialisable, ttl_seconds=ttl)
                except Exception:
                    pass
            return result

        return wrapper

    return decorator

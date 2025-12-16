"""
Redis cache implementation for analysis results.

Provides async caching with configurable TTL.
"""

import json
from functools import lru_cache
from typing import Any

import redis.asyncio as redis

from mizan.infrastructure.config import get_settings


class RedisCache:
    """
    Async Redis cache for analysis results.

    Caches expensive computations like:
    - Word/letter counts for verses
    - Abjad calculations
    - Search results
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        """Initialize with Redis client."""
        self._redis = redis_client
        self._settings = get_settings()

    @classmethod
    async def create(cls) -> "RedisCache":
        """Create a new RedisCache instance."""
        settings = get_settings()
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_pool_size,
        )
        return cls(client)

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.close()

    def _make_key(self, namespace: str, key: str) -> str:
        """Create a namespaced cache key."""
        return f"mizan:{namespace}:{key}"

    async def get(self, namespace: str, key: str) -> Any | None:
        """
        Get a cached value.

        Args:
            namespace: Cache namespace (e.g., "verse", "analysis")
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        cache_key = self._make_key(namespace, key)
        value = await self._redis.get(cache_key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """
        Set a cached value.

        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (default: from settings)
        """
        cache_key = self._make_key(namespace, key)
        ttl = ttl or self._settings.cache_ttl

        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        await self._redis.set(cache_key, value, ex=ttl)

    async def delete(self, namespace: str, key: str) -> bool:
        """
        Delete a cached value.

        Returns:
            True if key was deleted, False if not found
        """
        cache_key = self._make_key(namespace, key)
        result = await self._redis.delete(cache_key)
        return result > 0

    async def clear_namespace(self, namespace: str) -> int:
        """
        Clear all keys in a namespace.

        Returns:
            Number of keys deleted
        """
        pattern = self._make_key(namespace, "*")
        keys = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self._redis.delete(*keys)
        return 0

    async def exists(self, namespace: str, key: str) -> bool:
        """Check if a key exists in cache."""
        cache_key = self._make_key(namespace, key)
        return await self._redis.exists(cache_key) > 0

    async def get_or_set(
        self,
        namespace: str,
        key: str,
        factory: Any,
        ttl: int | None = None,
    ) -> Any:
        """
        Get cached value or compute and cache it.

        Args:
            namespace: Cache namespace
            key: Cache key
            factory: Async function to compute value if not cached
            ttl: Time-to-live in seconds

        Returns:
            Cached or computed value
        """
        value = await self.get(namespace, key)
        if value is not None:
            return value

        # Compute value
        if callable(factory):
            value = await factory() if hasattr(factory, "__await__") else factory()
        else:
            value = factory

        await self.set(namespace, key, value, ttl)
        return value

    # Convenience methods for common cache operations

    async def cache_verse_analysis(
        self,
        surah: int,
        verse: int,
        analysis_type: str,
        result: dict[str, Any],
    ) -> None:
        """Cache analysis result for a verse."""
        key = f"{surah}:{verse}:{analysis_type}"
        await self.set("analysis", key, result)

    async def get_verse_analysis(
        self,
        surah: int,
        verse: int,
        analysis_type: str,
    ) -> dict[str, Any] | None:
        """Get cached analysis result for a verse."""
        key = f"{surah}:{verse}:{analysis_type}"
        return await self.get("analysis", key)

    async def cache_search_results(
        self,
        query_hash: str,
        results: list[dict[str, Any]],
    ) -> None:
        """Cache search results."""
        await self.set("search", query_hash, results)

    async def get_search_results(
        self,
        query_hash: str,
    ) -> list[dict[str, Any]] | None:
        """Get cached search results."""
        return await self.get("search", query_hash)

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False


# Global cache instance
_cache: RedisCache | None = None


async def get_cache() -> RedisCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = await RedisCache.create()
    return _cache


async def close_cache() -> None:
    """Close the global cache instance."""
    global _cache
    if _cache is not None:
        await _cache.close()
        _cache = None

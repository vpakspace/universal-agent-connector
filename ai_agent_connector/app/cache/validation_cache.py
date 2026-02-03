"""
Validation caching for OntoGuard results.

Provides LRU in-memory cache with optional Redis backend for distributed caching.
Reduces latency for repeated validation requests.
"""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from threading import Lock
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Redis (optional dependency)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheEntry:
    """Single cache entry with TTL support."""
    value: Dict[str, Any]
    created_at: float
    ttl: float
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """Increment hit counter."""
        self.hits += 1


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 0
    evictions: int = 0
    expired: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(self.hit_rate, 2),
            'size': self.size,
            'max_size': self.max_size,
            'evictions': self.evictions,
            'expired': self.expired,
        }


class ValidationCache:
    """
    LRU cache for OntoGuard validation results.

    Features:
    - In-memory LRU cache with configurable max size
    - TTL (time-to-live) for entries
    - Thread-safe operations
    - Optional Redis backend for distributed caching
    - Cache statistics tracking

    Cache key format: hash(action:entity_type:role:domain)
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 300.0,  # 5 minutes
        redis_url: Optional[str] = None,
        redis_prefix: str = "uac:validation:",
        enabled: bool = True,
    ):
        """
        Initialize validation cache.

        Args:
            max_size: Maximum number of entries in memory cache
            default_ttl: Default TTL in seconds (5 minutes)
            redis_url: Optional Redis URL for distributed caching
            redis_prefix: Prefix for Redis keys
            enabled: Whether caching is enabled
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.redis_prefix = redis_prefix
        self.enabled = enabled

        # In-memory LRU cache (OrderedDict maintains insertion order)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._stats = CacheStats(max_size=max_size)

        # Optional Redis backend
        self._redis: Optional[Any] = None
        if redis_url and REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(redis_url)
                self._redis.ping()
                logger.info(f"Redis cache connected: {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory only: {e}")
                self._redis = None

    def _make_key(
        self,
        action: str,
        entity_type: str,
        role: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """
        Generate cache key from validation parameters.

        Args:
            action: Action being validated (read, create, update, delete)
            entity_type: Entity type or table name
            role: User role (optional)
            domain: Domain name (optional)

        Returns:
            Hashed cache key
        """
        key_parts = [
            action.lower(),
            entity_type.lower(),
            (role or '').lower(),
            (domain or 'default').lower(),
        ]
        key_str = ':'.join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def get(
        self,
        action: str,
        entity_type: str,
        role: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached validation result.

        Args:
            action: Action being validated
            entity_type: Entity type or table name
            role: User role
            domain: Domain name

        Returns:
            Cached validation result or None if not found/expired
        """
        if not self.enabled:
            return None

        key = self._make_key(action, entity_type, role, domain)

        # Try memory cache first
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired:
                    del self._cache[key]
                    self._stats.expired += 1
                    self._stats.misses += 1
                    self._stats.size = len(self._cache)
                else:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    entry.touch()
                    self._stats.hits += 1
                    logger.debug(f"Cache HIT: {key[:8]}... (hits: {entry.hits})")
                    return entry.value
            else:
                self._stats.misses += 1

        # Try Redis if available
        if self._redis:
            try:
                redis_key = f"{self.redis_prefix}{key}"
                data = self._redis.get(redis_key)
                if data:
                    value = json.loads(data)
                    # Populate memory cache
                    self._set_memory(key, value, self.default_ttl)
                    self._stats.hits += 1
                    logger.debug(f"Redis cache HIT: {key[:8]}...")
                    return value
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        return None

    def set(
        self,
        action: str,
        entity_type: str,
        value: Dict[str, Any],
        role: Optional[str] = None,
        domain: Optional[str] = None,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Cache validation result.

        Args:
            action: Action being validated
            entity_type: Entity type or table name
            value: Validation result to cache
            role: User role
            domain: Domain name
            ttl: TTL in seconds (uses default if not specified)
        """
        if not self.enabled:
            return

        key = self._make_key(action, entity_type, role, domain)
        ttl = ttl or self.default_ttl

        # Set in memory cache
        self._set_memory(key, value, ttl)

        # Set in Redis if available
        if self._redis:
            try:
                redis_key = f"{self.redis_prefix}{key}"
                self._redis.setex(redis_key, int(ttl), json.dumps(value))
                logger.debug(f"Redis cache SET: {key[:8]}...")
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

    def _set_memory(self, key: str, value: Dict[str, Any], ttl: float) -> None:
        """Set value in memory cache with LRU eviction."""
        with self._lock:
            # Remove if exists (to update position)
            if key in self._cache:
                del self._cache[key]

            # Evict oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1
                logger.debug(f"Cache eviction: {oldest_key[:8]}...")

            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl,
            )
            self._stats.size = len(self._cache)
            logger.debug(f"Cache SET: {key[:8]}... (size: {self._stats.size})")

    def invalidate(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        role: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> int:
        """
        Invalidate cache entries matching criteria.

        If all params are None, clears entire cache.
        If specific params provided, only matching entries are removed.

        Returns:
            Number of entries invalidated
        """
        if all(p is None for p in [action, entity_type, role, domain]):
            # Clear all
            count = len(self._cache)
            with self._lock:
                self._cache.clear()
                self._stats.size = 0

            if self._redis:
                try:
                    keys = self._redis.keys(f"{self.redis_prefix}*")
                    if keys:
                        self._redis.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis invalidate error: {e}")

            logger.info(f"Cache cleared: {count} entries")
            return count

        # Selective invalidation - generate key and remove
        key = self._make_key(
            action or '*',
            entity_type or '*',
            role,
            domain,
        )

        count = 0
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                count = 1
                self._stats.size = len(self._cache)

        if self._redis and count > 0:
            try:
                redis_key = f"{self.redis_prefix}{key}"
                self._redis.delete(redis_key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")

        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self._stats.size = len(self._cache)
        return self._stats.to_dict()

    def cleanup_expired(self) -> int:
        """Remove expired entries from memory cache."""
        count = 0
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
                count += 1
            self._stats.expired += count
            self._stats.size = len(self._cache)

        if count > 0:
            logger.debug(f"Cleanup: {count} expired entries removed")
        return count


# Global cache instance
_validation_cache: Optional[ValidationCache] = None


def get_validation_cache() -> ValidationCache:
    """Get or create global validation cache."""
    global _validation_cache
    if _validation_cache is None:
        _validation_cache = ValidationCache()
    return _validation_cache


def init_validation_cache(
    max_size: int = 1000,
    default_ttl: float = 300.0,
    redis_url: Optional[str] = None,
    enabled: bool = True,
) -> ValidationCache:
    """Initialize global validation cache with custom settings."""
    global _validation_cache
    _validation_cache = ValidationCache(
        max_size=max_size,
        default_ttl=default_ttl,
        redis_url=redis_url,
        enabled=enabled,
    )
    return _validation_cache


def cache_validation_result(
    action: str,
    entity_type: str,
    result: Dict[str, Any],
    role: Optional[str] = None,
    domain: Optional[str] = None,
    ttl: Optional[float] = None,
) -> None:
    """Cache a validation result."""
    cache = get_validation_cache()
    cache.set(action, entity_type, result, role, domain, ttl)


def get_cached_validation(
    action: str,
    entity_type: str,
    role: Optional[str] = None,
    domain: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get cached validation result."""
    cache = get_validation_cache()
    return cache.get(action, entity_type, role, domain)


def invalidate_cache(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    role: Optional[str] = None,
    domain: Optional[str] = None,
) -> int:
    """Invalidate cache entries."""
    cache = get_validation_cache()
    return cache.invalidate(action, entity_type, role, domain)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = get_validation_cache()
    return cache.get_stats()


def cached_validation(ttl: Optional[float] = None):
    """
    Decorator to cache validation function results.

    Usage:
        @cached_validation(ttl=300)
        def validate_action(action, entity_type, context):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(action: str, entity_type: str, context: Dict[str, Any] = None, *args, **kwargs):
            context = context or {}
            role = context.get('role')
            domain = context.get('domain')

            # Try cache first
            cached = get_cached_validation(action, entity_type, role, domain)
            if cached is not None:
                return cached

            # Execute function
            result = func(action, entity_type, context, *args, **kwargs)

            # Cache result (convert to dict if needed)
            if hasattr(result, 'to_dict'):
                cache_value = result.to_dict()
            elif hasattr(result, '__dict__'):
                cache_value = result.__dict__
            else:
                cache_value = result

            cache_validation_result(action, entity_type, cache_value, role, domain, ttl)

            return result
        return wrapper
    return decorator

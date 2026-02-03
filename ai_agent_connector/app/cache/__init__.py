"""
Caching module for Universal Agent Connector.

Provides in-memory LRU caching with optional Redis backend.
"""

from .validation_cache import (
    ValidationCache,
    CacheEntry,
    CacheStats,
    get_validation_cache,
    init_validation_cache,
    cache_validation_result,
    get_cached_validation,
    invalidate_cache,
    get_cache_stats,
    cached_validation,
)

__all__ = [
    'ValidationCache',
    'CacheEntry',
    'CacheStats',
    'get_validation_cache',
    'init_validation_cache',
    'cache_validation_result',
    'get_cached_validation',
    'invalidate_cache',
    'get_cache_stats',
    'cached_validation',
]

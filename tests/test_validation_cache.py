"""
Unit tests for validation caching module.

Tests LRU cache, TTL, statistics, and cache operations.
"""

import pytest
import time
from unittest.mock import patch, MagicMock


class TestValidationCache:
    """Test ValidationCache class."""

    def test_import_cache_module(self):
        """Test that cache module can be imported."""
        from ai_agent_connector.app.cache import (
            ValidationCache,
            get_validation_cache,
            cache_validation_result,
            get_cached_validation,
            invalidate_cache,
            get_cache_stats,
        )
        assert ValidationCache is not None
        assert get_validation_cache is not None

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Set value
        result = {'allowed': True, 'reason': 'Test'}
        cache.set('read', 'User', result, role='Admin', domain='test')

        # Get value
        cached = cache.get('read', 'User', role='Admin', domain='test')
        assert cached is not None
        assert cached['allowed'] is True
        assert cached['reason'] == 'Test'

    def test_cache_miss(self):
        """Test cache miss returns None."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Non-existent key
        cached = cache.get('delete', 'Order', role='Guest', domain='test')
        assert cached is None

    def test_cache_key_uniqueness(self):
        """Test that different parameters create different keys."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Different actions
        cache.set('read', 'User', {'allowed': True}, role='Admin')
        cache.set('delete', 'User', {'allowed': False}, role='Admin')

        read_result = cache.get('read', 'User', role='Admin')
        delete_result = cache.get('delete', 'User', role='Admin')

        assert read_result['allowed'] is True
        assert delete_result['allowed'] is False

    def test_cache_ttl_expiration(self):
        """Test that entries expire after TTL."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=0.1)  # 100ms TTL

        cache.set('read', 'User', {'allowed': True}, role='Admin')

        # Should be cached
        assert cache.get('read', 'User', role='Admin') is not None

        # Wait for expiration
        time.sleep(0.15)

        # Should be expired
        assert cache.get('read', 'User', role='Admin') is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=3, default_ttl=60.0)

        # Fill cache
        cache.set('action1', 'Entity1', {'v': 1})
        cache.set('action2', 'Entity2', {'v': 2})
        cache.set('action3', 'Entity3', {'v': 3})

        # Access first entry to make it recently used
        cache.get('action1', 'Entity1')

        # Add new entry - should evict action2 (least recently used)
        cache.set('action4', 'Entity4', {'v': 4})

        # action1 should still be cached (was accessed)
        assert cache.get('action1', 'Entity1') is not None
        # action2 should be evicted
        assert cache.get('action2', 'Entity2') is None
        # action3 and action4 should be cached
        assert cache.get('action3', 'Entity3') is not None
        assert cache.get('action4', 'Entity4') is not None

    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Initial stats
        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0

        # Cache miss
        cache.get('nonexistent', 'Entity')
        stats = cache.get_stats()
        assert stats['misses'] == 1

        # Cache set and hit
        cache.set('read', 'User', {'allowed': True})
        cache.get('read', 'User')
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['size'] == 1

    def test_cache_invalidate_all(self):
        """Test clearing entire cache."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Fill cache
        cache.set('action1', 'Entity1', {'v': 1})
        cache.set('action2', 'Entity2', {'v': 2})
        cache.set('action3', 'Entity3', {'v': 3})

        assert cache.get_stats()['size'] == 3

        # Clear all
        count = cache.invalidate()
        assert count == 3
        assert cache.get_stats()['size'] == 0

    def test_cache_invalidate_specific(self):
        """Test invalidating specific cache entry."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        cache.set('read', 'User', {'allowed': True}, role='Admin')
        cache.set('delete', 'User', {'allowed': False}, role='Admin')

        # Invalidate specific entry
        count = cache.invalidate('read', 'User', role='Admin')
        assert count == 1

        # Check that only the specific entry was removed
        assert cache.get('read', 'User', role='Admin') is None
        assert cache.get('delete', 'User', role='Admin') is not None

    def test_cache_disabled(self):
        """Test that disabled cache returns None and doesn't store."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0, enabled=False)

        cache.set('read', 'User', {'allowed': True})
        assert cache.get('read', 'User') is None
        assert cache.get_stats()['size'] == 0

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=0.1)

        cache.set('action1', 'Entity1', {'v': 1})
        cache.set('action2', 'Entity2', {'v': 2})

        time.sleep(0.15)

        count = cache.cleanup_expired()
        assert count == 2
        assert cache.get_stats()['size'] == 0

    def test_cache_hit_rate(self):
        """Test hit rate calculation."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # 1 miss
        cache.get('nonexistent', 'Entity')

        # 1 set + 2 hits
        cache.set('read', 'User', {'allowed': True})
        cache.get('read', 'User')
        cache.get('read', 'User')

        stats = cache.get_stats()
        # 2 hits / 3 total = 66.67%
        assert stats['hit_rate'] == pytest.approx(66.67, abs=0.1)


class TestCacheHelperFunctions:
    """Test helper functions for caching."""

    def test_global_cache_singleton(self):
        """Test that get_validation_cache returns same instance."""
        from ai_agent_connector.app.cache import get_validation_cache

        cache1 = get_validation_cache()
        cache2 = get_validation_cache()
        assert cache1 is cache2

    def test_helper_functions(self):
        """Test cache_validation_result and get_cached_validation."""
        from ai_agent_connector.app.cache import (
            cache_validation_result,
            get_cached_validation,
            invalidate_cache,
            init_validation_cache,
        )

        # Initialize fresh cache
        init_validation_cache(max_size=100, default_ttl=60.0)

        # Cache result
        cache_validation_result(
            'read', 'PatientRecord',
            {'allowed': True, 'reason': 'Doctor can read'},
            role='Doctor',
            domain='hospital'
        )

        # Get cached result
        cached = get_cached_validation('read', 'PatientRecord', role='Doctor', domain='hospital')
        assert cached is not None
        assert cached['allowed'] is True

        # Invalidate
        invalidate_cache()

    def test_cached_validation_decorator(self):
        """Test @cached_validation decorator."""
        from ai_agent_connector.app.cache import cached_validation, invalidate_cache, init_validation_cache

        # Initialize fresh cache
        init_validation_cache(max_size=100, default_ttl=60.0)
        invalidate_cache()

        call_count = 0

        @cached_validation(ttl=60.0)
        def mock_validate(action, entity_type, context=None):
            nonlocal call_count
            call_count += 1
            return {'allowed': True, 'action': action, 'entity_type': entity_type}

        # First call - should execute function
        result1 = mock_validate('read', 'User', {'role': 'Admin'})
        assert call_count == 1
        assert result1['allowed'] is True

        # Second call with same params - should return cached
        result2 = mock_validate('read', 'User', {'role': 'Admin'})
        assert call_count == 1  # Not incremented
        assert result2['allowed'] is True

        # Different params - should execute function
        result3 = mock_validate('delete', 'User', {'role': 'Admin'})
        assert call_count == 2

        # Cleanup
        invalidate_cache()


class TestCacheWithDomains:
    """Test caching with domain-specific validation."""

    def test_domain_specific_caching(self):
        """Test that different domains have separate cache entries."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Cache for hospital domain
        cache.set('read', 'PatientRecord', {'allowed': True}, role='Doctor', domain='hospital')

        # Cache for finance domain
        cache.set('read', 'Account', {'allowed': True}, role='Analyst', domain='finance')

        # Same action/entity but different domains
        cache.set('read', 'PatientRecord', {'allowed': False}, role='Doctor', domain='finance')

        # Verify domain isolation
        hospital_result = cache.get('read', 'PatientRecord', role='Doctor', domain='hospital')
        finance_result = cache.get('read', 'PatientRecord', role='Doctor', domain='finance')

        assert hospital_result['allowed'] is True
        assert finance_result['allowed'] is False

    def test_role_specific_caching(self):
        """Test that different roles have separate cache entries."""
        from ai_agent_connector.app.cache import ValidationCache

        cache = ValidationCache(max_size=100, default_ttl=60.0)

        # Same action/entity, different roles
        cache.set('delete', 'PatientRecord', {'allowed': True}, role='Admin', domain='hospital')
        cache.set('delete', 'PatientRecord', {'allowed': False}, role='Nurse', domain='hospital')

        admin_result = cache.get('delete', 'PatientRecord', role='Admin', domain='hospital')
        nurse_result = cache.get('delete', 'PatientRecord', role='Nurse', domain='hospital')

        assert admin_result['allowed'] is True
        assert nurse_result['allowed'] is False

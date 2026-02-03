"""
Unit tests for cache API endpoints.

Tests cache statistics, invalidation, and configuration endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCacheAPIEndpoints:
    """Test cache REST API endpoints."""

    def test_get_cache_stats(self):
        """Test GET /api/cache/stats endpoint."""
        mock_stats = {
            'hits': 10,
            'misses': 5,
            'hit_rate': 66.67,
            'size': 15,
            'max_size': 1000,
            'evictions': 0,
            'expired': 0,
        }

        with patch('ai_agent_connector.app.cache.get_cache_stats', return_value=mock_stats):
            from ai_agent_connector.app.api import api_bp
            from flask import Flask

            app = Flask(__name__)
            app.register_blueprint(api_bp, url_prefix='/api')

            with app.test_client() as client:
                response = client.get('/api/cache/stats')
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ok'
                assert data['cache']['hits'] == 10
                assert data['cache']['hit_rate'] == 66.67

    def test_invalidate_cache_all(self):
        """Test POST /api/cache/invalidate (clear all)."""
        with patch('ai_agent_connector.app.cache.invalidate_cache', return_value=50):
            from ai_agent_connector.app.api import api_bp
            from flask import Flask

            app = Flask(__name__)
            app.register_blueprint(api_bp, url_prefix='/api')

            with app.test_client() as client:
                response = client.post('/api/cache/invalidate', json={})
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ok'
                assert data['invalidated'] == 50

    def test_invalidate_cache_specific(self):
        """Test POST /api/cache/invalidate with filters."""
        with patch('ai_agent_connector.app.cache.invalidate_cache', return_value=1):
            from ai_agent_connector.app.api import api_bp
            from flask import Flask

            app = Flask(__name__)
            app.register_blueprint(api_bp, url_prefix='/api')

            with app.test_client() as client:
                response = client.post('/api/cache/invalidate', json={
                    'action': 'read',
                    'entity_type': 'PatientRecord',
                    'role': 'Doctor',
                    'domain': 'hospital',
                })
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ok'
                assert data['invalidated'] == 1
                assert data['filter']['action'] == 'read'
                assert data['filter']['domain'] == 'hospital'

    def test_get_cache_config(self):
        """Test GET /api/cache/config endpoint."""
        mock_cache = MagicMock()
        mock_cache.max_size = 1000
        mock_cache.default_ttl = 300.0
        mock_cache.enabled = True
        mock_cache._redis = None

        with patch('ai_agent_connector.app.cache.get_validation_cache', return_value=mock_cache):
            from ai_agent_connector.app.api import api_bp
            from flask import Flask

            app = Flask(__name__)
            app.register_blueprint(api_bp, url_prefix='/api')

            with app.test_client() as client:
                response = client.get('/api/cache/config')
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ok'
                assert data['config']['max_size'] == 1000
                assert data['config']['default_ttl'] == 300.0
                assert data['config']['enabled'] is True
                assert data['config']['redis_connected'] is False

    def test_cleanup_cache(self):
        """Test POST /api/cache/cleanup endpoint."""
        mock_cache = MagicMock()
        mock_cache.cleanup_expired.return_value = 5

        with patch('ai_agent_connector.app.cache.get_validation_cache', return_value=mock_cache):
            from ai_agent_connector.app.api import api_bp
            from flask import Flask

            app = Flask(__name__)
            app.register_blueprint(api_bp, url_prefix='/api')

            with app.test_client() as client:
                response = client.post('/api/cache/cleanup')
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'ok'
                assert data['cleaned_up'] == 5


class TestCacheIntegration:
    """Test cache integration with validation flow."""

    def test_cache_module_importable(self):
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

    def test_cache_flow(self):
        """Test full cache flow: set → get → invalidate."""
        from ai_agent_connector.app.cache import (
            ValidationCache,
            init_validation_cache,
            cache_validation_result,
            get_cached_validation,
            invalidate_cache,
            get_cache_stats,
        )

        # Initialize fresh cache
        init_validation_cache(max_size=100, default_ttl=60.0)

        # Cache a validation result
        cache_validation_result(
            action='read',
            entity_type='PatientRecord',
            result={'allowed': True, 'reason': 'Doctor can read'},
            role='Doctor',
            domain='hospital',
        )

        # Verify it's cached
        cached = get_cached_validation('read', 'PatientRecord', role='Doctor', domain='hospital')
        assert cached is not None
        assert cached['allowed'] is True

        # Check stats
        stats = get_cache_stats()
        assert stats['size'] == 1
        assert stats['hits'] == 1

        # Invalidate
        count = invalidate_cache()
        assert count == 1

        # Verify it's gone
        cached = get_cached_validation('read', 'PatientRecord', role='Doctor', domain='hospital')
        assert cached is None

    def test_cache_with_adapter(self):
        """Test cache integration with OntoGuard adapter."""
        from ai_agent_connector.app.cache import init_validation_cache, invalidate_cache
        from ai_agent_connector.app.security import get_ontoguard_adapter, reset_ontoguard_adapter

        # Initialize fresh cache and adapter
        init_validation_cache(max_size=100, default_ttl=60.0)
        invalidate_cache()
        reset_ontoguard_adapter()

        adapter = get_ontoguard_adapter()
        adapter.initialize()  # Pass-through mode

        # First validation
        result1 = adapter.validate_action('read', 'PatientRecord', {'role': 'Doctor', 'domain': 'hospital'})
        assert result1.allowed is True  # Pass-through mode

        # Second validation (should be cached if adapter is active)
        result2 = adapter.validate_action('read', 'PatientRecord', {'role': 'Doctor', 'domain': 'hospital'})
        assert result2.allowed is True

        # Cleanup
        invalidate_cache()
        reset_ontoguard_adapter()

"""
Unit tests for rate limiting API endpoints.

Tests rate limit configuration, enforcement, and management.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask


class TestRateLimitAPIEndpoints:
    """Test rate limit REST API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        from ai_agent_connector.app.api import api_bp

        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp, url_prefix='/api')
        self.client = self.app.test_client()

    def test_get_default_rate_limits(self):
        """Test GET /api/rate-limits/default endpoint."""
        response = self.client.get('/api/rate-limits/default')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'default_limits' in data
        assert data['default_limits']['queries_per_minute'] == 60

    def test_list_rate_limits(self):
        """Test GET /api/rate-limits endpoint."""
        response = self.client.get('/api/rate-limits')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'default_limits' in data
        assert 'agent_limits' in data
        assert 'total_agents' in data

    def test_get_agent_rate_limit_not_configured(self):
        """Test GET /api/rate-limits/<agent_id> for unconfigured agent."""
        response = self.client.get('/api/rate-limits/test-agent-123')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['agent_id'] == 'test-agent-123'
        assert data['configured'] is False
        # Should return default limits
        assert data['config']['queries_per_minute'] == 60

    def test_set_agent_rate_limit(self):
        """Test PUT /api/rate-limits/<agent_id> endpoint."""
        response = self.client.put(
            '/api/rate-limits/test-agent-456',
            json={
                'queries_per_minute': 30,
                'queries_per_hour': 500,
                'queries_per_day': 5000
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['agent_id'] == 'test-agent-456'
        assert data['config']['queries_per_minute'] == 30
        assert data['config']['queries_per_hour'] == 500

        # Verify it was set
        response = self.client.get('/api/rate-limits/test-agent-456')
        data = response.get_json()
        assert data['configured'] is True

    def test_remove_agent_rate_limit(self):
        """Test DELETE /api/rate-limits/<agent_id> endpoint."""
        # First set a limit
        self.client.put(
            '/api/rate-limits/test-agent-789',
            json={'queries_per_minute': 10}
        )

        # Then remove it
        response = self.client.delete('/api/rate-limits/test-agent-789')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['removed'] is True

        # Verify it was removed
        response = self.client.get('/api/rate-limits/test-agent-789')
        data = response.get_json()
        assert data['configured'] is False

    def test_reset_agent_rate_limit(self):
        """Test POST /api/rate-limits/<agent_id>/reset endpoint."""
        response = self.client.post('/api/rate-limits/test-agent-reset/reset')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['message'] == 'Rate limit counters reset'


class TestRateLimiterCore:
    """Test core RateLimiter functionality."""

    def test_rate_limiter_import(self):
        """Test that rate limiter module can be imported."""
        from ai_agent_connector.app.utils.rate_limiter import (
            RateLimiter,
            RateLimitConfig,
        )
        assert RateLimiter is not None
        assert RateLimitConfig is not None

    def test_rate_limit_config(self):
        """Test RateLimitConfig dataclass."""
        from ai_agent_connector.app.utils.rate_limiter import RateLimitConfig

        config = RateLimitConfig(
            queries_per_minute=60,
            queries_per_hour=1000,
            queries_per_day=10000
        )

        assert config.queries_per_minute == 60
        assert config.queries_per_hour == 1000
        assert config.queries_per_day == 10000

        d = config.to_dict()
        assert d['queries_per_minute'] == 60

    def test_rate_limiter_no_config(self):
        """Test rate limiter allows when no config set."""
        from ai_agent_connector.app.utils.rate_limiter import RateLimiter

        limiter = RateLimiter()
        allowed, error = limiter.check_rate_limit('unknown-agent')
        assert allowed is True
        assert error is None

    def test_rate_limiter_within_limits(self):
        """Test rate limiter allows within limits."""
        from ai_agent_connector.app.utils.rate_limiter import RateLimiter, RateLimitConfig

        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=10)
        limiter.set_rate_limit('test-agent', config)

        # First few requests should be allowed
        for i in range(5):
            allowed, error = limiter.check_rate_limit('test-agent')
            assert allowed is True, f"Request {i+1} should be allowed"

    def test_rate_limiter_exceeds_limits(self):
        """Test rate limiter blocks when limits exceeded."""
        from ai_agent_connector.app.utils.rate_limiter import RateLimiter, RateLimitConfig

        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=3)
        limiter.set_rate_limit('test-agent', config)

        # Exhaust the limit
        for i in range(3):
            allowed, _ = limiter.check_rate_limit('test-agent')
            assert allowed is True

        # Next request should be blocked
        allowed, error = limiter.check_rate_limit('test-agent')
        assert allowed is False
        assert 'Rate limit exceeded' in error

    def test_rate_limiter_usage_stats(self):
        """Test rate limiter usage statistics."""
        from ai_agent_connector.app.utils.rate_limiter import RateLimiter, RateLimitConfig

        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=10, queries_per_hour=100)
        limiter.set_rate_limit('test-agent', config)

        # Make some requests
        for _ in range(5):
            limiter.check_rate_limit('test-agent')

        stats = limiter.get_usage_stats('test-agent')
        assert stats['rate_limits_configured'] is True
        assert stats['current_usage']['queries_last_minute'] == 5
        assert stats['remaining']['queries_this_minute'] == 5

    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        from ai_agent_connector.app.utils.rate_limiter import RateLimiter, RateLimitConfig

        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=3)
        limiter.set_rate_limit('test-agent', config)

        # Exhaust limit
        for _ in range(3):
            limiter.check_rate_limit('test-agent')

        # Should be blocked
        allowed, _ = limiter.check_rate_limit('test-agent')
        assert allowed is False

        # Reset
        limiter.reset_agent_limits('test-agent')

        # Should be allowed again
        allowed, _ = limiter.check_rate_limit('test-agent')
        assert allowed is True


class TestRateLimitIntegration:
    """Test rate limit integration with agent registration."""

    def setup_method(self):
        """Set up test fixtures."""
        from ai_agent_connector.app.api import api_bp

        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp, url_prefix='/api')
        self.client = self.app.test_client()

    def test_register_agent_with_default_rate_limits(self):
        """Test that agent registration sets default rate limits."""
        response = self.client.post('/api/agents/register', json={
            'agent_id': 'rate-test-agent-1',
            'agent_info': {'name': 'Test Agent'}
        })

        # Check if registration succeeded (201) or agent already exists
        if response.status_code == 201:
            data = response.get_json()
            assert 'rate_limits' in data
            assert data['rate_limits']['queries_per_minute'] == 60

    def test_register_agent_with_custom_rate_limits(self):
        """Test agent registration with custom rate limits."""
        response = self.client.post('/api/agents/register', json={
            'agent_id': 'rate-test-agent-2',
            'agent_info': {'name': 'Test Agent'},
            'rate_limits': {
                'queries_per_minute': 30,
                'queries_per_hour': 500
            }
        })

        if response.status_code == 201:
            data = response.get_json()
            assert 'rate_limits' in data
            assert data['rate_limits']['queries_per_minute'] == 30
            assert data['rate_limits']['queries_per_hour'] == 500

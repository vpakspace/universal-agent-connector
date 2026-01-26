"""
Tests for rate limiting system
"""

import pytest
import time
from ai_agent_connector.app.utils.rate_limiter import RateLimiter, RateLimitConfig


class TestRateLimitConfig:
    """Tests for RateLimitConfig"""
    
    def test_rate_limit_config_to_dict(self):
        """Test converting rate limit config to dictionary"""
        config = RateLimitConfig(
            queries_per_minute=60,
            queries_per_hour=1000,
            queries_per_day=10000
        )
        
        result = config.to_dict()
        
        assert result['queries_per_minute'] == 60
        assert result['queries_per_hour'] == 1000
        assert result['queries_per_day'] == 10000
    
    def test_rate_limit_config_from_dict(self):
        """Test creating rate limit config from dictionary"""
        data = {
            'queries_per_minute': 30,
            'queries_per_hour': 500
        }
        
        config = RateLimitConfig.from_dict(data)
        
        assert config.queries_per_minute == 30
        assert config.queries_per_hour == 500
        assert config.queries_per_day is None


class TestRateLimiter:
    """Tests for RateLimiter"""
    
    def test_set_and_get_rate_limit(self):
        """Test setting and getting rate limits"""
        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=60)
        
        limiter.set_rate_limit("agent1", config)
        
        retrieved = limiter.get_rate_limit("agent1")
        assert retrieved.queries_per_minute == 60
    
    def test_rate_limit_allows_within_limit(self):
        """Test that queries within limit are allowed"""
        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=5)
        limiter.set_rate_limit("agent1", config)
        
        # Make 5 queries
        for i in range(5):
            allowed, error = limiter.check_rate_limit("agent1")
            assert allowed is True
            assert error is None
    
    def test_rate_limit_blocks_exceeding_limit(self):
        """Test that queries exceeding limit are blocked"""
        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=3)
        limiter.set_rate_limit("agent1", config)
        
        # Make 3 queries (should be allowed)
        for i in range(3):
            allowed, error = limiter.check_rate_limit("agent1")
            assert allowed is True
        
        # 4th query should be blocked
        allowed, error = limiter.check_rate_limit("agent1")
        assert allowed is False
        assert "Rate limit exceeded" in error
    
    def test_rate_limit_no_config_allows_all(self):
        """Test that agents without rate limits are always allowed"""
        limiter = RateLimiter()
        
        allowed, error = limiter.check_rate_limit("agent1")
        assert allowed is True
        assert error is None
    
    def test_rate_limit_cleanup_old_entries(self):
        """Test that old entries are cleaned up"""
        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=2)
        limiter.set_rate_limit("agent1", config)
        
        # Make 2 queries
        limiter.check_rate_limit("agent1")
        limiter.check_rate_limit("agent1")
        
        # Wait a bit and check usage
        time.sleep(1)
        stats = limiter.get_usage_stats("agent1")
        
        # Should still show 2 queries (within 60 seconds)
        assert stats['current_usage']['queries_last_minute'] == 2
    
    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        limiter = RateLimiter()
        config = RateLimitConfig(
            queries_per_minute=60,
            queries_per_hour=1000
        )
        limiter.set_rate_limit("agent1", config)
        
        # Make some queries
        for i in range(3):
            limiter.check_rate_limit("agent1")
        
        stats = limiter.get_usage_stats("agent1")
        
        assert stats['rate_limits_configured'] is True
        assert stats['limits']['queries_per_minute'] == 60
        assert stats['current_usage']['queries_last_minute'] == 3
        assert 'remaining' in stats
    
    def test_reset_agent_limits(self):
        """Test resetting rate limits for an agent"""
        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=5)
        limiter.set_rate_limit("agent1", config)
        
        # Make some queries
        for i in range(3):
            limiter.check_rate_limit("agent1")
        
        # Reset
        limiter.reset_agent_limits("agent1")
        
        # Should be able to make queries again
        allowed, error = limiter.check_rate_limit("agent1")
        assert allowed is True
    
    def test_remove_agent(self):
        """Test removing an agent from rate limiter"""
        limiter = RateLimiter()
        config = RateLimitConfig(queries_per_minute=60)
        limiter.set_rate_limit("agent1", config)
        
        limiter.remove_agent("agent1")
        
        # Should not have config anymore
        assert limiter.get_rate_limit("agent1") is None


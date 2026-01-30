"""Unit tests for rate limiter."""

import time
from unittest.mock import patch

import pytest
from ai_agent_connector.app.utils.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimitConfig:
    def test_defaults(self):
        cfg = RateLimitConfig()
        assert cfg.queries_per_minute is None
        assert cfg.queries_per_hour is None
        assert cfg.queries_per_day is None

    def test_to_dict(self):
        cfg = RateLimitConfig(queries_per_minute=10)
        d = cfg.to_dict()
        assert d["queries_per_minute"] == 10
        assert d["queries_per_hour"] is None

    def test_from_dict(self):
        cfg = RateLimitConfig.from_dict({"queries_per_hour": 100})
        assert cfg.queries_per_hour == 100
        assert cfg.queries_per_minute is None

    def test_roundtrip(self):
        orig = RateLimitConfig(queries_per_minute=5, queries_per_hour=50, queries_per_day=500)
        restored = RateLimitConfig.from_dict(orig.to_dict())
        assert restored.queries_per_minute == 5
        assert restored.queries_per_hour == 50
        assert restored.queries_per_day == 500


class TestRateLimiter:
    def test_no_config_allows(self):
        rl = RateLimiter()
        allowed, msg = rl.check_rate_limit("agent-1")
        assert allowed is True
        assert msg is None

    def test_set_get_limit(self):
        rl = RateLimiter()
        cfg = RateLimitConfig(queries_per_minute=2)
        rl.set_rate_limit("a", cfg)
        assert rl.get_rate_limit("a") is cfg
        assert rl.get_rate_limit("unknown") is None

    def test_within_limit(self):
        rl = RateLimiter()
        rl.set_rate_limit("a", RateLimitConfig(queries_per_minute=3))
        assert rl.check_rate_limit("a")[0] is True
        assert rl.check_rate_limit("a")[0] is True
        assert rl.check_rate_limit("a")[0] is True

    def test_exceeds_minute_limit(self):
        rl = RateLimiter()
        rl.set_rate_limit("a", RateLimitConfig(queries_per_minute=2))
        rl.check_rate_limit("a")
        rl.check_rate_limit("a")
        allowed, msg = rl.check_rate_limit("a")
        assert allowed is False
        assert "per minute" in msg

    def test_usage_stats_no_config(self):
        rl = RateLimiter()
        stats = rl.get_usage_stats("x")
        assert stats["rate_limits_configured"] is False

    def test_usage_stats_with_config(self):
        rl = RateLimiter()
        rl.set_rate_limit("a", RateLimitConfig(queries_per_minute=10))
        rl.check_rate_limit("a")
        stats = rl.get_usage_stats("a")
        assert stats["rate_limits_configured"] is True
        assert stats["current_usage"]["queries_last_minute"] == 1

    def test_reset_agent(self):
        rl = RateLimiter()
        rl.set_rate_limit("a", RateLimitConfig(queries_per_minute=2))
        rl.check_rate_limit("a")
        rl.check_rate_limit("a")
        rl.reset_agent_limits("a")
        allowed, _ = rl.check_rate_limit("a")
        assert allowed is True

    def test_remove_agent(self):
        rl = RateLimiter()
        rl.set_rate_limit("a", RateLimitConfig(queries_per_minute=5))
        rl.check_rate_limit("a")
        rl.remove_agent("a")
        assert rl.get_rate_limit("a") is None
        # After removal, no config → allow
        allowed, _ = rl.check_rate_limit("a")
        assert allowed is True

    def test_sliding_window_expiry(self):
        rl = RateLimiter()
        rl.set_rate_limit("a", RateLimitConfig(queries_per_minute=1))

        # First query at t=0
        with patch("ai_agent_connector.app.utils.rate_limiter.time") as mock_time:
            mock_time.time.return_value = 1000.0
            allowed, _ = rl.check_rate_limit("a")
            assert allowed is True

            # Second query still within window → denied
            mock_time.time.return_value = 1030.0
            allowed, _ = rl.check_rate_limit("a")
            assert allowed is False

            # After window expires → allowed
            mock_time.time.return_value = 1061.0
            allowed, _ = rl.check_rate_limit("a")
            assert allowed is True

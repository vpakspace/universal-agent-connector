"""Unit tests for retry policy."""

import random
from unittest.mock import patch, MagicMock

import pytest
from ai_agent_connector.app.utils.retry_policy import (
    RetryPolicy,
    RetryStrategy,
    RetryExecutor,
)


class TestRetryPolicy:
    def test_defaults(self):
        p = RetryPolicy()
        assert p.enabled is True
        assert p.max_retries == 3
        assert p.strategy == RetryStrategy.EXPONENTIAL

    def test_to_dict(self):
        p = RetryPolicy(strategy=RetryStrategy.FIXED)
        d = p.to_dict()
        assert d["strategy"] == "fixed"
        assert d["enabled"] is True

    def test_from_dict(self):
        p = RetryPolicy.from_dict({"strategy": "linear", "max_retries": 5})
        assert p.strategy == RetryStrategy.LINEAR
        assert p.max_retries == 5

    def test_roundtrip(self):
        orig = RetryPolicy(max_retries=7, strategy=RetryStrategy.FIXED, jitter=False)
        restored = RetryPolicy.from_dict(orig.to_dict())
        assert restored.max_retries == 7
        assert restored.strategy == RetryStrategy.FIXED

    def test_calculate_delay_attempt_zero(self):
        p = RetryPolicy(jitter=False)
        assert p.calculate_delay(0) == 0.0

    def test_calculate_delay_fixed(self):
        p = RetryPolicy(strategy=RetryStrategy.FIXED, initial_delay=2.0, jitter=False)
        assert p.calculate_delay(1) == 2.0
        assert p.calculate_delay(3) == 2.0

    def test_calculate_delay_exponential(self):
        p = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False,
        )
        assert p.calculate_delay(1) == 1.0
        assert p.calculate_delay(2) == 2.0
        assert p.calculate_delay(3) == 4.0

    def test_calculate_delay_linear(self):
        p = RetryPolicy(strategy=RetryStrategy.LINEAR, initial_delay=1.0, jitter=False)
        assert p.calculate_delay(1) == 1.0
        assert p.calculate_delay(2) == 2.0
        assert p.calculate_delay(3) == 3.0

    def test_calculate_delay_capped(self):
        p = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=10.0,
            max_delay=15.0,
            jitter=False,
        )
        assert p.calculate_delay(5) == 15.0

    def test_calculate_delay_disabled(self):
        p = RetryPolicy(enabled=False)
        assert p.calculate_delay(1) == 0.0

    def test_should_retry_retryable(self):
        p = RetryPolicy()
        assert p.should_retry(Exception("timeout occurred"), 0) is True

    def test_should_retry_non_retryable(self):
        p = RetryPolicy()
        assert p.should_retry(Exception("invalid syntax"), 0) is False

    def test_should_retry_max_exceeded(self):
        p = RetryPolicy(max_retries=2)
        assert p.should_retry(Exception("timeout"), 2) is False

    def test_should_retry_disabled(self):
        p = RetryPolicy(enabled=False)
        assert p.should_retry(Exception("timeout"), 0) is False


class TestRetryExecutor:
    def test_success_first_try(self):
        policy = RetryPolicy(jitter=False)
        executor = RetryExecutor(policy)
        result = executor.execute(lambda: 42)
        assert result == 42

    def test_retry_then_success(self):
        policy = RetryPolicy(jitter=False, initial_delay=0.0)
        executor = RetryExecutor(policy)

        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("connection_error")
            return "ok"

        with patch("ai_agent_connector.app.utils.retry_policy.time.sleep"):
            result = executor.execute(flaky)
        assert result == "ok"
        assert call_count == 3

    def test_exhausted_retries(self):
        policy = RetryPolicy(max_retries=1, jitter=False)
        executor = RetryExecutor(policy)

        def always_fail():
            raise Exception("timeout error")

        with patch("ai_agent_connector.app.utils.retry_policy.time.sleep"):
            with pytest.raises(Exception, match="timeout"):
                executor.execute(always_fail)

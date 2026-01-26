"""
Tests for retry policy system
"""

import pytest
import time
from unittest.mock import Mock, patch
from ai_agent_connector.app.utils.retry_policy import (
    RetryPolicy,
    RetryStrategy,
    RetryExecutor
)


class TestRetryPolicy:
    """Tests for RetryPolicy"""
    
    def test_retry_policy_to_dict(self):
        """Test converting retry policy to dictionary"""
        policy = RetryPolicy(
            enabled=True,
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL
        )
        
        result = policy.to_dict()
        
        assert result['enabled'] is True
        assert result['max_retries'] == 3
        assert result['strategy'] == 'exponential'
    
    def test_retry_policy_from_dict(self):
        """Test creating retry policy from dictionary"""
        data = {
            'enabled': True,
            'max_retries': 5,
            'strategy': 'fixed',
            'initial_delay': 2.0
        }
        
        policy = RetryPolicy.from_dict(data)
        
        assert policy.enabled is True
        assert policy.max_retries == 5
        assert policy.strategy == RetryStrategy.FIXED
        assert policy.initial_delay == 2.0
    
    def test_calculate_delay_fixed(self):
        """Test fixed delay calculation"""
        policy = RetryPolicy(
            strategy=RetryStrategy.FIXED,
            initial_delay=1.0
        )
        
        delay1 = policy.calculate_delay(1)
        delay2 = policy.calculate_delay(2)
        
        assert delay1 == 1.0
        assert delay2 == 1.0
    
    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation"""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=1.0,
            backoff_multiplier=2.0
        )
        
        delay1 = policy.calculate_delay(1)
        delay2 = policy.calculate_delay(2)
        delay3 = policy.calculate_delay(3)
        
        # Should be approximately 1, 2, 4 (with possible jitter)
        assert delay1 >= 0.9  # Account for jitter
        assert delay2 >= 1.8
        assert delay3 >= 3.6
    
    def test_calculate_delay_linear(self):
        """Test linear backoff delay calculation"""
        policy = RetryPolicy(
            strategy=RetryStrategy.LINEAR,
            initial_delay=1.0
        )
        
        delay1 = policy.calculate_delay(1)
        delay2 = policy.calculate_delay(2)
        
        assert delay1 >= 0.9  # Account for jitter
        assert delay2 >= 1.8
    
    def test_calculate_delay_max_delay(self):
        """Test that delay is capped at max_delay"""
        policy = RetryPolicy(
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=10.0,
            max_delay=20.0,
            backoff_multiplier=2.0
        )
        
        delay = policy.calculate_delay(10)  # Should exceed max_delay
        
        assert delay <= 20.0
    
    def test_should_retry_enabled(self):
        """Test retry decision when enabled"""
        policy = RetryPolicy(
            enabled=True,
            max_retries=3,
            retryable_errors=['timeout', 'connection_error']
        )
        
        # Should retry for retryable errors
        timeout_error = Exception("timeout occurred")
        assert policy.should_retry(timeout_error, 0) is True
        assert policy.should_retry(timeout_error, 1) is True
        
        # Should not retry after max_retries
        assert policy.should_retry(timeout_error, 3) is False
    
    def test_should_retry_disabled(self):
        """Test retry decision when disabled"""
        policy = RetryPolicy(enabled=False)
        
        error = Exception("timeout")
        assert policy.should_retry(error, 0) is False
    
    def test_should_retry_non_retryable_error(self):
        """Test that non-retryable errors are not retried"""
        policy = RetryPolicy(
            enabled=True,
            max_retries=3,
            retryable_errors=['timeout']
        )
        
        other_error = Exception("invalid input")
        assert policy.should_retry(other_error, 0) is False


class TestRetryExecutor:
    """Tests for RetryExecutor"""
    
    def test_execute_success_first_attempt(self):
        """Test successful execution on first attempt"""
        policy = RetryPolicy(max_retries=3)
        executor = RetryExecutor(policy)
        
        operation = Mock(return_value="success")
        result = executor.execute(operation)
        
        assert result == "success"
        assert operation.call_count == 1
    
    def test_execute_retry_on_failure(self):
        """Test retry on failure"""
        policy = RetryPolicy(
            max_retries=3,
            initial_delay=0.1,  # Short delay for testing
            retryable_errors=['timeout']
        )
        executor = RetryExecutor(policy)
        
        operation = Mock(side_effect=[
            Exception("timeout"),
            Exception("timeout"),
            "success"
        ])
        
        result = executor.execute(operation)
        
        assert result == "success"
        assert operation.call_count == 3
    
    def test_execute_exhaust_retries(self):
        """Test that all retries are exhausted before raising"""
        policy = RetryPolicy(
            max_retries=2,
            initial_delay=0.1,
            retryable_errors=['timeout']
        )
        executor = RetryExecutor(policy)
        
        operation = Mock(side_effect=Exception("timeout"))
        
        with pytest.raises(Exception):
            executor.execute(operation)
        
        assert operation.call_count == 3  # Initial + 2 retries
    
    def test_execute_non_retryable_error(self):
        """Test that non-retryable errors are not retried"""
        policy = RetryPolicy(
            max_retries=3,
            retryable_errors=['timeout']
        )
        executor = RetryExecutor(policy)
        
        operation = Mock(side_effect=ValueError("invalid input"))
        
        with pytest.raises(ValueError):
            executor.execute(operation)
        
        assert operation.call_count == 1  # No retries


"""
Retry policy configuration for failed agent requests
Supports configurable retry strategies
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import time
import random


class RetryStrategy(Enum):
    """Retry strategies"""
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    CUSTOM = "custom"  # Custom retry function


@dataclass
class RetryPolicy:
    """Configuration for retry policy"""
    enabled: bool = True
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retryable_errors: List[str] = field(default_factory=lambda: [
        'timeout', 'connection_error', 'rate_limit', 'server_error', '503', '502', '500'
    ])
    jitter: bool = True  # Add random jitter to prevent thundering herd
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'enabled': self.enabled,
            'max_retries': self.max_retries,
            'initial_delay': self.initial_delay,
            'max_delay': self.max_delay,
            'backoff_multiplier': self.backoff_multiplier,
            'strategy': self.strategy.value,
            'retryable_errors': self.retryable_errors,
            'jitter': self.jitter
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetryPolicy':
        """Create from dictionary"""
        return cls(
            enabled=data.get('enabled', True),
            max_retries=data.get('max_retries', 3),
            initial_delay=data.get('initial_delay', 1.0),
            max_delay=data.get('max_delay', 60.0),
            backoff_multiplier=data.get('backoff_multiplier', 2.0),
            strategy=RetryStrategy(data.get('strategy', 'exponential')),
            retryable_errors=data.get('retryable_errors', []),
            jitter=data.get('jitter', True)
        )
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a retry attempt.
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            float: Delay in seconds
        """
        if not self.enabled or attempt == 0:
            return 0.0
        
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        else:
            delay = self.initial_delay
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative
        
        return delay
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number
            
        Returns:
            bool: True if should retry, False otherwise
        """
        if not self.enabled:
            return False
        
        if attempt >= self.max_retries:
            return False
        
        # Check if error is retryable
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        for retryable in self.retryable_errors:
            if retryable.lower() in error_str or retryable.lower() in error_type:
                return True
        
        return False


class RetryExecutor:
    """Executor for retrying operations with configurable policies"""
    
    def __init__(self, policy: RetryPolicy):
        """
        Initialize retry executor.
        
        Args:
            policy: Retry policy configuration
        """
        self.policy = policy
    
    def execute(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of operation
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.policy.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.policy.should_retry(e, attempt):
                    raise e
                
                if attempt < self.policy.max_retries:
                    delay = self.policy.calculate_delay(attempt + 1)
                    if delay > 0:
                        time.sleep(delay)
        
        # All retries exhausted
        raise last_exception


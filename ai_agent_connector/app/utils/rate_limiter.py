"""
Rate limiting system for AI agent queries
Supports per-agent rate limits (queries per minute/hour)
"""

import time
from typing import Dict, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    queries_per_minute: Optional[int] = None
    queries_per_hour: Optional[int] = None
    queries_per_day: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'queries_per_minute': self.queries_per_minute,
            'queries_per_hour': self.queries_per_hour,
            'queries_per_day': self.queries_per_day
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RateLimitConfig':
        """Create from dictionary"""
        return cls(
            queries_per_minute=data.get('queries_per_minute'),
            queries_per_hour=data.get('queries_per_hour'),
            queries_per_day=data.get('queries_per_day')
        )


class RateLimiter:
    """
    Rate limiter for tracking and enforcing query limits per agent.
    Uses sliding window algorithm for accurate rate limiting.
    """
    
    def __init__(self):
        """Initialize rate limiter"""
        # agent_id -> deque of timestamps
        self._minute_queries: Dict[str, deque] = defaultdict(lambda: deque())
        self._hour_queries: Dict[str, deque] = defaultdict(lambda: deque())
        self._day_queries: Dict[str, deque] = defaultdict(lambda: deque())
        self._locks: Dict[str, Lock] = defaultdict(Lock)
        self._configs: Dict[str, RateLimitConfig] = {}
    
    def set_rate_limit(self, agent_id: str, config: RateLimitConfig) -> None:
        """
        Set rate limit configuration for an agent.
        
        Args:
            agent_id: Agent identifier
            config: Rate limit configuration
        """
        self._configs[agent_id] = config
    
    def get_rate_limit(self, agent_id: str) -> Optional[RateLimitConfig]:
        """
        Get rate limit configuration for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            RateLimitConfig or None if not configured
        """
        return self._configs.get(agent_id)
    
    def check_rate_limit(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if agent is within rate limits.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            tuple: (allowed, error_message)
            - allowed: True if within limits, False if exceeded
            - error_message: Error message if limit exceeded, None otherwise
        """
        config = self._configs.get(agent_id)
        if not config:
            # No rate limit configured, allow
            return True, None
        
        lock = self._locks[agent_id]
        with lock:
            current_time = time.time()
            
            # Clean old entries
            self._clean_old_entries(agent_id, current_time)
            
            # Check minute limit
            if config.queries_per_minute:
                minute_queries = self._minute_queries[agent_id]
                if len(minute_queries) >= config.queries_per_minute:
                    return False, f"Rate limit exceeded: {config.queries_per_minute} queries per minute"
            
            # Check hour limit
            if config.queries_per_hour:
                hour_queries = self._hour_queries[agent_id]
                if len(hour_queries) >= config.queries_per_hour:
                    return False, f"Rate limit exceeded: {config.queries_per_hour} queries per hour"
            
            # Check day limit
            if config.queries_per_day:
                day_queries = self._day_queries[agent_id]
                if len(day_queries) >= config.queries_per_day:
                    return False, f"Rate limit exceeded: {config.queries_per_day} queries per day"
            
            # Record query
            self._record_query(agent_id, current_time)
            
            return True, None
    
    def _clean_old_entries(self, agent_id: str, current_time: float) -> None:
        """Remove old entries outside the time windows"""
        # Clean minute window (last 60 seconds)
        minute_queries = self._minute_queries[agent_id]
        while minute_queries and current_time - minute_queries[0] > 60:
            minute_queries.popleft()
        
        # Clean hour window (last 3600 seconds)
        hour_queries = self._hour_queries[agent_id]
        while hour_queries and current_time - hour_queries[0] > 3600:
            hour_queries.popleft()
        
        # Clean day window (last 86400 seconds)
        day_queries = self._day_queries[agent_id]
        while day_queries and current_time - day_queries[0] > 86400:
            day_queries.popleft()
    
    def _record_query(self, agent_id: str, timestamp: float) -> None:
        """Record a query timestamp"""
        self._minute_queries[agent_id].append(timestamp)
        self._hour_queries[agent_id].append(timestamp)
        self._day_queries[agent_id].append(timestamp)
    
    def get_usage_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get current usage statistics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict containing usage statistics
        """
        config = self._configs.get(agent_id)
        if not config:
            return {
                'rate_limits_configured': False,
                'current_usage': {}
            }
        
        current_time = time.time()
        self._clean_old_entries(agent_id, current_time)
        
        return {
            'rate_limits_configured': True,
            'limits': config.to_dict(),
            'current_usage': {
                'queries_last_minute': len(self._minute_queries[agent_id]),
                'queries_last_hour': len(self._hour_queries[agent_id]),
                'queries_last_day': len(self._day_queries[agent_id])
            },
            'remaining': {
                'queries_this_minute': max(0, (config.queries_per_minute or float('inf')) - len(self._minute_queries[agent_id])),
                'queries_this_hour': max(0, (config.queries_per_hour or float('inf')) - len(self._hour_queries[agent_id])),
                'queries_this_day': max(0, (config.queries_per_day or float('inf')) - len(self._day_queries[agent_id]))
            }
        }
    
    def reset_agent_limits(self, agent_id: str) -> None:
        """Reset rate limit tracking for an agent"""
        with self._locks[agent_id]:
            self._minute_queries[agent_id].clear()
            self._hour_queries[agent_id].clear()
            self._day_queries[agent_id].clear()
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove all rate limit data for an agent"""
        self._minute_queries.pop(agent_id, None)
        self._hour_queries.pop(agent_id, None)
        self._day_queries.pop(agent_id, None)
        self._configs.pop(agent_id, None)
        self._locks.pop(agent_id, None)


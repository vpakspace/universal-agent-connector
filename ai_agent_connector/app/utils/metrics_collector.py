"""
Real-time metrics collection for query monitoring
Tracks query volume, latency, and error rates per agent
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from ..utils.helpers import get_timestamp
import threading


@dataclass
class QueryMetric:
    """A single query metric entry"""
    agent_id: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, NATURAL_LANGUAGE
    execution_time_ms: float
    success: bool
    error_type: Optional[str] = None
    timestamp: str = field(default_factory=get_timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'query_type': self.query_type,
            'execution_time_ms': self.execution_time_ms,
            'success': self.success,
            'error_type': self.error_type,
            'timestamp': self.timestamp
        }


@dataclass
class AgentMetrics:
    """Aggregated metrics for an agent"""
    agent_id: str
    time_window_seconds: int
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float
    error_rate: float
    queries_per_second: float
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'time_window_seconds': self.time_window_seconds,
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'avg_latency_ms': self.avg_latency_ms,
            'p50_latency_ms': self.p50_latency_ms,
            'p95_latency_ms': self.p95_latency_ms,
            'p99_latency_ms': self.p99_latency_ms,
            'max_latency_ms': self.max_latency_ms,
            'min_latency_ms': self.min_latency_ms,
            'error_rate': self.error_rate,
            'queries_per_second': self.queries_per_second,
            'error_breakdown': self.error_breakdown
        }


class MetricsCollector:
    """
    Collects and aggregates real-time metrics for query monitoring.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, max_metrics_per_agent: int = 10000, default_window_seconds: int = 60):
        """
        Initialize metrics collector.
        
        Args:
            max_metrics_per_agent: Maximum number of metrics to keep per agent
            default_window_seconds: Default time window for aggregations
        """
        # agent_id -> deque of QueryMetric
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_per_agent))
        self._lock = threading.Lock()
        self.default_window_seconds = default_window_seconds
    
    def record_query(
        self,
        agent_id: str,
        query_type: str,
        execution_time_ms: float,
        success: bool,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record a query metric.
        
        Args:
            agent_id: Agent ID
            query_type: Type of query (SELECT, INSERT, etc.)
            execution_time_ms: Execution time in milliseconds
            success: Whether query succeeded
            error_type: Type of error if failed
        """
        metric = QueryMetric(
            agent_id=agent_id,
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            success=success,
            error_type=error_type
        )
        
        with self._lock:
            self._metrics[agent_id].append(metric)
    
    def get_agent_metrics(
        self,
        agent_id: str,
        window_seconds: Optional[int] = None
    ) -> Optional[AgentMetrics]:
        """
        Get aggregated metrics for an agent.
        
        Args:
            agent_id: Agent ID
            window_seconds: Time window in seconds (default: self.default_window_seconds)
            
        Returns:
            AgentMetrics or None if no metrics available
        """
        window_seconds = window_seconds or self.default_window_seconds
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        
        with self._lock:
            if agent_id not in self._metrics:
                return None
            
            # Filter metrics within time window
            recent_metrics = [
                m for m in self._metrics[agent_id]
                if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00').split('.')[0]) >= cutoff_time
            ]
            
            if not recent_metrics:
                return None
            
            # Calculate statistics
            latencies = [m.execution_time_ms for m in recent_metrics]
            latencies.sort()
            
            total = len(recent_metrics)
            successful = sum(1 for m in recent_metrics if m.success)
            failed = total - successful
            
            # Percentiles
            def percentile(data: List[float], p: float) -> float:
                if not data:
                    return 0.0
                k = (len(data) - 1) * p
                f = int(k)
                c = k - f
                if f + 1 < len(data):
                    return data[f] + c * (data[f + 1] - data[f])
                return data[f]
            
            # Error breakdown
            error_breakdown = defaultdict(int)
            for m in recent_metrics:
                if not m.success and m.error_type:
                    error_breakdown[m.error_type] += 1
            
            return AgentMetrics(
                agent_id=agent_id,
                time_window_seconds=window_seconds,
                total_queries=total,
                successful_queries=successful,
                failed_queries=failed,
                avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
                p50_latency_ms=percentile(latencies, 0.50),
                p95_latency_ms=percentile(latencies, 0.95),
                p99_latency_ms=percentile(latencies, 0.99),
                max_latency_ms=max(latencies) if latencies else 0.0,
                min_latency_ms=min(latencies) if latencies else 0.0,
                error_rate=failed / total if total > 0 else 0.0,
                queries_per_second=total / window_seconds if window_seconds > 0 else 0.0,
                error_breakdown=dict(error_breakdown)
            )
    
    def get_all_agents_metrics(
        self,
        window_seconds: Optional[int] = None
    ) -> Dict[str, AgentMetrics]:
        """
        Get metrics for all agents.
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            Dictionary of agent_id -> AgentMetrics
        """
        with self._lock:
            agent_ids = list(self._metrics.keys())
        
        return {
            agent_id: metrics
            for agent_id in agent_ids
            if (metrics := self.get_agent_metrics(agent_id, window_seconds)) is not None
        }
    
    def get_dashboard_data(
        self,
        window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get dashboard data for all agents.
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            Dictionary with dashboard data
        """
        all_metrics = self.get_all_agents_metrics(window_seconds)
        
        # Calculate system-wide totals
        total_queries = sum(m.total_queries for m in all_metrics.values())
        total_successful = sum(m.successful_queries for m in all_metrics.values())
        total_failed = sum(m.failed_queries for m in all_metrics.values())
        
        # Calculate weighted average latency
        if total_queries > 0:
            weighted_avg_latency = sum(
                m.avg_latency_ms * m.total_queries
                for m in all_metrics.values()
            ) / total_queries
        else:
            weighted_avg_latency = 0.0
        
        return {
            'window_seconds': window_seconds or self.default_window_seconds,
            'timestamp': get_timestamp(),
            'system_metrics': {
                'total_queries': total_queries,
                'total_successful': total_successful,
                'total_failed': total_failed,
                'overall_error_rate': total_failed / total_queries if total_queries > 0 else 0.0,
                'weighted_avg_latency_ms': weighted_avg_latency,
                'total_queries_per_second': sum(m.queries_per_second for m in all_metrics.values())
            },
            'agent_metrics': {
                agent_id: metrics.to_dict()
                for agent_id, metrics in all_metrics.items()
            }
        }
    
    def clear_agent_metrics(self, agent_id: str) -> None:
        """Clear all metrics for an agent"""
        with self._lock:
            if agent_id in self._metrics:
                del self._metrics[agent_id]
    
    def clear_all_metrics(self) -> None:
        """Clear all metrics"""
        with self._lock:
            self._metrics.clear()


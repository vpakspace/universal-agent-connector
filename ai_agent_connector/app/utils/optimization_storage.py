"""
Storage for query optimization metrics and recommendations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class OptimizationMetric:
    """Query optimization metric"""
    query_id: str
    query: str
    agent_id: str
    before_execution_time: float
    after_execution_time: Optional[float]
    before_rows_examined: Optional[int]
    after_rows_examined: Optional[int]
    indexes_applied: List[str]
    rewrites_applied: List[str]
    improvement_percentage: Optional[float]
    recorded_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OptimizationStorage:
    """In-memory storage for optimization metrics (use database in production)"""
    
    def __init__(self):
        self._metrics: Dict[str, OptimizationMetric] = {}
        self._recommendations: Dict[str, List[Dict[str, Any]]] = {}  # agent_id -> recommendations
    
    def record_before_metrics(self, query_id: str, query: str, agent_id: str, 
                             execution_time: float, rows_examined: Optional[int] = None) -> str:
        """Record metrics before optimization"""
        metric = OptimizationMetric(
            query_id=query_id,
            query=query,
            agent_id=agent_id,
            before_execution_time=execution_time,
            after_execution_time=None,
            before_rows_examined=rows_examined,
            after_rows_examined=None,
            indexes_applied=[],
            rewrites_applied=[],
            improvement_percentage=None,
            recorded_at=datetime.utcnow().isoformat()
        )
        self._metrics[query_id] = metric
        return query_id
    
    def update_after_metrics(self, query_id: str, execution_time: float,
                            rows_examined: Optional[int] = None,
                            indexes_applied: Optional[List[str]] = None,
                            rewrites_applied: Optional[List[str]] = None):
        """Update metrics after optimization"""
        if query_id not in self._metrics:
            return
        
        metric = self._metrics[query_id]
        metric.after_execution_time = execution_time
        metric.after_rows_examined = rows_examined
        
        if indexes_applied:
            metric.indexes_applied = indexes_applied
        if rewrites_applied:
            metric.rewrites_applied = rewrites_applied
        
        # Calculate improvement percentage
        if metric.before_execution_time and execution_time:
            improvement = ((metric.before_execution_time - execution_time) / metric.before_execution_time) * 100
            metric.improvement_percentage = improvement
    
    def get_metric(self, query_id: str) -> Optional[OptimizationMetric]:
        """Get metric by query ID"""
        return self._metrics.get(query_id)
    
    def list_metrics(self, agent_id: Optional[str] = None) -> List[OptimizationMetric]:
        """List metrics, optionally filtered by agent"""
        metrics = list(self._metrics.values())
        if agent_id:
            metrics = [m for m in metrics if m.agent_id == agent_id]
        return sorted(metrics, key=lambda x: x.recorded_at, reverse=True)
    
    def save_recommendations(self, agent_id: str, recommendations: List[Dict[str, Any]]):
        """Save recommendations for an agent"""
        if agent_id not in self._recommendations:
            self._recommendations[agent_id] = []
        self._recommendations[agent_id].extend(recommendations)
    
    def get_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get recommendations for an agent"""
        return self._recommendations.get(agent_id, [])
    
    def clear_recommendations(self, agent_id: str):
        """Clear recommendations for an agent"""
        if agent_id in self._recommendations:
            del self._recommendations[agent_id]


# Global storage instance
optimization_storage = OptimizationStorage()


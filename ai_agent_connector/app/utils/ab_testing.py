"""
A/B testing for different AI models
Test different AI models on the same query
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import json


class ABTestStatus(Enum):
    """A/B test status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ABTestVariant:
    """A variant in an A/B test"""
    variant_id: str
    model_name: str
    model_config: Dict[str, Any]
    result: Optional[Any] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'variant_id': self.variant_id,
            'model_name': self.model_name,
            'model_config': self.model_config,
            'success': self.success,
            'execution_time_ms': self.execution_time_ms,
            'error': self.error
        }


@dataclass
class ABTest:
    """An A/B test"""
    test_id: str
    agent_id: str
    query: str
    query_type: str
    variants: List[ABTestVariant]
    status: ABTestStatus = ABTestStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    winner: Optional[str] = None  # variant_id of winner
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'test_id': self.test_id,
            'agent_id': self.agent_id,
            'query': self.query,
            'query_type': self.query_type,
            'variants': [v.to_dict() for v in self.variants],
            'status': self.status.value,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'winner': self.winner,
            'metrics': self.metrics,
            'metadata': self.metadata
        }


class ABTestManager:
    """
    Manages A/B testing for AI models.
    """
    
    def __init__(self):
        """Initialize A/B test manager"""
        # test_id -> ABTest
        self._tests: Dict[str, ABTest] = {}
        # agent_id -> list of test_ids
        self._agent_tests: Dict[str, List[str]] = {}
    
    def create_test(
        self,
        agent_id: str,
        query: str,
        query_type: str,
        variants: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ABTest:
        """
        Create an A/B test.
        
        Args:
            agent_id: Agent ID
            query: Query to test
            query_type: Type of query
            variants: List of variant configs (model_name, model_config)
            metadata: Additional metadata
            
        Returns:
            ABTest object
        """
        test_id = str(uuid.uuid4())
        
        # Create variants
        test_variants = []
        for variant_config in variants:
            variant = ABTestVariant(
                variant_id=str(uuid.uuid4()),
                model_name=variant_config['model_name'],
                model_config=variant_config.get('model_config', {})
            )
            test_variants.append(variant)
        
        test = ABTest(
            test_id=test_id,
            agent_id=agent_id,
            query=query,
            query_type=query_type,
            variants=test_variants,
            metadata=metadata or {}
        )
        
        self._tests[test_id] = test
        
        # Track by agent
        if agent_id not in self._agent_tests:
            self._agent_tests[agent_id] = []
        self._agent_tests[agent_id].append(test_id)
        
        return test
    
    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get an A/B test"""
        return self._tests.get(test_id)
    
    def list_tests(
        self,
        agent_id: Optional[str] = None,
        status: Optional[ABTestStatus] = None
    ) -> List[ABTest]:
        """
        List A/B tests.
        
        Args:
            agent_id: Filter by agent ID
            status: Filter by status
            
        Returns:
            List of ABTest objects
        """
        tests = list(self._tests.values())
        
        if agent_id:
            tests = [t for t in tests if t.agent_id == agent_id]
        
        if status:
            tests = [t for t in tests if t.status == status]
        
        # Sort by created_at (newest first)
        tests.sort(key=lambda x: x.created_at, reverse=True)
        
        return tests
    
    def update_variant_result(
        self,
        test_id: str,
        variant_id: str,
        result: Any,
        execution_time_ms: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> Optional[ABTest]:
        """
        Update variant result.
        
        Args:
            test_id: Test ID
            variant_id: Variant ID
            result: Query result
            execution_time_ms: Execution time in milliseconds
            success: Whether execution was successful
            error: Error message if failed
            
        Returns:
            Updated ABTest or None if not found
        """
        test = self._tests.get(test_id)
        if not test:
            return None
        
        variant = next((v for v in test.variants if v.variant_id == variant_id), None)
        if not variant:
            return None
        
        variant.result = result
        variant.execution_time_ms = execution_time_ms
        variant.success = success
        variant.error = error
        
        # Check if all variants are complete
        all_complete = all(v.result is not None or v.error for v in test.variants)
        if all_complete and test.status == ABTestStatus.RUNNING:
            test.status = ABTestStatus.COMPLETED
            test.completed_at = datetime.utcnow().isoformat()
            test.winner = self._determine_winner(test)
            test.metrics = self._calculate_metrics(test)
        
        return test
    
    def start_test(self, test_id: str) -> Optional[ABTest]:
        """Mark test as running"""
        test = self._tests.get(test_id)
        if not test:
            return None
        
        test.status = ABTestStatus.RUNNING
        return test
    
    def mark_test_failed(self, test_id: str, error: str) -> Optional[ABTest]:
        """Mark test as failed"""
        test = self._tests.get(test_id)
        if not test:
            return None
        
        test.status = ABTestStatus.FAILED
        test.metadata['error'] = error
        return test
    
    def delete_test(self, test_id: str) -> bool:
        """Delete an A/B test"""
        test = self._tests.get(test_id)
        if not test:
            return False
        
        # Remove from agent tracking
        if test.agent_id in self._agent_tests:
            self._agent_tests[test.agent_id] = [
                tid for tid in self._agent_tests[test.agent_id] if tid != test_id
            ]
        
        del self._tests[test_id]
        return True
    
    def _determine_winner(self, test: ABTest) -> Optional[str]:
        """Determine winner based on metrics"""
        successful_variants = [v for v in test.variants if v.success]
        
        if not successful_variants:
            return None
        
        # Winner is fastest successful variant
        winner = min(successful_variants, key=lambda v: v.execution_time_ms or float('inf'))
        return winner.variant_id
    
    def _calculate_metrics(self, test: ABTest) -> Dict[str, Any]:
        """Calculate test metrics"""
        successful_variants = [v for v in test.variants if v.success]
        failed_variants = [v for v in test.variants if not v.success]
        
        metrics = {
            'total_variants': len(test.variants),
            'successful_variants': len(successful_variants),
            'failed_variants': len(failed_variants),
            'success_rate': len(successful_variants) / len(test.variants) if test.variants else 0
        }
        
        if successful_variants:
            execution_times = [v.execution_time_ms for v in successful_variants if v.execution_time_ms]
            if execution_times:
                metrics['avg_execution_time_ms'] = sum(execution_times) / len(execution_times)
                metrics['min_execution_time_ms'] = min(execution_times)
                metrics['max_execution_time_ms'] = max(execution_times)
        
        return metrics


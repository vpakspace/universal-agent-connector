"""
Data retention policies for query logs
Automatically purges old data based on retention policies
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid


class RetentionPolicyType(Enum):
    """Retention policy types"""
    QUERY_LOGS = "query_logs"
    AUDIT_LOGS = "audit_logs"
    ERROR_LOGS = "error_logs"
    METRICS = "metrics"
    CACHE = "cache"
    DLQ = "dlq"  # Dead-letter queue


@dataclass
class RetentionPolicy:
    """A data retention policy"""
    policy_id: str
    name: str
    policy_type: RetentionPolicyType
    retention_days: int
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_run_at: Optional[str] = None
    last_purged_count: int = 0
    total_purged_count: int = 0
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'policy_type': self.policy_type.value,
            'retention_days': self.retention_days,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_run_at': self.last_run_at,
            'last_purged_count': self.last_purged_count,
            'total_purged_count': self.total_purged_count,
            'description': self.description,
            'metadata': self.metadata
        }
    
    def get_cutoff_date(self) -> datetime:
        """Get cutoff date for retention"""
        return datetime.utcnow() - timedelta(days=self.retention_days)


class DataRetentionManager:
    """
    Manages data retention policies.
    """
    
    def __init__(self):
        """Initialize data retention manager"""
        # policy_id -> RetentionPolicy
        self._policies: Dict[str, RetentionPolicy] = {}
        # policy_type -> list of policy_ids
        self._type_policies: Dict[RetentionPolicyType, List[str]] = {}
    
    def create_policy(
        self,
        name: str,
        policy_type: RetentionPolicyType,
        retention_days: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RetentionPolicy:
        """
        Create a retention policy.
        
        Args:
            name: Policy name
            policy_type: Type of data to retain
            retention_days: Number of days to retain
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            RetentionPolicy object
        """
        policy_id = str(uuid.uuid4())
        
        policy = RetentionPolicy(
            policy_id=policy_id,
            name=name,
            policy_type=policy_type,
            retention_days=retention_days,
            description=description,
            metadata=metadata or {}
        )
        
        self._policies[policy_id] = policy
        
        # Track by type
        if policy_type not in self._type_policies:
            self._type_policies[policy_type] = []
        self._type_policies[policy_type].append(policy_id)
        
        return policy
    
    def get_policy(self, policy_id: str) -> Optional[RetentionPolicy]:
        """Get a retention policy"""
        return self._policies.get(policy_id)
    
    def list_policies(
        self,
        policy_type: Optional[RetentionPolicyType] = None,
        is_active: Optional[bool] = None
    ) -> List[RetentionPolicy]:
        """
        List retention policies.
        
        Args:
            policy_type: Filter by policy type
            is_active: Filter by active status
            
        Returns:
            List of RetentionPolicy objects
        """
        policies = list(self._policies.values())
        
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        
        if is_active is not None:
            policies = [p for p in policies if p.is_active == is_active]
        
        return policies
    
    def update_policy(
        self,
        policy_id: str,
        name: Optional[str] = None,
        retention_days: Optional[int] = None,
        is_active: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Optional[RetentionPolicy]:
        """
        Update a retention policy.
        
        Args:
            policy_id: Policy ID
            name: New name
            retention_days: New retention days
            is_active: Active status
            description: New description
            
        Returns:
            Updated RetentionPolicy or None if not found
        """
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        
        if name is not None:
            policy.name = name
        
        if retention_days is not None:
            policy.retention_days = retention_days
        
        if is_active is not None:
            policy.is_active = is_active
        
        if description is not None:
            policy.description = description
        
        return policy
    
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a retention policy"""
        policy = self._policies.get(policy_id)
        if not policy:
            return False
        
        # Remove from type tracking
        if policy.policy_type in self._type_policies:
            self._type_policies[policy.policy_type] = [
                pid for pid in self._type_policies[policy.policy_type] if pid != policy_id
            ]
        
        del self._policies[policy_id]
        return True
    
    def execute_policy(
        self,
        policy_id: str,
        purge_function: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a retention policy.
        
        Args:
            policy_id: Policy ID
            purge_function: Optional function to call for purging (takes cutoff_date, returns count)
            
        Returns:
            Dict with execution result
        """
        policy = self._policies.get(policy_id)
        if not policy or not policy.is_active:
            return {
                'success': False,
                'error': 'Policy not found or not active'
            }
        
        cutoff_date = policy.get_cutoff_date()
        
        if purge_function:
            try:
                purged_count = purge_function(cutoff_date)
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            # Default: just return 0 (no actual purging)
            purged_count = 0
        
        # Update policy stats
        policy.last_run_at = datetime.utcnow().isoformat()
        policy.last_purged_count = purged_count
        policy.total_purged_count += purged_count
        
        return {
            'success': True,
            'policy_id': policy_id,
            'cutoff_date': cutoff_date.isoformat(),
            'purged_count': purged_count,
            'total_purged_count': policy.total_purged_count
        }
    
    def execute_all_policies(
        self,
        purge_functions: Optional[Dict[RetentionPolicyType, callable]] = None
    ) -> Dict[str, Any]:
        """
        Execute all active retention policies.
        
        Args:
            purge_functions: Optional dict mapping policy types to purge functions
            
        Returns:
            Dict with execution results
        """
        results = []
        total_purged = 0
        
        for policy in self._policies.values():
            if not policy.is_active:
                continue
            
            purge_func = None
            if purge_functions and policy.policy_type in purge_functions:
                purge_func = purge_functions[policy.policy_type]
            
            result = self.execute_policy(policy.policy_id, purge_func)
            results.append(result)
            
            if result.get('success'):
                total_purged += result.get('purged_count', 0)
        
        return {
            'success': True,
            'policies_executed': len(results),
            'total_purged': total_purged,
            'results': results
        }


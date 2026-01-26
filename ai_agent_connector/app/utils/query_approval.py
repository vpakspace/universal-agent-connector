"""
Query approval system for manual review of high-risk queries
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from ..utils.helpers import get_timestamp
from ..utils.query_validator import RiskLevel, ValidationResult


class ApprovalStatus(Enum):
    """Query approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class QueryApproval:
    """Query approval request"""
    approval_id: str
    agent_id: str
    query: str
    query_type: str
    risk_level: RiskLevel
    complexity_score: int
    validation_result: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: str = field(default_factory=get_timestamp)
    requested_by: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    rejected_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[str] = None
    execution_count: int = 0
    max_executions: int = 1  # How many times can this query be executed after approval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'approval_id': self.approval_id,
            'agent_id': self.agent_id,
            'query': self.query,
            'query_type': self.query_type,
            'risk_level': self.risk_level.value,
            'complexity_score': self.complexity_score,
            'validation_result': self.validation_result,
            'status': self.status.value,
            'requested_at': self.requested_at,
            'requested_by': self.requested_by,
            'approved_at': self.approved_at,
            'approved_by': self.approved_by,
            'rejected_at': self.rejected_at,
            'rejected_by': self.rejected_by,
            'rejection_reason': self.rejection_reason,
            'expires_at': self.expires_at,
            'execution_count': self.execution_count,
            'max_executions': self.max_executions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryApproval':
        """Create from dictionary"""
        return cls(
            approval_id=data['approval_id'],
            agent_id=data['agent_id'],
            query=data['query'],
            query_type=data['query_type'],
            risk_level=RiskLevel(data['risk_level']),
            complexity_score=data['complexity_score'],
            validation_result=data['validation_result'],
            status=ApprovalStatus(data.get('status', 'pending')),
            requested_at=data.get('requested_at', get_timestamp()),
            requested_by=data.get('requested_by'),
            approved_at=data.get('approved_at'),
            approved_by=data.get('approved_by'),
            rejected_at=data.get('rejected_at'),
            rejected_by=data.get('rejected_by'),
            rejection_reason=data.get('rejection_reason'),
            expires_at=data.get('expires_at'),
            execution_count=data.get('execution_count', 0),
            max_executions=data.get('max_executions', 1)
        )


class QueryApprovalManager:
    """
    Query approval manager.
    Handles approval workflow for high-risk queries.
    """
    
    def __init__(self, default_expiry_hours: int = 24):
        """
        Initialize query approval manager.
        
        Args:
            default_expiry_hours: Default expiry time in hours for approvals
        """
        # approval_id -> QueryApproval
        self._approvals: Dict[str, QueryApproval] = {}
        # agent_id -> list of approval_ids
        self._agent_approvals: Dict[str, List[str]] = {}
        self.default_expiry_hours = default_expiry_hours
    
    def request_approval(
        self,
        agent_id: str,
        query: str,
        query_type: str,
        validation_result: ValidationResult,
        requested_by: Optional[str] = None,
        expires_in_hours: Optional[int] = None
    ) -> QueryApproval:
        """
        Request approval for a query.
        
        Args:
            agent_id: Agent ID
            query: SQL query
            query_type: Query type
            validation_result: Validation result
            requested_by: User/agent requesting approval
            expires_in_hours: Expiry time in hours (None = use default)
            
        Returns:
            QueryApproval: Approval request
        """
        approval_id = f"approval_{int(datetime.now().timestamp() * 1000)}_{agent_id}"
        
        # Calculate expiry
        expires_at = None
        if expires_in_hours is None:
            expires_in_hours = self.default_expiry_hours
        
        if expires_in_hours > 0:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
        
        approval = QueryApproval(
            approval_id=approval_id,
            agent_id=agent_id,
            query=query,
            query_type=query_type,
            risk_level=validation_result.risk_level,
            complexity_score=validation_result.complexity_score,
            validation_result=validation_result.to_dict(),
            requested_by=requested_by or agent_id,
            expires_at=expires_at
        )
        
        self._approvals[approval_id] = approval
        
        if agent_id not in self._agent_approvals:
            self._agent_approvals[agent_id] = []
        self._agent_approvals[agent_id].append(approval_id)
        
        return approval
    
    def approve_query(
        self,
        approval_id: str,
        approved_by: str,
        max_executions: int = 1
    ) -> QueryApproval:
        """
        Approve a query.
        
        Args:
            approval_id: Approval ID
            approved_by: User/agent approving the query
            max_executions: Maximum number of times query can be executed
            
        Returns:
            QueryApproval: Updated approval
            
        Raises:
            ValueError: If approval not found or already processed
        """
        if approval_id not in self._approvals:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval = self._approvals[approval_id]
        
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status.value})")
        
        approval.status = ApprovalStatus.APPROVED
        approval.approved_at = get_timestamp()
        approval.approved_by = approved_by
        approval.max_executions = max_executions
        
        return approval
    
    def reject_query(
        self,
        approval_id: str,
        rejected_by: str,
        reason: Optional[str] = None
    ) -> QueryApproval:
        """
        Reject a query.
        
        Args:
            approval_id: Approval ID
            rejected_by: User/agent rejecting the query
            reason: Optional rejection reason
            
        Returns:
            QueryApproval: Updated approval
            
        Raises:
            ValueError: If approval not found or already processed
        """
        if approval_id not in self._approvals:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval = self._approvals[approval_id]
        
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status.value})")
        
        approval.status = ApprovalStatus.REJECTED
        approval.rejected_at = get_timestamp()
        approval.rejected_by = rejected_by
        approval.rejection_reason = reason
        
        return approval
    
    def get_approval(self, approval_id: str) -> Optional[QueryApproval]:
        """
        Get an approval by ID.
        
        Args:
            approval_id: Approval ID
            
        Returns:
            QueryApproval or None if not found
        """
        return self._approvals.get(approval_id)
    
    def check_approval(
        self,
        agent_id: str,
        query: str
    ) -> Optional[QueryApproval]:
        """
        Check if a query has been approved.
        
        Args:
            agent_id: Agent ID
            query: SQL query
            
        Returns:
            QueryApproval if approved and valid, None otherwise
        """
        if agent_id not in self._agent_approvals:
            return None
        
        # Check for matching approved queries
        for approval_id in self._agent_approvals[agent_id]:
            approval = self._approvals.get(approval_id)
            if not approval:
                continue
            
            # Check if query matches (normalized comparison)
            if self._queries_match(approval.query, query):
                # Check status
                if approval.status == ApprovalStatus.APPROVED:
                    # Check expiry
                    if approval.expires_at:
                        from datetime import datetime
                        try:
                            expires = datetime.fromisoformat(approval.expires_at)
                            if datetime.now() > expires:
                                approval.status = ApprovalStatus.EXPIRED
                                return None
                        except:
                            pass
                    
                    # Check execution count
                    if approval.execution_count >= approval.max_executions:
                        return None
                    
                    return approval
                elif approval.status == ApprovalStatus.PENDING:
                    return approval
        
        return None
    
    def record_execution(self, approval_id: str) -> None:
        """
        Record that an approved query was executed.
        
        Args:
            approval_id: Approval ID
        """
        if approval_id in self._approvals:
            self._approvals[approval_id].execution_count += 1
    
    def list_pending_approvals(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[QueryApproval]:
        """
        List pending approval requests.
        
        Args:
            agent_id: Optional agent ID to filter by
            limit: Maximum number of approvals to return
            
        Returns:
            List of pending QueryApproval objects
        """
        pending = []
        
        for approval in self._approvals.values():
            if approval.status == ApprovalStatus.PENDING:
                if agent_id is None or approval.agent_id == agent_id:
                    pending.append(approval)
        
        # Sort by requested_at (newest first)
        pending.sort(key=lambda x: x.requested_at, reverse=True)
        
        return pending[:limit]
    
    def list_approvals(
        self,
        agent_id: Optional[str] = None,
        status: Optional[ApprovalStatus] = None,
        limit: int = 100
    ) -> List[QueryApproval]:
        """
        List approvals with optional filtering.
        
        Args:
            agent_id: Optional agent ID to filter by
            status: Optional status to filter by
            limit: Maximum number of approvals to return
            
        Returns:
            List of QueryApproval objects
        """
        approvals = []
        
        for approval in self._approvals.values():
            if agent_id and approval.agent_id != agent_id:
                continue
            if status and approval.status != status:
                continue
            
            approvals.append(approval)
        
        # Sort by requested_at (newest first)
        approvals.sort(key=lambda x: x.requested_at, reverse=True)
        
        return approvals[:limit]
    
    def _queries_match(self, query1: str, query2: str) -> bool:
        """
        Check if two queries match (normalized comparison).
        
        Args:
            query1: First query
            query2: Second query
            
        Returns:
            bool: True if queries match
        """
        # Normalize queries (remove extra whitespace, case-insensitive)
        import re
        norm1 = re.sub(r'\s+', ' ', query1.strip().upper())
        norm2 = re.sub(r'\s+', ' ', query2.strip().upper())
        
        return norm1 == norm2
    
    def remove_agent_approvals(self, agent_id: str) -> None:
        """Remove all approvals for an agent"""
        if agent_id in self._agent_approvals:
            for approval_id in self._agent_approvals[agent_id]:
                self._approvals.pop(approval_id, None)
            del self._agent_approvals[agent_id]


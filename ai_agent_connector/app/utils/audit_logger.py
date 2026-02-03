"""
Audit logging system for tracking queries and agent actions
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from ..utils.helpers import get_timestamp


class ActionType(Enum):
    """Types of actions that can be logged"""
    QUERY_EXECUTION = "query_execution"
    NATURAL_LANGUAGE_QUERY = "natural_language_query"
    AGENT_REGISTERED = "agent_registered"
    AGENT_REVOKED = "agent_revoked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_SET = "permission_set"
    PERMISSION_LISTED = "permission_listed"
    TABLES_LISTED = "tables_listed"
    AGENT_VIEWED = "agent_viewed"
    AGENTS_LISTED = "agents_listed"
    # JWT Authentication
    JWT_TOKEN_GENERATED = "jwt_token_generated"
    JWT_TOKEN_REVOKED = "jwt_token_revoked"


class AuditLogger:
    """Manages audit logs for system activity"""
    
    def __init__(self, max_logs: int = 10000):
        """
        Initialize audit logger
        
        Args:
            max_logs: Maximum number of logs to keep in memory (default: 10000)
        """
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = max_logs
    
    def log(
        self,
        action_type: ActionType,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log an action
        
        Args:
            action_type: Type of action being logged
            agent_id: Agent ID involved in the action
            user_id: User ID who performed the action (if different from agent)
            details: Additional details about the action
            status: Status of the action (success, error, denied)
            error_message: Error message if status is error
            
        Returns:
            Dict containing the log entry
        """
        log_entry = {
            'id': len(self.logs) + 1,
            'timestamp': get_timestamp(),
            'action_type': action_type.value,
            'agent_id': agent_id,
            'user_id': user_id,
            'status': status,
            'details': details or {},
            'error_message': error_message
        }
        
        self.logs.append(log_entry)
        
        # Maintain max_logs limit (FIFO)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
        
        return log_entry
    
    def get_logs(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieve audit logs with filtering
        
        Args:
            agent_id: Filter by agent ID
            action_type: Filter by action type
            status: Filter by status
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dict containing filtered logs and metadata
        """
        filtered_logs = self.logs.copy()
        
        # Apply filters
        if agent_id:
            filtered_logs = [log for log in filtered_logs if log.get('agent_id') == agent_id]
        
        if action_type:
            filtered_logs = [log for log in filtered_logs if log.get('action_type') == action_type.value]
        
        if status:
            filtered_logs = [log for log in filtered_logs if log.get('status') == status]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply pagination
        total = len(filtered_logs)
        paginated_logs = filtered_logs[offset:offset + limit]
        
        return {
            'logs': paginated_logs,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total
        }
    
    def get_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific log entry by ID
        
        Args:
            log_id: Log entry ID
            
        Returns:
            Log entry or None if not found
        """
        for log in self.logs:
            if log.get('id') == log_id:
                return log
        return None
    
    def clear_logs(self) -> None:
        """Clear all logs (useful for testing)"""
        self.logs.clear()
    
    def get_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about logged actions
        
        Args:
            agent_id: Filter statistics by agent ID
            
        Returns:
            Dict containing statistics
        """
        logs = self.logs
        if agent_id:
            logs = [log for log in logs if log.get('agent_id') == agent_id]
        
        stats = {
            'total_actions': len(logs),
            'by_action_type': {},
            'by_status': {},
            'recent_actions': []
        }
        
        # Count by action type
        for log in logs:
            action_type = log.get('action_type', 'unknown')
            stats['by_action_type'][action_type] = stats['by_action_type'].get(action_type, 0) + 1
        
        # Count by status
        for log in logs:
            status = log.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Get recent actions (last 10)
        stats['recent_actions'] = sorted(
            logs,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]
        
        return stats


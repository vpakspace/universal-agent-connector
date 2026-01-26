"""
Security monitoring and notification system
Detects security issues and anomalous access patterns
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
from ..utils.helpers import get_timestamp


class SecuritySeverity(Enum):
    """Security alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events"""
    FAILED_AUTHENTICATION = "failed_authentication"
    PERMISSION_DENIED = "permission_denied"
    MULTIPLE_FAILURES = "multiple_failures"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    AGENT_REVOKED = "agent_revoked"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATABASE_CONNECTION_FAILURE = "database_connection_failure"


class SecurityMonitor:
    """Monitors security events and generates alerts"""
    
    def __init__(self, max_notifications: int = 1000):
        """
        Initialize security monitor
        
        Args:
            max_notifications: Maximum number of notifications to keep
        """
        self.notifications: List[Dict[str, Any]] = []
        self.max_notifications = max_notifications
        self.failed_auth_attempts: Dict[str, List[str]] = defaultdict(list)  # agent_id -> timestamps
        self.permission_denials: Dict[str, List[str]] = defaultdict(list)  # agent_id -> timestamps
        self.query_counts: Dict[str, List[str]] = defaultdict(list)  # agent_id -> timestamps
        self._cleanup_interval = timedelta(minutes=60)  # Clean up old tracking data every hour
    
    def check_security_event(
        self,
        action_type: str,
        agent_id: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an audit log event should trigger a security notification
        
        Args:
            action_type: Type of action from audit log
            agent_id: Agent ID involved
            status: Status of the action
            details: Additional details
            
        Returns:
            Dict containing notification if security event detected, None otherwise
        """
        timestamp = get_timestamp()
        notification = None
        
        # Failed authentication
        if action_type == "authentication" and status == "error":
            notification = self._create_notification(
                SecurityEventType.FAILED_AUTHENTICATION,
                SecuritySeverity.MEDIUM,
                agent_id=agent_id,
                message="Failed authentication attempt",
                details=details
            )
            if agent_id:
                self.failed_auth_attempts[agent_id].append(timestamp)
            elif details and details.get('ip'):
                # Track by IP if agent_id not available
                ip = details.get('ip')
                self.failed_auth_attempts[ip].append(timestamp)
        
        # Permission denied
        elif status == "denied":
            notification = self._create_notification(
                SecurityEventType.PERMISSION_DENIED,
                SecuritySeverity.MEDIUM,
                agent_id=agent_id,
                message="Permission denied",
                details=details
            )
            if agent_id:
                self.permission_denials[agent_id].append(timestamp)
        
        # Agent revoked
        elif action_type == "agent_revoked" and status == "success":
            notification = self._create_notification(
                SecurityEventType.AGENT_REVOKED,
                SecuritySeverity.HIGH,
                agent_id=agent_id,
                message=f"Agent {agent_id} was revoked",
                details=details
            )
        
        # Database connection failure
        elif "database" in action_type.lower() and status == "error":
            notification = self._create_notification(
                SecurityEventType.DATABASE_CONNECTION_FAILURE,
                SecuritySeverity.MEDIUM,
                agent_id=agent_id,
                message="Database connection failure",
                details=details
            )
        
        # Check for multiple failures (anomaly detection)
        if agent_id:
            notification = self._check_anomalies(agent_id, notification)
        
        if notification:
            self.notifications.append(notification)
            
            # Maintain max notifications limit
            if len(self.notifications) > self.max_notifications:
                self.notifications.pop(0)
        
        return notification
    
    def _check_anomalies(
        self,
        agent_id: str,
        existing_notification: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check for anomalous patterns that might indicate security issues
        
        Args:
            agent_id: Agent ID to check
            existing_notification: Existing notification if any
            
        Returns:
            Notification if anomaly detected, otherwise existing notification
        """
        now = datetime.now()
        time_window = timedelta(minutes=5)
        
        # Check for multiple failed authentications
        recent_failures = [
            ts for ts in self.failed_auth_attempts[agent_id]
            if self._is_recent(ts, time_window)
        ]
        
        if len(recent_failures) >= 3:
            return self._create_notification(
                SecurityEventType.MULTIPLE_FAILURES,
                SecuritySeverity.HIGH,
                agent_id=agent_id,
                message=f"Multiple failed authentication attempts ({len(recent_failures)}) in short time",
                details={'failure_count': len(recent_failures), 'time_window_minutes': 5}
            )
        
        # Check for multiple permission denials
        recent_denials = [
            ts for ts in self.permission_denials[agent_id]
            if self._is_recent(ts, time_window)
        ]
        
        if len(recent_denials) >= 5:
            return self._create_notification(
                SecurityEventType.UNUSUAL_ACCESS_PATTERN,
                SecuritySeverity.MEDIUM,
                agent_id=agent_id,
                message=f"Multiple permission denials ({len(recent_denials)}) in short time",
                details={'denial_count': len(recent_denials), 'time_window_minutes': 5}
            )
        
        # Check for unusual query rate
        recent_queries = [
            ts for ts in self.query_counts[agent_id]
            if self._is_recent(ts, time_window)
        ]
        
        if len(recent_queries) >= 50:  # 50 queries in 5 minutes
            return self._create_notification(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                SecuritySeverity.MEDIUM,
                agent_id=agent_id,
                message=f"Unusually high query rate ({len(recent_queries)} queries in 5 minutes)",
                details={'query_count': len(recent_queries), 'time_window_minutes': 5}
            )
        
        return existing_notification
    
    def _create_notification(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        agent_id: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a security notification
        
        Args:
            event_type: Type of security event
            severity: Severity level
            agent_id: Agent ID involved
            message: Human-readable message
            details: Additional details
            
        Returns:
            Dict containing notification
        """
        return {
            'id': len(self.notifications) + 1,
            'timestamp': get_timestamp(),
            'event_type': event_type.value,
            'severity': severity.value,
            'agent_id': agent_id,
            'message': message,
            'details': details or {},
            'read': False
        }
    
    def _is_recent(self, timestamp_str: str, window: timedelta) -> bool:
        """Check if timestamp is within the time window"""
        try:
            # Parse ISO timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if timestamp.tzinfo:
                timestamp = timestamp.replace(tzinfo=None)
            return (datetime.now() - timestamp) < window
        except Exception:
            return False
    
    def get_notifications(
        self,
        severity: Optional[SecuritySeverity] = None,
        agent_id: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get security notifications with filtering
        
        Args:
            severity: Filter by severity level
            agent_id: Filter by agent ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            
        Returns:
            Dict containing filtered notifications
        """
        filtered = self.notifications.copy()
        
        if severity:
            filtered = [n for n in filtered if n.get('severity') == severity.value]
        
        if agent_id:
            filtered = [n for n in filtered if n.get('agent_id') == agent_id]
        
        if unread_only:
            filtered = [n for n in filtered if not n.get('read', False)]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        filtered = filtered[:limit]
        
        unread_count = sum(1 for n in self.notifications if not n.get('read', False))
        
        return {
            'notifications': filtered,
            'total': len(self.notifications),
            'unread_count': unread_count,
            'count': len(filtered)
        }
    
    def mark_as_read(self, notification_id: int) -> bool:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            
        Returns:
            True if notification was found and marked, False otherwise
        """
        for notification in self.notifications:
            if notification.get('id') == notification_id:
                notification['read'] = True
                return True
        return False
    
    def mark_all_as_read(self) -> int:
        """
        Mark all notifications as read
        
        Returns:
            Number of notifications marked as read
        """
        count = 0
        for notification in self.notifications:
            if not notification.get('read', False):
                notification['read'] = True
                count += 1
        return count
    
    def record_query(self, agent_id: str) -> None:
        """Record a query execution for rate monitoring"""
        if agent_id:
            self.query_counts[agent_id].append(get_timestamp())
    
    def clear_notifications(self) -> None:
        """Clear all notifications (useful for testing)"""
        self.notifications.clear()
        self.failed_auth_attempts.clear()
        self.permission_denials.clear()
        self.query_counts.clear()


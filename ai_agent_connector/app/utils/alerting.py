"""
Alerting system for query performance monitoring
Sends alerts when query execution times exceed thresholds
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from ..utils.helpers import get_timestamp
import threading


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """An alert rule configuration"""
    rule_id: str
    name: str
    description: str
    agent_id: Optional[str] = None  # None for all agents
    threshold_ms: float = 1000.0  # Execution time threshold in milliseconds
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    cooldown_seconds: int = 60  # Minimum time between alerts
    created_at: str = field(default_factory=get_timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'agent_id': self.agent_id,
            'threshold_ms': self.threshold_ms,
            'severity': self.severity.value,
            'enabled': self.enabled,
            'cooldown_seconds': self.cooldown_seconds,
            'created_at': self.created_at
        }


@dataclass
class Alert:
    """An alert instance"""
    alert_id: str
    rule_id: str
    agent_id: str
    severity: AlertSeverity
    message: str
    execution_time_ms: float
    threshold_ms: float
    timestamp: str = field(default_factory=get_timestamp)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'rule_id': self.rule_id,
            'agent_id': self.agent_id,
            'severity': self.severity.value,
            'message': self.message,
            'execution_time_ms': self.execution_time_ms,
            'threshold_ms': self.threshold_ms,
            'timestamp': self.timestamp,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at
        }


class AlertManager:
    """
    Manages alert rules and triggers alerts when thresholds are exceeded.
    Supports custom alert handlers for integration with external systems.
    """
    
    def __init__(self):
        """Initialize alert manager"""
        # rule_id -> AlertRule
        self._rules: Dict[str, AlertRule] = {}
        # alert_id -> Alert
        self._alerts: Dict[str, Alert] = {}
        # rule_id -> last_alert_time
        self._last_alert_times: Dict[str, datetime] = {}
        # Custom alert handlers
        self._handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
    
    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Register a custom alert handler.
        
        Args:
            handler: Function that takes an Alert and handles it
        """
        with self._lock:
            self._handlers.append(handler)
    
    def create_rule(
        self,
        name: str,
        description: str,
        threshold_ms: float,
        agent_id: Optional[str] = None,
        severity: AlertSeverity = AlertSeverity.WARNING,
        cooldown_seconds: int = 60
    ) -> AlertRule:
        """
        Create an alert rule.
        
        Args:
            name: Rule name
            description: Rule description
            threshold_ms: Execution time threshold in milliseconds
            agent_id: Agent ID (None for all agents)
            severity: Alert severity
            cooldown_seconds: Cooldown period between alerts
            
        Returns:
            AlertRule: Created rule
        """
        import uuid
        
        rule = AlertRule(
            rule_id=str(uuid.uuid4()),
            name=name,
            description=description,
            agent_id=agent_id,
            threshold_ms=threshold_ms,
            severity=severity,
            cooldown_seconds=cooldown_seconds
        )
        
        with self._lock:
            self._rules[rule.rule_id] = rule
        
        return rule
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a rule by ID"""
        return self._rules.get(rule_id)
    
    def list_rules(self, agent_id: Optional[str] = None) -> List[AlertRule]:
        """
        List alert rules.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of AlertRule objects
        """
        rules = list(self._rules.values())
        
        if agent_id:
            rules = [r for r in rules if r.agent_id is None or r.agent_id == agent_id]
        
        return [r for r in rules if r.enabled]
    
    def update_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any]
    ) -> Optional[AlertRule]:
        """Update an alert rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        
        if 'name' in updates:
            rule.name = updates['name']
        if 'description' in updates:
            rule.description = updates['description']
        if 'threshold_ms' in updates:
            rule.threshold_ms = updates['threshold_ms']
        if 'severity' in updates:
            rule.severity = AlertSeverity(updates['severity'])
        if 'enabled' in updates:
            rule.enabled = updates['enabled']
        if 'cooldown_seconds' in updates:
            rule.cooldown_seconds = updates['cooldown_seconds']
        
        return rule
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
            return False
    
    def check_and_trigger(
        self,
        agent_id: str,
        execution_time_ms: float
    ) -> List[Alert]:
        """
        Check if execution time triggers any alerts and create alerts.
        
        Args:
            agent_id: Agent ID
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            List of triggered Alert objects
        """
        triggered_alerts = []
        now = datetime.now()
        
        with self._lock:
            # Find applicable rules
            applicable_rules = [
                r for r in self._rules.values()
                if r.enabled and (
                    r.agent_id is None or r.agent_id == agent_id
                ) and execution_time_ms >= r.threshold_ms
            ]
            
            for rule in applicable_rules:
                # Check cooldown
                last_alert_time = self._last_alert_times.get(rule.rule_id)
                if last_alert_time:
                    time_since_last = (now - last_alert_time).total_seconds()
                    if time_since_last < rule.cooldown_seconds:
                        continue
                
                # Create alert
                import uuid
                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    agent_id=agent_id,
                    severity=rule.severity,
                    message=f"Query execution time ({execution_time_ms:.2f}ms) exceeded threshold ({rule.threshold_ms}ms) for {rule.name}",
                    execution_time_ms=execution_time_ms,
                    threshold_ms=rule.threshold_ms
                )
                
                self._alerts[alert.alert_id] = alert
                self._last_alert_times[rule.rule_id] = now
                triggered_alerts.append(alert)
                
                # Call handlers
                for handler in self._handlers:
                    try:
                        handler(alert)
                    except Exception:
                        pass  # Don't fail if handler errors
        
        return triggered_alerts
    
    def get_alerts(
        self,
        agent_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alerts with filtering.
        
        Args:
            agent_id: Filter by agent ID
            severity: Filter by severity
            acknowledged: Filter by acknowledged status
            limit: Maximum number of alerts to return
            
        Returns:
            List of Alert objects
        """
        alerts = list(self._alerts.values())
        
        if agent_id:
            alerts = [a for a in alerts if a.agent_id == agent_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return alerts[:limit]
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> Optional[Alert]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User/agent who acknowledged
            
        Returns:
            Updated Alert or None if not found
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = get_timestamp()
        
        return alert


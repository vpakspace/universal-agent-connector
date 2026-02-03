"""
Alerting system for query performance monitoring and critical events.

Supports:
- Slack (webhooks)
- PagerDuty (Events API v2)
- Custom webhooks
- Email (SMTP)
"""

import json
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..utils.helpers import get_timestamp


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    QUERY_SLOW = "query_slow"
    ONTOGUARD_DENIED = "ontoguard_denied"
    SCHEMA_DRIFT_CRITICAL = "schema_drift_critical"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    DATABASE_ERROR = "database_error"
    SYSTEM_ERROR = "system_error"
    CUSTOM = "custom"


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


# =============================================================================
# Alert Channels for External Integrations
# =============================================================================

class AlertChannel(ABC):
    """Base class for alert channels"""

    @abstractmethod
    def send(self, alert: 'NotificationAlert') -> bool:
        """Send alert. Returns True if successful."""
        pass

    @abstractmethod
    def test(self) -> bool:
        """Test channel connectivity."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name"""
        pass


@dataclass
class NotificationAlert:
    """Alert data for external notifications"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    source: str = "universal-agent-connector"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    dedup_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'timestamp': self.timestamp,
            'agent_id': self.agent_id,
            'user_id': self.user_id,
            'details': self.details,
            'dedup_key': self.dedup_key,
        }


class SlackChannel(AlertChannel):
    """Slack webhook integration"""

    def __init__(
        self,
        webhook_url: str,
        channel: Optional[str] = None,
        username: str = "UAC Alerts",
        icon_emoji: str = ":warning:"
    ):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji

    @property
    def name(self) -> str:
        return "slack"

    def _severity_to_color(self, severity: AlertSeverity) -> str:
        """Map severity to Slack attachment color"""
        colors = {
            AlertSeverity.INFO: "#36a64f",      # green
            AlertSeverity.WARNING: "#ffcc00",   # yellow
            AlertSeverity.ERROR: "#ff6600",     # orange
            AlertSeverity.CRITICAL: "#ff0000",  # red
        }
        return colors.get(severity, "#808080")

    def _severity_to_emoji(self, severity: AlertSeverity) -> str:
        """Map severity to emoji"""
        emojis = {
            AlertSeverity.INFO: ":information_source:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.ERROR: ":x:",
            AlertSeverity.CRITICAL: ":rotating_light:",
        }
        return emojis.get(severity, ":bell:")

    def send(self, alert: NotificationAlert) -> bool:
        """Send alert to Slack"""
        try:
            emoji = self._severity_to_emoji(alert.severity)

            # Build attachment
            attachment = {
                "color": self._severity_to_color(alert.severity),
                "title": f"{emoji} {alert.title}",
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                    {"title": "Type", "value": alert.alert_type.value, "short": True},
                    {"title": "Source", "value": alert.source, "short": True},
                    {"title": "Timestamp", "value": alert.timestamp, "short": True},
                ],
                "footer": "Universal Agent Connector",
                "ts": int(time.time())
            }

            if alert.agent_id:
                attachment["fields"].append({
                    "title": "Agent ID",
                    "value": alert.agent_id,
                    "short": True
                })

            if alert.details:
                details_text = "\n".join(f"• {k}: {v}" for k, v in alert.details.items())
                attachment["fields"].append({
                    "title": "Details",
                    "value": details_text,
                    "short": False
                })

            payload = {
                "username": self.username,
                "icon_emoji": self.icon_emoji,
                "attachments": [attachment]
            }

            if self.channel:
                payload["channel"] = self.channel

            data = json.dumps(payload).encode('utf-8')
            req = Request(self.webhook_url, data=data, headers={
                'Content-Type': 'application/json'
            })

            with urlopen(req, timeout=10) as response:
                return response.status == 200

        except (URLError, HTTPError) as e:
            print(f"Slack alert failed: {e}")
            return False

    def test(self) -> bool:
        """Test Slack webhook"""
        test_alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.INFO,
            title="Test Alert",
            message="This is a test alert from Universal Agent Connector",
            details={"test": True}
        )
        return self.send(test_alert)


class PagerDutyChannel(AlertChannel):
    """PagerDuty Events API v2 integration"""

    EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"

    def __init__(
        self,
        routing_key: str,
        service_name: str = "Universal Agent Connector"
    ):
        self.routing_key = routing_key
        self.service_name = service_name

    @property
    def name(self) -> str:
        return "pagerduty"

    def _severity_to_pd(self, severity: AlertSeverity) -> str:
        """Map severity to PagerDuty severity"""
        mapping = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "critical",
        }
        return mapping.get(severity, "info")

    def send(self, alert: NotificationAlert) -> bool:
        """Send alert to PagerDuty"""
        try:
            payload = {
                "routing_key": self.routing_key,
                "event_action": "trigger",
                "dedup_key": alert.dedup_key or f"{alert.alert_type.value}_{alert.timestamp}",
                "payload": {
                    "summary": f"[{alert.severity.value.upper()}] {alert.title}",
                    "source": alert.source,
                    "severity": self._severity_to_pd(alert.severity),
                    "timestamp": alert.timestamp,
                    "component": self.service_name,
                    "group": alert.alert_type.value,
                    "class": alert.alert_type.value,
                    "custom_details": {
                        "message": alert.message,
                        "agent_id": alert.agent_id,
                        "user_id": alert.user_id,
                        **alert.details
                    }
                }
            }

            data = json.dumps(payload).encode('utf-8')
            req = Request(self.EVENTS_API_URL, data=data, headers={
                'Content-Type': 'application/json'
            })

            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('status') == 'success'

        except (URLError, HTTPError) as e:
            print(f"PagerDuty alert failed: {e}")
            return False

    def test(self) -> bool:
        """Test PagerDuty integration"""
        test_alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.INFO,
            title="Test Alert",
            message="This is a test alert from Universal Agent Connector",
            details={"test": True}
        )
        return self.send(test_alert)

    def resolve(self, dedup_key: str) -> bool:
        """Resolve a PagerDuty incident"""
        try:
            payload = {
                "routing_key": self.routing_key,
                "event_action": "resolve",
                "dedup_key": dedup_key
            }

            data = json.dumps(payload).encode('utf-8')
            req = Request(self.EVENTS_API_URL, data=data, headers={
                'Content-Type': 'application/json'
            })

            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('status') == 'success'

        except (URLError, HTTPError):
            return False


class WebhookChannel(AlertChannel):
    """Generic webhook integration"""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
        name_override: str = "webhook"
    ):
        self.url = url
        self.headers = headers or {}
        self.method = method
        self._name = name_override

    @property
    def name(self) -> str:
        return self._name

    def send(self, alert: NotificationAlert) -> bool:
        """Send alert to webhook"""
        try:
            data = json.dumps(alert.to_dict()).encode('utf-8')
            headers = {'Content-Type': 'application/json', **self.headers}

            req = Request(self.url, data=data, headers=headers, method=self.method)

            with urlopen(req, timeout=10) as response:
                return 200 <= response.status < 300

        except (URLError, HTTPError) as e:
            print(f"Webhook alert failed: {e}")
            return False

    def test(self) -> bool:
        """Test webhook"""
        test_alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.INFO,
            title="Test Alert",
            message="Test webhook connectivity"
        )
        return self.send(test_alert)


class NotificationManager:
    """
    Manages alert channels and dispatches notifications.

    Features:
    - Multiple channels support
    - Severity-based routing
    - Rate limiting (deduplication)
    - Async dispatch
    """

    def __init__(
        self,
        min_severity: AlertSeverity = AlertSeverity.WARNING,
        dedup_window_seconds: int = 300,
        async_dispatch: bool = True
    ):
        self.channels: Dict[str, AlertChannel] = {}
        self.min_severity = min_severity
        self.dedup_window = dedup_window_seconds
        self.async_dispatch = async_dispatch
        self._recent_alerts: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000

    def add_channel(self, channel: AlertChannel) -> None:
        """Add an alert channel"""
        self.channels[channel.name] = channel

    def remove_channel(self, name: str) -> bool:
        """Remove an alert channel"""
        if name in self.channels:
            del self.channels[name]
            return True
        return False

    def get_channels(self) -> List[str]:
        """Get list of configured channels"""
        return list(self.channels.keys())

    def _get_severity_level(self, severity: AlertSeverity) -> int:
        """Get numeric severity level"""
        levels = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3,
        }
        return levels.get(severity, 0)

    def _should_send(self, alert: NotificationAlert) -> bool:
        """Check if alert should be sent (severity + dedup)"""
        # Check severity
        if self._get_severity_level(alert.severity) < self._get_severity_level(self.min_severity):
            return False

        # Check deduplication
        dedup_key = alert.dedup_key or f"{alert.alert_type.value}_{alert.agent_id}"
        now = time.time()

        with self._lock:
            last_sent = self._recent_alerts.get(dedup_key)
            if last_sent and (now - last_sent) < self.dedup_window:
                return False

            self._recent_alerts[dedup_key] = now

            # Cleanup old entries
            cutoff = now - self.dedup_window
            self._recent_alerts = {
                k: v for k, v in self._recent_alerts.items()
                if v > cutoff
            }

        return True

    def _dispatch(self, alert: NotificationAlert) -> Dict[str, bool]:
        """Dispatch alert to all channels"""
        results = {}

        for name, channel in self.channels.items():
            try:
                results[name] = channel.send(alert)
            except Exception as e:
                print(f"Channel {name} failed: {e}")
                results[name] = False

        # Record in history
        with self._lock:
            self._history.append({
                'alert': alert.to_dict(),
                'results': results,
                'dispatched_at': datetime.now().isoformat()
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)

        return results

    def send(self, alert: NotificationAlert) -> Dict[str, bool]:
        """Send alert to all configured channels."""
        if not self._should_send(alert):
            return {}

        if not self.channels:
            return {}

        if self.async_dispatch:
            thread = threading.Thread(target=self._dispatch, args=(alert,))
            thread.daemon = True
            thread.start()
            return {name: True for name in self.channels}  # Optimistic
        else:
            return self._dispatch(alert)

    def send_critical(
        self,
        title: str,
        message: str,
        alert_type: AlertType = AlertType.SYSTEM_ERROR,
        agent_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """Convenience method for critical alerts"""
        alert = NotificationAlert(
            alert_type=alert_type,
            severity=AlertSeverity.CRITICAL,
            title=title,
            message=message,
            agent_id=agent_id,
            details=details or {}
        )
        return self.send(alert)

    def send_warning(
        self,
        title: str,
        message: str,
        alert_type: AlertType = AlertType.CUSTOM,
        agent_id: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """Convenience method for warning alerts"""
        alert = NotificationAlert(
            alert_type=alert_type,
            severity=AlertSeverity.WARNING,
            title=title,
            message=message,
            agent_id=agent_id,
            details=details or {}
        )
        return self.send(alert)

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        with self._lock:
            return self._history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self._lock:
            history = self._history.copy()

        by_severity = {}
        by_type = {}
        by_channel = {}

        for entry in history:
            alert = entry['alert']
            severity = alert.get('severity', 'unknown')
            alert_type = alert.get('alert_type', 'unknown')

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[alert_type] = by_type.get(alert_type, 0) + 1

            for channel, success in entry.get('results', {}).items():
                if channel not in by_channel:
                    by_channel[channel] = {'sent': 0, 'failed': 0}
                if success:
                    by_channel[channel]['sent'] += 1
                else:
                    by_channel[channel]['failed'] += 1

        return {
            'total_alerts': len(history),
            'by_severity': by_severity,
            'by_type': by_type,
            'by_channel': by_channel,
            'channels_configured': list(self.channels.keys()),
            'min_severity': self.min_severity.value,
            'dedup_window_seconds': self.dedup_window
        }

    def test_channels(self) -> Dict[str, bool]:
        """Test all configured channels"""
        results = {}
        for name, channel in self.channels.items():
            try:
                results[name] = channel.test()
            except Exception:
                results[name] = False
        return results

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            'channels': list(self.channels.keys()),
            'min_severity': self.min_severity.value,
            'dedup_window_seconds': self.dedup_window,
            'async_dispatch': self.async_dispatch
        }


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get or create global notification manager"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()

        # Auto-configure from environment
        slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        if slack_webhook:
            _notification_manager.add_channel(SlackChannel(
                webhook_url=slack_webhook,
                channel=os.environ.get('SLACK_CHANNEL')
            ))

        pagerduty_key = os.environ.get('PAGERDUTY_ROUTING_KEY')
        if pagerduty_key:
            _notification_manager.add_channel(PagerDutyChannel(
                routing_key=pagerduty_key
            ))

    return _notification_manager


def init_notification_manager(
    min_severity: AlertSeverity = AlertSeverity.WARNING,
    dedup_window_seconds: int = 300,
    async_dispatch: bool = True
) -> NotificationManager:
    """Initialize global notification manager with custom settings"""
    global _notification_manager
    _notification_manager = NotificationManager(
        min_severity=min_severity,
        dedup_window_seconds=dedup_window_seconds,
        async_dispatch=async_dispatch
    )
    return _notification_manager


# Convenience functions
def send_notification(alert: NotificationAlert) -> Dict[str, bool]:
    """Send notification via global manager"""
    return get_notification_manager().send(alert)


def send_critical_notification(
    title: str,
    message: str,
    alert_type: AlertType = AlertType.SYSTEM_ERROR,
    **kwargs
) -> Dict[str, bool]:
    """Send critical notification via global manager"""
    return get_notification_manager().send_critical(title, message, alert_type, **kwargs)


def send_warning_notification(
    title: str,
    message: str,
    alert_type: AlertType = AlertType.CUSTOM,
    **kwargs
) -> Dict[str, bool]:
    """Send warning notification via global manager"""
    return get_notification_manager().send_warning(title, message, alert_type, **kwargs)


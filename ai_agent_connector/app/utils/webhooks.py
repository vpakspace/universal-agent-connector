"""
Webhook notification system for agent query events
Supports success and failure notifications
"""

import json
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from threading import Thread
import requests
from urllib.parse import urlparse
from .helpers import get_timestamp


class WebhookEvent(Enum):
    """Webhook event types"""
    QUERY_SUCCESS = "query_success"
    QUERY_FAILURE = "query_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CONFIGURATION_CHANGED = "configuration_changed"
    AGENT_REGISTERED = "agent_registered"
    AGENT_REVOKED = "agent_revoked"


@dataclass
class WebhookConfig:
    """Configuration for a webhook"""
    url: str
    events: List[WebhookEvent]
    secret: Optional[str] = None  # For webhook signature verification
    timeout: int = 10
    retry_on_failure: bool = True
    max_retries: int = 3
    enabled: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'url': self.url,
            'events': [e.value for e in self.events],
            'secret': '***' if self.secret else None,
            'timeout': self.timeout,
            'retry_on_failure': self.retry_on_failure,
            'max_retries': self.max_retries,
            'enabled': self.enabled,
            'custom_headers': self.custom_headers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookConfig':
        """Create from dictionary"""
        events = [WebhookEvent(e) for e in data.get('events', [])]
        return cls(
            url=data['url'],
            events=events,
            secret=data.get('secret'),
            timeout=data.get('timeout', 10),
            retry_on_failure=data.get('retry_on_failure', True),
            max_retries=data.get('max_retries', 3),
            enabled=data.get('enabled', True),
            custom_headers=data.get('custom_headers', {})
        )
    
    def validate(self) -> bool:
        """Validate webhook configuration"""
        try:
            parsed = urlparse(self.url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
        except Exception:
            return False


@dataclass
class WebhookPayload:
    """Payload sent to webhook"""
    event: WebhookEvent
    agent_id: str
    timestamp: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event': self.event.value,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp,
            'data': self.data,
            'metadata': self.metadata
        }


class WebhookNotifier:
    """
    Webhook notification system.
    Sends asynchronous notifications for agent events.
    """
    
    def __init__(self):
        """Initialize webhook notifier"""
        # agent_id -> list of WebhookConfig
        self._webhooks: Dict[str, List[WebhookConfig]] = {}
        # Global webhooks (for all agents)
        self._global_webhooks: List[WebhookConfig] = []
        # Delivery history for debugging
        self._delivery_history: List[Dict[str, Any]] = []
    
    def register_webhook(
        self,
        agent_id: Optional[str],
        config: WebhookConfig
    ) -> str:
        """
        Register a webhook for an agent or globally.
        
        Args:
            agent_id: Agent identifier (None for global webhook)
            config: Webhook configuration
            
        Returns:
            str: Webhook ID
            
        Raises:
            ValueError: If webhook configuration is invalid
        """
        if not config.validate():
            raise ValueError(f"Invalid webhook URL: {config.url}")
        
        webhook_id = f"webhook_{int(time.time() * 1000)}"
        
        if agent_id:
            if agent_id not in self._webhooks:
                self._webhooks[agent_id] = []
            self._webhooks[agent_id].append(config)
        else:
            self._global_webhooks.append(config)
        
        return webhook_id
    
    def unregister_webhook(
        self,
        agent_id: Optional[str],
        webhook_url: str
    ) -> bool:
        """
        Unregister a webhook.
        
        Args:
            agent_id: Agent identifier (None for global)
            webhook_url: Webhook URL to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if agent_id:
            webhooks = self._webhooks.get(agent_id, [])
            for i, webhook in enumerate(webhooks):
                if webhook.url == webhook_url:
                    webhooks.pop(i)
                    return True
        else:
            for i, webhook in enumerate(self._global_webhooks):
                if webhook.url == webhook_url:
                    self._global_webhooks.pop(i)
                    return True
        
        return False
    
    def notify(
        self,
        event: WebhookEvent,
        agent_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send webhook notification for an event.
        This is asynchronous - notifications are sent in background threads.
        
        Args:
            event: Event type
            agent_id: Agent identifier
            data: Event data
            metadata: Optional metadata
        """
        payload = WebhookPayload(
            event=event,
            agent_id=agent_id,
            timestamp=get_timestamp(),
            data=data,
            metadata=metadata or {}
        )
        
        # Get webhooks for this agent and global webhooks
        webhooks = []
        if agent_id in self._webhooks:
            webhooks.extend(self._webhooks[agent_id])
        webhooks.extend(self._global_webhooks)
        
        # Send to each webhook that subscribes to this event
        for webhook in webhooks:
            if not webhook.enabled:
                continue
            
            if event not in webhook.events:
                continue
            
            # Send asynchronously
            thread = Thread(
                target=self._send_webhook,
                args=(webhook, payload),
                daemon=True
            )
            thread.start()
    
    def _send_webhook(
        self,
        webhook: WebhookConfig,
        payload: WebhookPayload
    ) -> None:
        """
        Send webhook notification (internal, runs in thread).
        
        Args:
            webhook: Webhook configuration
            payload: Payload to send
        """
        delivery_record = {
            'webhook_url': webhook.url,
            'event': payload.event.value,
            'agent_id': payload.agent_id,
            'timestamp': payload.timestamp,
            'status': 'pending',
            'attempts': 0
        }
        
        payload_dict = payload.to_dict()
        
        # Add signature if secret is configured
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Agent-Connector/1.0',
            **webhook.custom_headers
        }
        
        if webhook.secret:
            import hmac
            import hashlib
            payload_str = json.dumps(payload_dict, sort_keys=True)
            signature = hmac.new(
                webhook.secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f'sha256={signature}'
        
        # Retry logic
        last_error = None
        for attempt in range(webhook.max_retries + 1):
            try:
                response = requests.post(
                    webhook.url,
                    json=payload_dict,
                    headers=headers,
                    timeout=webhook.timeout
                )
                response.raise_for_status()
                
                delivery_record['status'] = 'success'
                delivery_record['response_code'] = response.status_code
                break
                
            except Exception as e:
                last_error = str(e)
                delivery_record['attempts'] = attempt + 1
                
                if attempt < webhook.max_retries and webhook.retry_on_failure:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    delivery_record['status'] = 'failed'
                    delivery_record['error'] = last_error
                    break
        
        delivery_record['completed_at'] = get_timestamp()
        self._delivery_history.append(delivery_record)
        
        # Keep only last 1000 delivery records
        if len(self._delivery_history) > 1000:
            self._delivery_history = self._delivery_history[-1000:]
    
    def get_webhooks(self, agent_id: Optional[str] = None) -> List[WebhookConfig]:
        """
        Get webhooks for an agent or all global webhooks.
        
        Args:
            agent_id: Agent identifier (None for global only)
            
        Returns:
            List of WebhookConfig
        """
        if agent_id:
            return self._webhooks.get(agent_id, [])
        return self._global_webhooks.copy()
    
    def get_delivery_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get webhook delivery history.
        
        Args:
            agent_id: Filter by agent ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of delivery records
        """
        history = self._delivery_history
        if agent_id:
            history = [h for h in history if h.get('agent_id') == agent_id]
        
        return history[-limit:] if limit else history
    
    def get_delivery_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get webhook delivery statistics.
        
        Args:
            agent_id: Filter by agent ID (optional)
            
        Returns:
            Dict containing statistics
        """
        history = self.get_delivery_history(agent_id, limit=None)
        
        total = len(history)
        successful = sum(1 for h in history if h.get('status') == 'success')
        failed = sum(1 for h in history if h.get('status') == 'failed')
        
        return {
            'total_deliveries': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }



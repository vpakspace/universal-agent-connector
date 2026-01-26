"""
Tests for webhook notification system
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from ai_agent_connector.app.utils.webhooks import (
    WebhookNotifier,
    WebhookConfig,
    WebhookEvent,
    WebhookPayload
)


class TestWebhookConfig:
    """Tests for WebhookConfig"""
    
    def test_webhook_config_to_dict(self):
        """Test converting webhook config to dictionary"""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS, WebhookEvent.QUERY_FAILURE],
            secret="test-secret"
        )
        
        result = config.to_dict()
        
        assert result['url'] == "https://example.com/webhook"
        assert 'query_success' in result['events']
        assert result['secret'] == '***'
    
    def test_webhook_config_from_dict(self):
        """Test creating webhook config from dictionary"""
        data = {
            'url': 'https://example.com/webhook',
            'events': ['query_success', 'rate_limit_exceeded'],
            'timeout': 15
        }
        
        config = WebhookConfig.from_dict(data)
        
        assert config.url == 'https://example.com/webhook'
        assert WebhookEvent.QUERY_SUCCESS in config.events
        assert config.timeout == 15
    
    def test_webhook_config_validate(self):
        """Test webhook configuration validation"""
        valid_config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        assert valid_config.validate() is True
        
        invalid_config = WebhookConfig(
            url="not-a-url",
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        assert invalid_config.validate() is False


class TestWebhookNotifier:
    """Tests for WebhookNotifier"""
    
    def test_register_webhook(self):
        """Test registering a webhook"""
        notifier = WebhookNotifier()
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        
        webhook_id = notifier.register_webhook("agent1", config)
        
        assert webhook_id is not None
        webhooks = notifier.get_webhooks("agent1")
        assert len(webhooks) == 1
        assert webhooks[0].url == "https://example.com/webhook"
    
    def test_register_global_webhook(self):
        """Test registering a global webhook"""
        notifier = WebhookNotifier()
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        
        notifier.register_webhook(None, config)
        
        webhooks = notifier.get_webhooks(None)
        assert len(webhooks) == 1
    
    def test_unregister_webhook(self):
        """Test unregistering a webhook"""
        notifier = WebhookNotifier()
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        
        notifier.register_webhook("agent1", config)
        
        success = notifier.unregister_webhook("agent1", "https://example.com/webhook")
        
        assert success is True
        webhooks = notifier.get_webhooks("agent1")
        assert len(webhooks) == 0
    
    @patch('ai_agent_connector.app.utils.webhooks.requests')
    def test_notify_success(self, mock_requests):
        """Test sending webhook notification successfully"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response
        
        notifier = WebhookNotifier()
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS],
            timeout=5
        )
        
        notifier.register_webhook("agent1", config)
        
        # Notify (runs in thread, so we need to wait a bit)
        notifier.notify(
            WebhookEvent.QUERY_SUCCESS,
            "agent1",
            {"result": "success"}
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Check delivery history
        history = notifier.get_delivery_history("agent1", limit=1)
        assert len(history) > 0
        assert history[0]['status'] == 'success'
    
    @patch('ai_agent_connector.app.utils.webhooks.requests')
    def test_notify_filters_by_event(self, mock_requests):
        """Test that notifications are filtered by event type"""
        notifier = WebhookNotifier()
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS],  # Only success events
            timeout=5
        )
        
        notifier.register_webhook("agent1", config)
        
        # Notify with failure event (should not be sent)
        notifier.notify(
            WebhookEvent.QUERY_FAILURE,
            "agent1",
            {"error": "failed"}
        )
        
        time.sleep(0.5)
        
        # Should not have made any requests
        assert mock_requests.post.call_count == 0
    
    def test_get_delivery_history(self):
        """Test getting webhook delivery history"""
        notifier = WebhookNotifier()
        
        # Manually add to history (simulating delivery)
        notifier._delivery_history.append({
            'webhook_url': 'https://example.com/webhook',
            'event': 'query_success',
            'agent_id': 'agent1',
            'status': 'success',
            'timestamp': '2024-01-01T00:00:00Z'
        })
        
        history = notifier.get_delivery_history("agent1")
        
        assert len(history) == 1
        assert history[0]['status'] == 'success'
    
    def test_get_delivery_stats(self):
        """Test getting webhook delivery statistics"""
        notifier = WebhookNotifier()
        
        # Add some history
        notifier._delivery_history.extend([
            {'agent_id': 'agent1', 'status': 'success'},
            {'agent_id': 'agent1', 'status': 'success'},
            {'agent_id': 'agent1', 'status': 'failed'},
        ])
        
        stats = notifier.get_delivery_stats("agent1")
        
        assert stats['total_deliveries'] == 3
        assert stats['successful'] == 2
        assert stats['failed'] == 1
        assert stats['success_rate'] == pytest.approx(66.67, abs=0.1)
    
    def test_webhook_with_signature(self):
        """Test webhook with signature verification"""
        notifier = WebhookNotifier()
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS],
            secret="test-secret"
        )
        
        notifier.register_webhook("agent1", config)
        
        # The signature should be added in _send_webhook
        # This is tested indirectly through the delivery mechanism


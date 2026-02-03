"""
Unit tests for the Alerting module.

Tests Slack, PagerDuty, and webhook channels plus NotificationManager.
"""

import json
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ai_agent_connector.app.utils.alerting import (
    AlertSeverity,
    AlertType,
    NotificationAlert,
    NotificationManager,
    PagerDutyChannel,
    SlackChannel,
    WebhookChannel,
    get_notification_manager,
    init_notification_manager,
)


class TestAlertSeverity:
    """Test AlertSeverity enum."""

    def test_severity_values(self):
        """Test severity values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestAlertType:
    """Test AlertType enum."""

    def test_alert_types(self):
        """Test alert type values."""
        assert AlertType.QUERY_SLOW.value == "query_slow"
        assert AlertType.ONTOGUARD_DENIED.value == "ontoguard_denied"
        assert AlertType.SCHEMA_DRIFT_CRITICAL.value == "schema_drift_critical"
        assert AlertType.RATE_LIMIT_EXCEEDED.value == "rate_limit_exceeded"
        assert AlertType.CUSTOM.value == "custom"


class TestNotificationAlert:
    """Test NotificationAlert dataclass."""

    def test_create_alert(self):
        """Test creating alert."""
        alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="This is a test"
        )

        assert alert.title == "Test Alert"
        assert alert.message == "This is a test"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.source == "universal-agent-connector"

    def test_alert_to_dict(self):
        """Test alert serialization."""
        alert = NotificationAlert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.CRITICAL,
            title="Critical Error",
            message="System failure",
            agent_id="agent-1",
            details={"error_code": 500}
        )

        d = alert.to_dict()

        assert d['alert_type'] == "system_error"
        assert d['severity'] == "critical"
        assert d['title'] == "Critical Error"
        assert d['agent_id'] == "agent-1"
        assert d['details']['error_code'] == 500


class TestSlackChannel:
    """Test SlackChannel."""

    def test_slack_channel_name(self):
        """Test channel name."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        assert channel.name == "slack"

    def test_severity_to_color(self):
        """Test severity to color mapping."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")

        assert channel._severity_to_color(AlertSeverity.INFO) == "#36a64f"
        assert channel._severity_to_color(AlertSeverity.WARNING) == "#ffcc00"
        assert channel._severity_to_color(AlertSeverity.CRITICAL) == "#ff0000"

    def test_severity_to_emoji(self):
        """Test severity to emoji mapping."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")

        assert ":information_source:" in channel._severity_to_emoji(AlertSeverity.INFO)
        assert ":warning:" in channel._severity_to_emoji(AlertSeverity.WARNING)
        assert ":rotating_light:" in channel._severity_to_emoji(AlertSeverity.CRITICAL)

    @patch('ai_agent_connector.app.utils.alerting.urlopen')
    def test_send_success(self, mock_urlopen):
        """Test successful send."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.WARNING,
            title="Test",
            message="Test message"
        )

        result = channel.send(alert)
        assert result is True
        mock_urlopen.assert_called_once()

    @patch('ai_agent_connector.app.utils.alerting.urlopen')
    def test_send_failure(self, mock_urlopen):
        """Test send failure."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection failed")

        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.WARNING,
            title="Test",
            message="Test message"
        )

        result = channel.send(alert)
        assert result is False


class TestPagerDutyChannel:
    """Test PagerDutyChannel."""

    def test_pagerduty_channel_name(self):
        """Test channel name."""
        channel = PagerDutyChannel(routing_key="test-key")
        assert channel.name == "pagerduty"

    def test_severity_mapping(self):
        """Test severity to PagerDuty mapping."""
        channel = PagerDutyChannel(routing_key="test-key")

        assert channel._severity_to_pd(AlertSeverity.INFO) == "info"
        assert channel._severity_to_pd(AlertSeverity.WARNING) == "warning"
        assert channel._severity_to_pd(AlertSeverity.CRITICAL) == "critical"

    @patch('ai_agent_connector.app.utils.alerting.urlopen')
    def test_send_success(self, mock_urlopen):
        """Test successful send."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "success", "dedup_key": "test"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        channel = PagerDutyChannel(routing_key="test-key")
        alert = NotificationAlert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.CRITICAL,
            title="Critical Error",
            message="System down"
        )

        result = channel.send(alert)
        assert result is True

    @patch('ai_agent_connector.app.utils.alerting.urlopen')
    def test_resolve_incident(self, mock_urlopen):
        """Test resolving incident."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "success"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        channel = PagerDutyChannel(routing_key="test-key")
        result = channel.resolve("dedup-key-123")

        assert result is True


class TestWebhookChannel:
    """Test WebhookChannel."""

    def test_webhook_channel_name(self):
        """Test channel name."""
        channel = WebhookChannel(url="https://example.com/webhook")
        assert channel.name == "webhook"

        channel2 = WebhookChannel(url="https://example.com/webhook", name_override="custom")
        assert channel2.name == "custom"

    @patch('ai_agent_connector.app.utils.alerting.urlopen')
    def test_send_success(self, mock_urlopen):
        """Test successful send."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        channel = WebhookChannel(url="https://example.com/webhook")
        alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.INFO,
            title="Test",
            message="Test"
        )

        result = channel.send(alert)
        assert result is True


class TestNotificationManager:
    """Test NotificationManager."""

    def test_add_remove_channel(self):
        """Test adding and removing channels."""
        manager = NotificationManager()

        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        manager.add_channel(channel)

        assert "slack" in manager.get_channels()

        manager.remove_channel("slack")
        assert "slack" not in manager.get_channels()

    def test_severity_level(self):
        """Test severity level comparison."""
        manager = NotificationManager()

        assert manager._get_severity_level(AlertSeverity.INFO) == 0
        assert manager._get_severity_level(AlertSeverity.WARNING) == 1
        assert manager._get_severity_level(AlertSeverity.ERROR) == 2
        assert manager._get_severity_level(AlertSeverity.CRITICAL) == 3

    def test_min_severity_filter(self):
        """Test minimum severity filtering."""
        manager = NotificationManager(min_severity=AlertSeverity.ERROR)

        # INFO alert should not pass
        alert_info = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.INFO,
            title="Info",
            message="Info message"
        )
        assert manager._should_send(alert_info) is False

        # CRITICAL alert should pass
        alert_critical = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.CRITICAL,
            title="Critical",
            message="Critical message"
        )
        assert manager._should_send(alert_critical) is True

    def test_deduplication(self):
        """Test alert deduplication."""
        manager = NotificationManager(
            min_severity=AlertSeverity.INFO,
            dedup_window_seconds=10
        )

        alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.WARNING,
            title="Test",
            message="Test",
            dedup_key="test-dedup"
        )

        # First should pass
        assert manager._should_send(alert) is True

        # Second with same dedup key should be blocked
        assert manager._should_send(alert) is False

    def test_get_config(self):
        """Test get configuration."""
        manager = NotificationManager(
            min_severity=AlertSeverity.ERROR,
            dedup_window_seconds=600
        )

        config = manager.get_config()

        assert config['min_severity'] == 'error'
        assert config['dedup_window_seconds'] == 600

    def test_get_statistics(self):
        """Test get statistics."""
        manager = NotificationManager()

        stats = manager.get_statistics()

        assert 'total_alerts' in stats
        assert 'by_severity' in stats
        assert 'by_type' in stats
        assert 'by_channel' in stats

    @patch('ai_agent_connector.app.utils.alerting.urlopen')
    def test_send_to_channels(self, mock_urlopen):
        """Test sending to channels."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        manager = NotificationManager(async_dispatch=False)
        manager.add_channel(SlackChannel(webhook_url="https://hooks.slack.com/test"))

        alert = NotificationAlert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.WARNING,
            title="Test",
            message="Test"
        )

        results = manager.send(alert)
        assert 'slack' in results

    def test_send_critical_convenience(self):
        """Test send_critical convenience method."""
        manager = NotificationManager(async_dispatch=False)

        # No channels configured, should return empty
        results = manager.send_critical(
            title="Critical Error",
            message="System down"
        )

        assert results == {}

    def test_history(self):
        """Test alert history."""
        manager = NotificationManager(async_dispatch=False)

        # No channels, so nothing in history
        history = manager.get_history()
        assert isinstance(history, list)


class TestGlobalNotificationManager:
    """Test global notification manager functions."""

    def test_get_notification_manager_singleton(self):
        """Test singleton behavior."""
        import ai_agent_connector.app.utils.alerting as alerting_module
        alerting_module._notification_manager = None

        mgr1 = get_notification_manager()
        mgr2 = get_notification_manager()

        assert mgr1 is mgr2

    def test_init_notification_manager(self):
        """Test initialization with custom settings."""
        manager = init_notification_manager(
            min_severity=AlertSeverity.ERROR,
            dedup_window_seconds=600,
            async_dispatch=False
        )

        config = manager.get_config()
        assert config['min_severity'] == 'error'
        assert config['dedup_window_seconds'] == 600
        assert config['async_dispatch'] is False


class TestAlertingAPIEndpoints:
    """Test alerting API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        from flask import Flask
        from ai_agent_connector.app.api import api_bp

        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp, url_prefix='/api')
        self.client = self.app.test_client()

        # Initialize with fresh manager
        init_notification_manager()

    def test_get_channels(self):
        """Test GET /api/alerts/channels."""
        response = self.client.get('/api/alerts/channels')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'channels' in data
        assert 'config' in data

    def test_add_slack_channel(self):
        """Test POST /api/alerts/channels/slack."""
        response = self.client.post('/api/alerts/channels/slack', json={
            'webhook_url': 'https://hooks.slack.com/services/test'
        })
        assert response.status_code == 201

        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['channel'] == 'slack'

    def test_add_slack_channel_missing_url(self):
        """Test slack channel without webhook_url."""
        response = self.client.post('/api/alerts/channels/slack', json={})
        assert response.status_code == 400

    def test_add_pagerduty_channel(self):
        """Test POST /api/alerts/channels/pagerduty."""
        response = self.client.post('/api/alerts/channels/pagerduty', json={
            'routing_key': 'test-routing-key'
        })
        assert response.status_code == 201

        data = response.get_json()
        assert data['channel'] == 'pagerduty'

    def test_add_pagerduty_missing_key(self):
        """Test pagerduty channel without routing_key."""
        response = self.client.post('/api/alerts/channels/pagerduty', json={})
        assert response.status_code == 400

    def test_add_webhook_channel(self):
        """Test POST /api/alerts/channels/webhook."""
        response = self.client.post('/api/alerts/channels/webhook', json={
            'url': 'https://example.com/webhook',
            'name': 'custom-webhook'
        })
        assert response.status_code == 201

        data = response.get_json()
        assert data['channel'] == 'custom-webhook'

    def test_remove_channel(self):
        """Test DELETE /api/alerts/channels/{name}."""
        # First add a channel
        self.client.post('/api/alerts/channels/slack', json={
            'webhook_url': 'https://hooks.slack.com/test'
        })

        # Then remove it
        response = self.client.delete('/api/alerts/channels/slack')
        assert response.status_code == 200

    def test_remove_nonexistent_channel(self):
        """Test removing non-existent channel."""
        response = self.client.delete('/api/alerts/channels/nonexistent')
        assert response.status_code == 404

    def test_send_alert(self):
        """Test POST /api/alerts/send."""
        response = self.client.post('/api/alerts/send', json={
            'title': 'Test Alert',
            'message': 'This is a test',
            'severity': 'warning'
        })
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'

    def test_send_alert_missing_fields(self):
        """Test send alert without required fields."""
        response = self.client.post('/api/alerts/send', json={
            'title': 'Test'
            # missing message
        })
        assert response.status_code == 400

    def test_send_alert_invalid_severity(self):
        """Test send alert with invalid severity."""
        response = self.client.post('/api/alerts/send', json={
            'title': 'Test',
            'message': 'Test',
            'severity': 'invalid'
        })
        assert response.status_code == 400

    def test_get_history(self):
        """Test GET /api/alerts/history."""
        response = self.client.get('/api/alerts/history')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'history' in data

    def test_get_statistics(self):
        """Test GET /api/alerts/statistics."""
        response = self.client.get('/api/alerts/statistics')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'total_alerts' in data

    def test_get_config(self):
        """Test GET /api/alerts/config."""
        response = self.client.get('/api/alerts/config')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'config' in data
        assert 'alert_types' in data
        assert 'severity_levels' in data

    def test_update_config(self):
        """Test POST /api/alerts/config."""
        response = self.client.post('/api/alerts/config', json={
            'min_severity': 'error',
            'dedup_window_seconds': 600
        })
        assert response.status_code == 200

        data = response.get_json()
        assert data['config']['min_severity'] == 'error'

    def test_update_config_invalid_severity(self):
        """Test update config with invalid severity."""
        response = self.client.post('/api/alerts/config', json={
            'min_severity': 'invalid'
        })
        assert response.status_code == 400

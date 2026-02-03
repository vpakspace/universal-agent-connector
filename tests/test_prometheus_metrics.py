"""
Unit tests for Prometheus metrics module.

Tests metrics collection, tracking functions, and /metrics endpoint.
Note: These tests require prometheus-client package.
"""

import pytest
from unittest.mock import patch, MagicMock
import time

# Check if prometheus-client is available
try:
    from prometheus_client import REGISTRY, Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PROMETHEUS_AVAILABLE,
    reason="prometheus-client not installed"
)


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestMetricsModule:
    """Test metrics module imports and structure."""

    def test_import_metrics_module(self):
        """Test that metrics module can be imported."""
        from ai_agent_connector.app.metrics import (
            init_metrics,
            get_metrics_blueprint,
            track_request,
            track_ontoguard_validation,
        )
        assert init_metrics is not None
        assert get_metrics_blueprint is not None
        assert track_request is not None
        assert track_ontoguard_validation is not None

    def test_metrics_constants_exist(self):
        """Test that metric constants are defined."""
        from ai_agent_connector.app.metrics import (
            HTTP_REQUEST_COUNT,
            HTTP_REQUEST_LATENCY,
            ONTOGUARD_VALIDATION_COUNT,
            ONTOGUARD_VALIDATION_LATENCY,
            WEBSOCKET_CONNECTIONS,
            SCHEMA_DRIFT_COUNT,
            DB_QUERY_COUNT,
            DB_QUERY_LATENCY,
            AGENT_OPERATION_COUNT,
        )
        assert HTTP_REQUEST_COUNT is not None
        assert HTTP_REQUEST_LATENCY is not None
        assert ONTOGUARD_VALIDATION_COUNT is not None
        assert ONTOGUARD_VALIDATION_LATENCY is not None
        assert WEBSOCKET_CONNECTIONS is not None
        assert SCHEMA_DRIFT_COUNT is not None
        assert DB_QUERY_COUNT is not None
        assert DB_QUERY_LATENCY is not None
        assert AGENT_OPERATION_COUNT is not None


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestTrackingFunctions:
    """Test metric tracking functions."""

    def test_track_request(self):
        """Test track_request function."""
        from ai_agent_connector.app.metrics import track_request

        # Should not raise
        track_request(
            method='GET',
            endpoint='/api/test',
            status=200,
            latency=0.05
        )

    def test_track_ontoguard_validation_allowed(self):
        """Test track_ontoguard_validation for allowed action."""
        from ai_agent_connector.app.metrics import track_ontoguard_validation

        # Should not raise
        track_ontoguard_validation(
            action='read',
            entity_type='User',
            allowed=True,
            role='Admin',
            latency=0.01
        )

    def test_track_ontoguard_validation_denied(self):
        """Test track_ontoguard_validation for denied action."""
        from ai_agent_connector.app.metrics import track_ontoguard_validation

        # Should not raise
        track_ontoguard_validation(
            action='delete',
            entity_type='User',
            allowed=False,
            role='Customer',
            latency=0.005
        )

    def test_track_websocket_connection(self):
        """Test track_websocket_connection function."""
        from ai_agent_connector.app.metrics import track_websocket_connection

        # Connect
        track_websocket_connection(event_type='validation', connected=True)
        # Disconnect
        track_websocket_connection(event_type='validation', connected=False)

    def test_track_schema_drift(self):
        """Test track_schema_drift function."""
        from ai_agent_connector.app.metrics import track_schema_drift

        track_schema_drift(
            domain='hospital',
            severity='WARNING',
            drift_type='type_change',
            issue_count=2
        )

    def test_track_db_query_success(self):
        """Test track_db_query for successful query."""
        from ai_agent_connector.app.metrics import track_db_query

        track_db_query(
            query_type='SELECT',
            success=True,
            agent_id='doctor-1',
            latency=0.025
        )

    def test_track_db_query_error(self):
        """Test track_db_query for failed query."""
        from ai_agent_connector.app.metrics import track_db_query

        track_db_query(
            query_type='INSERT',
            success=False,
            agent_id='nurse-1',
            latency=0.1
        )

    def test_track_agent_operation(self):
        """Test track_agent_operation function."""
        from ai_agent_connector.app.metrics import track_agent_operation

        track_agent_operation(operation='register', success=True)
        track_agent_operation(operation='query', success=False)


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestContextManagers:
    """Test context manager tracking functions."""

    def test_track_ontoguard_validation_time(self):
        """Test track_ontoguard_validation_time context manager."""
        from ai_agent_connector.app.metrics.prometheus_metrics import track_ontoguard_validation_time

        with track_ontoguard_validation_time('read', 'User'):
            time.sleep(0.01)  # Simulate some work

    def test_track_db_query_time(self):
        """Test track_db_query_time context manager."""
        from ai_agent_connector.app.metrics.prometheus_metrics import track_db_query_time

        with track_db_query_time('SELECT'):
            time.sleep(0.01)  # Simulate some work


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    @pytest.fixture
    def app_with_metrics(self):
        """Create Flask app with metrics enabled."""
        from flask import Flask
        from ai_agent_connector.app.metrics import init_metrics, get_metrics_blueprint

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True

        init_metrics(app)
        app.register_blueprint(get_metrics_blueprint())

        return app

    def test_metrics_endpoint_exists(self, app_with_metrics):
        """Test that /metrics endpoint returns 200."""
        client = app_with_metrics.test_client()
        response = client.get('/metrics')

        assert response.status_code == 200
        assert response.content_type.startswith('text/plain')

    def test_metrics_endpoint_contains_counters(self, app_with_metrics):
        """Test that /metrics contains expected metrics."""
        client = app_with_metrics.test_client()
        response = client.get('/metrics')

        data = response.data.decode('utf-8')

        # Check for our custom metrics
        assert 'uac_http_requests_total' in data or 'uac_' in data
        assert 'uac_build_info' in data

    def test_request_tracking(self, app_with_metrics):
        """Test that requests are tracked."""
        client = app_with_metrics.test_client()

        # Make a test request
        @app_with_metrics.route('/test')
        def test_route():
            return 'OK'

        client.get('/test')

        # Check metrics
        response = client.get('/metrics')
        data = response.data.decode('utf-8')

        # Should have recorded the request
        assert 'uac_http_requests_total' in data


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestEndpointNormalization:
    """Test endpoint path normalization."""

    def test_normalize_uuid(self):
        """Test UUID normalization."""
        from ai_agent_connector.app.metrics.prometheus_metrics import _normalize_endpoint

        path = '/api/agents/123e4567-e89b-12d3-a456-426614174000/query'
        normalized = _normalize_endpoint(path)

        assert '{id}' in normalized
        assert '123e4567' not in normalized

    def test_normalize_numeric_id(self):
        """Test numeric ID normalization."""
        from ai_agent_connector.app.metrics.prometheus_metrics import _normalize_endpoint

        path = '/api/users/12345/profile'
        normalized = _normalize_endpoint(path)

        assert '{id}' in normalized
        assert '12345' not in normalized

    def test_normalize_agent_id(self):
        """Test agent ID normalization."""
        from ai_agent_connector.app.metrics.prometheus_metrics import _normalize_endpoint

        path = '/api/agents/doctor-1/query'
        normalized = _normalize_endpoint(path)

        assert '{agent_id}' in normalized
        assert 'doctor-1' not in normalized

    def test_normalize_static_path(self):
        """Test that static paths are not changed."""
        from ai_agent_connector.app.metrics.prometheus_metrics import _normalize_endpoint

        path = '/api/ontoguard/status'
        normalized = _normalize_endpoint(path)

        assert normalized == '/api/ontoguard/status'


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestHelperFunctions:
    """Test helper functions."""

    def test_set_registered_agents(self):
        """Test set_registered_agents function."""
        from ai_agent_connector.app.metrics.prometheus_metrics import set_registered_agents

        set_registered_agents(5)
        set_registered_agents(10)

    def test_track_websocket_event(self):
        """Test track_websocket_event function."""
        from ai_agent_connector.app.metrics.prometheus_metrics import track_websocket_event

        track_websocket_event('validate_action', success=True)
        track_websocket_event('check_permissions', success=False)


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus-client not installed")
class TestDecorators:
    """Test metric decorators."""

    def test_track_latency_decorator(self):
        """Test track_latency decorator."""
        from ai_agent_connector.app.metrics.prometheus_metrics import track_latency

        @track_latency('test')
        def slow_function():
            time.sleep(0.01)
            return 'done'

        result = slow_function()
        assert result == 'done'

    def test_track_latency_with_exception(self):
        """Test track_latency decorator with exception."""
        from ai_agent_connector.app.metrics.prometheus_metrics import track_latency

        @track_latency('test')
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

"""
Unit tests for OntoGuard WebSocket handlers.

Tests WebSocket events for real-time OntoGuard validation.
Note: These tests require flask-socketio package.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Check if flask-socketio is available
try:
    from flask_socketio import SocketIO, SocketIOTestClient
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SOCKETIO_AVAILABLE,
    reason="flask-socketio not installed"
)


@pytest.fixture
def mock_ontoguard_adapter():
    """Create a mock OntoGuard adapter."""
    with patch('ai_agent_connector.app.security.get_ontoguard_adapter') as mock_get:
        adapter = MagicMock()
        adapter._initialized = True
        adapter._pass_through_mode = False
        adapter.is_active = True
        adapter.ontology_paths = ['/path/to/ontology.owl']

        # Mock validate_action result
        validation_result = MagicMock()
        validation_result.allowed = True
        validation_result.reason = "Action allowed by ontology rules"
        validation_result.constraints = []
        validation_result.suggestions = []
        validation_result.metadata = {}
        validation_result.to_dict.return_value = {
            'allowed': True,
            'reason': 'Action allowed by ontology rules',
            'constraints': [],
            'suggestions': [],
            'metadata': {}
        }
        adapter.validate_action.return_value = validation_result

        # Mock check_permissions
        adapter.check_permissions.return_value = True

        # Mock get_allowed_actions
        adapter.get_allowed_actions.return_value = ['read', 'create']

        # Mock explain_rule
        adapter.explain_rule.return_value = "Admin can perform read action on User"

        mock_get.return_value = adapter
        yield adapter


@pytest.mark.skipif(not SOCKETIO_AVAILABLE, reason="flask-socketio not installed")
class TestWebSocketModule:
    """Test WebSocket module imports and structure."""

    def test_import_websocket_module(self):
        """Test that websocket module can be imported."""
        from ai_agent_connector.app.websocket import register_websocket_handlers, get_socketio
        assert register_websocket_handlers is not None
        assert get_socketio is not None

    def test_ontoguard_ws_module_exists(self):
        """Test that ontoguard_ws module exists."""
        from ai_agent_connector.app.websocket import ontoguard_ws
        assert hasattr(ontoguard_ws, 'register_websocket_handlers')
        assert hasattr(ontoguard_ws, 'get_socketio')
        assert hasattr(ontoguard_ws, 'emit_validation_event')


@pytest.mark.skipif(not SOCKETIO_AVAILABLE, reason="flask-socketio not installed")
class TestWebSocketEvents:
    """Test WebSocket event handlers."""

    @pytest.fixture
    def app_with_socketio(self, mock_ontoguard_adapter):
        """Create Flask app with SocketIO for testing."""
        from flask import Flask
        from flask_socketio import SocketIO

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True

        socketio = SocketIO(app, async_mode='threading')

        # Register handlers
        from ai_agent_connector.app.websocket import register_websocket_handlers
        register_websocket_handlers(socketio)

        return app, socketio

    def test_connect_event(self, app_with_socketio):
        """Test WebSocket connect event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            assert client.is_connected()

            # Check for connected event
            received = client.get_received()
            connected_events = [r for r in received if r['name'] == 'connected']
            assert len(connected_events) == 1
            assert 'session_id' in connected_events[0]['args'][0]

            client.disconnect()

    def test_get_status_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test get_status WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()  # Clear connect event

            client.emit('get_status', {})

            received = client.get_received()
            status_events = [r for r in received if r['name'] == 'status']
            assert len(status_events) == 1

            status = status_events[0]['args'][0]
            assert 'initialized' in status
            assert 'active' in status
            assert 'timestamp' in status

            client.disconnect()

    def test_validate_action_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test validate_action WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()  # Clear connect event

            client.emit('validate_action', {
                'action': 'read',
                'entity_type': 'User',
                'context': {'role': 'Admin'},
                'request_id': 'test-123'
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'validation_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['allowed'] is True
            assert result['action'] == 'read'
            assert result['entity_type'] == 'User'
            assert result['request_id'] == 'test-123'
            assert 'timestamp' in result

            client.disconnect()

    def test_validate_action_missing_fields(self, app_with_socketio, mock_ontoguard_adapter):
        """Test validate_action with missing required fields."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            # Missing entity_type
            client.emit('validate_action', {
                'action': 'read'
            })

            received = client.get_received()
            error_events = [r for r in received if r['name'] == 'error']
            assert len(error_events) == 1
            assert error_events[0]['args'][0]['code'] == 'INVALID_REQUEST'

            client.disconnect()

    def test_check_permissions_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test check_permissions WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('check_permissions', {
                'role': 'Admin',
                'action': 'delete',
                'entity_type': 'User',
                'request_id': 'perm-123'
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'permission_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['allowed'] is True
            assert result['role'] == 'Admin'
            assert result['action'] == 'delete'
            assert result['entity_type'] == 'User'
            assert result['request_id'] == 'perm-123'

            client.disconnect()

    def test_get_allowed_actions_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test get_allowed_actions WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('get_allowed_actions', {
                'role': 'Admin',
                'entity_type': 'User'
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'allowed_actions_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['role'] == 'Admin'
            assert result['entity_type'] == 'User'
            assert 'allowed_actions' in result
            assert 'read' in result['allowed_actions']

            client.disconnect()

    def test_explain_rule_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test explain_rule WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('explain_rule', {
                'action': 'read',
                'entity_type': 'User',
                'context': {'role': 'Admin'}
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'rule_explanation']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['action'] == 'read'
            assert result['entity_type'] == 'User'
            assert 'explanation' in result

            client.disconnect()

    def test_validate_batch_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test validate_batch WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('validate_batch', {
                'validations': [
                    {'action': 'read', 'entity_type': 'User', 'context': {'role': 'Admin'}},
                    {'action': 'create', 'entity_type': 'Order', 'context': {'role': 'Admin'}},
                    {'action': 'delete', 'entity_type': 'User', 'context': {'role': 'Admin'}}
                ],
                'request_id': 'batch-123'
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'batch_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['total'] == 3
            assert 'results' in result
            assert len(result['results']) == 3
            assert result['request_id'] == 'batch-123'

            client.disconnect()

    def test_subscribe_validation_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test subscribe_validation WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('subscribe_validation', {
                'agent_id': 'agent-123'
            })

            received = client.get_received()
            sub_events = [r for r in received if r['name'] == 'subscribed']
            assert len(sub_events) == 1
            assert sub_events[0]['args'][0]['agent_id'] == 'agent-123'

            client.disconnect()

    def test_unsubscribe_validation_event(self, app_with_socketio, mock_ontoguard_adapter):
        """Test unsubscribe_validation WebSocket event."""
        app, socketio = app_with_socketio

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            # Subscribe first
            client.emit('subscribe_validation', {'agent_id': 'agent-123'})
            client.get_received()

            # Then unsubscribe
            client.emit('unsubscribe_validation', {'agent_id': 'agent-123'})

            received = client.get_received()
            unsub_events = [r for r in received if r['name'] == 'unsubscribed']
            assert len(unsub_events) == 1
            assert unsub_events[0]['args'][0]['agent_id'] == 'agent-123'

            client.disconnect()


@pytest.mark.skipif(not SOCKETIO_AVAILABLE, reason="flask-socketio not installed")
class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""

    @pytest.fixture
    def app_with_uninitialized_adapter(self):
        """Create Flask app with uninitialized OntoGuard adapter."""
        from flask import Flask
        from flask_socketio import SocketIO

        with patch('ai_agent_connector.app.security.get_ontoguard_adapter') as mock_get:
            adapter = MagicMock()
            adapter._initialized = False  # Not initialized
            mock_get.return_value = adapter

            app = Flask(__name__)
            app.config['SECRET_KEY'] = 'test-secret-key'
            app.config['TESTING'] = True

            socketio = SocketIO(app, async_mode='threading')

            from ai_agent_connector.app.websocket import register_websocket_handlers
            register_websocket_handlers(socketio)

            yield app, socketio

    def test_validate_action_not_initialized(self, app_with_uninitialized_adapter):
        """Test validate_action when OntoGuard is not initialized."""
        app, socketio = app_with_uninitialized_adapter

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('validate_action', {
                'action': 'read',
                'entity_type': 'User',
                'context': {'role': 'Admin'}
            })

            received = client.get_received()
            error_events = [r for r in received if r['name'] == 'error']
            assert len(error_events) == 1
            assert error_events[0]['args'][0]['code'] == 'NOT_INITIALIZED'

            client.disconnect()


@pytest.mark.skipif(not SOCKETIO_AVAILABLE, reason="flask-socketio not installed")
class TestEmitValidationEvent:
    """Test emit_validation_event function."""

    def test_emit_validation_event_function(self):
        """Test that emit_validation_event is callable."""
        from ai_agent_connector.app.websocket.ontoguard_ws import emit_validation_event

        # Should not raise when socketio is None
        emit_validation_event('agent-123', {'type': 'test'})

    def test_emit_validation_event_with_socketio(self):
        """Test emit_validation_event with active socketio."""
        from flask import Flask
        from flask_socketio import SocketIO
        from ai_agent_connector.app.websocket import register_websocket_handlers
        from ai_agent_connector.app.websocket.ontoguard_ws import emit_validation_event

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        socketio = SocketIO(app, async_mode='threading')
        register_websocket_handlers(socketio)

        # Just verify it doesn't raise
        with app.app_context():
            emit_validation_event('agent-123', {'type': 'validation', 'allowed': True})

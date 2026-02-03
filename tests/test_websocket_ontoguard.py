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


@pytest.mark.skipif(not SOCKETIO_AVAILABLE, reason="flask-socketio not installed")
class TestWebSocketDomainSupport:
    """Test WebSocket domain-aware functionality."""

    @pytest.fixture
    def mock_ontoguard_adapter_domain(self):
        """Create a mock OntoGuard adapter with domain support."""
        with patch('ai_agent_connector.app.security.get_ontoguard_adapter') as mock_get:
            adapter = MagicMock()
            adapter._initialized = True
            adapter._pass_through_mode = False
            adapter.is_active = True
            adapter.ontology_paths = ['/path/to/hospital.owl']
            adapter.initialize.return_value = True

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
            adapter.check_permissions.return_value = True
            adapter.get_allowed_actions.return_value = ['read', 'create', 'update']
            adapter.explain_rule.return_value = "Doctor can perform read action on PatientRecord"

            mock_get.return_value = adapter
            yield adapter

    @pytest.fixture
    def app_with_socketio_domain(self, mock_ontoguard_adapter_domain):
        """Create Flask app with SocketIO for domain testing."""
        from flask import Flask
        from flask_socketio import SocketIO

        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True

        socketio = SocketIO(app, async_mode='threading')

        from ai_agent_connector.app.websocket import register_websocket_handlers
        register_websocket_handlers(socketio)

        return app, socketio

    def test_validate_action_with_table_mapping(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test validate_action with table-to-entity mapping."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            # Use 'table' instead of 'entity_type' - should auto-map to PatientRecord
            client.emit('validate_action', {
                'action': 'read',
                'table': 'patients',
                'domain': 'hospital',
                'context': {'role': 'Doctor'}
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'validation_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['allowed'] is True
            assert result['entity_type'] == 'PatientRecord'
            assert result['domain'] == 'hospital'
            assert result['role'] == 'Doctor'

            client.disconnect()

    def test_validate_action_with_domain_in_context(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test validate_action with domain specified in context."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('validate_action', {
                'action': 'read',
                'entity_type': 'Account',
                'context': {
                    'role': 'Analyst',
                    'domain': 'finance'
                }
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'validation_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['domain'] == 'finance'

            client.disconnect()

    def test_check_permissions_with_table_mapping(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test check_permissions with table-to-entity mapping."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('check_permissions', {
                'role': 'LabTech',
                'action': 'read',
                'table': 'lab_results',
                'domain': 'hospital'
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'permission_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['entity_type'] == 'LabResult'
            assert result['domain'] == 'hospital'

            client.disconnect()

    def test_validate_action_invalid_role_for_domain(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test validate_action with invalid role for domain."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            # 'Teller' is a finance role, not hospital
            client.emit('validate_action', {
                'action': 'read',
                'entity_type': 'PatientRecord',
                'domain': 'hospital',
                'context': {'role': 'Teller'}
            })

            received = client.get_received()
            error_events = [r for r in received if r['name'] == 'error']
            assert len(error_events) == 1
            assert error_events[0]['args'][0]['code'] == 'INVALID_ROLE'
            assert 'Teller' in error_events[0]['args'][0]['message']

            client.disconnect()

    def test_get_allowed_actions_with_domain(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test get_allowed_actions with domain support."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('get_allowed_actions', {
                'role': 'Doctor',
                'table': 'medical_records',
                'domain': 'hospital'
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'allowed_actions_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['entity_type'] == 'MedicalRecord'
            assert result['domain'] == 'hospital'
            assert 'allowed_actions' in result

            client.disconnect()

    def test_explain_rule_with_domain(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test explain_rule with domain support."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('explain_rule', {
                'action': 'read',
                'table': 'patients',
                'domain': 'hospital',
                'context': {'role': 'Nurse'}
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'rule_explanation']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['entity_type'] == 'PatientRecord'
            assert result['domain'] == 'hospital'
            assert 'explanation' in result

            client.disconnect()

    def test_validate_batch_with_mixed_domains(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test validate_batch with validations from different domains."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('validate_batch', {
                'domain': 'hospital',  # default domain
                'validations': [
                    {'action': 'read', 'table': 'patients', 'context': {'role': 'Doctor'}},
                    {'action': 'read', 'entity_type': 'Account', 'context': {'role': 'Analyst', 'domain': 'finance'}},
                    {'action': 'create', 'table': 'appointments', 'context': {'role': 'Receptionist'}}
                ]
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'batch_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['total'] == 3
            assert result['default_domain'] == 'hospital'
            assert len(result['results']) == 3

            # Check first result uses hospital domain and table mapping
            assert result['results'][0]['entity_type'] == 'PatientRecord'
            assert result['results'][0]['domain'] == 'hospital'

            # Second should override to finance
            assert result['results'][1]['domain'] == 'finance'

            # Third uses default domain
            assert result['results'][2]['entity_type'] == 'Appointment'
            assert result['results'][2]['domain'] == 'hospital'

            client.disconnect()

    def test_validate_batch_with_invalid_role(self, app_with_socketio_domain, mock_ontoguard_adapter_domain):
        """Test validate_batch with one invalid role."""
        app, socketio = app_with_socketio_domain

        with app.test_client() as _:
            client = socketio.test_client(app)
            client.get_received()

            client.emit('validate_batch', {
                'domain': 'hospital',
                'validations': [
                    {'action': 'read', 'table': 'patients', 'context': {'role': 'Doctor'}},
                    {'action': 'read', 'table': 'patients', 'context': {'role': 'InvalidRole'}}
                ]
            })

            received = client.get_received()
            result_events = [r for r in received if r['name'] == 'batch_result']
            assert len(result_events) == 1

            result = result_events[0]['args'][0]
            assert result['total'] == 2
            # First should succeed
            assert result['results'][0].get('allowed') is True
            # Second should have error
            assert 'error' in result['results'][1]
            assert result['error_count'] == 1

            client.disconnect()


@pytest.mark.skipif(not SOCKETIO_AVAILABLE, reason="flask-socketio not installed")
class TestDomainHelperFunctions:
    """Test domain helper functions."""

    def test_resolve_entity_type_from_table(self):
        """Test _resolve_entity_type with table name."""
        from ai_agent_connector.app.websocket.ontoguard_ws import _resolve_entity_type

        # Hospital domain mappings
        data = {'table': 'patients', 'domain': 'hospital'}
        assert _resolve_entity_type(data) == 'PatientRecord'

        data = {'table': 'medical_records', 'domain': 'hospital'}
        assert _resolve_entity_type(data) == 'MedicalRecord'

        data = {'table': 'lab_results', 'domain': 'hospital'}
        assert _resolve_entity_type(data) == 'LabResult'

    def test_resolve_entity_type_prefers_explicit(self):
        """Test _resolve_entity_type prefers explicit entity_type over table."""
        from ai_agent_connector.app.websocket.ontoguard_ws import _resolve_entity_type

        # If both provided, entity_type wins
        data = {'entity_type': 'CustomEntity', 'table': 'patients', 'domain': 'hospital'}
        assert _resolve_entity_type(data) == 'CustomEntity'

    def test_resolve_entity_type_unknown_table(self):
        """Test _resolve_entity_type with unknown table."""
        from ai_agent_connector.app.websocket.ontoguard_ws import _resolve_entity_type

        # Unknown table returns table name as fallback
        data = {'table': 'unknown_table', 'domain': 'hospital'}
        assert _resolve_entity_type(data) == 'unknown_table'

    def test_validate_role_for_domain_valid(self):
        """Test _validate_role_for_domain with valid role."""
        from ai_agent_connector.app.websocket.ontoguard_ws import _validate_role_for_domain

        # Valid hospital roles
        assert _validate_role_for_domain('Doctor', 'hospital') is None
        assert _validate_role_for_domain('Nurse', 'hospital') is None
        assert _validate_role_for_domain('Admin', 'hospital') is None

        # Valid finance roles
        assert _validate_role_for_domain('Analyst', 'finance') is None
        assert _validate_role_for_domain('Teller', 'finance') is None

    def test_validate_role_for_domain_invalid(self):
        """Test _validate_role_for_domain with invalid role."""
        from ai_agent_connector.app.websocket.ontoguard_ws import _validate_role_for_domain

        # Hospital role in finance domain
        error = _validate_role_for_domain('Doctor', 'finance')
        assert error is not None
        assert 'Doctor' in error
        assert 'finance' in error

        # Finance role in hospital domain
        error = _validate_role_for_domain('Teller', 'hospital')
        assert error is not None
        assert 'Teller' in error

    def test_validate_role_for_domain_empty_role(self):
        """Test _validate_role_for_domain with empty role."""
        from ai_agent_connector.app.websocket.ontoguard_ws import _validate_role_for_domain

        # Empty/None role should pass (no validation)
        assert _validate_role_for_domain(None, 'hospital') is None
        assert _validate_role_for_domain('', 'hospital') is None

    def test_get_current_domain(self):
        """Test get_current_domain function."""
        from ai_agent_connector.app.websocket.ontoguard_ws import get_current_domain

        # Should return default domain initially
        domain = get_current_domain()
        assert domain == 'hospital'  # DEFAULT_DOMAIN

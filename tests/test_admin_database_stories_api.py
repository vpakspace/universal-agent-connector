"""
API endpoint tests for Admin database management stories
Tests the REST API endpoints for all three admin stories
"""

import pytest
from unittest.mock import MagicMock, patch

from main import create_app
from ai_agent_connector.app.api.routes import agent_registry, access_control
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_agent():
    """Create an admin agent for testing"""
    result = agent_registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'},
        credentials={'api_key': 'admin-key', 'api_secret': 'admin-secret'}
    )
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    return {'agent_id': 'admin-agent', 'api_key': result['api_key']}


class TestStory1_API_PoolingAndTimeouts:
    """API tests for Story 1: Connection pooling and timeout configuration"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_pooling_via_api(self, mock_connector_cls, client, admin_agent):
        """Test registering agent with pooling via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        response = client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-pool-api',
                'agent_info': {'name': 'Pool Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'user',
                    'password': 'pass',
                    'database': 'db',
                    'pooling': {
                        'enabled': True,
                        'min_size': 5,
                        'max_size': 20
                    },
                    'timeouts': {
                        'connect_timeout': 10,
                        'query_timeout': 30
                    }
                }
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['agent_id'] == 'agent-pool-api'
        assert data['database']['status'] == 'connected'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_with_pooling_via_api(self, mock_connector_cls, client, admin_agent):
        """Test testing connection with pooling config via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        response = client.post(
            '/admin/databases/test',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db',
                'pooling': {
                    'enabled': True,
                    'min_size': 10,
                    'max_size': 50
                },
                'timeouts': {
                    'connect_timeout': 5,
                    'query_timeout': 60
                }
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'database_info' in data


class TestStory2_API_EncryptedCredentials:
    """API tests for Story 2: Encrypted credentials at rest"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_credentials_encrypted(self, mock_connector_cls, client, admin_agent):
        """Test that credentials are encrypted when registered via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        original_password = 'secretpassword123'
        
        response = client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-encrypt-api',
                'agent_info': {'name': 'Encrypted Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'user',
                    'password': original_password,
                    'database': 'db'
                }
            }
        )
        
        assert response.status_code == 201
        
        # Verify credentials are encrypted in storage
        stored_config = agent_registry._agent_database_configs['agent-encrypt-api']
        assert stored_config.get('_encrypted') is True
        assert stored_config['password'] != original_password
        
        # Verify credentials can be decrypted
        decrypted = agent_registry._decrypt_database_config(stored_config)
        assert decrypted['password'] == original_password
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_update_credentials_stay_encrypted(self, mock_connector_cls, client, admin_agent):
        """Test that updated credentials remain encrypted"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        # Register agent
        client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-update-encrypt',
                'agent_info': {'name': 'Test Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'user1',
                    'password': 'pass1',
                    'database': 'db'
                }
            }
        )
        
        # Update credentials
        new_password = 'newencryptedpass456'
        response = client.put(
            '/api/agents/agent-update-encrypt/database',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user2',
                'password': new_password,
                'database': 'db'
            }
        )
        
        assert response.status_code == 200
        
        # Verify new credentials are encrypted
        stored_config = agent_registry._agent_database_configs['agent-update-encrypt']
        assert stored_config.get('_encrypted') is True
        assert stored_config['password'] != new_password
        
        # Verify decryption works
        decrypted = agent_registry._decrypt_database_config(stored_config)
        assert decrypted['password'] == new_password


class TestStory3_API_CredentialRotation:
    """API tests for Story 3: Credential rotation without breaking connections"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_credentials_via_api(self, mock_connector_cls, client, admin_agent):
        """Test rotating credentials via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        # Register agent
        client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-rotate-api',
                'agent_info': {'name': 'Test Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'olduser',
                    'password': 'oldpass',
                    'database': 'db'
                }
            }
        )
        
        # Rotate credentials
        response = client.post(
            '/admin/agents/agent-rotate-api/database/rotate',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'newuser',
                'password': 'newpass',
                'database': 'db',
                'validate_before_activate': True
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'staging'
        assert 'staged_at' in data
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_activate_credentials_via_api(self, mock_connector_cls, client, admin_agent):
        """Test activating rotated credentials via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        # Register and rotate
        client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-activate-api',
                'agent_info': {'name': 'Test Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'olduser',
                    'password': 'oldpass',
                    'database': 'db'
                }
            }
        )
        
        client.post(
            '/admin/agents/agent-activate-api/database/rotate',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'newuser',
                'password': 'newpass',
                'database': 'db'
            }
        )
        
        # Activate
        response = client.post(
            '/admin/agents/agent-activate-api/database/activate',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'active'
        assert 'activated_at' in data
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rollback_credentials_via_api(self, mock_connector_cls, client, admin_agent):
        """Test rolling back credential rotation via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        # Register and rotate
        client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-rollback-api',
                'agent_info': {'name': 'Test Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'olduser',
                    'password': 'oldpass',
                    'database': 'db'
                }
            }
        )
        
        client.post(
            '/admin/agents/agent-rollback-api/database/rotate',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'newuser',
                'password': 'newpass',
                'database': 'db'
            }
        )
        
        # Rollback
        response = client.post(
            '/admin/agents/agent-rollback-api/database/rollback',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'rolled_back'
        assert 'rolled_back_at' in data
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_get_rotation_status_via_api(self, mock_connector_cls, client, admin_agent):
        """Test getting rotation status via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        # Register and rotate
        client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-status-api',
                'agent_info': {'name': 'Test Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'user',
                    'password': 'pass',
                    'database': 'db'
                }
            }
        )
        
        client.post(
            '/admin/agents/agent-status-api/database/rotate',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'newuser',
                'password': 'newpass',
                'database': 'db'
            }
        )
        
        # Get status
        response = client.get(
            '/admin/agents/agent-status-api/database/rotation-status',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'rotation_status' in data
        assert data['rotation_status']['status'] == 'staging'


class TestAllStories_API_Integration:
    """API integration tests combining all three stories"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_full_workflow_via_api(self, mock_connector_cls, client, admin_agent):
        """Test complete workflow via API: register with pooling -> rotate -> activate"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        # Step 1: Register with pooling and timeouts
        register_response = client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-full-workflow',
                'agent_info': {'name': 'Full Workflow Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'user1',
                    'password': 'password1',
                    'database': 'testdb',
                    'pooling': {
                        'enabled': True,
                        'min_size': 5,
                        'max_size': 20
                    },
                    'timeouts': {
                        'connect_timeout': 10,
                        'query_timeout': 30
                    }
                }
            }
        )
        
        assert register_response.status_code == 201
        
        # Verify encryption
        stored = agent_registry._agent_database_configs['agent-full-workflow']
        assert stored.get('_encrypted') is True
        
        # Step 2: Rotate credentials
        rotate_response = client.post(
            '/admin/agents/agent-full-workflow/database/rotate',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user2',
                'password': 'password2',
                'database': 'testdb',
                'pooling': {
                    'enabled': True,
                    'min_size': 10,
                    'max_size': 30
                },
                'timeouts': {
                    'query_timeout': 60
                }
            }
        )
        
        assert rotate_response.status_code == 200
        rotate_data = rotate_response.get_json()
        assert rotate_data['status'] == 'staging'
        
        # Step 3: Check rotation status
        status_response = client.get(
            '/admin/agents/agent-full-workflow/database/rotation-status',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert status_response.status_code == 200
        status_data = status_response.get_json()
        assert status_data['rotation_status']['status'] == 'staging'
        
        # Step 4: Activate
        activate_response = client.post(
            '/admin/agents/agent-full-workflow/database/activate',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert activate_response.status_code == 200
        activate_data = activate_response.get_json()
        assert activate_data['status'] == 'active'
        
        # Verify final state
        final_stored = agent_registry._agent_database_configs['agent-full-workflow']
        assert final_stored.get('_encrypted') is True
        
        final_decrypted = agent_registry._decrypt_database_config(final_stored)
        assert final_decrypted['user'] == 'user2'
        assert final_decrypted['password'] == 'password2'
        assert final_decrypted['pooling']['min_size'] == 10
        assert final_decrypted['timeouts']['query_timeout'] == 60
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_with_invalid_credentials_rejected(self, mock_connector_cls, client, admin_agent):
        """Test that rotation with invalid credentials is rejected via API"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        # Register agent
        client.post(
            '/api/agents/register',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'agent_id': 'agent-invalid-rotate',
                'agent_info': {'name': 'Test Agent'},
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'user': 'user',
                    'password': 'pass',
                    'database': 'db'
                }
            }
        )
        
        # Try to rotate with invalid credentials
        mock_connector.connect.side_effect = ConnectionError("Connection failed")
        
        response = client.post(
            '/admin/agents/agent-invalid-rotate/database/rotate',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'postgresql',
                'host': 'invalid-host',
                'user': 'user',
                'password': 'wrongpass',
                'database': 'db'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'validation failed' in data['message'].lower()
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_non_admin_cannot_rotate_credentials(self, mock_connector_cls, client):
        """Test that non-admin users cannot rotate credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        # Create non-admin agent
        result = agent_registry.register_agent(
            agent_id='regular-agent',
            agent_info={'name': 'Regular Agent'},
            credentials={'api_key': 'regular-key', 'api_secret': 'regular-secret'}
        )
        
        # Try to rotate (should fail)
        response = client.post(
            '/admin/agents/regular-agent/database/rotate',
            headers={'X-API-Key': result['api_key']},
            json={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db'
            }
        )
        
        assert response.status_code == 403
        assert 'Admin permission required' in response.get_json()['error']


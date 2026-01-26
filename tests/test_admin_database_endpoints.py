"""
Unit tests for admin database management API endpoints
"""

import pytest
from unittest.mock import MagicMock, patch

from main import create_app
from ai_agent_connector.app.api.routes import agent_registry, access_control
from ai_agent_connector.app.permissions import Permission


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()


@pytest.fixture
def admin_agent():
    """Create an admin agent for testing"""
    # Register admin agent
    result = agent_registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'},
        credentials={'api_key': 'admin-key', 'api_secret': 'admin-secret'}
    )
    
    # Grant admin permission
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    
    return {
        'agent_id': 'admin-agent',
        'api_key': result['api_key']
    }


@pytest.fixture
def non_admin_agent():
    """Create a non-admin agent for testing"""
    result = agent_registry.register_agent(
        agent_id='regular-agent',
        agent_info={'name': ' Regular Agent'},
        credentials={'api_key': 'regular-key', 'api_secret': 'regular-secret'}
    )
    
    return {
        'agent_id': 'regular-agent',
        'api_key': result['api_key']
    }


class TestListDatabaseTypes:
    """Test GET /admin/databases endpoint"""
    
    def test_list_database_types_success(self, client, admin_agent):
        """Test listing database types as admin"""
        response = client.get(
            '/admin/databases',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'supported_types' in data
        assert 'database_details' in data
        assert 'postgresql' in data['supported_types']
        assert 'mysql' in data['supported_types']
        assert 'mongodb' in data['supported_types']
        assert 'bigquery' in data['supported_types']
        assert 'snowflake' in data['supported_types']
    
    def test_list_database_types_no_auth(self, client):
        """Test listing database types without authentication"""
        response = client.get('/admin/databases')
        
        assert response.status_code == 401
        assert 'API key required' in response.get_json()['error']
    
    def test_list_database_types_non_admin(self, client, non_admin_agent):
        """Test listing database types as non-admin"""
        response = client.get(
            '/admin/databases',
            headers={'X-API-Key': non_admin_agent['api_key']}
        )
        
        assert response.status_code == 403
        assert 'Admin permission required' in response.get_json()['error']
    
    def test_list_database_types_includes_details(self, client, admin_agent):
        """Test that database types include detailed information"""
        response = client.get(
            '/admin/databases',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        data = response.get_json()
        assert 'postgresql' in data['database_details']
        postgresql_info = data['database_details']['postgresql']
        assert 'name' in postgresql_info
        assert 'description' in postgresql_info
        assert 'required_params' in postgresql_info


class TestAdminTestDatabaseConnection:
    """Test POST /admin/databases/test endpoint"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_mysql_connection_success(self, mock_connector_cls, client, admin_agent):
        """Test testing MySQL connection as admin"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.get_database_info.return_value = {'type': 'mysql', 'version': '8.0'}
        mock_connector_cls.return_value = mock_connector
        
        response = client.post(
            '/admin/databases/test',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'mysql',
                'host': 'localhost',
                'user': 'testuser',
                'password': 'testpass',
                'database': 'testdb'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'database_info' in data
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_mongodb_connection_success(self, mock_connector_cls, client, admin_agent):
        """Test testing MongoDB connection as admin"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.get_database_info.return_value = {'type': 'mongodb', 'version': '6.0'}
        mock_connector_cls.return_value = mock_connector
        
        response = client.post(
            '/admin/databases/test',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'mongodb',
                'host': 'localhost',
                'port': 27017,
                'database': 'testdb'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_failure(self, mock_connector_cls, client, admin_agent):
        """Test connection failure"""
        mock_connector = MagicMock()
        mock_connector.connect.side_effect = ConnectionError("Connection failed")
        mock_connector_cls.return_value = mock_connector
        
        response = client.post(
            '/admin/databases/test',
            headers={'X-API-Key': admin_agent['api_key']},
            json={
                'type': 'mysql',
                'host': 'invalid-host',
                'user': 'user',
                'database': 'db'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'error' in data
    
    def test_test_connection_no_auth(self, client):
        """Test testing connection without authentication"""
        response = client.post(
            '/admin/databases/test',
            json={'type': 'mysql', 'host': 'localhost'}
        )
        
        assert response.status_code == 401
    
    def test_test_connection_non_admin(self, client, non_admin_agent):
        """Test testing connection as non-admin"""
        response = client.post(
            '/admin/databases/test',
            headers={'X-API-Key': non_admin_agent['api_key']},
            json={'type': 'mysql', 'host': 'localhost'}
        )
        
        assert response.status_code == 403
    
    def test_test_connection_missing_config(self, client, admin_agent):
        """Test testing connection with missing configuration"""
        response = client.post(
            '/admin/databases/test',
            headers={'X-API-Key': admin_agent['api_key']},
            json={}
        )
        
        assert response.status_code == 400
        assert 'Missing database configuration' in response.get_json()['error']


class TestListDatabaseConnections:
    """Test GET /admin/databases/connections endpoint"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_list_connections_success(self, mock_connector_cls, client, admin_agent):
        """Test listing all database connections as admin"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        # Register agents with different database types
        agent_registry.register_agent(
            agent_id='agent1',
            agent_info={'name': 'Agent 1'},
            credentials={'api_key': 'key1', 'api_secret': 'secret1'},
            database_config={
                'type': 'mysql',
                'host': 'localhost',
                'user': 'user',
                'database': 'db1'
            }
        )
        
        agent_registry.register_agent(
            agent_id='agent2',
            agent_info={'name': 'Agent 2'},
            credentials={'api_key': 'key2', 'api_secret': 'secret2'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'database': 'db2'
            }
        )
        
        response = client.get(
            '/admin/databases/connections',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'connections' in data
        assert 'count' in data
        assert data['count'] >= 2
        
        # Verify connection details
        connection_types = [conn['type'] for conn in data['connections']]
        assert 'mysql' in connection_types
        assert 'postgresql' in connection_types
    
    def test_list_connections_no_auth(self, client):
        """Test listing connections without authentication"""
        response = client.get('/admin/databases/connections')
        
        assert response.status_code == 401
    
    def test_list_connections_non_admin(self, client, non_admin_agent):
        """Test listing connections as non-admin"""
        response = client.get(
            '/admin/databases/connections',
            headers={'X-API-Key': non_admin_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_list_connections_empty(self, mock_connector_cls, client, admin_agent):
        """Test listing connections when none exist"""
        # State is already reset by the fixture
        
        response = client.get(
            '/admin/databases/connections',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 0
        assert data['connections'] == []


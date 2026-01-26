"""
Integration tests for permission enforcement in query execution
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from main import create_app
from ai_agent_connector.app.api.routes import agent_registry, access_control
from ai_agent_connector.app.permissions import Permission


@pytest.fixture(autouse=True)
def reset_state():
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()


@pytest.fixture
def client():
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def registered_agent_with_db(client):
    """Register an agent with database connection"""
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        response = client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_info': {'name': 'Test Agent'},
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
        
        assert response.status_code == 201
        body = response.get_json()
        api_key = body['api_key']
        
        return {
            'agent_id': 'agent-001',
            'api_key': api_key
        }


class TestPermissionEnforcement:
    """Test permission enforcement in query execution"""
    
    def test_query_with_read_permission_allowed(self, client, registered_agent_with_db):
        """Test that SELECT query is allowed with READ permission"""
        agent_id = registered_agent_with_db['agent_id']
        api_key = registered_agent_with_db['api_key']
        
        # Grant read permission on users table
        access_control.set_resource_permissions(
            agent_id=agent_id,
            resource_id='users',
            permissions=[Permission.READ],
            resource_type='table'
        )
        
        # Mock database connector
        with patch.object(agent_registry, 'get_database_connector') as mock_get_connector:
            mock_connector = MagicMock()
            mock_connector.connect.return_value = True
            mock_connector.execute_query.return_value = [('user1',), ('user2',)]
            mock_get_connector.return_value = mock_connector
            
            response = client.post(
                f'/api/agents/{agent_id}/query',
                json={'query': 'SELECT * FROM users'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 200
            body = response.get_json()
            assert body['success'] is True
            assert 'users' in body['tables_accessed']
            mock_connector.connect.assert_called_once()
            mock_connector.execute_query.assert_called_once()
    
    def test_query_without_permission_denied(self, client, registered_agent_with_db):
        """Test that query is denied without required permission"""
        agent_id = registered_agent_with_db['agent_id']
        api_key = registered_agent_with_db['api_key']
        
        # No permissions granted
        
        response = client.post(
            f'/api/agents/{agent_id}/query',
            json={'query': 'SELECT * FROM users'},
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 403
        body = response.get_json()
        assert body['error'] == 'Permission denied'
        assert len(body['denied_resources']) > 0
    
    def test_write_query_without_write_permission_denied(self, client, registered_agent_with_db):
        """Test that INSERT/UPDATE/DELETE requires WRITE permission"""
        agent_id = registered_agent_with_db['agent_id']
        api_key = registered_agent_with_db['api_key']
        
        # Grant only READ permission
        access_control.set_resource_permissions(
            agent_id=agent_id,
            resource_id='users',
            permissions=[Permission.READ],
            resource_type='table'
        )
        
        response = client.post(
            f'/api/agents/{agent_id}/query',
            json={'query': 'INSERT INTO users (name) VALUES (\'test\')'},
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 403
        body = response.get_json()
        assert body['error'] == 'Permission denied'
        assert any('write' in str(r).lower() for r in body['denied_resources'])
    
    def test_write_query_with_write_permission_allowed(self, client, registered_agent_with_db):
        """Test that INSERT is allowed with WRITE permission"""
        agent_id = registered_agent_with_db['agent_id']
        api_key = registered_agent_with_db['api_key']
        
        # Grant write permission
        access_control.set_resource_permissions(
            agent_id=agent_id,
            resource_id='users',
            permissions=[Permission.WRITE],
            resource_type='table'
        )
        
        with patch.object(agent_registry, 'get_database_connector') as mock_get_connector:
            mock_connector = MagicMock()
            mock_connector.connect.return_value = True
            mock_connector.execute_query.return_value = None
            mock_get_connector.return_value = mock_connector
            
            response = client.post(
                f'/api/agents/{agent_id}/query',
                json={'query': 'INSERT INTO users (name) VALUES (\'test\')'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 200
            body = response.get_json()
            assert body['success'] is True
    
    def test_query_multiple_tables_all_require_permission(self, client, registered_agent_with_db):
        """Test that queries accessing multiple tables require permission on all"""
        agent_id = registered_agent_with_db['agent_id']
        api_key = registered_agent_with_db['api_key']
        
        # Grant permission on only one table
        access_control.set_resource_permissions(
            agent_id=agent_id,
            resource_id='users',
            permissions=[Permission.READ],
            resource_type='table'
        )
        
        response = client.post(
            f'/api/agents/{agent_id}/query',
            json={'query': 'SELECT * FROM users u JOIN orders o ON u.id = o.user_id'},
            headers={'X-API-Key': api_key}
        )
        
        assert response.status_code == 403
        body = response.get_json()
        assert 'orders' in str(body['denied_resources'])
    
    def test_query_with_schema_table_format(self, client, registered_agent_with_db):
        """Test permission check with schema.table format"""
        agent_id = registered_agent_with_db['agent_id']
        api_key = registered_agent_with_db['api_key']
        
        # Grant permission on schema.table
        access_control.set_resource_permissions(
            agent_id=agent_id,
            resource_id='public.users',
            permissions=[Permission.READ],
            resource_type='table'
        )
        
        with patch.object(agent_registry, 'get_database_connector') as mock_get_connector:
            mock_connector = MagicMock()
            mock_connector.connect.return_value = True
            mock_connector.execute_query.return_value = [('user1',)]
            mock_get_connector.return_value = mock_connector
            
            response = client.post(
                f'/api/agents/{agent_id}/query',
                json={'query': 'SELECT * FROM public.users'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 200
    
    def test_query_requires_authentication(self, client, registered_agent_with_db):
        """Test that query endpoint requires API key authentication"""
        agent_id = registered_agent_with_db['agent_id']
        
        response = client.post(
            f'/api/agents/{agent_id}/query',
            json={'query': 'SELECT * FROM users'}
        )
        
        assert response.status_code == 401
        assert 'API key' in response.get_json()['error']
    
    def test_query_invalid_agent_id(self, client):
        """Test query with invalid agent ID"""
        response = client.post(
            '/api/agents/invalid-agent/query',
            json={'query': 'SELECT * FROM users'},
            headers={'X-API-Key': 'invalid-key'}
        )
        
        assert response.status_code in [401, 404]
    
    def test_query_agent_without_database(self, client):
        """Test query for agent without database configuration"""
        # Register agent with database, then manually remove it to simulate missing config
        with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
            mock_connector = MagicMock()
            mock_connector.connect.return_value = True
            mock_connector_cls.return_value = mock_connector
            
            response = client.post('/api/agents/register', json={
                'agent_id': 'agent-no-db',
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
            })
            
            assert response.status_code == 201
            api_key = response.get_json()['api_key']
            
            # Manually remove database config to simulate missing database
            agent_registry._agent_database_configs.pop('agent-no-db', None)
            
            response = client.post(
                '/api/agents/agent-no-db/query',
                json={'query': 'SELECT * FROM users'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 400
            assert 'database connection' in response.get_json()['error'].lower()


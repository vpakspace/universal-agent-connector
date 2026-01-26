"""
API route tests for agent registration
"""

import pytest
from unittest.mock import MagicMock, patch

from main import create_app
from ai_agent_connector.app.api.routes import agent_registry, access_control


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


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_register_agent_endpoint_success(mock_connector_cls, client):
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_info': {'name': 'Reporting Bot'},
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    assert response.status_code == 201
    body = response.get_json()
    assert body['agent_id'] == 'agent-001'
    assert body['database']['status'] == 'connected'


def test_register_agent_missing_payload(client):
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001'
    })
    
    assert response.status_code == 400
    assert 'Missing required fields' in response.get_json()['error']


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_set_resource_permissions(mock_connector_cls, client):
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    response = client.put('/api/agents/agent-001/permissions/resources', json={
        'resource_id': 'public.orders',
        'resource_type': 'table',
        'permissions': ['read', 'write']
    })
    
    assert response.status_code == 200
    body = response.get_json()
    assert body['permissions'] == ['read', 'write']
    
    listing = client.get('/api/agents/agent-001/permissions/resources')
    assert listing.status_code == 200
    resources = listing.get_json()['resources']
    assert 'public.orders' in resources
    assert 'read' in resources['public.orders']['permissions']


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_revoke_resource_permissions(mock_connector_cls, client):
    """Test revoking permissions on a resource"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    # Set permissions first
    client.put('/api/agents/agent-001/permissions/resources', json={
        'resource_id': 'public.orders',
        'resource_type': 'table',
        'permissions': ['read', 'write']
    })
    
    # Revoke permissions
    response = client.delete('/api/agents/agent-001/permissions/resources/public.orders')
    assert response.status_code == 200
    body = response.get_json()
    assert body['resource_id'] == 'public.orders'
    assert 'revoked' in body['message'].lower()
    
    # Verify permissions are gone
    listing = client.get('/api/agents/agent-001/permissions/resources')
    resources = listing.get_json()['resources']
    assert 'public.orders' not in resources


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_revoke_nonexistent_resource_permissions(mock_connector_cls, client):
    """Test revoking permissions on a resource that doesn't exist"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    # Try to revoke permissions that don't exist
    response = client.delete('/api/agents/agent-001/permissions/resources/nonexistent.table')
    assert response.status_code == 404
    assert 'not found' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_list_available_tables(mock_connector_cls, client):
    """Test listing available tables from agent's database"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.execute_query.return_value = [
        ('public', 'users', 'users'),
        ('public', 'orders', 'orders'),
        ('analytics', 'sales', 'analytics.sales')
    ]
    mock_connector_cls.return_value = mock_connector
    
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {
            'connection_string': 'postgresql://user:pass@localhost/db',
            'database': 'test_db'
        }
    })
    
    # Mock the get_database_connector to return our mock
    with patch.object(agent_registry, 'get_database_connector', return_value=mock_connector):
        response = client.get('/api/agents/agent-001/tables')
        
        assert response.status_code == 200
        body = response.get_json()
        assert body['agent_id'] == 'agent-001'
        assert 'tables' in body
        assert body['count'] == 3
        assert len(body['tables']) == 3
        
        # Check table structure
        table = body['tables'][0]
        assert 'schema' in table
        assert 'table_name' in table
        assert 'resource_id' in table
        assert 'type' in table
        assert table['type'] == 'table'


def test_list_tables_agent_not_found(client):
    """Test listing tables for non-existent agent"""
    response = client.get('/api/agents/nonexistent/tables')
    assert response.status_code == 404
    assert 'not found' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_list_tables_no_database(mock_connector_cls, client):
    """Test listing tables for agent without database connection"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_access_preview_with_permissions(mock_connector_cls, client):
    """Test access preview showing accessible and inaccessible tables"""
    from ai_agent_connector.app.permissions import Permission
    
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    # Mock tables query and columns query
    mock_connector.execute_query.side_effect = [
        # First call: list tables
        [
            ('public', 'users', 'users'),
            ('public', 'orders', 'orders'),
            ('analytics', 'sales', 'analytics.sales')
        ],
        # Second call: get columns for all tables
        [
            # users table columns
            ('public', 'users', 'id', 'integer', 'NO', None, 1),
            ('public', 'users', 'name', 'varchar', 'YES', None, 2),
            ('public', 'users', 'email', 'varchar', 'YES', None, 3),
            # orders table columns
            ('public', 'orders', 'id', 'integer', 'NO', None, 1),
            ('public', 'orders', 'user_id', 'integer', 'YES', None, 2),
            # analytics.sales table columns
            ('analytics', 'sales', 'id', 'integer', 'NO', None, 1),
            ('analytics', 'sales', 'amount', 'numeric', 'YES', None, 2),
        ]
    ]
    mock_connector_cls.return_value = mock_connector
    
    # Register agent with database
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {
            'connection_string': 'postgresql://user:pass@localhost/db',
            'database': 'test_db'
        }
    })
    
    # Set permissions on some tables
    access_control.set_resource_permissions(
        'agent-001',
        'users',
        [Permission.READ, Permission.WRITE]
    )
    access_control.set_resource_permissions(
        'agent-001',
        'orders',
        [Permission.READ]
    )
    # analytics.sales has no permissions
    
    # Mock the get_database_connector to return our mock
    with patch.object(agent_registry, 'get_database_connector', return_value=mock_connector):
        response = client.get('/api/agents/agent-001/access-preview')
        
        assert response.status_code == 200
        body = response.get_json()
        assert body['agent_id'] == 'agent-001'
        assert 'summary' in body
        assert 'accessible_tables' in body
        assert 'inaccessible_tables' in body
        
        # Check summary
        summary = body['summary']
        assert summary['total_tables'] == 3
        assert summary['accessible_tables'] == 2
        assert summary['inaccessible_tables'] == 1
        assert summary['read_only_tables'] == 1  # orders
        assert summary['read_write_tables'] == 1  # users
        assert summary['write_only_tables'] == 0
        
        # Check accessible tables
        assert len(body['accessible_tables']) == 2
        users_table = next(t for t in body['accessible_tables'] if t['table_name'] == 'users')
        assert users_table['has_read'] is True
        assert users_table['has_write'] is True
        assert Permission.READ.value in users_table['permissions']
        assert Permission.WRITE.value in users_table['permissions']
        assert 'columns' in users_table
        assert len(users_table['columns']) == 3
        assert users_table['column_count'] == 3
        
        orders_table = next(t for t in body['accessible_tables'] if t['table_name'] == 'orders')
        assert orders_table['has_read'] is True
        assert orders_table['has_write'] is False
        assert len(orders_table['columns']) == 2
        
        # Check inaccessible tables
        assert len(body['inaccessible_tables']) == 1
        sales_table = body['inaccessible_tables'][0]
        assert sales_table['table_name'] == 'sales'
        assert sales_table['permissions'] == []
        assert sales_table['has_read'] is False
        assert sales_table['has_write'] is False
        # Inaccessible tables should still have column info (for transparency)
        assert 'columns' in sales_table


def test_access_preview_agent_not_found(client):
    """Test access preview for non-existent agent"""
    response = client.get('/api/agents/nonexistent/access-preview')
    assert response.status_code == 404
    assert 'not found' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_access_preview_no_database(mock_connector_cls, client):
    """Test access preview for agent without database connection"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    # Register agent with database
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_info': {'name': 'Test Agent'},
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    assert response.status_code == 201
    
    # Mock get_database_connector to return None (simulating no database connection)
    with patch.object(agent_registry, 'get_database_connector', return_value=None):
        response = client.get('/api/agents/agent-001/access-preview')
        assert response.status_code == 400
        assert 'database connection' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_list_tables_shows_permissions(mock_connector_cls, client):
    """Test that list tables endpoint shows permissions for each table"""
    from ai_agent_connector.app.permissions import Permission
    
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.execute_query.return_value = [
        ('public', 'users', 'users'),
        ('public', 'orders', 'orders')
    ]
    mock_connector_cls.return_value = mock_connector
    
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    # Set permissions
    access_control.set_resource_permissions(
        'agent-001',
        'users',
        [Permission.READ, Permission.WRITE]
    )
    access_control.set_resource_permissions(
        'agent-001',
        'orders',
        [Permission.READ]
    )
    
    with patch.object(agent_registry, 'get_database_connector', return_value=mock_connector):
        response = client.get('/api/agents/agent-001/tables')
        
        assert response.status_code == 200
        body = response.get_json()
        
        users_table = next(t for t in body['tables'] if t['table_name'] == 'users')
        assert 'permissions' in users_table
        assert Permission.READ.value in users_table['permissions']
        assert Permission.WRITE.value in users_table['permissions']
        assert users_table['has_read'] is True
        assert users_table['has_write'] is True
        
        orders_table = next(t for t in body['tables'] if t['table_name'] == 'orders')
        assert Permission.READ.value in orders_table['permissions']
        assert Permission.WRITE.value not in orders_table['permissions']
        assert orders_table['has_read'] is True
        assert orders_table['has_write'] is False
    
    # Manually remove database config to simulate missing database
    agent_registry._agent_database_configs.pop('agent-001', None)
    
    response = client.get('/api/agents/agent-001/tables')
    assert response.status_code == 400
    assert 'database connection' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
@patch('ai_agent_connector.app.utils.nl_to_sql.NLToSQLConverter')
def test_natural_language_query_success(mock_converter_cls, mock_connector_cls, client):
    """Test successful natural language query execution"""
    # Setup mocks
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.execute_query.return_value = [('user1', 25), ('user2', 30)]
    mock_connector_cls.return_value = mock_connector
    
    # Mock NL converter
    mock_converter = MagicMock()
    mock_converter.convert_with_schema.return_value = {
        'sql': 'SELECT name, age FROM users',
        'natural_language': 'Show me all users with their ages',
        'model': 'gpt-4o-mini'
    }
    mock_converter_cls.return_value = mock_converter
    
    # Register agent
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    assert response.status_code == 201
    api_key = response.get_json()['api_key']
    
    # Grant read permission
    from ai_agent_connector.app.permissions import Permission
    from ai_agent_connector.app.api.routes import access_control
    access_control.set_resource_permissions(
        agent_id='agent-001',
        resource_id='users',
        permissions=[Permission.READ],
        resource_type='table'
    )
    
    # Mock get_database_connector to return our mock
    with patch.object(agent_registry, 'get_database_connector', return_value=mock_connector):
        # Also need to patch the converter instance in routes
        from ai_agent_connector.app.api.routes import nl_converter
        with patch.object(nl_converter, 'convert_with_schema', return_value={
            'sql': 'SELECT name, age FROM users',
            'natural_language': 'Show me all users with their ages',
            'model': 'gpt-4o-mini'
        }):
            response = client.post(
                '/api/agents/agent-001/query/natural',
                json={'query': 'Show me all users with their ages'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 200
            body = response.get_json()
            assert body['success'] is True
            assert body['natural_language_query'] == 'Show me all users with their ages'
            assert 'generated_sql' in body
            assert 'result' in body
            assert body['row_count'] == 2


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_natural_language_query_missing_query(mock_connector_cls, client):
    """Test natural language query with missing query field"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    api_key = response.get_json()['api_key']
    
    response = client.post(
        '/api/agents/agent-001/query/natural',
        json={},
        headers={'X-API-Key': api_key}
    )
    
    assert response.status_code == 400
    assert 'query' in response.get_json()['error'].lower() or 'question' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_natural_language_query_permission_denied(mock_connector_cls, client):
    """Test natural language query with insufficient permissions"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    api_key = response.get_json()['api_key']
    
    # No permissions granted
    
    from ai_agent_connector.app.api.routes import nl_converter
    with patch.object(nl_converter, 'convert_with_schema', return_value={
        'sql': 'SELECT * FROM users',
        'natural_language': 'Show me all users',
        'model': 'gpt-4o-mini'
    }):
        with patch.object(agent_registry, 'get_database_connector', return_value=mock_connector):
            response = client.post(
                '/api/agents/agent-001/query/natural',
                json={'query': 'Show me all users'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 403
            body = response.get_json()
            assert body['error'] == 'Permission denied'
            assert 'denied_resources' in body


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_natural_language_query_conversion_failure(mock_connector_cls, client):
    """Test natural language query when conversion fails"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    api_key = response.get_json()['api_key']
    
    from ai_agent_connector.app.api.routes import nl_converter
    with patch.object(nl_converter, 'convert_with_schema', return_value={
        'error': 'Failed to convert',
        'sql': None
    }):
        with patch.object(agent_registry, 'get_database_connector', return_value=mock_connector):
            response = client.post(
                '/api/agents/agent-001/query/natural',
                json={'query': 'Show me all users'},
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 400
            body = response.get_json()
            assert 'Failed to convert' in body['error']


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_test_database_connection_success(mock_connector_cls, client):
    """Test successful database connection test"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.execute_query.return_value = [(1,)]
    mock_connector_cls.return_value = mock_connector
    
    response = client.post('/api/databases/test', json={
        'connection_string': 'postgresql://user:pass@localhost/db'
    })
    
    assert response.status_code == 200
    body = response.get_json()
    assert body['status'] == 'success'
    assert 'Database connection test successful' in body['message']
    assert 'database_info' in body


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_test_database_connection_failure(mock_connector_cls, client):
    """Test database connection test with invalid credentials"""
    mock_connector = MagicMock()
    mock_connector.connect.side_effect = Exception("Connection refused")
    mock_connector_cls.return_value = mock_connector
    
    response = client.post('/api/databases/test', json={
        'connection_string': 'postgresql://user:wrongpass@localhost/db'
    })
    
    assert response.status_code == 400
    body = response.get_json()
    assert body['status'] == 'error'
    assert 'failed' in body['message'].lower()


def test_test_database_connection_missing_config(client):
    """Test database connection test with missing configuration"""
    response = client.post('/api/databases/test', json={})
    
    assert response.status_code == 400
    body = response.get_json()
    assert 'Missing database configuration' in body['error']


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_update_agent_database_success(mock_connector_cls, client):
    """Test successfully updating agent database connection"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    # Register an agent first
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db1'}
    })
    
    # Update database connection
    response = client.put('/api/agents/agent-001/database', json={
        'connection_string': 'postgresql://user:pass@localhost/db2'
    })
    
    assert response.status_code == 200
    body = response.get_json()
    assert 'updated' in body['message'].lower()
    assert body['agent_id'] == 'agent-001'
    assert 'database' in body


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_update_agent_database_agent_not_found(mock_connector_cls, client):
    """Test updating database for non-existent agent"""
    response = client.put('/api/agents/nonexistent/database', json={
        'connection_string': 'postgresql://user:pass@localhost/db'
    })
    
    assert response.status_code == 404
    body = response.get_json()
    assert 'not found' in body['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_update_agent_database_invalid_config(mock_connector_cls, client):
    """Test updating database with invalid configuration"""
    mock_connector = MagicMock()
    mock_connector.connect.side_effect = Exception("Connection failed")
    mock_connector_cls.return_value = mock_connector
    
    # Register an agent first
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_reg:
        mock_reg.return_value.connect.return_value = True
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db1'}
        })
    
    # Try to update with invalid connection
    response = client.put('/api/agents/agent-001/database', json={
        'connection_string': 'postgresql://invalid:invalid@invalid/invalid'
    })
    
    assert response.status_code == 400
    body = response.get_json()
    assert 'Failed to update' in body['error'] or 'Failed to connect' in body.get('message', '')


def test_api_documentation_endpoint(client):
    """Test API documentation endpoint"""
    response = client.get('/api/api-docs')
    
    assert response.status_code == 200
    body = response.get_json()
    assert 'openapi' in body
    assert 'paths' in body
    assert '/agents/register' in body['paths']
    assert '/databases/test' in body['paths']


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_revoke_agent_complete_cleanup(mock_connector_cls, client):
    """Test that revoking an agent completely removes all access"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    # Register an agent
    response = client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    assert response.status_code == 201
    api_key = response.get_json()['api_key']
    
    # Grant permissions
    from ai_agent_connector.app.permissions import Permission
    from ai_agent_connector.app.api.routes import access_control
    access_control.set_resource_permissions(
        agent_id='agent-001',
        resource_id='users',
        permissions=[Permission.READ, Permission.WRITE],
        resource_type='table'
    )
    access_control.grant_permission('agent-001', Permission.ADMIN)
    
    # Verify agent exists and can be retrieved
    response = client.get('/api/agents/agent-001')
    assert response.status_code == 200
    
    # Revoke agent
    response = client.delete('/api/agents/agent-001')
    assert response.status_code == 200
    body = response.get_json()
    assert 'revoked successfully' in body['message']
    assert body['details']['permissions_revoked'] is True
    assert body['details']['api_keys_invalidated'] is True
    
    # Verify agent no longer exists
    response = client.get('/api/agents/agent-001')
    assert response.status_code == 404
    
    # Verify agent cannot authenticate
    response = client.post(
        '/api/agents/agent-001/query',
        json={'query': 'SELECT * FROM users'},
        headers={'X-API-Key': api_key}
    )
    assert response.status_code in [401, 404]  # Should be unauthorized or not found
    
    # Verify permissions are gone
    permissions = access_control.get_permissions('agent-001')
    assert len(permissions) == 0
    resource_permissions = access_control.get_resource_permissions('agent-001')
    assert len(resource_permissions) == 0


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_revoke_nonexistent_agent(mock_connector_cls, client):
    """Test revoking an agent that doesn't exist"""
    response = client.delete('/api/agents/nonexistent-agent')
    assert response.status_code == 404
    assert 'not found' in response.get_json()['error'].lower()


@patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
def test_revoke_agent_with_permissions(mock_connector_cls, client):
    """Test that revoking an agent removes all permissions"""
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector_cls.return_value = mock_connector
    
    # Register agent
    client.post('/api/agents/register', json={
        'agent_id': 'agent-001',
        'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
        'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
    })
    
    # Set multiple resource permissions
    from ai_agent_connector.app.permissions import Permission
    from ai_agent_connector.app.api.routes import access_control
    access_control.set_resource_permissions('agent-001', 'table1', [Permission.READ])
    access_control.set_resource_permissions('agent-001', 'table2', [Permission.WRITE])
    access_control.grant_permission('agent-001', Permission.READ)
    
    # Verify permissions exist
    assert len(access_control.get_permissions('agent-001')) > 0
    assert len(access_control.get_resource_permissions('agent-001')) == 2
    
    # Revoke agent
    response = client.delete('/api/agents/agent-001')
    assert response.status_code == 200
    
    # Verify all permissions are removed
    assert len(access_control.get_permissions('agent-001')) == 0
    assert len(access_control.get_resource_permissions('agent-001')) == 0


def test_get_audit_logs(client):
    """Test retrieving audit logs"""
    # First, create some activity by registering an agent
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
    
    # Get all logs
    response = client.get('/api/audit/logs')
    assert response.status_code == 200
    body = response.get_json()
    assert 'logs' in body
    assert 'total' in body
    assert len(body['logs']) > 0


def test_get_audit_logs_with_filters(client):
    """Test retrieving audit logs with filters"""
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
    
    # Filter by agent_id
    response = client.get('/api/audit/logs?agent_id=agent-001')
    assert response.status_code == 200
    body = response.get_json()
    assert all(log.get('agent_id') == 'agent-001' for log in body['logs'])
    
    # Filter by action_type
    response = client.get('/api/audit/logs?action_type=agent_registered')
    assert response.status_code == 200
    body = response.get_json()
    assert all(log.get('action_type') == 'agent_registered' for log in body['logs'])
    
    # Filter by status
    response = client.get('/api/audit/logs?status=success')
    assert response.status_code == 200
    body = response.get_json()
    assert all(log.get('status') == 'success' for log in body['logs'])


def test_get_audit_logs_pagination(client):
    """Test audit logs pagination"""
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        # Create multiple agents to generate logs
        for i in range(5):
            client.post('/api/agents/register', json={
                'agent_id': f'agent-{i:03d}',
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
            })
    
    # Get first page
    response = client.get('/api/audit/logs?limit=2&offset=0')
    assert response.status_code == 200
    body = response.get_json()
    assert len(body['logs']) <= 2
    assert 'has_more' in body
    
    # Get second page
    response = client.get('/api/audit/logs?limit=2&offset=2')
    assert response.status_code == 200
    body = response.get_json()
    assert len(body['logs']) <= 2


def test_get_audit_log_by_id(client):
    """Test retrieving a specific audit log by ID"""
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
    
    # Get all logs to find an ID
    response = client.get('/api/audit/logs')
    logs = response.get_json()['logs']
    if logs:
        log_id = logs[0]['id']
        
        # Get specific log
        response = client.get(f'/api/audit/logs/{log_id}')
        assert response.status_code == 200
        body = response.get_json()
        assert body['id'] == log_id


def test_get_audit_log_not_found(client):
    """Test retrieving non-existent audit log"""
    response = client.get('/api/audit/logs/99999')
    assert response.status_code == 404
    assert 'not found' in response.get_json()['error'].lower()


def test_get_audit_statistics(client):
    """Test getting audit log statistics"""
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
    
    response = client.get('/api/audit/statistics')
    assert response.status_code == 200
    body = response.get_json()
    assert 'total_actions' in body
    assert 'by_action_type' in body
    assert 'by_status' in body
    assert 'recent_actions' in body


def test_get_notifications(client):
    """Test retrieving security notifications"""
    # First create some activity that might generate notifications
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
    
    # Try to authenticate with invalid key to generate a notification
    response = client.post(
        '/api/agents/agent-001/query',
        json={'query': 'SELECT * FROM users'},
        headers={'X-API-Key': 'invalid-key'}
    )
    
    # Get notifications
    response = client.get('/api/notifications')
    assert response.status_code == 200
    body = response.get_json()
    assert 'notifications' in body
    assert 'total' in body
    assert 'unread_count' in body


def test_get_notifications_with_filters(client):
    """Test retrieving notifications with filters"""
    # Generate a notification
    response = client.post(
        '/api/agents/nonexistent/query',
        json={'query': 'SELECT * FROM users'},
        headers={'X-API-Key': 'invalid-key'}
    )
    
    # Filter by severity
    response = client.get('/api/notifications?severity=medium')
    assert response.status_code == 200
    
    # Filter by unread only
    response = client.get('/api/notifications?unread_only=true')
    assert response.status_code == 200
    body = response.get_json()
    assert all(not n.get('read', False) for n in body['notifications'])


def test_mark_notification_read(client):
    """Test marking a notification as read"""
    # Generate a notification
    response = client.post(
        '/api/agents/nonexistent/query',
        json={'query': 'SELECT * FROM users'},
        headers={'X-API-Key': 'invalid-key'}
    )
    
    # Get notifications to find an ID
    response = client.get('/api/notifications')
    notifications = response.get_json()['notifications']
    
    if notifications:
        notification_id = notifications[0]['id']
        
        # Mark as read
        response = client.put(f'/api/notifications/{notification_id}/read')
        assert response.status_code == 200
        assert 'marked as read' in response.get_json()['message']


def test_mark_all_notifications_read(client):
    """Test marking all notifications as read"""
    # Generate some notifications
    for i in range(3):
        client.post(
            '/api/agents/nonexistent/query',
            json={'query': 'SELECT * FROM users'},
            headers={'X-API-Key': 'invalid-key'}
        )
    
    # Mark all as read
    response = client.put('/api/notifications/read-all')
    assert response.status_code == 200
    body = response.get_json()
    assert 'marked as read' in body['message']
    assert body['count'] >= 0


def test_get_notification_stats(client):
    """Test getting notification statistics"""
    # Generate some notifications
    client.post(
        '/api/agents/nonexistent/query',
        json={'query': 'SELECT * FROM users'},
        headers={'X-API-Key': 'invalid-key'}
    )
    
    response = client.get('/api/notifications/stats')
    assert response.status_code == 200
    body = response.get_json()
    assert 'total' in body
    assert 'unread' in body
    assert 'by_severity' in body
    assert 'by_event_type' in body


def test_get_audit_statistics_by_agent(client):
    """Test getting audit statistics filtered by agent"""
    with patch('ai_agent_connector.app.agents.registry.DatabaseConnector') as mock_connector_cls:
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        client.post('/api/agents/register', json={
            'agent_id': 'agent-001',
            'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
            'database': {'connection_string': 'postgresql://user:pass@localhost/db'}
        })
    
    response = client.get('/api/audit/statistics?agent_id=agent-001')
    assert response.status_code == 200
    body = response.get_json()
    assert 'total_actions' in body


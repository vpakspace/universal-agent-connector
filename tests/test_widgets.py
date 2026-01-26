"""
Tests for Embeddable Query Widgets
Tests widget creation, management, embedding, and query execution
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from ai_agent_connector.app.widgets import widget_bp
from ai_agent_connector.app.widgets.routes import widget_store, generate_widget_key, validate_widget_key


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.register_blueprint(widget_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry"""
    with patch('ai_agent_connector.app.widgets.routes.agent_registry') as mock:
        mock.get_agent.return_value = {
            'agent_id': 'test-agent',
            'api_key': 'test-agent-api-key',
            'name': 'Test Agent'
        }
        mock.get_database_connector.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_ai_agent_manager():
    """Mock AI agent manager"""
    with patch('ai_agent_connector.app.widgets.routes.ai_agent_manager') as mock:
        mock.execute_query.return_value = {
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 100},
                {'id': 2, 'name': 'Product 2', 'price': 200}
            ],
            'columns': ['id', 'name', 'price']
        }
        yield mock


@pytest.fixture
def mock_nl_converter():
    """Mock NL to SQL converter"""
    with patch('ai_agent_connector.app.widgets.routes.nl_converter') as mock:
        mock.get_schema_info.return_value = {'tables': []}
        mock.convert_to_sql.return_value = {
            'sql': 'SELECT * FROM products LIMIT 10',
            'error': None
        }
        yield mock


@pytest.fixture
def sample_widget():
    """Create a sample widget for testing"""
    widget_id = 'test-widget-123'
    widget_data = {
        'widget_id': widget_id,
        'name': 'Test Widget',
        'agent_id': 'test-agent',
        'api_key': 'test-widget-api-key',
        'theme': 'light',
        'height': '600px',
        'width': '100%',
        'created_at': '2024-01-15T00:00:00',
        'usage_count': 0
    }
    widget_store[widget_id] = widget_data
    return widget_id, widget_data


class TestWidgetCreation:
    """Tests for widget creation"""
    
    def test_create_widget_success(self, client, mock_agent_registry):
        """Test successful widget creation"""
        # Clear widget store
        widget_store.clear()
        
        response = client.post('/widget/api/create',
            json={
                'agent_id': 'test-agent',
                'name': 'My Widget',
                'theme': 'light',
                'height': '600px',
                'width': '100%'
            },
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'widget_id' in data
        assert 'widget_api_key' in data
        assert 'embed_code' in data
        assert 'embed_url' in data
        assert data['widget']['name'] == 'My Widget'
    
    def test_create_widget_missing_agent_id(self, client):
        """Test widget creation without agent_id"""
        response = client.post('/widget/api/create',
            json={'name': 'My Widget'},
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'agent_id' in data['error'].lower()
    
    def test_create_widget_missing_name(self, client):
        """Test widget creation without name"""
        response = client.post('/widget/api/create',
            json={'agent_id': 'test-agent'},
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'name' in data['error'].lower()
    
    def test_create_widget_missing_api_key(self, client):
        """Test widget creation without API key"""
        response = client.post('/widget/api/create',
            json={
                'agent_id': 'test-agent',
                'name': 'My Widget'
            }
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'api key' in data['error'].lower()
    
    def test_create_widget_invalid_api_key(self, client, mock_agent_registry):
        """Test widget creation with invalid API key"""
        mock_agent_registry.get_agent.return_value = None
        
        response = client.post('/widget/api/create',
            json={
                'agent_id': 'test-agent',
                'name': 'My Widget'
            },
            headers={'X-API-Key': 'invalid-key'}
        )
        
        assert response.status_code == 401
    
    def test_create_widget_with_custom_css(self, client, mock_agent_registry):
        """Test widget creation with custom CSS"""
        widget_store.clear()
        
        response = client.post('/widget/api/create',
            json={
                'agent_id': 'test-agent',
                'name': 'Custom Widget',
                'theme': 'light',
                'custom_css': ':root { --widget-primary-color: #ff0000; }'
            },
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        widget_id = data['widget_id']
        assert widget_store[widget_id]['custom_css'] == ':root { --widget-primary-color: #ff0000; }'
    
    def test_create_widget_with_custom_js(self, client, mock_agent_registry):
        """Test widget creation with custom JavaScript"""
        widget_store.clear()
        
        response = client.post('/widget/api/create',
            json={
                'agent_id': 'test-agent',
                'name': 'Custom Widget',
                'custom_js': 'console.log("custom");'
            },
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        widget_id = data['widget_id']
        assert widget_store[widget_id]['custom_js'] == 'console.log("custom");'


class TestWidgetManagement:
    """Tests for widget management operations"""
    
    def test_list_widgets(self, client, mock_agent_registry, sample_widget):
        """Test listing widgets"""
        widget_id, widget_data = sample_widget
        
        response = client.get('/widget/api/list',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'widgets' in data
        assert len(data['widgets']) > 0
        assert data['widgets'][0]['widget_id'] == widget_id
    
    def test_list_widgets_invalid_api_key(self, client):
        """Test listing widgets with invalid API key"""
        response = client.get('/widget/api/list',
            headers={'X-API-Key': 'invalid-key'}
        )
        
        assert response.status_code == 401
    
    def test_get_widget(self, client, mock_agent_registry, sample_widget):
        """Test getting widget details"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/api/{widget_id}',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['widget']['widget_id'] == widget_id
        assert data['widget']['name'] == widget_data['name']
        # API key should not be in response
        assert 'api_key' not in data['widget']
    
    def test_get_widget_not_found(self, client, mock_agent_registry):
        """Test getting non-existent widget"""
        response = client.get('/widget/api/non-existent',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 404
    
    def test_update_widget(self, client, mock_agent_registry, sample_widget):
        """Test updating widget"""
        widget_id, widget_data = sample_widget
        
        response = client.put(f'/widget/api/{widget_id}',
            json={
                'name': 'Updated Widget',
                'theme': 'dark',
                'height': '700px'
            },
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert widget_store[widget_id]['name'] == 'Updated Widget'
        assert widget_store[widget_id]['theme'] == 'dark'
        assert widget_store[widget_id]['height'] == '700px'
    
    def test_delete_widget(self, client, mock_agent_registry, sample_widget):
        """Test deleting widget"""
        widget_id, widget_data = sample_widget
        
        response = client.delete(f'/widget/api/{widget_id}',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert widget_id not in widget_store
    
    def test_delete_widget_not_found(self, client, mock_agent_registry):
        """Test deleting non-existent widget"""
        response = client.delete('/widget/api/non-existent',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 404


class TestEmbedCode:
    """Tests for embed code generation"""
    
    def test_get_embed_code(self, client, mock_agent_registry, sample_widget):
        """Test getting embed code"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/api/{widget_id}/embed-code',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'embed_code' in data
        assert 'embed_url' in data
        assert widget_id in data['embed_code']
        assert 'iframe' in data['embed_code']
    
    def test_get_embed_code_with_theme(self, client, mock_agent_registry, sample_widget):
        """Test getting embed code with theme parameter"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/api/{widget_id}/embed-code?theme=dark&height=700px',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'theme=dark' in data['embed_code']
        assert 'height="700px"' in data['embed_code']


class TestWidgetQuery:
    """Tests for widget query execution"""
    
    def test_widget_query_success(self, client, mock_agent_registry, mock_ai_agent_manager, 
                                   mock_nl_converter, sample_widget):
        """Test successful widget query"""
        widget_id, widget_data = sample_widget
        
        response = client.post('/widget/api/query',
            json={'query': 'What are the top products?'},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data
        assert widget_store[widget_id]['usage_count'] == 1
        assert 'last_used' in widget_store[widget_id]
    
    def test_widget_query_missing_key(self, client):
        """Test widget query without API key"""
        response = client.post('/widget/api/query',
            json={'query': 'What are the top products?'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'api key' in data['error'].lower()
    
    def test_widget_query_invalid_key(self, client):
        """Test widget query with invalid API key"""
        response = client.post('/widget/api/query',
            json={'query': 'What are the top products?'},
            headers={'X-Widget-Key': 'invalid-key'}
        )
        
        assert response.status_code == 401
    
    def test_widget_query_missing_query(self, client, sample_widget):
        """Test widget query without query parameter"""
        widget_id, widget_data = sample_widget
        
        response = client.post('/widget/api/query',
            json={},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'query' in data['error'].lower()
    
    def test_widget_query_nl_conversion_error(self, client, mock_agent_registry, 
                                              mock_ai_agent_manager, mock_nl_converter, 
                                              sample_widget):
        """Test widget query with NL conversion error"""
        widget_id, widget_data = sample_widget
        mock_nl_converter.convert_to_sql.return_value = {
            'sql': None,
            'error': 'Conversion failed'
        }
        
        response = client.post('/widget/api/query',
            json={'query': 'Invalid query'},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data


class TestWidgetEmbedding:
    """Tests for widget embedding"""
    
    def test_embed_widget_success(self, client, mock_agent_registry, sample_widget):
        """Test embedding widget"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/embed/{widget_id}')
        
        assert response.status_code == 200
        assert b'widget-container' in response.data
        assert b'query-form' in response.data
        # Check iframe-friendly headers
        assert 'X-Frame-Options' in response.headers or 'ALLOWALL' in str(response.headers)
    
    def test_embed_widget_with_theme(self, client, mock_agent_registry, sample_widget):
        """Test embedding widget with theme"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/embed/{widget_id}?theme=dark')
        
        assert response.status_code == 200
        assert b'dark' in response.data.lower() or b'--widget-bg-color: #1a1a1a' in response.data
    
    def test_embed_widget_not_found(self, client):
        """Test embedding non-existent widget"""
        response = client.get('/widget/embed/non-existent')
        
        assert response.status_code == 404
    
    def test_embed_widget_agent_not_found(self, client, mock_agent_registry):
        """Test embedding widget with non-existent agent"""
        widget_id = 'test-widget'
        widget_store[widget_id] = {
            'widget_id': widget_id,
            'agent_id': 'non-existent-agent',
            'api_key': 'test-key'
        }
        mock_agent_registry.get_agent.return_value = None
        
        response = client.get(f'/widget/embed/{widget_id}')
        
        assert response.status_code == 404


class TestAPIKeyManagement:
    """Tests for API key management"""
    
    def test_regenerate_widget_key(self, client, mock_agent_registry, sample_widget):
        """Test regenerating widget API key"""
        widget_id, widget_data = sample_widget
        old_key = widget_data['api_key']
        
        response = client.post(f'/widget/api/{widget_id}/regenerate-key',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'widget_api_key' in data
        assert data['widget_api_key'] != old_key
        assert widget_store[widget_id]['api_key'] == data['widget_api_key']
    
    def test_regenerate_key_invalid_api_key(self, client, sample_widget):
        """Test regenerating key with invalid API key"""
        widget_id, widget_data = sample_widget
        
        response = client.post(f'/widget/api/{widget_id}/regenerate-key',
            headers={'X-API-Key': 'invalid-key'}
        )
        
        assert response.status_code == 401
    
    def test_regenerate_key_widget_not_found(self, client, mock_agent_registry):
        """Test regenerating key for non-existent widget"""
        response = client.post('/widget/api/non-existent/regenerate-key',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        
        assert response.status_code == 404


class TestWidgetThemes:
    """Tests for widget theme customization"""
    
    def test_widget_light_theme(self, client, mock_agent_registry, sample_widget):
        """Test light theme"""
        widget_id, widget_data = sample_widget
        widget_store[widget_id]['theme'] = 'light'
        
        response = client.get(f'/widget/embed/{widget_id}?theme=light')
        
        assert response.status_code == 200
        # Check for light theme CSS variables
        assert b'--widget-bg-color: #ffffff' in response.data or b'light' in response.data.lower()
    
    def test_widget_dark_theme(self, client, mock_agent_registry, sample_widget):
        """Test dark theme"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/embed/{widget_id}?theme=dark')
        
        assert response.status_code == 200
        # Check for dark theme CSS variables
        assert b'--widget-bg-color: #1a1a1a' in response.data or b'dark' in response.data.lower()
    
    def test_widget_minimal_theme(self, client, mock_agent_registry, sample_widget):
        """Test minimal theme"""
        widget_id, widget_data = sample_widget
        
        response = client.get(f'/widget/embed/{widget_id}?theme=minimal')
        
        assert response.status_code == 200
    
    def test_widget_custom_css(self, client, mock_agent_registry):
        """Test widget with custom CSS"""
        widget_id = 'custom-widget'
        widget_store[widget_id] = {
            'widget_id': widget_id,
            'agent_id': 'test-agent',
            'api_key': 'test-key',
            'custom_css': ':root { --widget-primary-color: #ff0000; }'
        }
        
        response = client.get(f'/widget/embed/{widget_id}')
        
        assert response.status_code == 200
        assert b'--widget-primary-color: #ff0000' in response.data


class TestWidgetSecurity:
    """Tests for widget security"""
    
    def test_widget_key_validation(self):
        """Test widget key validation"""
        widget_id = 'test-widget'
        widget_key = generate_widget_key()
        widget_store[widget_id] = {
            'widget_id': widget_id,
            'api_key': widget_key
        }
        
        result = validate_widget_key(widget_key)
        assert result is not None
        assert result['widget_id'] == widget_id
        
        invalid_result = validate_widget_key('invalid-key')
        assert invalid_result is None
    
    def test_widget_query_requires_widget_key(self, client):
        """Test that widget queries require widget key"""
        response = client.post('/widget/api/query',
            json={'query': 'test query'}
        )
        
        assert response.status_code == 401
    
    def test_widget_management_requires_agent_key(self, client):
        """Test that widget management requires agent key"""
        response = client.post('/widget/api/create',
            json={'agent_id': 'test', 'name': 'test'}
        )
        
        assert response.status_code == 401
    
    def test_widget_cross_agent_access(self, client, mock_agent_registry):
        """Test that widgets can't access other agents"""
        widget_id = 'widget-1'
        widget_store[widget_id] = {
            'widget_id': widget_id,
            'agent_id': 'agent-1',
            'api_key': 'widget-key-1'
        }
        
        # Try to use widget key for different agent
        mock_agent_registry.get_agent.return_value = {
            'agent_id': 'agent-2',
            'api_key': 'agent-2-key'
        }
        
        response = client.get(f'/widget/api/{widget_id}',
            headers={'X-API-Key': 'agent-2-key'}
        )
        
        # Should fail because agent-2-key doesn't match agent-1
        assert response.status_code == 401


class TestWidgetUsageTracking:
    """Tests for widget usage tracking"""
    
    def test_widget_usage_count_increments(self, client, mock_agent_registry, 
                                          mock_ai_agent_manager, mock_nl_converter, 
                                          sample_widget):
        """Test that widget usage count increments"""
        widget_id, widget_data = sample_widget
        initial_count = widget_data['usage_count']
        
        response = client.post('/widget/api/query',
            json={'query': 'test query'},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 200
        assert widget_store[widget_id]['usage_count'] == initial_count + 1
    
    def test_widget_last_used_timestamp(self, client, mock_agent_registry,
                                       mock_ai_agent_manager, mock_nl_converter,
                                       sample_widget):
        """Test that last_used timestamp is updated"""
        widget_id, widget_data = sample_widget
        
        response = client.post('/widget/api/query',
            json={'query': 'test query'},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 200
        assert 'last_used' in widget_store[widget_id]
        assert widget_store[widget_id]['last_used'] is not None


class TestWidgetErrorHandling:
    """Tests for widget error handling"""
    
    def test_widget_query_database_error(self, client, mock_agent_registry,
                                        mock_ai_agent_manager, mock_nl_converter,
                                        sample_widget):
        """Test widget query with database error"""
        widget_id, widget_data = sample_widget
        mock_agent_registry.get_database_connector.return_value = None
        
        response = client.post('/widget/api/query',
            json={'query': 'test query'},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_widget_query_execution_error(self, client, mock_agent_registry,
                                         mock_ai_agent_manager, mock_nl_converter,
                                         sample_widget):
        """Test widget query with execution error"""
        widget_id, widget_data = sample_widget
        mock_ai_agent_manager.execute_query.side_effect = Exception('Database error')
        
        response = client.post('/widget/api/query',
            json={'query': 'test query'},
            headers={'X-Widget-Key': 'test-widget-api-key'}
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data


class TestWidgetIntegration:
    """Integration tests for widgets"""
    
    def test_full_widget_lifecycle(self, client, mock_agent_registry, 
                                   mock_ai_agent_manager, mock_nl_converter):
        """Test complete widget lifecycle"""
        widget_store.clear()
        
        # 1. Create widget
        create_response = client.post('/widget/api/create',
            json={
                'agent_id': 'test-agent',
                'name': 'Lifecycle Widget',
                'theme': 'light'
            },
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        assert create_response.status_code == 201
        widget_data = json.loads(create_response.data)
        widget_id = widget_data['widget_id']
        widget_key = widget_data['widget_api_key']
        
        # 2. Get widget
        get_response = client.get(f'/widget/api/{widget_id}',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        assert get_response.status_code == 200
        
        # 3. Get embed code
        embed_response = client.get(f'/widget/api/{widget_id}/embed-code',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        assert embed_response.status_code == 200
        
        # 4. Embed widget
        embed_page = client.get(f'/widget/embed/{widget_id}')
        assert embed_page.status_code == 200
        
        # 5. Execute query
        query_response = client.post('/widget/api/query',
            json={'query': 'What are the top products?'},
            headers={'X-Widget-Key': widget_key}
        )
        assert query_response.status_code == 200
        
        # 6. Update widget
        update_response = client.put(f'/widget/api/{widget_id}',
            json={'theme': 'dark'},
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        assert update_response.status_code == 200
        
        # 7. Delete widget
        delete_response = client.delete(f'/widget/api/{widget_id}',
            headers={'X-API-Key': 'test-agent-api-key'}
        )
        assert delete_response.status_code == 200
        assert widget_id not in widget_store


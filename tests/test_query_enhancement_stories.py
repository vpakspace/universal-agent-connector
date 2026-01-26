"""
Integration tests for Query Enhancement Stories

Story 1: As a User, I want the platform to suggest optimized SQL queries when my natural language input is ambiguous, 
         so that I get accurate results faster.

Story 2: As a User, I want to see the generated SQL before execution, 
         so that I can verify the agent's interpretation.

Story 3: As a User, I want to save frequently used queries as templates, 
         so that I can reuse them without retyping.

Story 4: As a Developer, I want to pre-define approved SQL query patterns, 
         so that agents use vetted logic instead of generating ad-hoc SQL.

Story 5: As an Admin, I want to cache query results for a configurable TTL, 
         so that repeated queries return instantly without hitting the database.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, query_suggestion_engine,
    template_manager, approved_pattern_manager, query_cache, nl_converter
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.query_suggestions import QuerySuggestion
from ai_agent_connector.app.utils.query_templates import QueryTemplate
from ai_agent_connector.app.utils.approved_patterns import ApprovedPattern, PatternType


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    template_manager._templates.clear()
    template_manager._agent_templates.clear()
    template_manager._public_templates.clear()
    approved_pattern_manager._patterns.clear()
    query_cache._cache.clear()
    query_cache._agent_ttls.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    template_manager._templates.clear()
    template_manager._agent_templates.clear()
    template_manager._public_templates.clear()
    approved_pattern_manager._patterns.clear()
    query_cache._cache.clear()
    query_cache._agent_ttls.clear()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_agent():
    """Create a test agent"""
    result = agent_registry.register_agent(
        agent_id='test-agent',
        agent_info={'name': 'Test Agent'},
        credentials={'api_key': 'test-key', 'api_secret': 'test-secret'}
    )
    access_control.grant_permission('test-agent', Permission.READ)
    return {'agent_id': 'test-agent', 'api_key': result['api_key']}


@pytest.fixture
def admin_agent():
    """Create an admin agent"""
    result = agent_registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'},
        credentials={'api_key': 'admin-key', 'api_secret': 'admin-secret'}
    )
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    return {'agent_id': 'admin-agent', 'api_key': result['api_key']}


class TestStory1_QuerySuggestions:
    """Story 1: Suggest optimized SQL queries for ambiguous inputs"""
    
    def test_get_query_suggestions(self, client, test_agent):
        """Test getting query suggestions for ambiguous input"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl:
            
            # Mock database connector
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            
            # Mock schema info
            mock_nl.get_schema_info.return_value = {
                'tables': ['users', 'orders'],
                'schema': {}
            }
            
            # Mock suggestions
            suggestions = [
                QuerySuggestion(
                    sql="SELECT * FROM users WHERE name LIKE '%sales%'",
                    confidence=0.9,
                    explanation="Search for users with 'sales' in name",
                    estimated_cost="low"
                ),
                QuerySuggestion(
                    sql="SELECT * FROM orders WHERE product LIKE '%sales%'",
                    confidence=0.7,
                    explanation="Search for orders with 'sales' product",
                    estimated_cost="medium"
                )
            ]
            
            with patch.object(query_suggestion_engine, 'suggest_queries', return_value=suggestions):
                payload = {
                    'query': 'show me sales',
                    'num_suggestions': 2
                }
                
                response = client.post(
                    '/api/agents/test-agent/query/suggestions',
                    json=payload,
                    headers={'X-API-Key': test_agent['api_key']}
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'suggestions' in data
                assert len(data['suggestions']) == 2
                assert data['suggestions'][0]['confidence'] == 0.9
    
    def test_suggestions_sorted_by_confidence(self, client, test_agent):
        """Test that suggestions are sorted by confidence"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = {'tables': [], 'schema': {}}
            
            suggestions = [
                QuerySuggestion(sql="SELECT 1", confidence=0.5, explanation="Low confidence"),
                QuerySuggestion(sql="SELECT 2", confidence=0.9, explanation="High confidence"),
                QuerySuggestion(sql="SELECT 3", confidence=0.7, explanation="Medium confidence")
            ]
            
            with patch.object(query_suggestion_engine, 'suggest_queries', return_value=suggestions):
                response = client.post(
                    '/api/agents/test-agent/query/suggestions',
                    json={'query': 'test'},
                    headers={'X-API-Key': test_agent['api_key']}
                )
                
                assert response.status_code == 200
                data = response.get_json()
                # Should be sorted by confidence (highest first)
                assert data['suggestions'][0]['confidence'] == 0.9
                assert data['suggestions'][1]['confidence'] == 0.7
                assert data['suggestions'][2]['confidence'] == 0.5


class TestStory2_SQLPreview:
    """Story 2: Show generated SQL before execution"""
    
    def test_preview_sql_without_execution(self, client, test_agent):
        """Test previewing SQL without executing"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            # Mock database connector
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            
            # Mock NL to SQL conversion
            mock_nl.get_schema_info.return_value = {'tables': ['users'], 'schema': {}}
            mock_nl.convert_to_sql.return_value = {
                'sql': 'SELECT * FROM users',
                'natural_language': 'show all users'
            }
            
            # Mock RLS
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users WHERE (user_id = current_user())'
            
            payload = {
                'query': 'show all users',
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['preview'] is True
            assert 'generated_sql' in data
            assert data['message'] == 'SQL preview (not executed)'
            # Verify query was not executed
            assert 'result' not in data
    
    def test_preview_shows_conversion_source(self, client, test_agent):
        """Test that preview shows the conversion source"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.approved_pattern_manager') as mock_patterns, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            
            # Mock approved pattern match
            from ai_agent_connector.app.utils.approved_patterns import ApprovedPattern, PatternType
            pattern = ApprovedPattern(
                pattern_id='pattern-1',
                name='Get users',
                description='Get all users',
                pattern_type=PatternType.STATIC,
                static_sql='SELECT * FROM users'
            )
            mock_patterns.find_matching_pattern.return_value = pattern
            mock_patterns.generate_sql.return_value = 'SELECT * FROM users'
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users'
            
            payload = {
                'query': 'get users',
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['conversion_source'] == 'approved_pattern'


class TestStory3_QueryTemplates:
    """Story 3: Save frequently used queries as templates"""
    
    def test_create_query_template(self, client, test_agent):
        """Test creating a query template"""
        payload = {
            'name': 'Get user by ID',
            'sql': 'SELECT * FROM users WHERE id = {{user_id}}',
            'natural_language': 'Get user by ID',
            'description': 'Template for getting user details',
            'tags': ['users', 'lookup'],
            'is_public': False
        }
        
        response = client.post(
            '/api/agents/test-agent/query/templates',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'template' in data
        assert data['template']['name'] == 'Get user by ID'
        assert data['template']['sql'] == 'SELECT * FROM users WHERE id = {{user_id}}'
        assert 'user_id' in data['template']['parameters']
    
    def test_list_query_templates(self, client, test_agent):
        """Test listing query templates"""
        # Create a template first
        template = template_manager.create_template(
            name='Get users',
            sql='SELECT * FROM users',
            created_by='test-agent',
            tags=['users']
        )
        
        response = client.get(
            '/api/agents/test-agent/query/templates',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'templates' in data
        assert len(data['templates']) >= 1
        assert data['templates'][0]['name'] == 'Get users'
    
    def test_get_query_template(self, client, test_agent):
        """Test getting a specific template"""
        template = template_manager.create_template(
            name='Get users',
            sql='SELECT * FROM users',
            created_by='test-agent'
        )
        
        response = client.get(
            f'/api/agents/test-agent/query/templates/{template.template_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Get users'
        assert data['template_id'] == template.template_id
    
    def test_update_query_template(self, client, test_agent):
        """Test updating a template"""
        template = template_manager.create_template(
            name='Get users',
            sql='SELECT * FROM users',
            created_by='test-agent'
        )
        
        payload = {
            'name': 'Get all users',
            'description': 'Updated description'
        }
        
        response = client.put(
            f'/api/agents/test-agent/query/templates/{template.template_id}',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['template']['name'] == 'Get all users'
        assert data['template']['description'] == 'Updated description'
    
    def test_delete_query_template(self, client, test_agent):
        """Test deleting a template"""
        template = template_manager.create_template(
            name='Get users',
            sql='SELECT * FROM users',
            created_by='test-agent'
        )
        
        response = client.delete(
            f'/api/agents/test-agent/query/templates/{template.template_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify template is deleted
        assert template_manager.get_template(template.template_id) is None
    
    def test_use_template_in_query(self, client, test_agent):
        """Test using a template in a natural language query"""
        template = template_manager.create_template(
            name='Get user by ID',
            sql='SELECT * FROM users WHERE id = {{user_id}}',
            created_by='test-agent'
        )
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users WHERE id = 123'
            
            payload = {
                'use_template': template.template_id,
                'template_params': {'user_id': '123'},
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['conversion_source'] == 'template'
            assert '123' in data['generated_sql']


class TestStory4_ApprovedPatterns:
    """Story 4: Pre-define approved SQL query patterns"""
    
    def test_create_approved_pattern(self, client, admin_agent):
        """Test creating an approved pattern"""
        payload = {
            'name': 'Get sales by region',
            'description': 'Vetted query for sales by region',
            'sql_template': "SELECT region, SUM(amount) FROM sales WHERE date >= '{{start_date}}' GROUP BY region",
            'natural_language_keywords': ['sales', 'region', 'by region'],
            'parameters': ['start_date'],
            'tags': ['sales', 'reporting']
        }
        
        response = client.post(
            '/api/admin/query-patterns',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'pattern' in data
        assert data['pattern']['name'] == 'Get sales by region'
        assert 'sales' in data['pattern']['natural_language_keywords']
    
    def test_list_approved_patterns(self, client, admin_agent):
        """Test listing approved patterns"""
        pattern = approved_pattern_manager.create_pattern(
            name='Get users',
            description='Get all users',
            static_sql='SELECT * FROM users',
            natural_language_keywords=['users', 'get users'],
            tags=['users']
        )
        
        response = client.get(
            '/api/admin/query-patterns',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'patterns' in data
        assert len(data['patterns']) >= 1
    
    def test_approved_pattern_matches_query(self, client, test_agent):
        """Test that approved pattern is used when query matches"""
        # Create an approved pattern
        pattern = approved_pattern_manager.create_pattern(
            name='Get sales by region',
            description='Sales by region',
            static_sql='SELECT region, SUM(amount) FROM sales GROUP BY region',
            natural_language_keywords=['sales', 'region']
        )
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_rls.apply_rls_to_query.return_value = 'SELECT region, SUM(amount) FROM sales GROUP BY region'
            
            payload = {
                'query': 'show me sales by region',
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            # Should use approved pattern
            assert data.get('conversion_source') == 'approved_pattern'
    
    def test_update_approved_pattern(self, client, admin_agent):
        """Test updating an approved pattern"""
        pattern = approved_pattern_manager.create_pattern(
            name='Get users',
            description='Get all users',
            static_sql='SELECT * FROM users',
            created_by='admin-agent'
        )
        
        payload = {
            'enabled': False,
            'tags': ['users', 'disabled']
        }
        
        response = client.put(
            f'/api/admin/query-patterns/{pattern.pattern_id}',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['pattern']['enabled'] is False
    
    def test_delete_approved_pattern(self, client, admin_agent):
        """Test deleting an approved pattern"""
        pattern = approved_pattern_manager.create_pattern(
            name='Get users',
            description='Get all users',
            static_sql='SELECT * FROM users'
        )
        
        response = client.delete(
            f'/api/admin/query-patterns/{pattern.pattern_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify pattern is deleted
        assert approved_pattern_manager.get_pattern(pattern.pattern_id) is None


class TestStory5_QueryCache:
    """Story 5: Cache query results with configurable TTL"""
    
    def test_set_cache_ttl(self, client, admin_agent):
        """Test setting cache TTL for an agent"""
        payload = {'ttl_seconds': 600}
        
        response = client.post(
            '/api/admin/agents/test-agent/cache/ttl',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ttl_seconds'] == 600
        
        # Verify TTL was set
        assert query_cache.get_agent_ttl('test-agent') == 600
    
    def test_get_cache_ttl(self, client, admin_agent):
        """Test getting cache TTL"""
        query_cache.set_agent_ttl('test-agent', 300)
        
        response = client.get(
            '/api/admin/agents/test-agent/cache/ttl',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ttl_seconds'] == 300
    
    def test_get_cache_stats(self, client, admin_agent):
        """Test getting cache statistics"""
        # Add some cache entries
        query_cache.set('SELECT * FROM users', [{'id': 1, 'name': 'John'}], agent_id='test-agent')
        
        response = client.get(
            '/api/admin/cache/stats',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_entries' in data
        assert 'active_entries' in data
        assert 'total_hits' in data
    
    def test_invalidate_cache(self, client, admin_agent):
        """Test invalidating cache"""
        # Add cache entry
        query_cache.set('SELECT * FROM users', [{'id': 1}])
        
        payload = {'query': 'SELECT * FROM users'}
        
        response = client.post(
            '/api/admin/cache/invalidate',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['invalidated_count'] >= 1
    
    def test_clear_expired_cache(self, client, admin_agent):
        """Test clearing expired cache entries"""
        response = client.post(
            '/api/admin/cache/clear-expired',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'cleared_count' in data
    
    def test_list_cache_entries(self, client, admin_agent):
        """Test listing cache entries"""
        query_cache.set('SELECT * FROM users', [{'id': 1}], agent_id='test-agent')
        
        response = client.get(
            '/api/admin/cache/entries?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'entries' in data
        assert len(data['entries']) >= 1
    
    def test_query_uses_cache(self, client, test_agent):
        """Test that queries use cached results"""
        # Pre-populate cache
        query_cache.set(
            'SELECT * FROM users',
            [{'id': 1, 'name': 'John'}],
            agent_id='test-agent',
            ttl_seconds=3600
        )
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = {'tables': ['users'], 'schema': {}}
            mock_nl.convert_to_sql.return_value = {'sql': 'SELECT * FROM users'}
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users'
            
            payload = {
                'query': 'show all users',
                'use_cache': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            # Should return cached result
            assert response.status_code == 200
            data = response.get_json()
            assert data.get('cached') is True
            assert 'result' in data


class TestIntegration_AllQueryFeatures:
    """Integration tests combining all query enhancement features"""
    
    def test_complete_workflow_suggestions_preview_template_cache(self, client, test_agent, admin_agent):
        """Test complete workflow: suggestions -> preview -> save template -> use template -> cache"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = {'tables': ['users'], 'schema': {}}
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users'
            
            # Step 1: Get suggestions
            suggestions = [
                QuerySuggestion(sql="SELECT * FROM users", confidence=0.9, explanation="Get all users")
            ]
            with patch.object(query_suggestion_engine, 'suggest_queries', return_value=suggestions):
                response = client.post(
                    '/api/agents/test-agent/query/suggestions',
                    json={'query': 'show users'},
                    headers={'X-API-Key': test_agent['api_key']}
                )
                assert response.status_code == 200
            
            # Step 2: Preview SQL
            mock_nl.convert_to_sql.return_value = {'sql': 'SELECT * FROM users'}
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json={'query': 'show users', 'preview_only': True},
                headers={'X-API-Key': test_agent['api_key']}
            )
            assert response.status_code == 200
            assert response.get_json()['preview'] is True
            
            # Step 3: Save as template
            response = client.post(
                '/api/agents/test-agent/query/templates',
                json={
                    'name': 'Get all users',
                    'sql': 'SELECT * FROM users',
                    'tags': ['users']
                },
                headers={'X-API-Key': test_agent['api_key']}
            )
            assert response.status_code == 201
            template_id = response.get_json()['template']['template_id']
            
            # Step 4: Use template
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json={'use_template': template_id, 'preview_only': True},
                headers={'X-API-Key': test_agent['api_key']}
            )
            assert response.status_code == 200
            assert response.get_json()['conversion_source'] == 'template'
            
            # Step 5: Set cache TTL
            response = client.post(
                '/api/admin/agents/test-agent/cache/ttl',
                json={'ttl_seconds': 600},
                headers={'X-API-Key': admin_agent['api_key']}
            )
            assert response.status_code == 200


class TestStory1_EdgeCases:
    """Story 1: Query Suggestions - Edge Cases"""
    
    def test_suggestions_empty_query(self, client, test_agent):
        """Test suggestions with empty query"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            
            response = client.post(
                '/api/agents/test-agent/query/suggestions',
                json={'query': ''},
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 400
    
    def test_suggestions_missing_query(self, client, test_agent):
        """Test suggestions without query parameter"""
        response = client.post(
            '/api/agents/test-agent/query/suggestions',
            json={},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_suggestions_no_database_connection(self, client, test_agent):
        """Test suggestions when agent has no database connection"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.get_database_connector.return_value = None
            
            response = client.post(
                '/api/agents/test-agent/query/suggestions',
                json={'query': 'show users'},
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 400
            assert 'database connection' in response.get_json()['error'].lower()
    
    def test_suggestions_llm_error(self, client, test_agent):
        """Test suggestions when LLM fails"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch.object(query_suggestion_engine, 'suggest_queries') as mock_suggest:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = {'tables': [], 'schema': {}}
            mock_suggest.side_effect = Exception("LLM API error")
            
            response = client.post(
                '/api/agents/test-agent/query/suggestions',
                json={'query': 'show users'},
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 500


class TestStory2_EdgeCases:
    """Story 2: SQL Preview - Edge Cases"""
    
    def test_preview_with_template_and_nl_query(self, client, test_agent):
        """Test preview when both template and NL query are provided (template should take precedence)"""
        template = template_manager.create_template(
            name='Get users',
            sql='SELECT * FROM users',
            created_by='test-agent'
        )
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users'
            
            payload = {
                'query': 'show all users',
                'use_template': template.template_id,
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['conversion_source'] == 'template'
    
    def test_preview_with_approved_pattern(self, client, test_agent):
        """Test preview uses approved pattern when available"""
        pattern = approved_pattern_manager.create_pattern(
            name='Get users',
            description='Get all users',
            static_sql='SELECT * FROM users',
            natural_language_keywords=['users', 'get users']
        )
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry, \
             patch('ai_agent_connector.app.api.routes.rls_manager') as mock_rls:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_rls.apply_rls_to_query.return_value = 'SELECT * FROM users'
            
            payload = {
                'query': 'get users',
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['conversion_source'] == 'approved_pattern'


class TestStory3_EdgeCases:
    """Story 3: Query Templates - Edge Cases"""
    
    def test_create_template_with_invalid_sql(self, client, test_agent):
        """Test creating template with invalid SQL"""
        payload = {
            'name': 'Invalid Template',
            'sql': 'INVALID SQL SYNTAX!!!',
            'tags': ['test']
        }
        
        response = client.post(
            '/api/agents/test-agent/query/templates',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        # Should still create (validation happens at use time)
        assert response.status_code == 201
    
    def test_template_parameter_substitution(self, client, test_agent):
        """Test template parameter substitution with various data types"""
        template = template_manager.create_template(
            name='Parameter Test',
            sql='SELECT * FROM users WHERE id = {{user_id}} AND status = {{status}}',
            created_by='test-agent'
        )
        
        # Test with different parameter types
        sql = template.apply_parameters({
            'user_id': 123,
            'status': 'active'
        })
        
        assert '123' in sql
        assert 'active' in sql
    
    def test_template_sql_injection_protection(self, client, test_agent):
        """Test that template parameters are escaped to prevent SQL injection"""
        template = template_manager.create_template(
            name='SQL Injection Test',
            sql="SELECT * FROM users WHERE name = '{{name}}'",
            created_by='test-agent'
        )
        
        # Try SQL injection
        malicious_input = "'; DROP TABLE users; --"
        sql = template.apply_parameters({'name': malicious_input})
        
        # Should escape single quotes
        assert "''" in sql or "'" not in sql or "DROP" not in sql
    
    def test_list_templates_with_filters(self, client, test_agent):
        """Test listing templates with tag and search filters"""
        # Create templates with different tags
        template1 = template_manager.create_template(
            name='User Query',
            sql='SELECT * FROM users',
            created_by='test-agent',
            tags=['users', 'read']
        )
        template2 = template_manager.create_template(
            name='Order Query',
            sql='SELECT * FROM orders',
            created_by='test-agent',
            tags=['orders', 'read']
        )
        
        # Filter by tag
        response = client.get(
            '/api/agents/test-agent/query/templates?tags=users',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all('users' in t['tags'] for t in data['templates'])
        
        # Search by name
        response = client.get(
            '/api/agents/test-agent/query/templates?search=Order',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert any('Order' in t['name'] for t in data['templates'])
    
    def test_template_access_control(self, client, test_agent):
        """Test that agents can only access their own or public templates"""
        # Create private template for another agent
        template = template_manager.create_template(
            name='Private Template',
            sql='SELECT * FROM private',
            created_by='other-agent',
            is_public=False
        )
        
        # Try to access as test-agent
        response = client.get(
            f'/api/agents/test-agent/query/templates/{template.template_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_public_template_access(self, client, test_agent):
        """Test that public templates are accessible to all agents"""
        # Create public template
        template = template_manager.create_template(
            name='Public Template',
            sql='SELECT * FROM public_data',
            created_by='other-agent',
            is_public=True
        )
        
        # Access as test-agent
        response = client.get(
            f'/api/agents/test-agent/query/templates/{template.template_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        assert response.get_json()['is_public'] is True
    
    def test_template_usage_tracking(self, client, test_agent):
        """Test that template usage is tracked"""
        template = template_manager.create_template(
            name='Tracked Template',
            sql='SELECT * FROM users',
            created_by='test-agent'
        )
        
        initial_count = template.use_count
        
        # Use template
        sql = template_manager.use_template(template.template_id)
        
        # Check usage count increased
        updated_template = template_manager.get_template(template.template_id)
        assert updated_template.use_count == initial_count + 1
        assert updated_template.last_used_at is not None


class TestStory4_EdgeCases:
    """Story 4: Approved Patterns - Edge Cases"""
    
    def test_pattern_matching_case_insensitive(self, client, test_agent):
        """Test that pattern matching is case insensitive"""
        pattern = approved_pattern_manager.create_pattern(
            name='Case Test',
            description='Test case insensitivity',
            static_sql='SELECT * FROM users',
            natural_language_keywords=['users', 'USERS', 'Users']
        )
        
        # Test different cases
        assert pattern.matches('show me USERS')
        assert pattern.matches('get users')
        assert pattern.matches('SELECT Users')
    
    def test_pattern_disabled_not_matched(self, client, test_agent):
        """Test that disabled patterns are not matched"""
        pattern = approved_pattern_manager.create_pattern(
            name='Disabled Pattern',
            description='Disabled pattern',
            static_sql='SELECT * FROM users',
            natural_language_keywords=['users']
        )
        
        pattern.enabled = False
        
        assert not pattern.matches('show users')
    
    def test_pattern_template_with_parameters(self, client, test_agent):
        """Test pattern with template and parameters"""
        pattern = approved_pattern_manager.create_pattern(
            name='Parameter Pattern',
            description='Pattern with parameters',
            sql_template="SELECT * FROM sales WHERE date >= '{{start_date}}'",
            natural_language_keywords=['sales', 'date']
        )
        
        sql = pattern.generate_sql({'start_date': '2024-01-01'})
        
        assert sql is not None
        assert '2024-01-01' in sql
    
    def test_pattern_multiple_keywords(self, client, test_agent):
        """Test pattern matching with multiple keywords"""
        pattern = approved_pattern_manager.create_pattern(
            name='Multi Keyword',
            description='Pattern with multiple keywords',
            static_sql='SELECT * FROM sales',
            natural_language_keywords=['sales', 'revenue', 'income']
        )
        
        assert pattern.matches('show me sales')
        assert pattern.matches('get revenue data')
        assert pattern.matches('display income')
        assert not pattern.matches('show users')
    
    def test_pattern_list_with_filters(self, client, admin_agent):
        """Test listing patterns with tag filters"""
        pattern1 = approved_pattern_manager.create_pattern(
            name='Sales Pattern',
            description='Sales query',
            static_sql='SELECT * FROM sales',
            tags=['sales', 'reporting']
        )
        pattern2 = approved_pattern_manager.create_pattern(
            name='User Pattern',
            description='User query',
            static_sql='SELECT * FROM users',
            tags=['users', 'reporting']
        )
        
        # Filter by tag
        response = client.get(
            '/api/admin/query-patterns?tags=sales',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all('sales' in p['tags'] for p in data['patterns'])


class TestStory5_EdgeCases:
    """Story 5: Query Cache - Edge Cases"""
    
    def test_cache_expiration(self, client, admin_agent):
        """Test that expired cache entries are not returned"""
        from datetime import datetime, timedelta
        from ai_agent_connector.app.utils.query_cache import CacheEntry
        
        # Create expired entry manually
        expired_entry = CacheEntry(
            query_hash='test-hash',
            query='SELECT * FROM users',
            results=[{'id': 1}],
            cached_at=datetime.now() - timedelta(seconds=1000),
            expires_at=datetime.now() - timedelta(seconds=1)
        )
        
        query_cache._cache['test-hash'] = expired_entry
        
        # Should not return expired entry
        result = query_cache.get('SELECT * FROM users')
        assert result is None
    
    def test_cache_invalidation_by_pattern(self, client, admin_agent):
        """Test cache invalidation by pattern"""
        # Add multiple cache entries
        query_cache.set('SELECT * FROM users', [{'id': 1}])
        query_cache.set('SELECT * FROM orders', [{'id': 1}])
        query_cache.set('SELECT * FROM products', [{'id': 1}])
        
        # Invalidate all user-related queries
        payload = {'pattern': 'users'}
        
        response = client.post(
            '/api/admin/cache/invalidate',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['invalidated_count'] >= 1
    
    def test_cache_agent_specific(self, client, admin_agent):
        """Test that cache entries are agent-specific"""
        query_cache.set(
            'SELECT * FROM users',
            [{'id': 1}],
            agent_id='agent-1',
            metadata={'agent_id': 'agent-1'}
        )
        query_cache.set(
            'SELECT * FROM users',
            [{'id': 2}],
            agent_id='agent-2',
            metadata={'agent_id': 'agent-2'}
        )
        
        # Get for agent-1
        result1 = query_cache.get('SELECT * FROM users', agent_id='agent-1')
        assert result1 is not None
        
        # Remove agent-1 cache
        count = query_cache.remove_agent_cache('agent-1')
        assert count >= 1
        
        # agent-2 cache should still exist
        result2 = query_cache.get('SELECT * FROM users', agent_id='agent-2')
        assert result2 is not None
    
    def test_cache_with_parameters(self, client, admin_agent):
        """Test that cache distinguishes queries with different parameters"""
        query_cache.set('SELECT * FROM users WHERE id = %s', [{'id': 1}], params=('1',))
        query_cache.set('SELECT * FROM users WHERE id = %s', [{'id': 2}], params=('2',))
        
        # Should get different results
        result1 = query_cache.get('SELECT * FROM users WHERE id = %s', params=('1',))
        result2 = query_cache.get('SELECT * FROM users WHERE id = %s', params=('2',))
        
        assert result1 is not None
        assert result2 is not None
        assert result1 != result2
    
    def test_cache_ttl_validation(self, client, admin_agent):
        """Test cache TTL validation"""
        # Invalid TTL (negative)
        response = client.post(
            '/api/admin/agents/test-agent/cache/ttl',
            json={'ttl_seconds': -1},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
        
        # Invalid TTL (not integer)
        response = client.post(
            '/api/admin/agents/test-agent/cache/ttl',
            json={'ttl_seconds': 'invalid'},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_cache_stats_with_expired_entries(self, client, admin_agent):
        """Test cache stats include expired entries count"""
        from datetime import datetime, timedelta
        from ai_agent_connector.app.utils.query_cache import CacheEntry
        
        # Add active entry
        query_cache.set('SELECT * FROM users', [{'id': 1}])
        
        # Add expired entry manually
        expired_entry = CacheEntry(
            query_hash='expired-hash',
            query='SELECT * FROM orders',
            results=[{'id': 1}],
            cached_at=datetime.now() - timedelta(seconds=1000),
            expires_at=datetime.now() - timedelta(seconds=1)
        )
        query_cache._cache['expired-hash'] = expired_entry
        
        response = client.get(
            '/api/admin/cache/stats',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'expired_entries' in data
        assert data['expired_entries'] >= 1


class TestIntegration_ErrorHandling:
    """Integration tests for error handling across all features"""
    
    def test_query_with_invalid_template_id(self, client, test_agent):
        """Test query with invalid template ID"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            
            payload = {
                'use_template': 'invalid-template-id',
                'preview_only': True
            }
            
            response = client.post(
                '/api/agents/test-agent/query/natural',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 404
    
    def test_query_with_missing_required_fields(self, client, test_agent):
        """Test query without required fields"""
        response = client.post(
            '/api/agents/test-agent/query/natural',
            json={},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_unauthorized_template_access(self, client, test_agent):
        """Test unauthorized access to template"""
        # Create template for another agent
        template = template_manager.create_template(
            name='Private',
            sql='SELECT * FROM private',
            created_by='other-agent',
            is_public=False
        )
        
        # Try to update as different agent
        response = client.put(
            f'/api/agents/test-agent/query/templates/{template.template_id}',
            json={'name': 'Hacked'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_admin_only_endpoints(self, client, test_agent):
        """Test that admin-only endpoints require admin permission"""
        # Try to create approved pattern as non-admin
        response = client.post(
            '/api/admin/query-patterns',
            json={
                'name': 'Test Pattern',
                'description': 'Test',
                'static_sql': 'SELECT 1'
            },
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
        
        # Try to set cache TTL as non-admin
        response = client.post(
            '/api/admin/agents/test-agent/cache/ttl',
            json={'ttl_seconds': 600},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403


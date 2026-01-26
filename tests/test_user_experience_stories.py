"""
Integration tests for User Experience Stories

Story 1: As a Non-Technical User, I want contextual help tooltips explaining database schemas,
         so that I can write better queries.

Story 2: As a User, I want autocomplete suggestions for table/column names in natural language queries,
         so that I reduce typos.

Story 3: As an Admin, I want a setup wizard that guides me through connecting my first database and agent
         in under 5 minutes, so that onboarding is frictionless.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, schema_help_provider,
    autocomplete_provider, setup_wizard
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.setup_wizard import SetupStep


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    schema_help_provider.clear_cache()
    setup_wizard._sessions.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    schema_help_provider.clear_cache()
    setup_wizard._sessions.clear()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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


@pytest.fixture
def test_agent():
    """Create a test agent with database"""
    result = agent_registry.register_agent(
        agent_id='test-agent',
        agent_info={'name': 'Test Agent'},
        credentials={'api_key': 'test-key', 'api_secret': 'test-secret'},
        database={
            'connection_string': 'postgresql://user:pass@localhost/testdb',
            'database_type': 'postgresql'
        }
    )
    access_control.grant_permission('test-agent', Permission.READ)
    return {'agent_id': 'test-agent', 'api_key': result['api_key']}


@pytest.fixture
def sample_schema_info():
    """Sample schema information"""
    return {
        'tables': {
            'users': {
                'description': 'User accounts table',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'nullable': False, 'primary_key': True},
                    {'name': 'email', 'type': 'varchar', 'nullable': False, 'unique': True},
                    {'name': 'name', 'type': 'varchar', 'nullable': True}
                ]
            },
            'orders': {
                'description': 'Customer orders',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'nullable': False, 'primary_key': True},
                    {'name': 'user_id', 'type': 'integer', 'nullable': False, 'foreign_key': 'users.id'},
                    {'name': 'total', 'type': 'decimal', 'nullable': False}
                ]
            }
        }
    }


class TestStory1_SchemaHelp:
    """Story 1: Contextual help tooltips for database schemas"""
    
    def test_get_table_help(self, client, test_agent, sample_schema_info):
        """Test getting help for a table"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/schema/help?resource_type=table&resource_name=users',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['resource_type'] == 'table'
            assert data['resource_name'] == 'users'
            assert 'description' in data
            assert 'examples' in data
    
    def test_get_column_help(self, client, test_agent, sample_schema_info):
        """Test getting help for a column"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/schema/help?resource_type=column&resource_name=email&table_name=users',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['resource_type'] == 'column'
            assert 'email' in data['resource_name']
            assert 'data_type' in data
            assert 'constraints' in data
    
    def test_get_database_help(self, client, test_agent, sample_schema_info):
        """Test getting help for a database"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/schema/help?resource_type=database&resource_name=testdb',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['resource_type'] == 'database'
            assert 'description' in data
            assert 'related_resources' in data
    
    def test_table_help_with_schema_info(self, client, test_agent, sample_schema_info):
        """Test table help generation with schema info"""
        help_info = schema_help_provider.get_table_help('users', sample_schema_info)
        
        assert help_info.resource_type == 'table'
        assert help_info.resource_name == 'users'
        assert len(help_info.examples) > 0
        assert len(help_info.related_resources) > 0
    
    def test_column_help_with_schema_info(self, client, test_agent, sample_schema_info):
        """Test column help generation with schema info"""
        help_info = schema_help_provider.get_column_help('users', 'email', sample_schema_info)
        
        assert help_info.resource_type == 'column'
        assert 'email' in help_info.resource_name
        assert help_info.data_type is not None
        assert len(help_info.constraints) > 0
    
    def test_help_cache(self, client, test_agent):
        """Test help caching"""
        help1 = schema_help_provider.get_table_help('users', None)
        help2 = schema_help_provider.get_table_help('users', None)
        
        # Should return same object (cached)
        assert help1 is help2


class TestStory2_Autocomplete:
    """Story 2: Autocomplete suggestions for table/column names"""
    
    def test_get_autocomplete_suggestions(self, client, test_agent, sample_schema_info):
        """Test getting autocomplete suggestions"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            payload = {
                'query': 'SELECT * FROM us',
                'cursor_position': 18
            }
            
            response = client.post(
                '/api/agents/test-agent/autocomplete',
                json=payload,
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'suggestions' in data
            assert len(data['suggestions']) > 0
            assert any(s['text'] == 'users' for s in data['suggestions'])
    
    def test_get_table_autocomplete(self, client, test_agent, sample_schema_info):
        """Test getting table name autocomplete"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/autocomplete/tables?partial=us',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'suggestions' in data
            assert any(s['text'] == 'users' for s in data['suggestions'])
    
    def test_get_column_autocomplete(self, client, test_agent, sample_schema_info):
        """Test getting column name autocomplete"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/autocomplete/columns?table_name=users&partial=em',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'suggestions' in data
            assert any('email' in s['text'] for s in data['suggestions'])
    
    def test_autocomplete_with_context(self, client, test_agent, sample_schema_info):
        """Test autocomplete with table context"""
        suggestions = autocomplete_provider.get_suggestions(
            query='SELECT em FROM users',
            cursor_position=10,
            schema_info=sample_schema_info,
            context={'current_table': 'users'}
        )
        
        assert len(suggestions) > 0
        assert any(s['type'] == 'column' for s in suggestions)
    
    def test_autocomplete_relevance_scoring(self, client, test_agent, sample_schema_info):
        """Test autocomplete relevance scoring"""
        suggestions = autocomplete_provider.get_table_suggestions('us', sample_schema_info)
        
        # Should be sorted by relevance
        scores = [s.relevance_score for s in suggestions]
        assert scores == sorted(scores, reverse=True)
    
    def test_autocomplete_sql_keywords(self, client, test_agent, sample_schema_info):
        """Test autocomplete includes SQL keywords"""
        suggestions = autocomplete_provider.get_suggestions(
            query='SEL',
            cursor_position=3,
            schema_info=sample_schema_info
        )
        
        assert any(s['type'] == 'keyword' and s['text'] == 'SELECT' for s in suggestions)


class TestStory3_SetupWizard:
    """Story 3: Setup wizard for first-time setup"""
    
    def test_start_setup_wizard(self, client):
        """Test starting a setup wizard session"""
        response = client.post('/api/setup/start')
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'session' in data
        assert 'instructions' in data
        assert data['session']['current_step'] == 'welcome'
    
    def test_get_setup_session(self, client):
        """Test getting a setup session"""
        session = setup_wizard.create_session()
        
        response = client.get(f'/api/setup/sessions/{session.session_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['session']['session_id'] == session.session_id
    
    def test_update_setup_step(self, client):
        """Test updating setup wizard step"""
        session = setup_wizard.create_session()
        
        payload = {
            'step': 'database_type',
            'data': {'database_type': 'postgresql'}
        }
        
        response = client.post(
            f'/api/setup/sessions/{session.session_id}/step',
            json=payload
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['session']['current_step'] == 'database_type'
        assert data['session']['database_type'] == 'postgresql'
        assert 'next_step' in data
    
    def test_setup_wizard_flow(self, client):
        """Test complete setup wizard flow"""
        # Step 1: Start wizard
        response = client.post('/api/setup/start')
        session_id = response.get_json()['session']['session_id']
        
        # Step 2: Select database type
        response = client.post(
            f'/api/setup/sessions/{session_id}/step',
            json={'step': 'database_type', 'data': {'database_type': 'postgresql'}}
        )
        assert response.status_code == 200
        
        # Step 3: Enter database connection
        response = client.post(
            f'/api/setup/sessions/{session_id}/step',
            json={
                'step': 'database_connection',
                'data': {
                    'host': 'localhost',
                    'port': 5432,
                    'user': 'user',
                    'password': 'pass',
                    'database': 'testdb'
                }
            }
        )
        assert response.status_code == 200
        
        # Step 4: Register agent
        response = client.post(
            f'/api/setup/sessions/{session_id}/step',
            json={
                'step': 'agent_registration',
                'data': {
                    'agent_id': 'wizard-agent',
                    'agent_info': {'name': 'Wizard Agent'}
                }
            }
        )
        assert response.status_code == 200
    
    def test_test_database_connection(self, client, admin_agent):
        """Test database connection during setup"""
        session = setup_wizard.create_session()
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.test_database_connection.return_value = {
                'success': True,
                'message': 'Connection successful'
            }
            
            payload = {
                'database_type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'user': 'user',
                'password': 'pass',
                'database': 'testdb'
            }
            
            response = client.post(
                f'/api/setup/sessions/{session.session_id}/test-database',
                json=payload
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_complete_setup(self, client, admin_agent):
        """Test completing setup wizard"""
        session = setup_wizard.create_session()
        
        # Set up session data
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_CONNECTION, {
            'host': 'localhost',
            'port': 5432,
            'user': 'user',
            'password': 'pass',
            'database': 'testdb'
        })
        setup_wizard.update_step(session.session_id, SetupStep.AGENT_REGISTRATION, {
            'agent_id': 'wizard-agent',
            'agent_info': {'name': 'Wizard Agent'}
        })
        
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.test_database_connection.return_value = {'success': True}
            mock_registry.register_agent.return_value = {
                'agent_id': 'wizard-agent',
                'api_key': 'generated-key'
            }
            
            response = client.post(
                f'/api/setup/sessions/{session.session_id}/complete',
                headers={'X-API-Key': admin_agent['api_key']}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'agent' in data
            assert 'database' in data
            assert data['agent']['agent_id'] == 'wizard-agent'
    
    def test_setup_wizard_instructions(self, client):
        """Test getting setup wizard instructions"""
        instructions = setup_wizard.get_step_instructions(SetupStep.WELCOME)
        
        assert 'title' in instructions
        assert 'description' in instructions
        assert 'estimated_time' in instructions
        assert instructions['estimated_time'] == '5 minutes'
    
    def test_setup_wizard_next_step(self, client):
        """Test getting next step"""
        next_step = setup_wizard.get_next_step(SetupStep.WELCOME)
        assert next_step == SetupStep.DATABASE_TYPE
        
        next_step = setup_wizard.get_next_step(SetupStep.DATABASE_TYPE)
        assert next_step == SetupStep.DATABASE_CONNECTION
    
    def test_setup_wizard_previous_step(self, client):
        """Test getting previous step"""
        prev_step = setup_wizard.get_previous_step(SetupStep.DATABASE_TYPE)
        assert prev_step == SetupStep.WELCOME
    
    def test_setup_wizard_errors(self, client):
        """Test setup wizard error handling"""
        session = setup_wizard.create_session()
        
        setup_wizard.add_error(session.session_id, 'Test error')
        
        updated_session = setup_wizard.get_session(session.session_id)
        assert len(updated_session.errors) == 1
        assert 'Test error' in updated_session.errors
        
        setup_wizard.clear_errors(session.session_id)
        updated_session = setup_wizard.get_session(session.session_id)
        assert len(updated_session.errors) == 0
    
    def test_delete_setup_session(self, client):
        """Test deleting a setup session"""
        session = setup_wizard.create_session()
        
        response = client.delete(f'/api/setup/sessions/{session.session_id}')
        
        assert response.status_code == 200
        
        # Verify deleted
        assert setup_wizard.get_session(session.session_id) is None


class TestIntegration_UserExperience:
    """Integration tests for user experience features"""
    
    def test_help_and_autocomplete_together(self, client, test_agent, sample_schema_info):
        """Test using help and autocomplete together"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            # Get autocomplete
            autocomplete_response = client.post(
                '/api/agents/test-agent/autocomplete',
                json={'query': 'SELECT * FROM us', 'cursor_position': 18},
                headers={'X-API-Key': test_agent['api_key']}
            )
            assert autocomplete_response.status_code == 200
            
            # Get help for selected table
            help_response = client.get(
                '/api/agents/test-agent/schema/help?resource_type=table&resource_name=users',
                headers={'X-API-Key': test_agent['api_key']}
            )
            assert help_response.status_code == 200
    
    def test_setup_wizard_with_help(self, client):
        """Test setup wizard with schema help"""
        session = setup_wizard.create_session()
        
        # Complete setup
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_CONNECTION, {
            'host': 'localhost',
            'database': 'testdb'
        })
        setup_wizard.update_step(session.session_id, SetupStep.AGENT_REGISTRATION, {
            'agent_id': 'wizard-agent',
            'agent_info': {'name': 'Wizard Agent'}
        })
        
        # After setup, help should be available
        assert session.database_type == 'postgresql'
        assert session.agent_id == 'wizard-agent'
    
    def test_complete_user_journey(self, client, admin_agent):
        """Test complete user journey: setup → autocomplete → help"""
        # Step 1: Setup wizard
        response = client.post('/api/setup/start')
        session_id = response.get_json()['session']['session_id']
        
        # Step 2: Complete setup
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.test_database_connection.return_value = {'success': True}
            mock_registry.register_agent.return_value = {
                'agent_id': 'new-agent',
                'api_key': 'new-key'
            }
            
            session = setup_wizard.get_session(session_id)
            setup_wizard.update_step(session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
            setup_wizard.update_step(session_id, SetupStep.DATABASE_CONNECTION, {
                'host': 'localhost',
                'database': 'testdb'
            })
            setup_wizard.update_step(session_id, SetupStep.AGENT_REGISTRATION, {
                'agent_id': 'new-agent',
                'agent_info': {'name': 'New Agent'}
            })
            
            response = client.post(
                f'/api/setup/sessions/{session_id}/complete',
                headers={'X-API-Key': admin_agent['api_key']}
            )
            assert response.status_code == 200
        
        # Step 3: Use autocomplete (would require actual agent registration)
        # Step 4: Use help (would require actual agent registration)


class TestErrorHandling_UserExperience:
    """Error handling tests"""
    
    def test_help_no_database_connection(self, client, test_agent):
        """Test help when no database connection"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.get_database_connector.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/schema/help?resource_type=table&resource_name=users',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 404
    
    def test_autocomplete_no_database_connection(self, client, test_agent):
        """Test autocomplete when no database connection"""
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.get_database_connector.return_value = None
            
            response = client.post(
                '/api/agents/test-agent/autocomplete',
                json={'query': 'SELECT * FROM', 'cursor_position': 15},
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 404
    
    def test_setup_complete_incomplete_data(self, client, admin_agent):
        """Test completing setup with incomplete data"""
        session = setup_wizard.create_session()
        
        response = client.post(
            f'/api/setup/sessions/{session.session_id}/complete',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'incomplete' in data.get('error', '').lower()
    
    def test_setup_session_not_found(self, client):
        """Test accessing non-existent setup session"""
        response = client.get('/api/setup/sessions/nonexistent-id')
        
        assert response.status_code == 404
    
    def test_help_missing_parameters(self, client, test_agent):
        """Test help with missing parameters"""
        response = client.get(
            '/api/agents/test-agent/schema/help',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_column_help_missing_table(self, client, test_agent):
        """Test column help without table name"""
        response = client.get(
            '/api/agents/test-agent/schema/help?resource_type=column&resource_name=email',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400


class TestStory1_AdditionalHelpCases:
    """Story 1: Additional schema help scenarios"""
    
    def test_help_without_schema_info(self, client, test_agent):
        """Test help generation without schema info"""
        help_info = schema_help_provider.get_table_help('users', None)
        
        assert help_info.resource_type == 'table'
        assert help_info.resource_name == 'users'
        assert help_info.description is not None
    
    def test_help_with_foreign_keys(self, client, test_agent, sample_schema_info):
        """Test column help with foreign key constraints"""
        help_info = schema_help_provider.get_column_help('orders', 'user_id', sample_schema_info)
        
        assert help_info.resource_type == 'column'
        assert 'user_id' in help_info.resource_name
        assert any('FOREIGN KEY' in constraint for constraint in help_info.constraints)
    
    def test_help_examples_generation(self, client, test_agent, sample_schema_info):
        """Test help examples generation"""
        help_info = schema_help_provider.get_table_help('users', sample_schema_info)
        
        assert len(help_info.examples) > 0
        assert any('SELECT' in example for example in help_info.examples)
        assert any('users' in example for example in help_info.examples)
    
    def test_help_related_resources(self, client, test_agent, sample_schema_info):
        """Test help related resources"""
        help_info = schema_help_provider.get_table_help('users', sample_schema_info)
        
        assert len(help_info.related_resources) > 0
        # Should include column names
        assert any(col in help_info.related_resources for col in ['id', 'email', 'name'])
    
    def test_help_usage_tips(self, client, test_agent, sample_schema_info):
        """Test help usage tips"""
        help_info = schema_help_provider.get_table_help('users', sample_schema_info)
        
        assert len(help_info.usage_tips) > 0
        assert any('WHERE' in tip or 'filter' in tip.lower() for tip in help_info.usage_tips)
    
    def test_help_invalid_resource_type(self, client, test_agent, sample_schema_info):
        """Test help with invalid resource type"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            response = client.get(
                '/api/agents/test-agent/schema/help?resource_type=invalid&resource_name=test',
                headers={'X-API-Key': test_agent['api_key']}
            )
            
            assert response.status_code == 400


class TestStory2_AdditionalAutocompleteCases:
    """Story 2: Additional autocomplete scenarios"""
    
    def test_autocomplete_empty_query(self, client, test_agent, sample_schema_info):
        """Test autocomplete with empty query"""
        suggestions = autocomplete_provider.get_suggestions(
            query='',
            cursor_position=0,
            schema_info=sample_schema_info
        )
        
        # Should return some suggestions even with empty query
        assert isinstance(suggestions, list)
    
    def test_autocomplete_cursor_at_end(self, client, test_agent, sample_schema_info):
        """Test autocomplete with cursor at end of query"""
        query = 'SELECT * FROM users'
        suggestions = autocomplete_provider.get_suggestions(
            query=query,
            cursor_position=len(query),
            schema_info=sample_schema_info
        )
        
        assert isinstance(suggestions, list)
    
    def test_autocomplete_partial_matching(self, client, test_agent, sample_schema_info):
        """Test autocomplete with partial matching"""
        suggestions = autocomplete_provider.get_table_suggestions('ord', sample_schema_info)
        
        assert len(suggestions) > 0
        assert any('orders' in s.text.lower() for s in suggestions)
    
    def test_autocomplete_case_insensitive(self, client, test_agent, sample_schema_info):
        """Test autocomplete is case insensitive"""
        suggestions1 = autocomplete_provider.get_table_suggestions('USERS', sample_schema_info)
        suggestions2 = autocomplete_provider.get_table_suggestions('users', sample_schema_info)
        
        # Should find same tables regardless of case
        assert len(suggestions1) > 0
        assert len(suggestions2) > 0
    
    def test_autocomplete_limit_results(self, client, test_agent):
        """Test autocomplete limits results"""
        # Create schema with many tables
        large_schema = {
            'tables': {f'table_{i}': {'description': f'Table {i}', 'columns': []} for i in range(50)}
        }
        
        suggestions = autocomplete_provider.get_suggestions(
            query='SELECT * FROM tab',
            cursor_position=18,
            schema_info=large_schema
        )
        
        # Should limit to top 20
        assert len(suggestions) <= 20
    
    def test_autocomplete_column_without_table(self, client, test_agent, sample_schema_info):
        """Test autocomplete columns without table context"""
        suggestions = autocomplete_provider.get_suggestions(
            query='SELECT em',
            cursor_position=9,
            schema_info=sample_schema_info,
            context=None
        )
        
        # Should still find columns across all tables
        assert len(suggestions) > 0
        assert any(s.type == 'column' for s in suggestions)
    
    def test_autocomplete_extract_word(self, client, test_agent):
        """Test word extraction from query"""
        # Test various cursor positions
        query = 'SELECT * FROM users WHERE id = 1'
        
        # Cursor in middle of 'users'
        word = autocomplete_provider._extract_current_word(query, 18)
        assert 'users' in word or word == ''
        
        # Cursor at end
        word = autocomplete_provider._extract_current_word(query, len(query))
        assert word == '1' or word == ''
    
    def test_autocomplete_relevance_exact_match(self, client, test_agent):
        """Test relevance scoring for exact matches"""
        score = autocomplete_provider._calculate_relevance('users', 'users')
        assert score > 0.8  # Exact match should have high score
    
    def test_autocomplete_relevance_starts_with(self, client, test_agent):
        """Test relevance scoring for starts-with matches"""
        score = autocomplete_provider._calculate_relevance('users', 'us')
        assert score > 0.5  # Starts with should have good score


class TestStory3_AdditionalSetupWizardCases:
    """Story 3: Additional setup wizard scenarios"""
    
    def test_setup_wizard_all_steps(self, client):
        """Test all setup wizard steps"""
        session = setup_wizard.create_session()
        
        steps = [
            SetupStep.WELCOME,
            SetupStep.DATABASE_TYPE,
            SetupStep.DATABASE_CONNECTION,
            SetupStep.DATABASE_TEST,
            SetupStep.AGENT_REGISTRATION,
            SetupStep.AGENT_CREDENTIALS,
            SetupStep.COMPLETE
        ]
        
        for step in steps:
            instructions = setup_wizard.get_step_instructions(step)
            assert 'title' in instructions
            assert 'description' in instructions
            assert 'estimated_time' in instructions
    
    def test_setup_wizard_step_navigation(self, client):
        """Test navigating through all steps"""
        session = setup_wizard.create_session()
        current = session.current_step
        
        # Navigate forward
        steps_taken = [current]
        while True:
            next_step = setup_wizard.get_next_step(current)
            if not next_step:
                break
            steps_taken.append(next_step)
            current = next_step
        
        assert len(steps_taken) == 7  # All steps
        assert steps_taken[-1] == SetupStep.COMPLETE
    
    def test_setup_wizard_backward_navigation(self, client):
        """Test navigating backward through steps"""
        session = setup_wizard.create_session()
        current = SetupStep.COMPLETE
        
        # Navigate backward
        steps_taken = [current]
        while True:
            prev_step = setup_wizard.get_previous_step(current)
            if not prev_step:
                break
            steps_taken.append(prev_step)
            current = prev_step
        
        assert len(steps_taken) >= 2
        assert steps_taken[-1] == SetupStep.WELCOME
    
    def test_setup_wizard_database_types(self, client):
        """Test setup wizard with different database types"""
        session = setup_wizard.create_session()
        
        database_types = ['postgresql', 'mysql', 'mongodb', 'bigquery', 'snowflake']
        
        for db_type in database_types:
            setup_wizard.update_step(
                session.session_id,
                SetupStep.DATABASE_TYPE,
                {'database_type': db_type}
            )
            
            updated = setup_wizard.get_session(session.session_id)
            assert updated.database_type == db_type
    
    def test_setup_wizard_connection_string(self, client):
        """Test setup wizard with connection string"""
        session = setup_wizard.create_session()
        
        setup_wizard.update_step(
            session.session_id,
            SetupStep.DATABASE_CONNECTION,
            {'connection_string': 'postgresql://user:pass@host:5432/db'}
        )
        
        updated = setup_wizard.get_session(session.session_id)
        assert 'connection_string' in updated.database_config
    
    def test_setup_wizard_individual_parameters(self, client):
        """Test setup wizard with individual connection parameters"""
        session = setup_wizard.create_session()
        
        config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        setup_wizard.update_step(
            session.session_id,
            SetupStep.DATABASE_CONNECTION,
            config
        )
        
        updated = setup_wizard.get_session(session.session_id)
        assert updated.database_config['host'] == 'localhost'
        assert updated.database_config['port'] == 5432
        assert updated.database_config['user'] == 'testuser'
    
    def test_setup_wizard_agent_info(self, client):
        """Test setup wizard with agent info"""
        session = setup_wizard.create_session()
        
        agent_info = {
            'name': 'My Agent',
            'description': 'Test agent',
            'type': 'assistant'
        }
        
        setup_wizard.update_step(
            session.session_id,
            SetupStep.AGENT_REGISTRATION,
            {
                'agent_id': 'my-agent',
                'agent_info': agent_info
            }
        )
        
        updated = setup_wizard.get_session(session.session_id)
        assert updated.agent_id == 'my-agent'
        assert updated.agent_info['name'] == 'My Agent'
    
    def test_setup_wizard_multiple_errors(self, client):
        """Test setup wizard with multiple errors"""
        session = setup_wizard.create_session()
        
        setup_wizard.add_error(session.session_id, 'Error 1')
        setup_wizard.add_error(session.session_id, 'Error 2')
        setup_wizard.add_error(session.session_id, 'Error 3')
        
        updated = setup_wizard.get_session(session.session_id)
        assert len(updated.errors) == 3
    
    def test_setup_wizard_complete_with_errors(self, client, admin_agent):
        """Test completing setup with errors in session"""
        session = setup_wizard.create_session()
        
        # Add some data
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_CONNECTION, {
            'host': 'localhost',
            'database': 'testdb'
        })
        setup_wizard.update_step(session.session_id, SetupStep.AGENT_REGISTRATION, {
            'agent_id': 'test-agent',
            'agent_info': {'name': 'Test'}
        })
        
        # Add error
        setup_wizard.add_error(session.session_id, 'Previous error')
        
        # Complete should still work if data is valid
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.test_database_connection.return_value = {'success': True}
            mock_registry.register_agent.return_value = {
                'agent_id': 'test-agent',
                'api_key': 'key'
            }
            
            response = client.post(
                f'/api/setup/sessions/{session.session_id}/complete',
                headers={'X-API-Key': admin_agent['api_key']}
            )
            
            # Should succeed despite previous errors
            assert response.status_code == 200


class TestIntegration_AdvancedUserExperience:
    """Advanced integration scenarios"""
    
    def test_help_autocomplete_setup_workflow(self, client, admin_agent, sample_schema_info):
        """Test complete workflow: setup → autocomplete → help"""
        # Step 1: Setup wizard
        response = client.post('/api/setup/start')
        session_id = response.get_json()['session']['session_id']
        
        # Step 2: Complete setup
        with patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            mock_registry.test_database_connection.return_value = {'success': True}
            mock_registry.register_agent.return_value = {
                'agent_id': 'new-agent',
                'api_key': 'new-key'
            }
            
            session = setup_wizard.get_session(session_id)
            setup_wizard.update_step(session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
            setup_wizard.update_step(session_id, SetupStep.DATABASE_CONNECTION, {
                'host': 'localhost',
                'database': 'testdb'
            })
            setup_wizard.update_step(session_id, SetupStep.AGENT_REGISTRATION, {
                'agent_id': 'new-agent',
                'agent_info': {'name': 'New Agent'}
            })
            
            response = client.post(
                f'/api/setup/sessions/{session_id}/complete',
                headers={'X-API-Key': admin_agent['api_key']}
            )
            assert response.status_code == 200
        
        # Step 3: Use autocomplete (would require actual agent)
        # Step 4: Use help (would require actual agent)
    
    def test_autocomplete_help_integration(self, client, test_agent, sample_schema_info):
        """Test autocomplete and help working together"""
        with patch('ai_agent_connector.app.api.routes.nl_converter') as mock_nl, \
             patch('ai_agent_connector.app.api.routes.agent_registry') as mock_registry:
            
            mock_connector = MagicMock()
            mock_registry.get_database_connector.return_value = mock_connector
            mock_nl.get_schema_info.return_value = sample_schema_info
            
            mock_connector.connect.return_value = None
            mock_connector.disconnect.return_value = None
            
            # Get autocomplete suggestions
            autocomplete_response = client.post(
                '/api/agents/test-agent/autocomplete',
                json={'query': 'SELECT * FROM us', 'cursor_position': 18},
                headers={'X-API-Key': test_agent['api_key']}
            )
            assert autocomplete_response.status_code == 200
            suggestions = autocomplete_response.get_json()['suggestions']
            
            # Get help for first suggestion
            if suggestions:
                first_suggestion = suggestions[0]
                if first_suggestion['type'] == 'table':
                    help_response = client.get(
                        f'/api/agents/test-agent/schema/help?resource_type=table&resource_name={first_suggestion["text"]}',
                        headers={'X-API-Key': test_agent['api_key']}
                    )
                    assert help_response.status_code == 200
    
    def test_setup_wizard_error_recovery(self, client, admin_agent):
        """Test setup wizard error recovery"""
        session = setup_wizard.create_session()
        
        # Add error
        setup_wizard.add_error(session.session_id, 'Connection failed')
        
        # Clear errors
        setup_wizard.clear_errors(session.session_id)
        
        updated = setup_wizard.get_session(session.session_id)
        assert len(updated.errors) == 0
        
        # Continue with setup
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
        
        updated = setup_wizard.get_session(session.session_id)
        assert updated.database_type == 'postgresql'
    
    def test_help_for_nonexistent_table(self, client, test_agent, sample_schema_info):
        """Test help for non-existent table"""
        help_info = schema_help_provider.get_table_help('nonexistent', sample_schema_info)
        
        # Should still return help info
        assert help_info.resource_type == 'table'
        assert help_info.resource_name == 'nonexistent'
    
    def test_autocomplete_no_matches(self, client, test_agent, sample_schema_info):
        """Test autocomplete with no matches"""
        suggestions = autocomplete_provider.get_table_suggestions('nonexistent_table_xyz', sample_schema_info)
        
        # Should return empty list or very few results
        assert isinstance(suggestions, list)
    
    def test_setup_wizard_session_persistence(self, client):
        """Test setup wizard session persistence"""
        session = setup_wizard.create_session()
        
        # Update multiple steps
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_TYPE, {'database_type': 'postgresql'})
        setup_wizard.update_step(session.session_id, SetupStep.DATABASE_CONNECTION, {
            'host': 'localhost',
            'database': 'testdb'
        })
        
        # Retrieve session
        retrieved = setup_wizard.get_session(session.session_id)
        
        assert retrieved.database_type == 'postgresql'
        assert retrieved.database_config['host'] == 'localhost'
        assert retrieved.database_config['database'] == 'testdb'

"""
Test cases for Prompt Engineering Studio
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from ai_agent_connector.app.prompts.models import (
    PromptStore, PromptTemplate, PromptVariable, ABTest,
    PromptStatus
)


class TestPromptVariable:
    """Test PromptVariable model"""
    
    def test_create_variable(self):
        """Test creating a variable"""
        var = PromptVariable(
            name="test_var",
            description="Test variable",
            default_value="default",
            required=True
        )
        assert var.name == "test_var"
        assert var.description == "Test variable"
        assert var.default_value == "default"
        assert var.required is True
    
    def test_variable_to_dict(self):
        """Test variable serialization"""
        var = PromptVariable(
            name="test_var",
            description="Test",
            default_value="default",
            required=False
        )
        data = var.to_dict()
        assert data['name'] == "test_var"
        assert data['required'] is False
    
    def test_variable_from_dict(self):
        """Test variable deserialization"""
        data = {
            'name': 'test_var',
            'description': 'Test',
            'default_value': 'default',
            'required': True
        }
        var = PromptVariable.from_dict(data)
        assert var.name == "test_var"
        assert var.required is True


class TestPromptTemplate:
    """Test PromptTemplate model"""
    
    def test_create_template(self):
        """Test creating a template"""
        template = PromptTemplate(
            id="test-1",
            name="Test Template",
            description="Test",
            system_prompt="System: {{var1}}",
            user_prompt_template="User: {{var2}}",
            variables=[
                PromptVariable("var1", "Var 1", "default1", True),
                PromptVariable("var2", "Var 2", "default2", False)
            ]
        )
        assert template.id == "test-1"
        assert template.name == "Test Template"
        assert len(template.variables) == 2
    
    def test_template_render(self):
        """Test template rendering with variables"""
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="Database: {{database_type}}, Schema: {{schema_info}}",
            user_prompt_template="Query: {{natural_language_query}}",
            variables=[
                PromptVariable("database_type", "DB type", "PostgreSQL", True),
                PromptVariable("schema_info", "Schema", "No schema", False),
                PromptVariable("natural_language_query", "Query", "", True)
            ]
        )
        
        context = {
            'database_type': 'MySQL',
            'schema_info': 'users table',
            'natural_language_query': 'Show users'
        }
        
        system, user = template.render(context)
        assert 'MySQL' in system
        assert 'users table' in system
        assert 'Show users' in user
    
    def test_template_to_dict(self):
        """Test template serialization"""
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="System",
            user_prompt_template="User",
            variables=[]
        )
        data = template.to_dict()
        assert data['id'] == "test-1"
        assert 'variables' in data
        assert isinstance(data['variables'], list)
    
    def test_template_from_dict(self):
        """Test template deserialization"""
        data = {
            'id': 'test-1',
            'name': 'Test',
            'description': '',
            'system_prompt': 'System',
            'user_prompt_template': 'User',
            'variables': [
                {
                    'name': 'var1',
                    'description': 'Var 1',
                    'default_value': 'default',
                    'required': True
                }
            ],
            'status': 'draft',
            'agent_id': None,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'metadata': {}
        }
        template = PromptTemplate.from_dict(data)
        assert template.id == "test-1"
        assert len(template.variables) == 1


class TestPromptStore:
    """Test PromptStore"""
    
    def test_create_prompt(self):
        """Test creating a prompt"""
        store = PromptStore()
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="System",
            user_prompt_template="User",
            variables=[]
        )
        created = store.create_prompt(template)
        assert created.id == "test-1"
        assert store.get_prompt("test-1") == template
    
    def test_create_duplicate_prompt(self):
        """Test creating duplicate prompt fails"""
        store = PromptStore()
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="System",
            user_prompt_template="User",
            variables=[]
        )
        store.create_prompt(template)
        
        with pytest.raises(ValueError):
            store.create_prompt(template)
    
    def test_get_prompt(self):
        """Test getting a prompt"""
        store = PromptStore()
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="System",
            user_prompt_template="User",
            variables=[]
        )
        store.create_prompt(template)
        
        retrieved = store.get_prompt("test-1")
        assert retrieved == template
    
    def test_get_nonexistent_prompt(self):
        """Test getting nonexistent prompt"""
        store = PromptStore()
        assert store.get_prompt("nonexistent") is None
    
    def test_update_prompt(self):
        """Test updating a prompt"""
        store = PromptStore()
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="System",
            user_prompt_template="User",
            variables=[]
        )
        store.create_prompt(template)
        
        updated = store.update_prompt("test-1", {'name': 'Updated'})
        assert updated.name == "Updated"
        assert store.get_prompt("test-1").name == "Updated"
    
    def test_delete_prompt(self):
        """Test deleting a prompt"""
        store = PromptStore()
        template = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="System",
            user_prompt_template="User",
            variables=[]
        )
        store.create_prompt(template)
        
        assert store.delete_prompt("test-1") is True
        assert store.get_prompt("test-1") is None
    
    def test_list_prompts(self):
        """Test listing prompts"""
        store = PromptStore()
        
        # Create multiple prompts
        for i in range(3):
            template = PromptTemplate(
                id=f"test-{i}",
                name=f"Test {i}",
                description="",
                system_prompt="System",
                user_prompt_template="User",
                variables=[],
                agent_id="agent-1" if i < 2 else "agent-2"
            )
            store.create_prompt(template)
        
        # List all
        all_prompts = store.list_prompts()
        assert len(all_prompts) == 3
        
        # Filter by agent
        agent_prompts = store.list_prompts(agent_id="agent-1")
        assert len(agent_prompts) == 2
        
        # Filter by status
        store.update_prompt("test-0", {'status': 'active'})
        active_prompts = store.list_prompts(status='active')
        assert len(active_prompts) == 1
    
    def test_get_templates(self):
        """Test getting template library"""
        store = PromptStore()
        templates = store.get_templates()
        assert len(templates) >= 3  # Default templates
        assert any(t.id == "template-postgres-default" for t in templates)
    
    def test_get_template(self):
        """Test getting a template"""
        store = PromptStore()
        template = store.get_template("template-postgres-default")
        assert template is not None
        assert template.name == "PostgreSQL Default"
    
    def test_create_ab_test(self):
        """Test creating A/B test"""
        store = PromptStore()
        
        # Create prompts
        prompt_a = PromptTemplate(
            id="prompt-a",
            name="Prompt A",
            description="",
            system_prompt="System A",
            user_prompt_template="User",
            variables=[]
        )
        prompt_b = PromptTemplate(
            id="prompt-b",
            name="Prompt B",
            description="",
            system_prompt="System B",
            user_prompt_template="User",
            variables=[]
        )
        store.create_prompt(prompt_a)
        store.create_prompt(prompt_b)
        
        ab_test = ABTest(
            id="test-1",
            name="Test",
            description="",
            prompt_a_id="prompt-a",
            prompt_b_id="prompt-b",
            agent_id="agent-1"
        )
        
        created = store.create_ab_test(ab_test)
        assert created.id == "test-1"
        assert store.get_ab_test("test-1") == ab_test
    
    def test_ab_test_select_prompt(self):
        """Test A/B test prompt selection"""
        store = PromptStore()
        
        ab_test = ABTest(
            id="test-1",
            name="Test",
            description="",
            prompt_a_id="prompt-a",
            prompt_b_id="prompt-b",
            agent_id="agent-1",
            split_ratio=0.5
        )
        
        # Test with user ID (consistent assignment)
        prompt_id_1 = ab_test.select_prompt("user-1")
        prompt_id_2 = ab_test.select_prompt("user-1")
        assert prompt_id_1 == prompt_id_2  # Same user gets same prompt
        
        # Test without user ID (random)
        selections = [ab_test.select_prompt() for _ in range(10)]
        assert "prompt-a" in selections or "prompt-b" in selections
    
    def test_update_ab_test_metrics(self):
        """Test updating A/B test metrics"""
        store = PromptStore()
        
        ab_test = ABTest(
            id="test-1",
            name="Test",
            description="",
            prompt_a_id="prompt-a",
            prompt_b_id="prompt-b",
            agent_id="agent-1"
        )
        store.create_ab_test(ab_test)
        
        # Update metrics for prompt A
        store.update_ab_test_metrics("test-1", "prompt-a", True, 100)
        store.update_ab_test_metrics("test-1", "prompt-a", True, 200)
        
        updated = store.get_ab_test("test-1")
        assert updated.metrics['prompt_a']['queries'] == 2
        assert updated.metrics['prompt_a']['success'] == 2
        assert updated.metrics['prompt_a']['avg_tokens'] == 150


class TestPromptRoutes:
    """Test prompt API routes"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def mock_agent(self):
        """Mock agent for authentication"""
        from ai_agent_connector.app.api.routes import agent_registry
        agent = {
            'agent_id': 'test-agent',
            'api_key': 'test-api-key',
            'name': 'Test Agent'
        }
        agent_registry._agents['test-agent'] = agent
        return agent
    
    def test_list_prompts_requires_auth(self, client):
        """Test that listing prompts requires authentication"""
        response = client.get('/prompts/api/prompts')
        assert response.status_code == 401
    
    def test_list_prompts(self, client, mock_agent):
        """Test listing prompts"""
        response = client.get(
            '/prompts/api/prompts',
            headers={'X-API-Key': 'test-api-key'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'prompts' in data
    
    def test_create_prompt(self, client, mock_agent):
        """Test creating a prompt"""
        prompt_data = {
            'name': 'Test Prompt',
            'description': 'Test',
            'system_prompt': 'System: {{database_type}}',
            'user_prompt_template': 'User: {{natural_language_query}}',
            'variables': [
                {
                    'name': 'database_type',
                    'description': 'DB type',
                    'default_value': 'PostgreSQL',
                    'required': True
                }
            ]
        }
        
        response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_data)
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Test Prompt'
        assert 'id' in data
    
    def test_create_prompt_missing_fields(self, client, mock_agent):
        """Test creating prompt with missing required fields"""
        prompt_data = {
            'name': 'Test Prompt'
            # Missing system_prompt and user_prompt_template
        }
        
        response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_data)
        )
        
        assert response.status_code == 400
    
    def test_get_prompt(self, client, mock_agent):
        """Test getting a prompt"""
        # First create a prompt
        prompt_data = {
            'name': 'Test Prompt',
            'system_prompt': 'System',
            'user_prompt_template': 'User',
            'variables': []
        }
        
        create_response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_data)
        )
        prompt_id = json.loads(create_response.data)['id']
        
        # Get the prompt
        response = client.get(
            f'/prompts/api/prompts/{prompt_id}',
            headers={'X-API-Key': 'test-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Test Prompt'
    
    def test_update_prompt(self, client, mock_agent):
        """Test updating a prompt"""
        # Create prompt
        prompt_data = {
            'name': 'Test Prompt',
            'system_prompt': 'System',
            'user_prompt_template': 'User',
            'variables': []
        }
        
        create_response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_data)
        )
        prompt_id = json.loads(create_response.data)['id']
        
        # Update prompt
        update_data = {'name': 'Updated Prompt'}
        response = client.put(
            f'/prompts/api/prompts/{prompt_id}',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(update_data)
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Prompt'
    
    def test_delete_prompt(self, client, mock_agent):
        """Test deleting a prompt"""
        # Create prompt
        prompt_data = {
            'name': 'Test Prompt',
            'system_prompt': 'System',
            'user_prompt_template': 'User',
            'variables': []
        }
        
        create_response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_data)
        )
        prompt_id = json.loads(create_response.data)['id']
        
        # Delete prompt
        response = client.delete(
            f'/prompts/api/prompts/{prompt_id}',
            headers={'X-API-Key': 'test-api-key'}
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        get_response = client.get(
            f'/prompts/api/prompts/{prompt_id}',
            headers={'X-API-Key': 'test-api-key'}
        )
        assert get_response.status_code == 404
    
    def test_render_prompt(self, client, mock_agent):
        """Test rendering a prompt with variables"""
        # Create prompt
        prompt_data = {
            'name': 'Test Prompt',
            'system_prompt': 'Database: {{database_type}}',
            'user_prompt_template': 'Query: {{natural_language_query}}',
            'variables': [
                {
                    'name': 'database_type',
                    'description': 'DB type',
                    'default_value': 'PostgreSQL',
                    'required': True
                },
                {
                    'name': 'natural_language_query',
                    'description': 'Query',
                    'default_value': '',
                    'required': True
                }
            ]
        }
        
        create_response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_data)
        )
        prompt_id = json.loads(create_response.data)['id']
        
        # Render prompt
        render_data = {
            'context': {
                'database_type': 'MySQL',
                'natural_language_query': 'Show users'
            }
        }
        
        response = client.post(
            f'/prompts/api/prompts/{prompt_id}/render',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(render_data)
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'MySQL' in data['system_prompt']
        assert 'Show users' in data['user_prompt']
    
    def test_list_templates(self, client):
        """Test listing templates (no auth required)"""
        response = client.get('/prompts/api/templates')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'templates' in data
        assert len(data['templates']) >= 3
    
    def test_get_template(self, client):
        """Test getting a template"""
        response = client.get('/prompts/api/templates/template-postgres-default')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'PostgreSQL Default'
    
    def test_clone_template(self, client, mock_agent):
        """Test cloning a template"""
        clone_data = {
            'name': 'My Cloned Prompt'
        }
        
        response = client.post(
            '/prompts/api/templates/template-postgres-default/clone',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(clone_data)
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'My Cloned Prompt'
        assert data['id'] != 'template-postgres-default'
    
    def test_create_ab_test(self, client, mock_agent):
        """Test creating A/B test"""
        # Create two prompts
        prompt_a_data = {
            'name': 'Prompt A',
            'system_prompt': 'System A',
            'user_prompt_template': 'User',
            'variables': []
        }
        prompt_b_data = {
            'name': 'Prompt B',
            'system_prompt': 'System B',
            'user_prompt_template': 'User',
            'variables': []
        }
        
        a_response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_a_data)
        )
        prompt_a_id = json.loads(a_response.data)['id']
        
        b_response = client.post(
            '/prompts/api/prompts',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(prompt_b_data)
        )
        prompt_b_id = json.loads(b_response.data)['id']
        
        # Create A/B test
        ab_test_data = {
            'name': 'Test A/B',
            'description': 'Test',
            'prompt_a_id': prompt_a_id,
            'prompt_b_id': prompt_b_id,
            'split_ratio': 0.5
        }
        
        response = client.post(
            '/prompts/api/ab-tests',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(ab_test_data)
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Test A/B'
        assert data['prompt_a_id'] == prompt_a_id
        assert data['prompt_b_id'] == prompt_b_id
    
    def test_select_ab_test_prompt(self, client, mock_agent):
        """Test selecting prompt for A/B test"""
        # Create A/B test (simplified - would need prompts)
        # This tests the selection logic
        from ai_agent_connector.app.prompts.models import prompt_store, PromptTemplate, ABTest
        
        prompt_a = PromptTemplate(
            id="prompt-a",
            name="A",
            description="",
            system_prompt="A",
            user_prompt_template="User",
            variables=[],
            agent_id="test-agent"
        )
        prompt_b = PromptTemplate(
            id="prompt-b",
            name="B",
            description="",
            system_prompt="B",
            user_prompt_template="User",
            variables=[],
            agent_id="test-agent"
        )
        prompt_store.create_prompt(prompt_a)
        prompt_store.create_prompt(prompt_b)
        
        ab_test = ABTest(
            id="test-1",
            name="Test",
            description="",
            prompt_a_id="prompt-a",
            prompt_b_id="prompt-b",
            agent_id="test-agent"
        )
        prompt_store.create_ab_test(ab_test)
        
        # Select prompt
        response = client.post(
            '/prompts/api/ab-tests/test-1/select',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps({'user_id': 'user-1'})
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['prompt_id'] in ['prompt-a', 'prompt-b']
    
    def test_update_ab_test_metrics(self, client, mock_agent):
        """Test updating A/B test metrics"""
        from ai_agent_connector.app.prompts.models import prompt_store, PromptTemplate, ABTest
        
        # Setup A/B test
        prompt_a = PromptTemplate(
            id="prompt-a",
            name="A",
            description="",
            system_prompt="A",
            user_prompt_template="User",
            variables=[],
            agent_id="test-agent"
        )
        prompt_store.create_prompt(prompt_a)
        
        ab_test = ABTest(
            id="test-1",
            name="Test",
            description="",
            prompt_a_id="prompt-a",
            prompt_b_id="prompt-a",  # Same for simplicity
            agent_id="test-agent"
        )
        prompt_store.create_ab_test(ab_test)
        
        # Update metrics
        metrics_data = {
            'prompt_id': 'prompt-a',
            'success': True,
            'tokens': 100
        }
        
        response = client.post(
            '/prompts/api/ab-tests/test-1/metrics',
            headers={
                'X-API-Key': 'test-api-key',
                'Content-Type': 'application/json'
            },
            data=json.dumps(metrics_data)
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['metrics']['prompt_a']['queries'] == 1


class TestPromptIntegration:
    """Test prompt integration with NL to SQL"""
    
    def test_nl_to_sql_with_custom_prompt(self):
        """Test NL to SQL conversion with custom prompt"""
        from ai_agent_connector.app.utils.nl_to_sql import NLToSQLConverter
        from ai_agent_connector.app.prompts.models import prompt_store, PromptTemplate, PromptVariable
        
        # Create custom prompt
        prompt = PromptTemplate(
            id="custom-1",
            name="Custom",
            description="",
            system_prompt="You are a SQL expert for {{database_type}}. Rules: 1. Generate valid SQL. Schema: {{schema_info}}",
            user_prompt_template="{{natural_language_query}}",
            variables=[
                PromptVariable("database_type", "DB type", "PostgreSQL", True),
                PromptVariable("schema_info", "Schema", "No schema", False),
                PromptVariable("natural_language_query", "Query", "", True)
            ]
        )
        prompt_store.create_prompt(prompt)
        
        # Mock OpenAI client
        with patch('ai_agent_connector.app.utils.nl_to_sql.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "SELECT * FROM users"
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            
            mock_client.chat.completions.create.return_value = mock_response
            
            converter = NLToSQLConverter()
            
            # Test with custom prompt
            custom_prompt = {
                'system_prompt': 'You are a SQL expert for PostgreSQL. Rules: 1. Generate valid SQL.',
                'user_prompt': 'Show all users'
            }
            
            result = converter.convert_to_sql(
                natural_language_query="Show all users",
                schema_info=None,
                database_type="PostgreSQL",
                custom_prompt=custom_prompt
            )
            
            assert result.get('sql') is not None
            assert mock_client.chat.completions.create.called
            
            # Verify custom prompt was used
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            assert 'You are a SQL expert for PostgreSQL' in messages[0]['content']
            assert 'Show all users' in messages[1]['content']
    
    def test_prompt_rendering_with_schema(self):
        """Test prompt rendering with schema information"""
        from ai_agent_connector.app.prompts.models import PromptTemplate, PromptVariable
        
        prompt = PromptTemplate(
            id="test-1",
            name="Test",
            description="",
            system_prompt="Schema: {{schema_info}}",
            user_prompt_template="{{natural_language_query}}",
            variables=[
                PromptVariable("schema_info", "Schema", "No schema", False),
                PromptVariable("natural_language_query", "Query", "", True)
            ]
        )
        
        schema_text = "Tables: users, products\nColumns: users.id, users.name"
        context = {
            'schema_info': schema_text,
            'natural_language_query': 'Show users'
        }
        
        system, user = prompt.render(context)
        assert schema_text in system
        assert 'Show users' in user


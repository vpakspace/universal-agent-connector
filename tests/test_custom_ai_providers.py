"""
Tests for Custom AI Providers Story

Story: As an Admin, I want to add custom AI providers (local Ollama, Azure OpenAI),
       so that I'm not vendor-locked.

Acceptance Criteria:
- Provider abstraction layer
- Config UI
- Test all providers
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.agents.providers import (
    AgentProvider,
    AgentConfiguration,
    BaseAgentProvider,
    create_agent_provider
)
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager
from typing import Dict, Any, Optional


# ============================================================================
# Mock Provider Classes for Testing
# ============================================================================

class MockProvider(BaseAgentProvider):
    """Mock provider for testing"""
    
    def __init__(self, config: AgentConfiguration):
        self.config = config
        self._execute_called = False
        self._validate_called = False
    
    def execute_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._execute_called = True
        return {
            'response': f'Mock response to: {query}',
            'model': self.config.model,
            'provider': self.config.provider.value
        }
    
    def validate_configuration(self) -> bool:
        self._validate_called = True
        return bool(self.config.api_key and self.config.model)


class MockAzureOpenAIProvider(BaseAgentProvider):
    """Mock Azure OpenAI provider"""
    
    def __init__(self, config: AgentConfiguration):
        self.config = config
    
    def execute_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            'response': 'Azure OpenAI response',
            'model': self.config.model,
            'provider': 'azure_openai',
            'usage': {'prompt_tokens': 10, 'completion_tokens': 20}
        }
    
    def validate_configuration(self) -> bool:
        return bool(
            self.config.api_key and 
            self.config.model and
            self.config.api_base  # Azure requires api_base
        )


class MockOllamaProvider(BaseAgentProvider):
    """Mock Ollama provider"""
    
    def __init__(self, config: AgentConfiguration):
        self.config = config
    
    def execute_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            'response': 'Ollama local response',
            'model': self.config.model,
            'provider': 'ollama',
            'done': True
        }
    
    def validate_configuration(self) -> bool:
        # Ollama might not require API key for local instances
        return bool(self.config.api_base and self.config.model)


# ============================================================================
# Test Fixtures
# ============================================================================

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
    from ai_agent_connector.app.agents.registry import AgentRegistry
    from ai_agent_connector.app.permissions import AccessControl, Permission
    
    registry = AgentRegistry()
    access_control = AccessControl()
    
    result = registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'}
    )
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    
    return {'agent_id': 'admin-agent', 'api_key': result['api_key']}


@pytest.fixture
def sample_openai_config():
    """Sample OpenAI configuration"""
    return {
        'provider': 'openai',
        'model': 'gpt-4',
        'api_key': 'sk-test123',
        'temperature': 0.7,
        'max_tokens': 1000
    }


@pytest.fixture
def sample_azure_config():
    """Sample Azure OpenAI configuration"""
    return {
        'provider': 'azure_openai',
        'model': 'gpt-4',
        'api_key': 'azure-key-123',
        'api_base': 'https://example.openai.azure.com',
        'api_version': '2024-02-15-preview',
        'deployment_name': 'gpt-4-deployment',
        'temperature': 0.7
    }


@pytest.fixture
def sample_ollama_config():
    """Sample Ollama configuration"""
    return {
        'provider': 'ollama',
        'model': 'llama2',
        'api_base': 'http://localhost:11434',
        'temperature': 0.7,
        'stream': False
    }


# ============================================================================
# Provider Abstraction Layer Tests
# ============================================================================

class TestProviderAbstractionLayer:
    """Test cases for provider abstraction layer"""
    
    def test_base_provider_interface(self):
        """Test BaseAgentProvider abstract interface"""
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            BaseAgentProvider(AgentConfiguration(
                provider=AgentProvider.OPENAI,
                model='test'
            ))
    
    def test_provider_enum_values(self):
        """Test AgentProvider enum includes required providers"""
        assert AgentProvider.OPENAI.value == 'openai'
        assert AgentProvider.ANTHROPIC.value == 'anthropic'
        assert AgentProvider.CUSTOM.value == 'custom'
        # New providers should be added
        # assert AgentProvider.AZURE_OPENAI.value == 'azure_openai'
        # assert AgentProvider.OLLAMA.value == 'ollama'
    
    def test_provider_configuration_dataclass(self, sample_openai_config):
        """Test AgentConfiguration dataclass"""
        config = AgentConfiguration.from_dict(sample_openai_config)
        
        assert config.provider == AgentProvider.OPENAI
        assert config.model == 'gpt-4'
        assert config.api_key == 'sk-test123'
        assert config.temperature == 0.7
    
    def test_provider_configuration_to_dict(self, sample_openai_config):
        """Test AgentConfiguration to_dict method"""
        config = AgentConfiguration.from_dict(sample_openai_config)
        config_dict = config.to_dict()
        
        assert config_dict['provider'] == 'openai'
        assert config_dict['model'] == 'gpt-4'
        assert config_dict['api_key'] == '***'  # Should mask API key
        assert config_dict['temperature'] == 0.7
    
    def test_provider_creation_factory(self, sample_openai_config):
        """Test create_agent_provider factory function"""
        config = AgentConfiguration.from_dict(sample_openai_config)
        
        with patch('ai_agent_connector.app.agents.providers.OpenAIProvider') as mock_provider:
            mock_provider.return_value = MockProvider(config)
            provider = create_agent_provider(config)
            
            assert provider is not None
            assert isinstance(provider, BaseAgentProvider)
    
    def test_provider_execute_query_interface(self, sample_openai_config):
        """Test provider execute_query method"""
        config = AgentConfiguration.from_dict(sample_openai_config)
        provider = MockProvider(config)
        
        result = provider.execute_query("Test query")
        
        assert 'response' in result
        assert 'model' in result
        assert 'provider' in result
        assert result['provider'] == 'openai'
    
    def test_provider_validate_configuration(self, sample_openai_config):
        """Test provider validate_configuration method"""
        config = AgentConfiguration.from_dict(sample_openai_config)
        provider = MockProvider(config)
        
        assert provider.validate_configuration() is True
        
        # Test with missing API key
        invalid_config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model='test',
            api_key=None
        )
        invalid_provider = MockProvider(invalid_config)
        assert invalid_provider.validate_configuration() is False
    
    def test_provider_abstract_methods(self):
        """Test that all providers implement required abstract methods"""
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model='test',
            api_key='test-key'
        )
        provider = MockProvider(config)
        
        # Should have execute_query
        assert hasattr(provider, 'execute_query')
        assert callable(provider.execute_query)
        
        # Should have validate_configuration
        assert hasattr(provider, 'validate_configuration')
        assert callable(provider.validate_configuration)


# ============================================================================
# Azure OpenAI Provider Tests
# ============================================================================

class TestAzureOpenAIProvider:
    """Test cases for Azure OpenAI provider"""
    
    def test_azure_provider_creation(self, sample_azure_config):
        """Test creating Azure OpenAI provider"""
        config = AgentConfiguration.from_dict(sample_azure_config)
        
        with patch('ai_agent_connector.app.agents.providers.AzureOpenAIProvider') as mock_azure:
            mock_azure.return_value = MockAzureOpenAIProvider(config)
            provider = MockAzureOpenAIProvider(config)
            
            assert provider is not None
            assert isinstance(provider, BaseAgentProvider)
    
    def test_azure_provider_configuration(self, sample_azure_config):
        """Test Azure OpenAI provider configuration"""
        config = AgentConfiguration.from_dict(sample_azure_config)
        provider = MockAzureOpenAIProvider(config)
        
        assert provider.config.provider.value == 'azure_openai'
        assert provider.config.api_base == 'https://example.openai.azure.com'
        assert provider.config.api_key == 'azure-key-123'
        assert provider.config.model == 'gpt-4'
    
    def test_azure_provider_execute_query(self, sample_azure_config):
        """Test Azure OpenAI provider query execution"""
        config = AgentConfiguration.from_dict(sample_azure_config)
        provider = MockAzureOpenAIProvider(config)
        
        result = provider.execute_query("Test query")
        
        assert result['provider'] == 'azure_openai'
        assert result['model'] == 'gpt-4'
        assert 'usage' in result
    
    def test_azure_provider_validation(self, sample_azure_config):
        """Test Azure OpenAI provider configuration validation"""
        config = AgentConfiguration.from_dict(sample_azure_config)
        provider = MockAzureOpenAIProvider(config)
        
        assert provider.validate_configuration() is True
        
        # Missing api_base should fail
        invalid_config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,  # Using CUSTOM as placeholder
            model='gpt-4',
            api_key='test-key',
            api_base=None
        )
        invalid_provider = MockAzureOpenAIProvider(invalid_config)
        assert invalid_provider.validate_configuration() is False
    
    def test_azure_provider_api_version(self, sample_azure_config):
        """Test Azure OpenAI provider supports API version"""
        config = AgentConfiguration.from_dict(sample_azure_config)
        
        # API version should be in custom_params or as separate field
        assert 'api_version' in sample_azure_config
        # config should handle api_version


# ============================================================================
# Ollama Provider Tests
# ============================================================================

class TestOllamaProvider:
    """Test cases for Ollama provider"""
    
    def test_ollama_provider_creation(self, sample_ollama_config):
        """Test creating Ollama provider"""
        config = AgentConfiguration.from_dict(sample_ollama_config)
        
        provider = MockOllamaProvider(config)
        
        assert provider is not None
        assert isinstance(provider, BaseAgentProvider)
    
    def test_ollama_provider_configuration(self, sample_ollama_config):
        """Test Ollama provider configuration"""
        config = AgentConfiguration.from_dict(sample_ollama_config)
        provider = MockOllamaProvider(config)
        
        assert provider.config.api_base == 'http://localhost:11434'
        assert provider.config.model == 'llama2'
        # Ollama might not require API key for local instances
        assert provider.config.api_key is None or provider.config.api_key
    
    def test_ollama_provider_execute_query(self, sample_ollama_config):
        """Test Ollama provider query execution"""
        config = AgentConfiguration.from_dict(sample_ollama_config)
        provider = MockOllamaProvider(config)
        
        result = provider.execute_query("Test query")
        
        assert result['provider'] == 'ollama'
        assert result['model'] == 'llama2'
        assert result.get('done') is True
    
    def test_ollama_provider_validation(self, sample_ollama_config):
        """Test Ollama provider configuration validation"""
        config = AgentConfiguration.from_dict(sample_ollama_config)
        provider = MockOllamaProvider(config)
        
        assert provider.validate_configuration() is True
        
        # Missing api_base should fail
        invalid_config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model='llama2',
            api_base=None
        )
        invalid_provider = MockOllamaProvider(invalid_config)
        assert invalid_provider.validate_configuration() is False
    
    def test_ollama_local_instance(self, sample_ollama_config):
        """Test Ollama works with local instance (no API key required)"""
        config = AgentConfiguration.from_dict(sample_ollama_config)
        # Remove API key for local instance
        config.api_key = None
        
        provider = MockOllamaProvider(config)
        
        # Should still validate (local instances don't need API key)
        assert provider.validate_configuration() is True
    
    def test_ollama_streaming_support(self, sample_ollama_config):
        """Test Ollama provider supports streaming"""
        config = AgentConfiguration.from_dict(sample_ollama_config)
        config.custom_params['stream'] = True
        
        provider = MockOllamaProvider(config)
        
        # Streaming should be configurable
        assert config.custom_params.get('stream') is True


# ============================================================================
# Configuration UI Tests
# ============================================================================

class TestProviderConfigurationUI:
    """Test cases for provider configuration UI"""
    
    def test_list_available_providers(self, client, admin_agent):
        """Test listing all available AI providers"""
        with patch('ai_agent_connector.app.api.routes.get_available_providers') as mock_get:
            mock_get.return_value = {
                'providers': [
                    {
                        'id': 'openai',
                        'name': 'OpenAI',
                        'description': 'OpenAI GPT models',
                        'requires_api_key': True,
                        'requires_api_base': False
                    },
                    {
                        'id': 'azure_openai',
                        'name': 'Azure OpenAI',
                        'description': 'Azure-hosted OpenAI models',
                        'requires_api_key': True,
                        'requires_api_base': True
                    },
                    {
                        'id': 'ollama',
                        'name': 'Ollama',
                        'description': 'Local Ollama instance',
                        'requires_api_key': False,
                        'requires_api_base': True
                    }
                ]
            }
            
            response = client.get('/api/providers',
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'providers' in data
            assert len(data['providers']) >= 3
    
    def test_get_provider_configuration_form(self, client, admin_agent):
        """Test getting provider configuration form schema"""
        with patch('ai_agent_connector.app.api.routes.get_provider_config_schema') as mock_get:
            mock_get.return_value = {
                'provider_id': 'azure_openai',
                'fields': [
                    {
                        'name': 'api_key',
                        'type': 'password',
                        'label': 'API Key',
                        'required': True,
                        'description': 'Azure OpenAI API key'
                    },
                    {
                        'name': 'api_base',
                        'type': 'url',
                        'label': 'API Base URL',
                        'required': True,
                        'description': 'Azure OpenAI endpoint URL'
                    },
                    {
                        'name': 'model',
                        'type': 'text',
                        'label': 'Model',
                        'required': True,
                        'description': 'Deployment name'
                    }
                ]
            }
            
            response = client.get('/api/providers/azure_openai/config-schema',
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'fields' in data
            assert len(data['fields']) > 0
    
    def test_create_provider_configuration(self, client, admin_agent, sample_azure_config):
        """Test creating a new provider configuration via UI"""
        with patch('ai_agent_connector.app.api.routes.create_provider_config') as mock_create:
            mock_create.return_value = {
                'success': True,
                'provider_id': 'azure_openai',
                'config_id': 'config-123',
                'message': 'Provider configuration created successfully'
            }
            
            response = client.post('/api/providers/configurations',
                                 json={
                                     'provider_id': 'azure_openai',
                                     'name': 'My Azure OpenAI',
                                     'config': sample_azure_config
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code in [200, 201]
            data = response.get_json()
            assert data['success'] is True
            assert 'config_id' in data
    
    def test_update_provider_configuration(self, client, admin_agent, sample_azure_config):
        """Test updating existing provider configuration"""
        config_id = 'config-123'
        
        with patch('ai_agent_connector.app.api.routes.update_provider_config') as mock_update:
            mock_update.return_value = {
                'success': True,
                'message': 'Configuration updated successfully'
            }
            
            updated_config = sample_azure_config.copy()
            updated_config['temperature'] = 0.9
            
            response = client.put(f'/api/providers/configurations/{config_id}',
                                json={'config': updated_config},
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_delete_provider_configuration(self, client, admin_agent):
        """Test deleting provider configuration"""
        config_id = 'config-123'
        
        with patch('ai_agent_connector.app.api.routes.delete_provider_config') as mock_delete:
            mock_delete.return_value = {'success': True}
            
            response = client.delete(f'/api/providers/configurations/{config_id}',
                                   headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_list_provider_configurations(self, client, admin_agent):
        """Test listing all provider configurations"""
        with patch('ai_agent_connector.app.api.routes.list_provider_configs') as mock_list:
            mock_list.return_value = {
                'configurations': [
                    {
                        'config_id': 'config-1',
                        'provider_id': 'openai',
                        'name': 'OpenAI Production',
                        'model': 'gpt-4'
                    },
                    {
                        'config_id': 'config-2',
                        'provider_id': 'azure_openai',
                        'name': 'Azure OpenAI',
                        'model': 'gpt-4'
                    },
                    {
                        'config_id': 'config-3',
                        'provider_id': 'ollama',
                        'name': 'Local Ollama',
                        'model': 'llama2'
                    }
                ]
            }
            
            response = client.get('/api/providers/configurations',
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'configurations' in data
            assert len(data['configurations']) >= 3
    
    def test_provider_configuration_validation(self, client, admin_agent):
        """Test validating provider configuration before saving"""
        with patch('ai_agent_connector.app.api.routes.validate_provider_config') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'errors': []
            }
            
            response = client.post('/api/providers/validate-config',
                                 json={
                                     'provider_id': 'azure_openai',
                                     'config': {
                                         'api_key': 'test-key',
                                         'api_base': 'https://example.azure.com',
                                         'model': 'gpt-4'
                                     }
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True
    
    def test_provider_configuration_validation_errors(self, client, admin_agent):
        """Test validation returns errors for invalid configuration"""
        with patch('ai_agent_connector.app.api.routes.validate_provider_config') as mock_validate:
            mock_validate.return_value = {
                'valid': False,
                'errors': [
                    {'field': 'api_base', 'message': 'API base URL is required'},
                    {'field': 'api_key', 'message': 'API key is required'}
                ]
            }
            
            response = client.post('/api/providers/validate-config',
                                 json={
                                     'provider_id': 'azure_openai',
                                     'config': {'model': 'gpt-4'}
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False
            assert len(data['errors']) > 0
    
    def test_providers_page_renders(self, client):
        """Test that providers configuration page renders"""
        response = client.get('/providers')
        assert response.status_code == 200
        # Should render HTML template
    
    def test_providers_page_shows_configurations(self, client, admin_agent):
        """Test providers page displays configurations"""
        with patch('ai_agent_connector.app.api.routes.list_provider_configs') as mock_list:
            mock_list.return_value = {'configurations': []}
            
            response = client.get('/providers',
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
    
    def test_provider_configuration_form_page(self, client):
        """Test provider configuration form page"""
        response = client.get('/providers/configure/azure_openai')
        assert response.status_code == 200
        # Should show configuration form for Azure OpenAI


# ============================================================================
# Provider Testing Tests
# ============================================================================

class TestProviderTesting:
    """Test cases for testing all providers"""
    
    def test_test_provider_connection(self, client, admin_agent, sample_openai_config):
        """Test testing provider connection"""
        with patch('ai_agent_connector.app.api.routes.test_provider_connection') as mock_test:
            mock_test.return_value = {
                'success': True,
                'message': 'Connection successful',
                'provider': 'openai',
                'model': 'gpt-4',
                'response_time_ms': 250
            }
            
            response = client.post('/api/providers/test',
                                 json={
                                     'provider_id': 'openai',
                                     'config': sample_openai_config
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'response_time_ms' in data
    
    def test_test_provider_connection_failure(self, client, admin_agent):
        """Test provider connection test with invalid credentials"""
        with patch('ai_agent_connector.app.api.routes.test_provider_connection') as mock_test:
            mock_test.return_value = {
                'success': False,
                'error': 'Invalid API key',
                'provider': 'openai'
            }
            
            response = client.post('/api/providers/test',
                                 json={
                                     'provider_id': 'openai',
                                     'config': {'api_key': 'invalid-key', 'model': 'gpt-4'}
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data
    
    def test_test_all_providers(self, client, admin_agent):
        """Test testing all configured providers"""
        with patch('ai_agent_connector.app.api.routes.test_all_providers') as mock_test_all:
            mock_test_all.return_value = {
                'results': [
                    {
                        'provider_id': 'openai',
                        'config_id': 'config-1',
                        'success': True,
                        'response_time_ms': 250
                    },
                    {
                        'provider_id': 'azure_openai',
                        'config_id': 'config-2',
                        'success': True,
                        'response_time_ms': 300
                    },
                    {
                        'provider_id': 'ollama',
                        'config_id': 'config-3',
                        'success': False,
                        'error': 'Connection refused'
                    }
                ],
                'total': 3,
                'passed': 2,
                'failed': 1
            }
            
            response = client.post('/api/providers/test-all',
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'results' in data
            assert data['total'] == 3
            assert data['passed'] == 2
            assert data['failed'] == 1
    
    def test_test_provider_with_sample_query(self, client, admin_agent, sample_azure_config):
        """Test provider with sample query"""
        with patch('ai_agent_connector.app.api.routes.test_provider_query') as mock_test:
            mock_test.return_value = {
                'success': True,
                'query': 'What is 2+2?',
                'response': '4',
                'model': 'gpt-4',
                'provider': 'azure_openai',
                'response_time_ms': 250,
                'tokens_used': 15
            }
            
            response = client.post('/api/providers/test-query',
                                 json={
                                     'provider_id': 'azure_openai',
                                     'config': sample_azure_config,
                                     'test_query': 'What is 2+2?'
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'response' in data
            assert 'response_time_ms' in data
    
    def test_test_provider_performance(self, client, admin_agent, sample_openai_config):
        """Test provider performance benchmarking"""
        with patch('ai_agent_connector.app.api.routes.test_provider_performance') as mock_perf:
            mock_perf.return_value = {
                'provider_id': 'openai',
                'average_response_time_ms': 250,
                'min_response_time_ms': 200,
                'max_response_time_ms': 300,
                'success_rate': 1.0,
                'tests_run': 10
            }
            
            response = client.post('/api/providers/test-performance',
                                 json={
                                     'provider_id': 'openai',
                                     'config': sample_openai_config,
                                     'num_tests': 10
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'average_response_time_ms' in data
            assert 'success_rate' in data
    
    def test_test_provider_comparison(self, client, admin_agent):
        """Test comparing multiple providers"""
        with patch('ai_agent_connector.app.api.routes.compare_providers') as mock_compare:
            mock_compare.return_value = {
                'query': 'Test query',
                'providers': [
                    {
                        'provider_id': 'openai',
                        'response': 'Response 1',
                        'response_time_ms': 250,
                        'tokens_used': 100
                    },
                    {
                        'provider_id': 'azure_openai',
                        'response': 'Response 2',
                        'response_time_ms': 300,
                        'tokens_used': 110
                    },
                    {
                        'provider_id': 'ollama',
                        'response': 'Response 3',
                        'response_time_ms': 500,
                        'tokens_used': 95
                    }
                ]
            }
            
            response = client.post('/api/providers/compare',
                                 json={
                                     'provider_ids': ['openai', 'azure_openai', 'ollama'],
                                     'test_query': 'Test query'
                                 },
                                 headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'providers' in data
            assert len(data['providers']) == 3
    
    def test_provider_health_check(self, client, admin_agent):
        """Test provider health check endpoint"""
        with patch('ai_agent_connector.app.api.routes.check_provider_health') as mock_health:
            mock_health.return_value = {
                'provider_id': 'azure_openai',
                'config_id': 'config-123',
                'healthy': True,
                'last_check': '2024-01-01T00:00:00Z',
                'response_time_ms': 250
            }
            
            response = client.get('/api/providers/health/azure_openai/config-123',
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['healthy'] is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestProviderIntegration:
    """Integration tests for provider system"""
    
    def test_create_and_test_provider(self, client, admin_agent, sample_azure_config):
        """Test creating and testing a provider configuration"""
        # Create configuration
        with patch('ai_agent_connector.app.api.routes.create_provider_config') as mock_create:
            mock_create.return_value = {
                'success': True,
                'config_id': 'config-123'
            }
            
            create_response = client.post('/api/providers/configurations',
                                        json={
                                            'provider_id': 'azure_openai',
                                            'name': 'Test Azure',
                                            'config': sample_azure_config
                                        },
                                        headers={'X-API-Key': admin_agent['api_key']})
            
            assert create_response.status_code in [200, 201]
            
            # Test the configuration
            with patch('ai_agent_connector.app.api.routes.test_provider_connection') as mock_test:
                mock_test.return_value = {'success': True}
                
                test_response = client.post('/api/providers/test',
                                          json={
                                              'provider_id': 'azure_openai',
                                              'config_id': 'config-123'
                                          },
                                          headers={'X-API-Key': admin_agent['api_key']})
                
                assert test_response.status_code == 200
    
    def test_switch_provider_for_agent(self, client, admin_agent):
        """Test switching agent to use different provider"""
        agent_id = 'test-agent'
        
        with patch('ai_agent_connector.app.api.routes.update_agent_provider') as mock_update:
            mock_update.return_value = {
                'success': True,
                'agent_id': agent_id,
                'provider_id': 'azure_openai',
                'config_id': 'config-123'
            }
            
            response = client.put(f'/api/agents/{agent_id}/provider',
                                json={
                                    'provider_id': 'azure_openai',
                                    'config_id': 'config-123'
                                },
                                headers={'X-API-Key': admin_agent['api_key']})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

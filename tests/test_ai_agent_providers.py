"""
Tests for AI agent providers (OpenAI, Anthropic, custom)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_agent_connector.app.agents.providers import (
    AgentProvider,
    AgentConfiguration,
    OpenAIProvider,
    AnthropicProvider,
    CustomProvider,
    create_agent_provider
)


class TestAgentConfiguration:
    """Tests for AgentConfiguration"""
    
    def test_configuration_to_dict(self):
        """Test converting configuration to dictionary"""
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
            temperature=0.8
        )
        
        result = config.to_dict()
        
        assert result['provider'] == 'openai'
        assert result['model'] == 'gpt-4'
        assert result['api_key'] == '***'
        assert result['temperature'] == 0.8
    
    def test_configuration_from_dict(self):
        """Test creating configuration from dictionary"""
        data = {
            'provider': 'anthropic',
            'model': 'claude-3-opus',
            'api_key': 'test-key',
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        config = AgentConfiguration.from_dict(data)
        
        assert config.provider == AgentProvider.ANTHROPIC
        assert config.model == 'claude-3-opus'
        assert config.api_key == 'test-key'
        assert config.temperature == 0.7
        assert config.max_tokens == 1000


class TestOpenAIProvider:
    """Tests for OpenAI provider"""
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_openai_provider_execute_query(self, mock_openai_class):
        """Test OpenAI provider query execution"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        provider = OpenAIProvider(config)
        result = provider.execute_query("Test query")
        
        assert result['response'] == "Test response"
        assert result['model'] == "gpt-4"
        assert result['provider'] == 'openai'
        assert result['usage']['total_tokens'] == 30
    
    def test_openai_provider_validate_configuration(self):
        """Test OpenAI provider configuration validation"""
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        provider = OpenAIProvider(config)
        assert provider.validate_configuration() is True
        
        # Missing API key
        config_no_key = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4"
        )
        provider_no_key = OpenAIProvider(config_no_key)
        assert provider_no_key.validate_configuration() is False


class TestAnthropicProvider:
    """Tests for Anthropic provider"""
    
    @patch('ai_agent_connector.app.agents.providers.anthropic')
    def test_anthropic_provider_execute_query(self, mock_anthropic):
        """Test Anthropic provider query execution"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Claude response"
        mock_response.model = "claude-3-opus"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 25
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        
        config = AgentConfiguration(
            provider=AgentProvider.ANTHROPIC,
            model="claude-3-opus",
            api_key="test-key"
        )
        
        provider = AnthropicProvider(config)
        result = provider.execute_query("Test query")
        
        assert result['response'] == "Claude response"
        assert result['model'] == "claude-3-opus"
        assert result['provider'] == 'anthropic'
        assert result['usage']['input_tokens'] == 15
    
    def test_anthropic_provider_validate_configuration(self):
        """Test Anthropic provider configuration validation"""
        config = AgentConfiguration(
            provider=AgentProvider.ANTHROPIC,
            model="claude-3-opus",
            api_key="test-key"
        )
        
        provider = AnthropicProvider(config)
        assert provider.validate_configuration() is True


class TestCustomProvider:
    """Tests for custom provider"""
    
    @patch('ai_agent_connector.app.agents.providers.requests')
    def test_custom_provider_execute_query(self, mock_requests):
        """Test custom provider query execution"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Custom response'}
        mock_response.raise_for_status = MagicMock()
        mock_requests.Session.return_value.post.return_value = mock_response
        
        config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model",
            api_base="https://api.example.com/query",
            api_key="test-key"
        )
        
        provider = CustomProvider(config)
        result = provider.execute_query("Test query")
        
        assert result['response'] == 'Custom response'
        assert result['model'] == 'custom-model'
        assert result['provider'] == 'custom'
    
    def test_custom_provider_validate_configuration(self):
        """Test custom provider configuration validation"""
        config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model",
            api_base="https://api.example.com"
        )
        
        provider = CustomProvider(config)
        assert provider.validate_configuration() is True
        
        # Missing api_base
        config_no_base = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model"
        )
        provider_no_base = CustomProvider(config_no_base)
        assert provider_no_base.validate_configuration() is False


class TestCreateAgentProvider:
    """Tests for provider factory"""
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider"""
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        provider = create_agent_provider(config)
        assert isinstance(provider, OpenAIProvider)
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider"""
        config = AgentConfiguration(
            provider=AgentProvider.ANTHROPIC,
            model="claude-3-opus",
            api_key="test-key"
        )
        
        provider = create_agent_provider(config)
        assert isinstance(provider, AnthropicProvider)
    
    def test_create_custom_provider(self):
        """Test creating custom provider"""
        config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model",
            api_base="https://api.example.com"
        )
        
        provider = create_agent_provider(config)
        assert isinstance(provider, CustomProvider)
    
    def test_create_provider_invalid(self):
        """Test creating provider with invalid type"""
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,  # Will be overridden
            model="test"
        )
        config.provider = "invalid"
        
        with pytest.raises(ValueError):
            create_agent_provider(config)


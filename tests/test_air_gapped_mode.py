"""
Tests for Air-Gapped Mode functionality
Tests network isolation, local AI model support, and external API blocking
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from ai_agent_connector.app.utils.air_gapped import (
    is_air_gapped_mode,
    validate_provider_allowed,
    is_external_url,
    get_local_ai_config,
    AirGappedModeError
)
from ai_agent_connector.app.agents.providers import (
    AgentProvider,
    AgentConfiguration,
    OpenAIProvider,
    AnthropicProvider,
    CustomProvider,
    LocalProvider,
    create_agent_provider
)
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager
from ai_agent_connector.app.utils.nl_to_sql import NLToSQLConverter


class TestAirGappedModeUtilities:
    """Tests for air-gapped mode utility functions"""
    
    def test_is_air_gapped_mode_false_by_default(self):
        """Test that air-gapped mode is False by default"""
        # Clear environment variable
        if 'AIR_GAPPED_MODE' in os.environ:
            del os.environ['AIR_GAPPED_MODE']
        
        assert is_air_gapped_mode() is False
    
    def test_is_air_gapped_mode_true(self):
        """Test enabling air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        assert is_air_gapped_mode() is True
        
        os.environ['AIR_GAPPED_MODE'] = '1'
        assert is_air_gapped_mode() is True
        
        os.environ['AIR_GAPPED_MODE'] = 'yes'
        assert is_air_gapped_mode() is True
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_is_air_gapped_mode_false(self):
        """Test disabling air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'false'
        assert is_air_gapped_mode() is False
        
        os.environ['AIR_GAPPED_MODE'] = '0'
        assert is_air_gapped_mode() is False
        
        os.environ['AIR_GAPPED_MODE'] = 'no'
        assert is_air_gapped_mode() is False
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_validate_provider_allowed_local(self):
        """Test that local provider is always allowed"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        # Should not raise
        validate_provider_allowed('local')
        validate_provider_allowed('LOCAL')
        validate_provider_allowed('Local')
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_validate_provider_allowed_external_when_disabled(self):
        """Test that external providers are allowed when air-gapped mode is disabled"""
        if 'AIR_GAPPED_MODE' in os.environ:
            del os.environ['AIR_GAPPED_MODE']
        
        # Should not raise
        validate_provider_allowed('openai')
        validate_provider_allowed('anthropic')
        validate_provider_allowed('custom', 'https://api.example.com')
    
    def test_validate_provider_allowed_external_blocked(self):
        """Test that external providers are blocked in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        with pytest.raises(AirGappedModeError) as exc_info:
            validate_provider_allowed('openai')
        assert 'openai' in str(exc_info.value).lower()
        assert 'not allowed' in str(exc_info.value).lower()
        
        with pytest.raises(AirGappedModeError) as exc_info:
            validate_provider_allowed('anthropic')
        assert 'anthropic' in str(exc_info.value).lower()
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_validate_provider_custom_local_allowed(self):
        """Test that custom provider with local URL is allowed"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        # Should not raise
        validate_provider_allowed('custom', 'http://localhost:8080')
        validate_provider_allowed('custom', 'http://127.0.0.1:5000')
        validate_provider_allowed('custom', 'http://192.168.1.100:8080')
        validate_provider_allowed('custom', 'http://10.0.0.1:8080')
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_validate_provider_custom_external_blocked(self):
        """Test that custom provider with external URL is blocked"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        with pytest.raises(AirGappedModeError) as exc_info:
            validate_provider_allowed('custom', 'https://api.openai.com')
        assert 'external' in str(exc_info.value).lower()
        
        with pytest.raises(AirGappedModeError) as exc_info:
            validate_provider_allowed('custom', 'https://api.anthropic.com')
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_is_external_url_localhost(self):
        """Test that localhost URLs are not external"""
        assert is_external_url('http://localhost:8080') is False
        assert is_external_url('http://127.0.0.1:5000') is False
        assert is_external_url('http://0.0.0.0:8080') is False
    
    def test_is_external_url_private_network(self):
        """Test that private network URLs are not external"""
        assert is_external_url('http://192.168.1.100:8080') is False
        assert is_external_url('http://10.0.0.1:8080') is False
        assert is_external_url('http://172.16.0.1:8080') is False
        assert is_external_url('http://172.31.255.255:8080') is False
    
    def test_is_external_url_external(self):
        """Test that external URLs are detected"""
        assert is_external_url('https://api.openai.com') is True
        assert is_external_url('https://api.anthropic.com') is True
        assert is_external_url('http://example.com:8080') is True
        assert is_external_url('https://8.8.8.8:8080') is True  # Public IP
    
    def test_get_local_ai_config_defaults(self):
        """Test getting local AI config with defaults"""
        # Clear environment variables
        for key in ['LOCAL_AI_BASE_URL', 'LOCAL_AI_MODEL', 'LOCAL_AI_API_KEY']:
            if key in os.environ:
                del os.environ[key]
        
        config = get_local_ai_config()
        
        assert config['base_url'] == 'http://localhost:11434'
        assert config['model'] == 'llama2'
        assert config.get('api_key') is None
    
    def test_get_local_ai_config_custom(self):
        """Test getting local AI config with custom values"""
        os.environ['LOCAL_AI_BASE_URL'] = 'http://192.168.1.100:8080'
        os.environ['LOCAL_AI_MODEL'] = 'mistral'
        os.environ['LOCAL_AI_API_KEY'] = 'test-key'
        
        config = get_local_ai_config()
        
        assert config['base_url'] == 'http://192.168.1.100:8080'
        assert config['model'] == 'mistral'
        assert config['api_key'] == 'test-key'
        
        # Cleanup
        for key in ['LOCAL_AI_BASE_URL', 'LOCAL_AI_MODEL', 'LOCAL_AI_API_KEY']:
            if key in os.environ:
                del os.environ[key]


class TestLocalProvider:
    """Tests for Local AI provider"""
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_local_provider_creation(self, mock_openai_class):
        """Test creating a local provider"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2",
            api_base="http://localhost:11434"
        )
        
        provider = LocalProvider(config)
        assert provider.config.model == "llama2"
        assert provider.config.api_base == "http://localhost:11434"
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_local_provider_default_base_url(self, mock_openai_class):
        """Test local provider uses default base URL if not provided"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Clear environment variable
        if 'OLLAMA_BASE_URL' in os.environ:
            del os.environ['OLLAMA_BASE_URL']
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2"
        )
        
        provider = LocalProvider(config)
        # Should use default
        assert provider.config.api_base is None  # Will use default in _get_client
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_local_provider_execute_query(self, mock_openai_class):
        """Test local provider query execution"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Local AI response"
        mock_response.model = "llama2"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2",
            api_base="http://localhost:11434"
        )
        
        provider = LocalProvider(config)
        result = provider.execute_query("Test query")
        
        assert result['response'] == "Local AI response"
        assert result['model'] == "llama2"
        assert result['provider'] == 'local'
        assert result['usage']['total_tokens'] == 30
        
        # Verify client was called with correct base_url
        mock_openai_class.assert_called_once()
        call_kwargs = mock_openai_class.call_args[1]
        assert call_kwargs['base_url'] == "http://localhost:11434"
    
    def test_local_provider_validate_configuration(self):
        """Test local provider configuration validation"""
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2"
        )
        
        provider = LocalProvider(config)
        assert provider.validate_configuration() is True
        
        # Missing model
        config_no_model = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model=""
        )
        provider_no_model = LocalProvider(config_no_model)
        assert provider_no_model.validate_configuration() is False


class TestProviderBlocking:
    """Tests for blocking external providers in air-gapped mode"""
    
    def test_openai_provider_blocked_in_air_gapped_mode(self):
        """Test that OpenAI provider is blocked in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        with pytest.raises(AirGappedModeError) as exc_info:
            OpenAIProvider(config)
        
        assert 'openai' in str(exc_info.value).lower()
        assert 'not allowed' in str(exc_info.value).lower()
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_anthropic_provider_blocked_in_air_gapped_mode(self):
        """Test that Anthropic provider is blocked in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.ANTHROPIC,
            model="claude-3-opus",
            api_key="test-key"
        )
        
        with pytest.raises(AirGappedModeError) as exc_info:
            AnthropicProvider(config)
        
        assert 'anthropic' in str(exc_info.value).lower()
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_custom_provider_external_blocked(self):
        """Test that custom provider with external URL is blocked"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model",
            api_base="https://api.openai.com"
        )
        
        with pytest.raises(AirGappedModeError) as exc_info:
            CustomProvider(config)
        
        assert 'external' in str(exc_info.value).lower()
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_custom_provider_local_allowed(self):
        """Test that custom provider with local URL is allowed"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model",
            api_base="http://localhost:8080"
        )
        
        # Should not raise
        provider = CustomProvider(config)
        assert provider is not None
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_local_provider_allowed_in_air_gapped_mode(self):
        """Test that local provider is allowed in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2",
            api_base="http://localhost:11434"
        )
        
        # Should not raise
        provider = LocalProvider(config)
        assert provider is not None
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_create_agent_provider_local(self):
        """Test creating local provider via factory"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2",
            api_base="http://localhost:11434"
        )
        
        provider = create_agent_provider(config)
        assert isinstance(provider, LocalProvider)
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_create_agent_provider_external_blocked(self):
        """Test that factory blocks external providers"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        with pytest.raises(AirGappedModeError):
            create_agent_provider(config)
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']


class TestAIAgentManagerAirGapped:
    """Tests for AIAgentManager with air-gapped mode"""
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_register_local_agent_in_air_gapped_mode(self, mock_openai):
        """Test registering local agent in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2",
            api_base="http://localhost:11434"
        )
        
        result = manager.register_ai_agent(
            agent_id="local-agent",
            config=config
        )
        
        assert result['agent_id'] == "local-agent"
        assert result['provider'] == "local"
        assert result['model'] == "llama2"
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_register_external_agent_blocked(self):
        """Test that registering external agent is blocked in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        with pytest.raises(AirGappedModeError):
            manager.register_ai_agent(
                agent_id="external-agent",
                config=config
            )
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_execute_query_local_agent(self, mock_openai_class):
        """Test executing query with local agent"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Local response"
        mock_response.model = "llama2"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2",
            api_base="http://localhost:11434"
        )
        
        manager.register_ai_agent("local-agent", config)
        
        # Mock the provider's execute_query
        mock_provider = manager._providers["local-agent"]
        mock_provider.execute_query = Mock(return_value={
            "response": "Local response",
            "model": "llama2",
            "usage": {"total_tokens": 30},
            "provider": "local"
        })
        
        result = manager.execute_query("local-agent", "Test query")
        
        assert result['response'] == "Local response"
        assert result['provider'] == "local"
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']


class TestNLToSQLAirGapped:
    """Tests for NL to SQL converter with air-gapped mode"""
    
    def test_nl_to_sql_uses_local_in_air_gapped_mode(self):
        """Test that NL to SQL uses local model in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        os.environ['LOCAL_AI_BASE_URL'] = 'http://localhost:11434'
        os.environ['LOCAL_AI_MODEL'] = 'llama2'
        
        converter = NLToSQLConverter()
        
        # Should use local configuration
        assert converter.api_base == 'http://localhost:11434'
        assert converter.model == 'llama2'
        
        # Cleanup
        for key in ['AIR_GAPPED_MODE', 'LOCAL_AI_BASE_URL', 'LOCAL_AI_MODEL']:
            if key in os.environ:
                del os.environ[key]
    
    def test_nl_to_sql_uses_openai_when_not_air_gapped(self):
        """Test that NL to SQL uses OpenAI when air-gapped mode is disabled"""
        if 'AIR_GAPPED_MODE' in os.environ:
            del os.environ['AIR_GAPPED_MODE']
        
        os.environ['OPENAI_API_KEY'] = 'test-key'
        os.environ['OPENAI_MODEL'] = 'gpt-4o-mini'
        
        converter = NLToSQLConverter()
        
        # Should use OpenAI configuration
        assert converter.api_key == 'test-key'
        assert converter.model == 'gpt-4o-mini'
        
        # Cleanup
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        if 'OPENAI_MODEL' in os.environ:
            del os.environ['OPENAI_MODEL']
    
    @patch('ai_agent_connector.app.utils.nl_to_sql.OpenAI')
    def test_nl_to_sql_convert_with_local_model(self, mock_openai_class):
        """Test NL to SQL conversion with local model"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        os.environ['LOCAL_AI_BASE_URL'] = 'http://localhost:11434'
        os.environ['LOCAL_AI_MODEL'] = 'llama2'
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "SELECT * FROM users"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 60
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        converter = NLToSQLConverter()
        result = converter.convert_to_sql("Show all users")
        
        assert result['sql'] == "SELECT * FROM users"
        assert result['model'] == 'llama2'
        
        # Verify client was created with local base URL
        mock_openai_class.assert_called_once()
        call_kwargs = mock_openai_class.call_args[1]
        assert call_kwargs['base_url'] == 'http://localhost:11434'
        
        # Cleanup
        for key in ['AIR_GAPPED_MODE', 'LOCAL_AI_BASE_URL', 'LOCAL_AI_MODEL']:
            if key in os.environ:
                del os.environ[key]


class TestAirGappedIntegration:
    """Integration tests for air-gapped mode"""
    
    def test_full_workflow_air_gapped(self):
        """Test full workflow in air-gapped mode"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        os.environ['LOCAL_AI_BASE_URL'] = 'http://localhost:11434'
        os.environ['LOCAL_AI_MODEL'] = 'llama2'
        
        # Test that we can get local config
        config = get_local_ai_config()
        assert config['base_url'] == 'http://localhost:11434'
        assert config['model'] == 'llama2'
        
        # Test that local provider is allowed
        validate_provider_allowed('local')
        
        # Test that external providers are blocked
        with pytest.raises(AirGappedModeError):
            validate_provider_allowed('openai')
        
        # Cleanup
        for key in ['AIR_GAPPED_MODE', 'LOCAL_AI_BASE_URL', 'LOCAL_AI_MODEL']:
            if key in os.environ:
                del os.environ[key]
    
    def test_network_isolation_validation(self):
        """Test network isolation URL validation"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        # Local URLs should be allowed
        assert is_external_url('http://localhost:8080') is False
        assert is_external_url('http://127.0.0.1:5000') is False
        assert is_external_url('http://192.168.1.100:8080') is False
        assert is_external_url('http://10.0.0.1:8080') is False
        
        # External URLs should be blocked
        assert is_external_url('https://api.openai.com') is True
        assert is_external_url('https://api.anthropic.com') is True
        assert is_external_url('http://8.8.8.8:8080') is True
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_error_messages_are_helpful(self):
        """Test that error messages provide helpful guidance"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        try:
            validate_provider_allowed('openai')
            assert False, "Should have raised AirGappedModeError"
        except AirGappedModeError as e:
            error_msg = str(e).lower()
            assert 'openai' in error_msg
            assert 'not allowed' in error_msg
            assert 'local' in error_msg  # Should suggest using local
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']


class TestAirGappedModeEdgeCases:
    """Tests for edge cases in air-gapped mode"""
    
    def test_case_insensitive_air_gapped_mode(self):
        """Test that air-gapped mode is case-insensitive"""
        for value in ['TRUE', 'True', 'true', 'YES', 'Yes', 'yes', '1']:
            os.environ['AIR_GAPPED_MODE'] = value
            assert is_air_gapped_mode() is True
        
        for value in ['FALSE', 'False', 'false', 'NO', 'No', 'no', '0']:
            os.environ['AIR_GAPPED_MODE'] = value
            assert is_air_gapped_mode() is False
        
        # Cleanup
        if 'AIR_GAPPED_MODE' in os.environ:
            del os.environ['AIR_GAPPED_MODE']
    
    def test_empty_api_base_for_local(self):
        """Test that local provider works without explicit api_base"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.LOCAL,
            model="llama2"
            # No api_base - should use default
        )
        
        # Should not raise
        provider = LocalProvider(config)
        assert provider is not None
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_custom_provider_without_api_base(self):
        """Test custom provider validation without api_base"""
        os.environ['AIR_GAPPED_MODE'] = 'true'
        
        config = AgentConfiguration(
            provider=AgentProvider.CUSTOM,
            model="custom-model"
            # No api_base
        )
        
        # Should not raise during initialization (validation happens later)
        provider = CustomProvider(config)
        
        # But should raise when trying to execute
        with pytest.raises(ValueError):
            provider.execute_query("test")
        
        # Cleanup
        del os.environ['AIR_GAPPED_MODE']
    
    def test_ipv6_localhost(self):
        """Test IPv6 localhost detection"""
        assert is_external_url('http://[::1]:8080') is False
        assert is_external_url('http://[::1]') is False


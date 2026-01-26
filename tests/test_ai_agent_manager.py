"""
Tests for AI Agent Manager integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager
from ai_agent_connector.app.agents.providers import (
    AgentProvider,
    AgentConfiguration
)
from ai_agent_connector.app.utils.rate_limiter import RateLimitConfig
from ai_agent_connector.app.utils.retry_policy import RetryPolicy
from ai_agent_connector.app.utils.webhooks import WebhookConfig, WebhookEvent


class TestAIAgentManager:
    """Tests for AIAgentManager"""
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_register_ai_agent(self, mock_openai):
        """Test registering an AI agent"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        rate_limit = RateLimitConfig(queries_per_minute=60)
        
        result = manager.register_ai_agent(
            agent_id="agent1",
            config=config,
            rate_limit=rate_limit
        )
        
        assert result['agent_id'] == "agent1"
        assert result['provider'] == "openai"
        assert result['version'] == 1
    
    def test_register_ai_agent_duplicate(self):
        """Test that duplicate agent registration fails"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config)
        
        with pytest.raises(ValueError):
            manager.register_ai_agent("agent1", config)
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_execute_query_with_rate_limit(self, mock_openai):
        """Test executing query with rate limiting"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        rate_limit = RateLimitConfig(queries_per_minute=2)
        
        manager.register_ai_agent(
            agent_id="agent1",
            config=config,
            rate_limit=rate_limit
        )
        
        # Mock the provider's execute_query
        mock_provider = manager._providers["agent1"]
        mock_provider.execute_query = Mock(return_value={"response": "test"})
        
        # First two queries should succeed
        result1 = manager.execute_query("agent1", "query1")
        result2 = manager.execute_query("agent1", "query2")
        
        assert result1['response'] == "test"
        assert result2['response'] == "test"
        
        # Third query should be rate limited
        with pytest.raises(RuntimeError) as exc_info:
            manager.execute_query("agent1", "query3")
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_set_and_get_rate_limit(self, mock_openai):
        """Test setting and getting rate limits"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config)
        
        rate_limit = RateLimitConfig(queries_per_minute=100)
        manager.set_rate_limit("agent1", rate_limit)
        
        retrieved = manager.get_rate_limit("agent1")
        assert retrieved.queries_per_minute == 100
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_set_and_get_retry_policy(self, mock_openai):
        """Test setting and getting retry policies"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config)
        
        retry_policy = RetryPolicy(max_retries=5)
        manager.set_retry_policy("agent1", retry_policy)
        
        retrieved = manager.get_retry_policy("agent1")
        assert retrieved.max_retries == 5
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_rollback_configuration(self, mock_openai):
        """Test rolling back configuration"""
        manager = AIAgentManager()
        
        config1 = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config1)
        
        # Update configuration
        manager.update_ai_agent_configuration(
            "agent1",
            {"model": "gpt-3.5"}
        )
        
        # Rollback to version 1
        rollback_version = manager.rollback_configuration("agent1", version=1)
        
        assert rollback_version.version == 3  # New version created
        assert rollback_version.config["model"] == "gpt-4"  # From version 1
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_register_webhook(self, mock_openai):
        """Test registering webhooks"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config)
        
        webhook_config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        
        webhook_id = manager.register_webhook("agent1", webhook_config)
        
        assert webhook_id is not None
        webhooks = manager.get_webhooks("agent1")
        assert len(webhooks) == 1
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_list_agents(self, mock_openai):
        """Test listing all agents"""
        manager = AIAgentManager()
        
        config1 = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        config2 = AgentConfiguration(
            provider=AgentProvider.ANTHROPIC,
            model="claude-3",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config1)
        manager.register_ai_agent("agent2", config2)
        
        agents = manager.list_agents()
        
        assert "agent1" in agents
        assert "agent2" in agents
        assert len(agents) == 2
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_get_agent(self, mock_openai):
        """Test getting agent information"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        rate_limit = RateLimitConfig(queries_per_minute=60)
        
        manager.register_ai_agent(
            agent_id="agent1",
            config=config,
            rate_limit=rate_limit
        )
        
        agent_info = manager.get_agent("agent1")
        
        assert agent_info['agent_id'] == "agent1"
        assert agent_info['configuration']['model'] == "gpt-4"
        assert agent_info['rate_limit'] is not None
        assert agent_info['current_version'] == 1
    
    @patch('ai_agent_connector.app.agents.providers.OpenAI')
    def test_remove_agent(self, mock_openai):
        """Test removing an agent"""
        manager = AIAgentManager()
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        
        manager.register_ai_agent("agent1", config)
        
        success = manager.remove_agent("agent1")
        
        assert success is True
        assert "agent1" not in manager.list_agents()


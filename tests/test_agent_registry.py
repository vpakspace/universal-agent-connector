"""
Unit tests for AgentRegistry enhancements
"""

import pytest
from unittest.mock import MagicMock, patch

from ai_agent_connector.app.agents.registry import AgentRegistry


class TestAgentRegistry:
    """Test cases for agent registration with credentials and database linking"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_credentials_and_database(self, mock_connector_cls):
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-123',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'agent-key', 'api_secret': 'agent-secret'},
            database_config={'connection_string': 'postgresql://user:pass@localhost/db'}
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        assert registry.agent_database_links['agent-123']['connection_string'] == '***'
    
    def test_register_agent_missing_credentials(self):
        registry = AgentRegistry()
        
        with pytest.raises(ValueError, match="agent_credentials are required"):
            registry.register_agent(
                agent_id='agent-123',
                agent_info={},
                database_config={'connection_string': 'postgresql://user:pass@localhost/db'}
            )
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_database_failure(self, mock_connector_cls):
        mock_connector = MagicMock()
        mock_connector.connect.side_effect = RuntimeError("boom")
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        with pytest.raises(ValueError, match="Failed to connect to database"):
            registry.register_agent(
                agent_id='agent-123',
                agent_info={},
                credentials={'api_key': 'agent-key', 'api_secret': 'agent-secret'},
                database_config={'connection_string': 'postgresql://user:pass@localhost/db'}
            )
    
    def test_reset_clears_state(self):
        registry = AgentRegistry()
        registry.agents['a'] = {}
        registry.api_keys['key'] = 'a'
        registry.agent_credentials['a'] = {}
        registry.agent_database_links['a'] = {}
        
        registry.reset()
        
        assert registry.agents == {}
        assert registry.api_keys == {}
        assert registry.agent_credentials == {}
        assert registry.agent_database_links == {}
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_database_type(self, mock_connector_cls):
        """Test registering agent with explicit database type"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-typed',
            agent_info={'name': 'Typed Agent'},
            credentials={'api_key': 'agent-key', 'api_secret': 'agent-secret'},
            database_config={
                'type': 'mysql',
                'host': 'localhost',
                'user': 'user',
                'database': 'db'
            }
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        assert payload['database']['type'] == 'mysql'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_update_agent_database_with_type(self, mock_connector_cls):
        """Test updating agent database with different type"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        # Register with PostgreSQL
        registry.register_agent(
            agent_id='agent-switch',
            agent_info={'name': 'Switch Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'database': 'pgdb'
            }
        )
        
        # Update to MySQL
        result = registry.update_agent_database('agent-switch', {
            'type': 'mysql',
            'host': 'localhost',
            'user': 'user',
            'database': 'mysqldb'
        })
        
        assert result['database']['type'] == 'mysql'
        assert registry.agent_database_links['agent-switch']['type'] == 'mysql'





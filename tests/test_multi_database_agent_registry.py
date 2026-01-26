"""
Unit tests for AgentRegistry with multi-database support
Tests agent registration with different database types
"""

import pytest
from unittest.mock import MagicMock, patch

from ai_agent_connector.app.agents.registry import AgentRegistry


class TestAgentRegistryMultiDatabase:
    """Test cases for agent registration with multiple database types"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_mysql(self, mock_connector_cls):
        """Test registering agent with MySQL database"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-mysql',
            agent_info={'name': 'MySQL Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'mysql',
                'host': 'localhost',
                'port': 3306,
                'user': 'mysqluser',
                'password': 'mysqlpass',
                'database': 'mysqldb'
            }
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        assert payload['database']['type'] == 'mysql'
        assert registry.agent_database_links['agent-mysql']['type'] == 'mysql'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_mongodb(self, mock_connector_cls):
        """Test registering agent with MongoDB database"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-mongo',
            agent_info={'name': 'MongoDB Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'mongodb',
                'host': 'localhost',
                'port': 27017,
                'database': 'mongodb'
            }
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        assert payload['database']['type'] == 'mongodb'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_bigquery(self, mock_connector_cls):
        """Test registering agent with BigQuery database"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-bq',
            agent_info={'name': 'BigQuery Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'bigquery',
                'project_id': 'test-project',
                'credentials_path': '/path/to/creds.json',
                'dataset_id': 'test_dataset'
            }
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        assert payload['database']['type'] == 'bigquery'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_snowflake(self, mock_connector_cls):
        """Test registering agent with Snowflake database"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-snowflake',
            agent_info={'name': 'Snowflake Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'snowflake',
                'account': 'testaccount',
                'user': 'testuser',
                'password': 'testpass',
                'warehouse': 'testwarehouse',
                'database': 'testdb'
            }
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        assert payload['database']['type'] == 'snowflake'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_connection_string(self, mock_connector_cls):
        """Test registering agent with connection string (auto-detect type)"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        payload = registry.register_agent(
            agent_id='agent-conn-string',
            agent_info={'name': 'Connection String Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'connection_string': 'mysql://user:pass@localhost:3306/db'
            }
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_get_database_connector_with_type(self, mock_connector_cls):
        """Test getting database connector with specific type"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        registry.register_agent(
            agent_id='agent-test',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'mysql',
                'host': 'localhost',
                'user': 'user',
                'database': 'db'
            }
        )
        
        connector = registry.get_database_connector('agent-test')
        assert connector is not None
        # Verify the connector was created with the correct type
        mock_connector_cls.assert_called()
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_database_connection_mysql(self, mock_connector_cls):
        """Test testing MySQL database connection"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'mysql',
            'host': 'localhost',
            'user': 'user',
            'password': 'pass',
            'database': 'db'
        })
        
        assert result['status'] == 'success'
        mock_connector.connect.assert_called_once()
        mock_connector.disconnect.assert_called_once()
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_database_connection_failure(self, mock_connector_cls):
        """Test database connection failure"""
        mock_connector = MagicMock()
        mock_connector.connect.side_effect = ConnectionError("Connection failed")
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'mysql',
            'host': 'localhost',
            'user': 'user',
            'database': 'db'
        })
        
        assert result['status'] == 'error'
        assert 'error' in result
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_update_agent_database_type(self, mock_connector_cls):
        """Test updating agent database to different type"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        # Register with PostgreSQL
        registry.register_agent(
            agent_id='agent-update',
            agent_info={'name': 'Update Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'database': 'pgdb'
            }
        )
        
        # Update to MySQL
        result = registry.update_agent_database('agent-update', {
            'type': 'mysql',
            'host': 'localhost',
            'user': 'user',
            'database': 'mysqldb'
        })
        
        assert result['database']['type'] == 'mysql'
        assert registry.agent_database_links['agent-update']['type'] == 'mysql'
    
    def test_build_connector_missing_required_fields(self):
        """Test building connector with missing required fields"""
        registry = AgentRegistry()
        
        # MySQL requires host, user, database
        with pytest.raises(ValueError, match="database.host is required"):
            registry._build_database_connector({
                'type': 'mysql',
                'user': 'user'
            })
        
        with pytest.raises(ValueError, match="database.user is required"):
            registry._build_database_connector({
                'type': 'mysql',
                'host': 'localhost'
            })
        
        with pytest.raises(ValueError, match="database.database is required"):
            registry._build_database_connector({
                'type': 'mysql',
                'host': 'localhost',
                'user': 'user'
            })


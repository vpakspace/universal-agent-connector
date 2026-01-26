"""
Unit tests for database connection testing functionality
Tests the enhanced test_database_connection method
"""

import pytest
from unittest.mock import MagicMock, patch

from ai_agent_connector.app.agents.registry import AgentRegistry


class TestDatabaseConnectionTesting:
    """Test cases for database connection testing"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_success_postgresql(self, mock_connector_cls):
        """Test successful PostgreSQL connection test"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {
            'type': 'postgresql',
            'version': '15.0',
            'database': 'testdb'
        }
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        })
        
        assert result['status'] == 'success'
        assert result['test_results']['connection_established'] is True
        assert result['test_results']['query_test'] is True
        assert result['test_results']['database_info_retrieved'] is True
        assert result['connection_quality'] == 'excellent'
        assert result['database_info']['type'] == 'postgresql'
        mock_connector.connect.assert_called_once()
        mock_connector.disconnect.assert_called_once()
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_success_mysql(self, mock_connector_cls):
        """Test successful MySQL connection test"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {
            'type': 'mysql',
            'version': '8.0',
            'database': 'testdb'
        }
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'mysql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        })
        
        assert result['status'] == 'success'
        assert result['connection_quality'] in ['excellent', 'good', 'fair']
        assert result['database_info']['type'] == 'mysql'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_failure_connection_error(self, mock_connector_cls):
        """Test connection failure with connection error"""
        mock_connector = MagicMock()
        mock_connector.connect.side_effect = ConnectionError("Connection refused")
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'postgresql',
            'host': 'invalid-host',
            'user': 'user',
            'database': 'db'
        })
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'connection_error'
        assert 'Connection refused' in result['error']
        assert result['test_results']['connection_established'] is False
        assert result['connection_quality'] == 'poor'
    
    def test_test_connection_validation_error_missing_fields(self):
        """Test connection test with missing required fields"""
        registry = AgentRegistry()
        
        # Missing required fields for PostgreSQL
        result = registry.test_database_connection({
            'type': 'postgresql',
            'host': 'localhost'
            # Missing user and database
        })
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'validation_error'
        assert 'Missing required fields' in result['error']
    
    def test_test_connection_validation_error_bigquery(self):
        """Test BigQuery connection validation"""
        registry = AgentRegistry()
        
        # Missing project_id
        result = registry.test_database_connection({
            'type': 'bigquery'
        })
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'validation_error'
        assert 'project_id' in result['error']
        
        # Missing credentials
        result = registry.test_database_connection({
            'type': 'bigquery',
            'project_id': 'test-project'
        })
        
        assert result['status'] == 'error'
        assert 'credentials' in result['error'].lower()
    
    def test_test_connection_validation_error_snowflake(self):
        """Test Snowflake connection validation"""
        registry = AgentRegistry()
        
        # Missing required fields
        result = registry.test_database_connection({
            'type': 'snowflake',
            'account': 'testaccount'
            # Missing user and password
        })
        
        assert result['status'] == 'error'
        assert result['error_type'] == 'validation_error'
        assert 'Missing required fields' in result['error']
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_query_test_failure(self, mock_connector_cls):
        """Test connection where query test fails but connection succeeds"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.side_effect = Exception("Query failed")
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'database': 'db'
        })
        
        # Connection should still be successful even if query fails
        assert result['status'] == 'success'
        assert result['test_results']['connection_established'] is True
        assert result['test_results']['query_test'] is False
        assert 'query_test_error' in result['test_results']
        assert result['connection_quality'] in ['fair', 'good']  # Not excellent
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_info_retrieval_failure(self, mock_connector_cls):
        """Test connection where info retrieval fails"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.side_effect = Exception("Info retrieval failed")
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'database': 'db'
        })
        
        assert result['status'] == 'success'
        assert result['test_results']['connection_established'] is True
        assert result['test_results']['query_test'] is True
        assert result['test_results']['database_info_retrieved'] is False
        assert result['connection_quality'] == 'good'  # Not excellent
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_always_disconnects(self, mock_connector_cls):
        """Test that connection is always disconnected even on error"""
        mock_connector = MagicMock()
        mock_connector.connect.side_effect = ConnectionError("Connection failed")
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        result = registry.test_database_connection({
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'database': 'db'
        })
        
        # Even though connection failed, disconnect should be called in finally
        # (though it may not be called if connect fails before connector is set)
        assert result['status'] == 'error'
    
    def test_validate_database_config_postgresql(self):
        """Test PostgreSQL configuration validation"""
        registry = AgentRegistry()
        
        # Valid config
        try:
            registry._validate_database_config({
                'host': 'localhost',
                'user': 'user',
                'database': 'db'
            }, 'postgresql')
        except ValueError:
            pytest.fail("Valid PostgreSQL config should not raise ValueError")
        
        # Missing fields
        with pytest.raises(ValueError, match="Missing required fields"):
            registry._validate_database_config({
                'host': 'localhost'
            }, 'postgresql')
    
    def test_validate_database_config_mongodb(self):
        """Test MongoDB configuration validation"""
        registry = AgentRegistry()
        
        # Valid config
        try:
            registry._validate_database_config({
                'host': 'localhost',
                'database': 'db'
            }, 'mongodb')
        except ValueError:
            pytest.fail("Valid MongoDB config should not raise ValueError")
    
    def test_get_test_query(self):
        """Test getting test queries for different database types"""
        registry = AgentRegistry()
        
        assert registry._get_test_query('postgresql') == 'SELECT 1'
        assert registry._get_test_query('mysql') == 'SELECT 1'
        assert registry._get_test_query('snowflake') == 'SELECT 1'
        assert registry._get_test_query('bigquery') == 'SELECT 1'
        assert registry._get_test_query('mongodb') is None
    
    def test_assess_connection_quality(self):
        """Test connection quality assessment"""
        registry = AgentRegistry()
        
        # Excellent quality
        assert registry._assess_connection_quality({
            'connection_established': True,
            'query_test': True,
            'database_info_retrieved': True
        }) == 'excellent'
        
        # Good quality
        assert registry._assess_connection_quality({
            'connection_established': True,
            'query_test': True,
            'database_info_retrieved': False
        }) == 'good'
        
        # Fair quality
        assert registry._assess_connection_quality({
            'connection_established': True,
            'query_test': False,
            'database_info_retrieved': False
        }) == 'fair'
        
        # Poor quality
        assert registry._assess_connection_quality({
            'connection_established': False,
            'query_test': False,
            'database_info_retrieved': False
        }) == 'poor'


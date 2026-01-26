"""
Unit tests for connection pooling and timeout functionality
"""

import pytest
from unittest.mock import MagicMock, patch

from ai_agent_connector.app.db.pooling import (
    PoolingConfig,
    TimeoutConfig,
    extract_pooling_config,
    extract_timeout_config,
    validate_pooling_config,
    validate_timeout_config
)
from ai_agent_connector.app.db.connectors import PostgreSQLConnector, MySQLConnector


class TestPoolingConfig:
    """Test cases for PoolingConfig"""
    
    def test_default_pooling_config(self):
        """Test default pooling configuration"""
        config = PoolingConfig()
        assert config.enabled is False
        assert config.min_size == 1
        assert config.max_size == 10
        assert config.max_overflow == 5
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.pool_pre_ping is True
    
    def test_pooling_config_from_dict(self):
        """Test creating PoolingConfig from dictionary"""
        config_dict = {
            'enabled': True,
            'min_size': 2,
            'max_size': 20,
            'max_overflow': 10,
            'pool_timeout': 60,
            'pool_recycle': 7200,
            'pool_pre_ping': False
        }
        config = PoolingConfig.from_dict(config_dict)
        assert config.enabled is True
        assert config.min_size == 2
        assert config.max_size == 20
        assert config.max_overflow == 10
        assert config.pool_timeout == 60
        assert config.pool_recycle == 7200
        assert config.pool_pre_ping is False
    
    def test_pooling_config_to_dict(self):
        """Test converting PoolingConfig to dictionary"""
        config = PoolingConfig(enabled=True, min_size=5, max_size=15)
        config_dict = config.to_dict()
        assert config_dict['enabled'] is True
        assert config_dict['min_size'] == 5
        assert config_dict['max_size'] == 15


class TestTimeoutConfig:
    """Test cases for TimeoutConfig"""
    
    def test_default_timeout_config(self):
        """Test default timeout configuration"""
        config = TimeoutConfig()
        assert config.connect_timeout == 10
        assert config.query_timeout == 30
        assert config.read_timeout == 30
        assert config.write_timeout == 30
    
    def test_timeout_config_from_dict(self):
        """Test creating TimeoutConfig from dictionary"""
        config_dict = {
            'connect_timeout': 20,
            'query_timeout': 60,
            'read_timeout': 45,
            'write_timeout': 45
        }
        config = TimeoutConfig.from_dict(config_dict)
        assert config.connect_timeout == 20
        assert config.query_timeout == 60
        assert config.read_timeout == 45
        assert config.write_timeout == 45
    
    def test_timeout_config_to_dict(self):
        """Test converting TimeoutConfig to dictionary"""
        config = TimeoutConfig(connect_timeout=15, query_timeout=45)
        config_dict = config.to_dict()
        assert config_dict['connect_timeout'] == 15
        assert config_dict['query_timeout'] == 45


class TestConfigExtraction:
    """Test cases for extracting configs from database config"""
    
    def test_extract_pooling_config(self):
        """Test extracting pooling config from database config"""
        db_config = {
            'host': 'localhost',
            'pooling': {
                'enabled': True,
                'min_size': 2,
                'max_size': 20
            }
        }
        pooling = extract_pooling_config(db_config)
        assert pooling.enabled is True
        assert pooling.min_size == 2
        assert pooling.max_size == 20
    
    def test_extract_pooling_config_defaults(self):
        """Test extracting pooling config with defaults"""
        db_config = {'host': 'localhost'}
        pooling = extract_pooling_config(db_config)
        assert pooling.enabled is False
        assert pooling.min_size == 1
    
    def test_extract_timeout_config(self):
        """Test extracting timeout config from database config"""
        db_config = {
            'host': 'localhost',
            'timeouts': {
                'connect_timeout': 20,
                'query_timeout': 60
            }
        }
        timeouts = extract_timeout_config(db_config)
        assert timeouts.connect_timeout == 20
        assert timeouts.query_timeout == 60
    
    def test_extract_timeout_config_defaults(self):
        """Test extracting timeout config with defaults"""
        db_config = {'host': 'localhost'}
        timeouts = extract_timeout_config(db_config)
        assert timeouts.connect_timeout == 10
        assert timeouts.query_timeout == 30


class TestConfigValidation:
    """Test cases for configuration validation"""
    
    def test_validate_pooling_config_valid(self):
        """Test validating valid pooling config"""
        pooling = PoolingConfig(
            enabled=True,
            min_size=2,
            max_size=10,
            max_overflow=5
        )
        # Should not raise
        validate_pooling_config(pooling)
    
    def test_validate_pooling_config_invalid_min_size(self):
        """Test validating invalid min_size"""
        pooling = PoolingConfig(min_size=0)
        with pytest.raises(ValueError, match="min_size must be at least 1"):
            validate_pooling_config(pooling)
    
    def test_validate_pooling_config_invalid_max_size(self):
        """Test validating invalid max_size"""
        pooling = PoolingConfig(min_size=10, max_size=5)
        with pytest.raises(ValueError, match="max_size must be >= min_size"):
            validate_pooling_config(pooling)
    
    def test_validate_pooling_config_invalid_max_overflow(self):
        """Test validating invalid max_overflow"""
        pooling = PoolingConfig(max_overflow=-1)
        with pytest.raises(ValueError, match="max_overflow must be >= 0"):
            validate_pooling_config(pooling)
    
    def test_validate_timeout_config_valid(self):
        """Test validating valid timeout config"""
        timeouts = TimeoutConfig(
            connect_timeout=10,
            query_timeout=30
        )
        # Should not raise
        validate_timeout_config(timeouts)
    
    def test_validate_timeout_config_invalid_connect_timeout(self):
        """Test validating invalid connect_timeout"""
        timeouts = TimeoutConfig(connect_timeout=0)
        with pytest.raises(ValueError, match="connect_timeout must be at least 1"):
            validate_timeout_config(timeouts)
    
    def test_validate_timeout_config_invalid_query_timeout(self):
        """Test validating invalid query_timeout"""
        timeouts = TimeoutConfig(query_timeout=0)
        with pytest.raises(ValueError, match="query_timeout must be at least 1"):
            validate_timeout_config(timeouts)


class TestPostgreSQLConnectorWithPooling:
    """Test cases for PostgreSQL connector with pooling"""
    
    @patch('ai_agent_connector.app.db.connectors.psycopg2.connect')
    def test_postgresql_without_pooling(self, mock_connect):
        """Test PostgreSQL connector without pooling"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = PostgreSQLConnector({
            'host': 'localhost',
            'user': 'user',
            'database': 'db',
            'pooling': {'enabled': False}
        })
        
        connector.connect()
        assert connector.is_connected is True
        assert connector.pool is None
    
    @patch('ai_agent_connector.app.db.connectors.pool.ThreadedConnectionPool')
    def test_postgresql_with_pooling(self, mock_pool_class):
        """Test PostgreSQL connector with pooling"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_pool.getconn.return_value = mock_conn
        mock_pool_class.return_value = mock_pool
        
        connector = PostgreSQLConnector({
            'host': 'localhost',
            'user': 'user',
            'database': 'db',
            'pooling': {
                'enabled': True,
                'min_size': 2,
                'max_size': 10
            }
        })
        
        connector.connect()
        assert connector.is_connected is True
        assert connector.pool is not None
        mock_pool.getconn.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connectors.psycopg2.connect')
    def test_postgresql_with_timeouts(self, mock_connect):
        """Test PostgreSQL connector with timeout settings"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = PostgreSQLConnector({
            'host': 'localhost',
            'user': 'user',
            'database': 'db',
            'timeouts': {
                'connect_timeout': 20,
                'query_timeout': 60
            }
        })
        
        connector.connect()
        # Verify connect was called with timeout
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs.get('connect_timeout') == 20


class TestMySQLConnectorWithPooling:
    """Test cases for MySQL connector with pooling"""
    
    @patch('ai_agent_connector.app.db.connectors.pymysql.connect')
    def test_mysql_without_pooling(self, mock_connect):
        """Test MySQL connector without pooling"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        connector = MySQLConnector({
            'host': 'localhost',
            'user': 'user',
            'database': 'db',
            'pooling': {'enabled': False}
        })
        
        connector.connect()
        assert connector.is_connected is True
        assert connector.pool is None
    
    @patch('ai_agent_connector.app.db.connectors.pymysql.connect')
    def test_mysql_with_timeouts(self, mock_connect):
        """Test MySQL connector with timeout settings"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        connector = MySQLConnector({
            'host': 'localhost',
            'user': 'user',
            'database': 'db',
            'timeouts': {
                'connect_timeout': 20,
                'read_timeout': 45,
                'write_timeout': 45
            }
        })
        
        connector.connect()
        # Verify connect was called with timeouts
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs.get('connect_timeout') == 20
        assert call_kwargs.get('read_timeout') == 45
        assert call_kwargs.get('write_timeout') == 45


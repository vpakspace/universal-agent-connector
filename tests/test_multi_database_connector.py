"""
Unit tests for multi-database connector functionality
Tests the factory, base connector, and individual database connectors
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from ai_agent_connector.app.db.factory import DatabaseConnectorFactory
from ai_agent_connector.app.db.connector import DatabaseConnector
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector


class TestDatabaseConnectorFactory:
    """Test cases for DatabaseConnectorFactory"""
    
    def test_get_supported_types(self):
        """Test getting list of supported database types"""
        types = DatabaseConnectorFactory.get_supported_types()
        assert isinstance(types, list)
        assert 'postgresql' in types
        assert 'mysql' in types
        assert 'mongodb' in types
        assert 'bigquery' in types
        assert 'snowflake' in types
    
    def test_create_postgresql_connector(self):
        """Test creating PostgreSQL connector"""
        config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        connector = DatabaseConnectorFactory.create_connector('postgresql', config)
        assert isinstance(connector, BaseDatabaseConnector)
        assert connector.config == config
    
    def test_create_mysql_connector(self):
        """Test creating MySQL connector"""
        config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        connector = DatabaseConnectorFactory.create_connector('mysql', config)
        assert isinstance(connector, BaseDatabaseConnector)
    
    def test_create_mongodb_connector(self):
        """Test creating MongoDB connector"""
        config = {
            'host': 'localhost',
            'port': 27017,
            'database': 'testdb'
        }
        connector = DatabaseConnectorFactory.create_connector('mongodb', config)
        assert isinstance(connector, BaseDatabaseConnector)
    
    def test_create_bigquery_connector(self):
        """Test creating BigQuery connector"""
        config = {
            'project_id': 'test-project',
            'credentials_path': '/path/to/creds.json'
        }
        connector = DatabaseConnectorFactory.create_connector('bigquery', config)
        assert isinstance(connector, BaseDatabaseConnector)
    
    def test_create_snowflake_connector(self):
        """Test creating Snowflake connector"""
        config = {
            'account': 'testaccount',
            'user': 'testuser',
            'password': 'testpass'
        }
        connector = DatabaseConnectorFactory.create_connector('snowflake', config)
        assert isinstance(connector, BaseDatabaseConnector)
    
    def test_create_unsupported_type(self):
        """Test creating connector with unsupported type"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseConnectorFactory.create_connector('invalid_type', {})
    
    def test_detect_database_type_from_config(self):
        """Test detecting database type from configuration"""
        # Explicit type
        config = {'type': 'mysql', 'host': 'localhost'}
        assert DatabaseConnectorFactory.detect_database_type(config) == 'mysql'
        
        # From connection string
        config = {'connection_string': 'postgresql://user:pass@host/db'}
        assert DatabaseConnectorFactory.detect_database_type(config) == 'postgresql'
        
        config = {'connection_string': 'mysql://user:pass@host/db'}
        assert DatabaseConnectorFactory.detect_database_type(config) == 'mysql'
        
        config = {'connection_string': 'mongodb://host:27017/db'}
        assert DatabaseConnectorFactory.detect_database_type(config) == 'mongodb'
        
        # Default to postgresql
        config = {'host': 'localhost'}
        assert DatabaseConnectorFactory.detect_database_type(config) == 'postgresql'


class TestMultiDatabaseConnector:
    """Test cases for DatabaseConnector with multiple database types"""
    
    def test_init_with_database_type(self):
        """Test initializing connector with explicit database type"""
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        assert connector.database_type == 'mysql'
    
    def test_init_detects_type_from_connection_string(self):
        """Test detecting database type from connection string"""
        connector = DatabaseConnector(
            connection_string='mysql://user:pass@host:3306/db'
        )
        assert connector.database_type == 'mysql'
    
    def test_init_defaults_to_postgresql(self):
        """Test defaulting to PostgreSQL when type not specified"""
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb'
        )
        assert connector.database_type == 'postgresql'
    
    @patch('ai_agent_connector.app.db.connector.DatabaseConnectorFactory')
    def test_connect_delegates_to_connector(self, mock_factory):
        """Test that connect delegates to underlying connector"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_factory.create_connector.return_value = mock_connector
        
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        
        result = connector.connect()
        
        assert result is True
        mock_connector.connect.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.DatabaseConnectorFactory')
    def test_disconnect_delegates_to_connector(self, mock_factory):
        """Test that disconnect delegates to underlying connector"""
        mock_connector = MagicMock()
        mock_factory.create_connector.return_value = mock_connector
        
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        
        connector.disconnect()
        mock_connector.disconnect.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.DatabaseConnectorFactory')
    def test_execute_query_delegates_to_connector(self, mock_factory):
        """Test that execute_query delegates to underlying connector"""
        mock_connector = MagicMock()
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [('result',)]
        mock_factory.create_connector.return_value = mock_connector
        
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        
        results = connector.execute_query("SELECT 1")
        
        assert results == [('result',)]
        mock_connector.execute_query.assert_called_once_with("SELECT 1", None, True, False)
    
    @patch('ai_agent_connector.app.db.connector.DatabaseConnectorFactory')
    def test_get_database_info(self, mock_factory):
        """Test getting database information"""
        mock_connector = MagicMock()
        mock_connector.get_database_info.return_value = {'type': 'mysql', 'version': '8.0'}
        mock_factory.create_connector.return_value = mock_connector
        
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        
        info = connector.get_database_info()
        
        assert info == {'type': 'mysql', 'version': '8.0'}
        mock_connector.get_database_info.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.DatabaseConnectorFactory')
    def test_context_manager(self, mock_factory):
        """Test using connector as context manager"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_factory.create_connector.return_value = mock_connector
        
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        
        with connector:
            pass
        
        mock_connector.connect.assert_called_once()
        mock_connector.disconnect.assert_called_once()
    
    def test_repr(self):
        """Test string representation"""
        connector = DatabaseConnector(
            host='localhost',
            user='testuser',
            database='testdb',
            database_type='mysql'
        )
        
        repr_str = repr(connector)
        assert 'mysql' in repr_str
        assert 'testdb' in repr_str


class TestPostgreSQLConnector:
    """Test cases for PostgreSQL connector"""
    
    @patch('ai_agent_connector.app.db.connectors.psycopg2.connect')
    def test_postgresql_connect(self, mock_connect):
        """Test PostgreSQL connection"""
        from ai_agent_connector.app.db.connectors import PostgreSQLConnector
        
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = PostgreSQLConnector({
            'host': 'localhost',
            'user': 'testuser',
            'database': 'testdb'
        })
        
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected is True
    
    @patch('ai_agent_connector.app.db.connectors.psycopg2.connect')
    def test_postgresql_execute_query(self, mock_connect):
        """Test PostgreSQL query execution"""
        from ai_agent_connector.app.db.connectors import PostgreSQLConnector
        
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('result',)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = PostgreSQLConnector({
            'host': 'localhost',
            'user': 'testuser',
            'database': 'testdb'
        })
        connector.connect()
        
        results = connector.execute_query("SELECT 1")
        
        assert results == [('result',)]


class TestMySQLConnector:
    """Test cases for MySQL connector"""
    
    @patch('ai_agent_connector.app.db.connectors.pymysql.connect')
    def test_mysql_connect(self, mock_connect):
        """Test MySQL connection"""
        from ai_agent_connector.app.db.connectors import MySQLConnector
        
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        connector = MySQLConnector({
            'host': 'localhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        })
        
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected is True
    
    @patch('ai_agent_connector.app.db.connectors.pymysql.connect')
    def test_mysql_execute_query(self, mock_connect):
        """Test MySQL query execution"""
        from ai_agent_connector.app.db.connectors import MySQLConnector
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = MySQLConnector({
            'host': 'localhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        })
        connector.connect()
        
        results = connector.execute_query("SELECT * FROM users", as_dict=True)
        
        assert results == [{'id': 1, 'name': 'test'}]


class TestMongoDBConnector:
    """Test cases for MongoDB connector"""
    
    @patch('ai_agent_connector.app.db.connectors.MongoClient')
    def test_mongodb_connect(self, mock_client_class):
        """Test MongoDB connection"""
        from ai_agent_connector.app.db.connectors import MongoDBConnector
        
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {'ok': 1}
        mock_client_class.return_value = mock_client
        
        connector = MongoDBConnector({
            'host': 'localhost',
            'port': 27017,
            'database': 'testdb'
        })
        
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected is True


class TestBigQueryConnector:
    """Test cases for BigQuery connector"""
    
    @patch('ai_agent_connector.app.db.connectors.bigquery.Client')
    def test_bigquery_connect(self, mock_client_class):
        """Test BigQuery connection"""
        from ai_agent_connector.app.db.connectors import BigQueryConnector
        
        mock_client = MagicMock()
        mock_client.list_datasets.return_value = []
        mock_client_class.return_value = mock_client
        
        connector = BigQueryConnector({
            'project_id': 'test-project',
            'credentials_path': '/path/to/creds.json'
        })
        
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected is True


class TestSnowflakeConnector:
    """Test cases for Snowflake connector"""
    
    @patch('ai_agent_connector.app.db.connectors.snowflake.connector.connect')
    def test_snowflake_connect(self, mock_connect):
        """Test Snowflake connection"""
        from ai_agent_connector.app.db.connectors import SnowflakeConnector
        
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        connector = SnowflakeConnector({
            'account': 'testaccount',
            'user': 'testuser',
            'password': 'testpass'
        })
        
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected is True
    
    @patch('ai_agent_connector.app.db.connectors.snowflake.connector.connect')
    def test_snowflake_execute_query(self, mock_connect):
        """Test Snowflake query execution"""
        from ai_agent_connector.app.db.connectors import SnowflakeConnector
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'test')]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = SnowflakeConnector({
            'account': 'testaccount',
            'user': 'testuser',
            'password': 'testpass'
        })
        connector.connect()
        
        results = connector.execute_query("SELECT * FROM users", as_dict=True)
        
        assert len(results) == 1
        assert results[0]['id'] == 1


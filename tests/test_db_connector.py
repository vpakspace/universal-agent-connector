"""
Unit tests for DatabaseConnector
"""

import pytest  # type: ignore
import os
from unittest.mock import Mock, patch, MagicMock
from ai_agent_connector.app.db.connector import DatabaseConnector


class TestDatabaseConnector:
    """Test cases for DatabaseConnector class"""
    
    def test_init_with_env_vars(self):
        """Test initialization with environment variables"""
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb'
        }):
            connector = DatabaseConnector()
            assert connector.host == 'localhost'
            assert connector.port == 5432
            assert connector.user == 'testuser'
            assert connector.password == 'testpass'
            assert connector.database == 'testdb'
    
    def test_init_with_parameters(self):
        """Test initialization with explicit parameters"""
        connector = DatabaseConnector(
            host='testhost',
            port=5433,
            user='user',
            password='pass',
            database='db'
        )
        assert connector.host == 'testhost'
        assert connector.port == 5433
        assert connector.user == 'user'
        assert connector.database == 'db'
    
    def test_init_with_connection_string(self):
        """Test initialization with connection string"""
        conn_string = "postgresql://user:pass@host:5432/db"
        connector = DatabaseConnector(connection_string=conn_string)
        assert connector.connection_string == conn_string
        assert connector.host is None
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_connect_success(self, mock_connect):
        """Test successful connection"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        
        result = connector.connect()
        
        assert result is True
        assert connector.is_connected is True
        mock_connect.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_connect_failure(self, mock_connect):
        """Test connection failure"""
        import psycopg2  # type: ignore
        mock_connect.side_effect = psycopg2.Error("Connection failed")
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        
        with pytest.raises(Exception):
            connector.connect()
        
        assert connector.is_connected is False
    
    def test_connect_missing_parameters(self):
        """Test connection with missing required parameters"""
        connector = DatabaseConnector()
        
        with pytest.raises(ValueError, match="Missing required connection parameters"):
            connector.connect()
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_disconnect(self, mock_connect):
        """Test disconnection"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        connector.connect()
        connector.disconnect()
        
        mock_conn.close.assert_called_once()
        assert connector.is_connected is False
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_execute_query_select(self, mock_connect):
        """Test executing a SELECT query"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('result1',), ('result2',)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        connector.connect()
        
        results = connector.execute_query("SELECT * FROM users WHERE id = %s", (1,))
        
        assert results == [('result1',), ('result2',)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (1,))
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_execute_query_insert(self, mock_connect):
        """Test executing an INSERT query"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        connector.connect()
        
        result = connector.execute_query(
            "INSERT INTO users (name) VALUES (%s)",
            ('John',),
            fetch=False
        )
        
        assert result is None
        mock_conn.commit.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_execute_query_as_dict(self, mock_connect):
        """Test executing query with dictionary results"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'John'}]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        connector.connect()
        
        results = connector.execute_query("SELECT * FROM users", as_dict=True)
        
        assert results == [{'id': 1, 'name': 'John'}]
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_execute_query_not_connected(self, mock_connect):
        """Test executing query without connection"""
        connector = DatabaseConnector()
        
        with pytest.raises(ConnectionError, match="Database not connected"):
            connector.execute_query("SELECT 1")
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_execute_query_error_rollback(self, mock_connect):
        """Test that errors trigger rollback"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        import psycopg2  # type: ignore
        mock_cursor.execute.side_effect = psycopg2.Error("Query failed")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        connector.connect()
        
        with pytest.raises(Exception):
            connector.execute_query("INVALID SQL")
        
        mock_conn.rollback.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_execute_many(self, mock_connect):
        """Test bulk query execution"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        connector.connect()
        
        params_list = [('John',), ('Jane',), ('Bob',)]
        connector.execute_many("INSERT INTO users (name) VALUES (%s)", params_list)
        
        mock_cursor.executemany.assert_called_once_with(
            "INSERT INTO users (name) VALUES (%s)",
            params_list
        )
        mock_conn.commit.assert_called_once()
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_context_manager(self, mock_connect):
        """Test using connector as context manager"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        
        with connector as db:
            assert db.is_connected is True
        
        mock_conn.close.assert_called_once()
        assert connector.is_connected is False
    
    def test_is_connected_property(self):
        """Test is_connected property"""
        connector = DatabaseConnector(
            host='localhost',
            user='user',
            database='db'
        )
        assert connector.is_connected is False
        
        with patch('ai_agent_connector.app.db.connector.psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.closed = False
            mock_connect.return_value = mock_conn
            
            connector.connect()
            assert connector.is_connected is True
            
            mock_conn.closed = True
            assert connector.is_connected is False


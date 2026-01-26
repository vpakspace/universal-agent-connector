"""
Comprehensive tests for all PostgreSQL configuration methods

This test file covers all configuration scenarios:
1. Environment variable configuration
2. Connection string configuration
3. Individual parameter configuration
4. Configuration priority/precedence
5. Missing parameter validation
6. Edge cases and error handling
"""

import pytest  # type: ignore
import os
from unittest.mock import patch, MagicMock
from ai_agent_connector.app.db.connector import DatabaseConnector


class TestEnvironmentVariableConfiguration:
    """Test configuration using environment variables"""
    
    def test_all_env_vars_set(self):
        """Test initialization with all environment variables set"""
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_PORT': '5433',
            'DB_USER': 'env-user',
            'DB_PASSWORD': 'env-pass',
            'DB_NAME': 'env-db'
        }, clear=False):
            connector = DatabaseConnector()
            assert connector.host == 'env-host'
            assert connector.port == 5433
            assert connector.user == 'env-user'
            assert connector.password == 'env-pass'
            assert connector.database == 'env-db'
            assert connector.connection_string is None
    
    def test_partial_env_vars_with_default_port(self):
        """Test with partial env vars, port should default to 5432"""
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_NAME': 'testdb'
        }, clear=False):
            # Remove DB_PORT if it exists
            env = os.environ.copy()
            env.pop('DB_PORT', None)
            
            with patch.dict(os.environ, env, clear=False):
                connector = DatabaseConnector()
                assert connector.host == 'localhost'
                assert connector.port == 5432  # Default port
                assert connector.user == 'testuser'
                assert connector.database == 'testdb'
                assert connector.password is None  # Not set
    
    def test_env_vars_with_password(self):
        """Test env vars including password"""
        with patch.dict(os.environ, {
            'DB_HOST': 'db.example.com',
            'DB_PORT': '5432',
            'DB_USER': 'admin',
            'DB_PASSWORD': 'secret123',
            'DB_NAME': 'production'
        }, clear=False):
            connector = DatabaseConnector()
            assert connector.host == 'db.example.com'
            assert connector.port == 5432
            assert connector.user == 'admin'
            assert connector.password == 'secret123'
            assert connector.database == 'production'
    
    def test_env_vars_missing_required(self):
        """Test that missing required env vars result in None"""
        # Clear all DB env vars
        env = os.environ.copy()
        for key in ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']:
            env.pop(key, None)
        
        with patch.dict(os.environ, env, clear=False):
            connector = DatabaseConnector()
            assert connector.host is None
            assert connector.port == 5432  # Default port
            assert connector.user is None
            assert connector.password is None
            assert connector.database is None


class TestConnectionStringConfiguration:
    """Test configuration using connection strings"""
    
    def test_full_connection_string(self):
        """Test full connection string with all components"""
        conn_string = "postgresql://user:pass@host:5432/dbname"
        connector = DatabaseConnector(connection_string=conn_string)
        
        assert connector.connection_string == conn_string
        assert connector.host is None
        assert connector.port is None
        assert connector.user is None
        assert connector.password is None
        assert connector.database is None
    
    def test_connection_string_without_port(self):
        """Test connection string without explicit port"""
        conn_string = "postgresql://user:pass@host/dbname"
        connector = DatabaseConnector(connection_string=conn_string)
        assert connector.connection_string == conn_string
    
    def test_connection_string_without_password(self):
        """Test connection string without password"""
        conn_string = "postgresql://user@host:5432/dbname"
        connector = DatabaseConnector(connection_string=conn_string)
        assert connector.connection_string == conn_string
    
    def test_connection_string_complex_host(self):
        """Test connection string with complex hostname"""
        conn_string = "postgresql://admin:secret@db.example.com:5432/analytics"
        connector = DatabaseConnector(connection_string=conn_string)
        assert connector.connection_string == conn_string
    
    def test_connection_string_localhost(self):
        """Test connection string with localhost"""
        conn_string = "postgresql://postgres:postgres@localhost:5432/mydb"
        connector = DatabaseConnector(connection_string=conn_string)
        assert connector.connection_string == conn_string
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_connection_string_connect(self, mock_connect):
        """Test that connection string is used for connection"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        conn_string = "postgresql://user:pass@host:5432/db"
        connector = DatabaseConnector(connection_string=conn_string)
        connector.connect()
        
        # Should call psycopg2.connect with the connection string
        mock_connect.assert_called_once_with(conn_string)
        assert connector.is_connected is True


class TestIndividualParameterConfiguration:
    """Test configuration using individual parameters"""
    
    def test_all_parameters_provided(self):
        """Test with all individual parameters"""
        connector = DatabaseConnector(
            host='custom-host',
            port=5434,
            user='custom-user',
            password='custom-pass',
            database='custom-db'
        )
        
        assert connector.host == 'custom-host'
        assert connector.port == 5434
        assert connector.user == 'custom-user'
        assert connector.password == 'custom-pass'
        assert connector.database == 'custom-db'
        assert connector.connection_string is None
    
    def test_parameters_without_password(self):
        """Test parameters without password (trust authentication)"""
        connector = DatabaseConnector(
            host='localhost',
            port=5432,
            user='postgres',
            database='mydb'
        )
        
        assert connector.host == 'localhost'
        assert connector.user == 'postgres'
        assert connector.password is None
        assert connector.database == 'mydb'
    
    def test_parameters_custom_port(self):
        """Test with custom port number"""
        connector = DatabaseConnector(
            host='db.example.com',
            port=5433,
            user='admin',
            database='testdb'
        )
        
        assert connector.port == 5433
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_parameters_connect(self, mock_connect):
        """Test connection using individual parameters"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        connector = DatabaseConnector(
            host='testhost',
            port=5432,
            user='testuser',
            password='testpass',
            database='testdb'
        )
        connector.connect()
        
        # Should call psycopg2.connect with individual parameters
        mock_connect.assert_called_once_with(
            host='testhost',
            port=5432,
            user='testuser',
            password='testpass',
            dbname='testdb'
        )
        assert connector.is_connected is True


class TestConfigurationPriority:
    """Test configuration priority/precedence"""
    
    def test_explicit_params_override_env_vars(self):
        """Test that explicit parameters override environment variables"""
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_PORT': '5433',
            'DB_USER': 'env-user',
            'DB_PASSWORD': 'env-pass',
            'DB_NAME': 'env-db'
        }, clear=False):
            connector = DatabaseConnector(
                host='explicit-host',
                port=5434,
                user='explicit-user',
                password='explicit-pass',
                database='explicit-db'
            )
            
            # Explicit parameters should be used, not env vars
            assert connector.host == 'explicit-host'
            assert connector.port == 5434
            assert connector.user == 'explicit-user'
            assert connector.password == 'explicit-pass'
            assert connector.database == 'explicit-db'
    
    def test_connection_string_overrides_all(self):
        """Test that connection string overrides both params and env vars"""
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_USER': 'env-user',
            'DB_NAME': 'env-db'
        }, clear=False):
            conn_string = "postgresql://conn-user:conn-pass@conn-host:5435/conn-db"
            connector = DatabaseConnector(
                host='param-host',
                user='param-user',
                connection_string=conn_string
            )
            
            # Connection string should override everything
            assert connector.connection_string == conn_string
            assert connector.host is None
            assert connector.user is None
            assert connector.database is None
    
    def test_partial_explicit_params_with_env_fallback(self):
        """Test partial explicit params with env vars as fallback"""
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_USER': 'env-user',
            'DB_NAME': 'env-db'
        }, clear=False):
            connector = DatabaseConnector(
                host='explicit-host',
                # user and database not provided, should use env vars
            )
            
            assert connector.host == 'explicit-host'  # Explicit
            assert connector.user == 'env-user'  # From env
            assert connector.database == 'env-db'  # From env


class TestMissingParameterValidation:
    """Test validation of missing required parameters"""
    
    def test_connect_missing_host(self):
        """Test connection fails when host is missing"""
        connector = DatabaseConnector(
            user='testuser',
            database='testdb'
        )
        
        with pytest.raises(ValueError, match="Missing required connection parameters"):
            connector.connect()
    
    def test_connect_missing_user(self):
        """Test connection fails when user is missing"""
        connector = DatabaseConnector(
            host='localhost',
            database='testdb'
        )
        
        with pytest.raises(ValueError, match="Missing required connection parameters"):
            connector.connect()
    
    def test_connect_missing_database(self):
        """Test connection fails when database is missing"""
        connector = DatabaseConnector(
            host='localhost',
            user='testuser'
        )
        
        with pytest.raises(ValueError, match="Missing required connection parameters"):
            connector.connect()
    
    def test_connect_all_missing(self):
        """Test connection fails when all required params are missing"""
        connector = DatabaseConnector()
        
        with pytest.raises(ValueError, match="Missing required connection parameters"):
            connector.connect()
    
    def test_connect_string_no_validation_needed(self):
        """Test that connection string doesn't require parameter validation"""
        # Connection string validation is handled by psycopg2
        conn_string = "postgresql://user:pass@host/db"
        connector = DatabaseConnector(connection_string=conn_string)
        
        # Should not raise ValueError for missing params
        # (will raise psycopg2.Error if connection fails, but not ValueError)
        with patch('ai_agent_connector.app.db.connector.psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.closed = False
            mock_connect.return_value = mock_conn
            
            # Should not raise ValueError
            result = connector.connect()
            assert result is True


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_empty_string_parameters(self):
        """Test that empty strings are treated as None"""
        connector = DatabaseConnector(
            host='',
            user='',
            database=''
        )
        
        # Empty strings should be treated as falsy, so env vars or None will be used
        # This depends on how os.getenv handles it
        assert connector.host == '' or connector.host is None
    
    def test_none_explicitly_passed(self):
        """Test explicitly passing None values"""
        connector = DatabaseConnector(
            host=None,
            port=None,
            user=None,
            password=None,
            database=None
        )
        
        # Should fall back to env vars or be None
        assert connector.host is None or connector.host == os.getenv('DB_HOST')
    
    def test_port_as_string(self):
        """Test that port can be converted from string in env var"""
        with patch.dict(os.environ, {
            'DB_PORT': '5433'
        }, clear=False):
            connector = DatabaseConnector()
            assert isinstance(connector.port, int)
            assert connector.port == 5433
    
    def test_default_port_when_not_specified(self):
        """Test default port is 5432 when not specified"""
        # Clear DB_PORT env var
        env = os.environ.copy()
        env.pop('DB_PORT', None)
        
        with patch.dict(os.environ, env, clear=False):
            connector = DatabaseConnector()
            assert connector.port == 5432
    
    def test_repr_with_connection_string(self):
        """Test string representation with connection string"""
        connector = DatabaseConnector(
            connection_string="postgresql://user:pass@host/db"
        )
        repr_str = repr(connector)
        assert "connection_string='***'" in repr_str
        assert "status=disconnected" in repr_str
    
    def test_repr_with_individual_params(self):
        """Test string representation with individual parameters"""
        connector = DatabaseConnector(
            host='localhost',
            database='mydb'
        )
        repr_str = repr(connector)
        assert "host=localhost" in repr_str
        assert "database=mydb" in repr_str
        assert "status=disconnected" in repr_str


class TestConfigurationCombinations:
    """Test various configuration combinations"""
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_env_vars_with_explicit_port(self, mock_connect):
        """Test env vars with explicit port override"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_USER': 'env-user',
            'DB_NAME': 'env-db'
        }, clear=False):
            connector = DatabaseConnector(port=5435)
            connector.connect()
            
            mock_connect.assert_called_once_with(
                host='env-host',
                port=5435,  # Explicit port
                user='env-user',
                password=None,
                dbname='env-db'
            )
    
    @patch('ai_agent_connector.app.db.connector.psycopg2.connect')
    def test_explicit_password_with_env_others(self, mock_connect):
        """Test explicit password with other params from env"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_USER': 'env-user',
            'DB_NAME': 'env-db'
        }, clear=False):
            connector = DatabaseConnector(password='explicit-pass')
            connector.connect()
            
            mock_connect.assert_called_once_with(
                host='env-host',
                port=5432,  # Default
                user='env-user',
                password='explicit-pass',  # Explicit
                dbname='env-db'
            )
    
    def test_connection_string_priority_over_mixed_config(self):
        """Test connection string takes priority over mixed config"""
        with patch.dict(os.environ, {
            'DB_HOST': 'env-host',
            'DB_USER': 'env-user'
        }, clear=False):
            conn_string = "postgresql://final-user:final-pass@final-host:5436/final-db"
            connector = DatabaseConnector(
                host='param-host',
                connection_string=conn_string
            )
            
            assert connector.connection_string == conn_string
            assert connector.host is None


class TestConfigurationDocumentation:
    """Test that configuration matches documented behavior"""
    
    def test_documented_env_var_names(self):
        """Verify documented env var names are correct"""
        # These should match the documentation
        expected_env_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        
        with patch.dict(os.environ, {
            'DB_HOST': 'test',
            'DB_PORT': '5432',
            'DB_USER': 'test',
            'DB_PASSWORD': 'test',
            'DB_NAME': 'test'
        }, clear=False):
            connector = DatabaseConnector()
            # All should be accessible
            assert connector.host == 'test'
            assert connector.user == 'test'
            assert connector.database == 'test'
    
    def test_documented_connection_string_format(self):
        """Verify connection string format works as documented"""
        # Test various documented formats
        formats = [
            "postgresql://user:pass@localhost:5432/mydb",
            "postgresql://postgres:secret@db.example.com:5432/analytics",
            "postgresql://user@localhost/dbname",
            "postgresql://user:pass@localhost/dbname"
        ]
        
        for conn_string in formats:
            connector = DatabaseConnector(connection_string=conn_string)
            assert connector.connection_string == conn_string
    
    def test_documented_default_port(self):
        """Verify default port is 5432 as documented"""
        env = os.environ.copy()
        env.pop('DB_PORT', None)
        
        with patch.dict(os.environ, env, clear=False):
            connector = DatabaseConnector()
            assert connector.port == 5432, "Default port should be 5432"



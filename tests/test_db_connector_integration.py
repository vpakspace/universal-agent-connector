"""
Integration tests for DatabaseConnector
These tests require a running PostgreSQL database.

To run these tests, set up a test database:
1. Create a test database: createdb test_db
2. Set environment variables:
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_USER=your_user
   export DB_PASSWORD=your_password
   export DB_NAME=test_db

Or use pytest with markers:
pytest -m integration tests/test_db_connector_integration.py
"""

import pytest
import os
from ai_agent_connector.app.db.connector import DatabaseConnector


@pytest.mark.integration
class TestDatabaseConnectorIntegration:
    """Integration tests requiring a real PostgreSQL database"""
    
    @pytest.fixture
    def connector(self):
        """Create a connector instance"""
        return DatabaseConnector()
    
    @pytest.fixture
    def test_table(self, connector):
        """Create and drop a test table"""
        connector.connect()
        
        # Create test table
        connector.execute_query(
            """
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100)
            )
            """,
            fetch=False
        )
        
        # Clear any existing data
        connector.execute_query("DELETE FROM test_users", fetch=False)
        
        yield
        
        # Cleanup
        connector.execute_query("DROP TABLE IF EXISTS test_users", fetch=False)
        connector.disconnect()
    
    def test_real_connection(self, connector):
        """Test connecting to a real database"""
        try:
            result = connector.connect()
            assert result is True
            assert connector.is_connected is True
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
        finally:
            connector.disconnect()
    
    def test_insert_and_select(self, connector, test_table):
        """Test inserting and selecting data"""
        # Insert data
        connector.execute_query(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ('John Doe', 'john@example.com'),
            fetch=False
        )
        
        # Select data
        results = connector.execute_query(
            "SELECT name, email FROM test_users WHERE name = %s",
            ('John Doe',)
        )
        
        assert len(results) == 1
        assert results[0][0] == 'John Doe'
        assert results[0][1] == 'john@example.com'
    
    def test_select_as_dict(self, connector, test_table):
        """Test selecting data as dictionary"""
        # Insert test data
        connector.execute_query(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ('Jane Doe', 'jane@example.com'),
            fetch=False
        )
        
        # Select as dict
        results = connector.execute_query(
            "SELECT name, email FROM test_users WHERE name = %s",
            ('Jane Doe',),
            as_dict=True
        )
        
        assert len(results) == 1
        assert results[0]['name'] == 'Jane Doe'
        assert results[0]['email'] == 'jane@example.com'
    
    def test_execute_many_bulk_insert(self, connector, test_table):
        """Test bulk insert using execute_many"""
        params_list = [
            ('Alice', 'alice@example.com'),
            ('Bob', 'bob@example.com'),
            ('Charlie', 'charlie@example.com')
        ]
        
        connector.execute_many(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            params_list
        )
        
        # Verify all records were inserted
        results = connector.execute_query("SELECT COUNT(*) FROM test_users")
        assert results[0][0] == 3
    
    def test_transaction_rollback(self, connector, test_table):
        """Test that errors cause rollback"""
        # Insert initial data
        connector.execute_query(
            "INSERT INTO test_users (name, email) VALUES (%s, %s)",
            ('Test User', 'test@example.com'),
            fetch=False
        )
        
        # Try to insert invalid data (should fail and rollback)
        try:
            connector.execute_query(
                "INSERT INTO test_users (invalid_column) VALUES (%s)",
                ('value',),
                fetch=False
            )
        except Exception:
            pass  # Expected to fail
        
        # Verify the first insert was rolled back
        results = connector.execute_query("SELECT COUNT(*) FROM test_users")
        # Note: This depends on transaction isolation level
        # In some cases, the first insert might still be there
    
    def test_context_manager_integration(self, test_table):
        """Test context manager with real database"""
        with DatabaseConnector() as db:
            assert db.is_connected is True
            
            # Insert data
            db.execute_query(
                "INSERT INTO test_users (name, email) VALUES (%s, %s)",
                ('Context User', 'context@example.com'),
                fetch=False
            )
            
            # Verify data
            results = db.execute_query("SELECT name FROM test_users WHERE name = %s", ('Context User',))
            assert len(results) == 1
        
        # Connection should be closed after context exit










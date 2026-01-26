"""
Manual test script for DatabaseConnector
Run this script to manually test the connector with a real database.

Usage:
    python tests/manual_test.py

Make sure to set environment variables or modify the connection parameters below.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_connector.app.db.connector import DatabaseConnector


def test_basic_operations():
    """Test basic database operations"""
    print("=" * 60)
    print("Testing DatabaseConnector - Basic Operations")
    print("=" * 60)
    
    # Initialize connector
    print("\n1. Initializing connector...")
    connector = DatabaseConnector()
    print(f"   Connector created: {connector}")
    
    # Try to connect
    print("\n2. Attempting to connect...")
    try:
        connector.connect()
        print("   ✓ Connection successful!")
        print(f"   Connection status: {connector.is_connected}")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n   Note: Make sure PostgreSQL is running and environment variables are set:")
        print("   - DB_HOST")
        print("   - DB_PORT (default: 5432)")
        print("   - DB_USER")
        print("   - DB_PASSWORD")
        print("   - DB_NAME")
        return
    
    # Test query execution
    print("\n3. Testing query execution...")
    try:
        # Test a simple SELECT query
        result = connector.execute_query("SELECT version()")
        if result:
            print(f"   ✓ Query executed successfully")
            print(f"   PostgreSQL version: {result[0][0][:50]}...")
    except Exception as e:
        print(f"   ✗ Query execution failed: {e}")
    
    # Test with parameters
    print("\n4. Testing parameterized query...")
    try:
        result = connector.execute_query("SELECT current_database(), current_user")
        if result:
            print(f"   ✓ Parameterized query works")
            print(f"   Database: {result[0][0]}, User: {result[0][1]}")
    except Exception as e:
        print(f"   ✗ Parameterized query failed: {e}")
    
    # Test as_dict
    print("\n5. Testing dictionary results...")
    try:
        result = connector.execute_query(
            "SELECT current_database() as db, current_user as user",
            as_dict=True
        )
        if result:
            print(f"   ✓ Dictionary results work")
            print(f"   Result: {result[0]}")
    except Exception as e:
        print(f"   ✗ Dictionary query failed: {e}")
    
    # Disconnect
    print("\n6. Disconnecting...")
    connector.disconnect()
    print(f"   ✓ Disconnected. Status: {connector.is_connected}")
    
    print("\n" + "=" * 60)
    print("Basic operations test completed!")
    print("=" * 60)


def test_context_manager():
    """Test context manager usage"""
    print("\n" + "=" * 60)
    print("Testing DatabaseConnector - Context Manager")
    print("=" * 60)
    
    try:
        with DatabaseConnector() as db:
            print("\n1. Entered context manager")
            print(f"   Connection status: {db.is_connected}")
            
            # Execute a query
            result = db.execute_query("SELECT 1 as test_value")
            print(f"   ✓ Query result: {result[0][0]}")
            
            print("\n2. Exiting context manager (should auto-disconnect)")
        
        print("   ✓ Context manager exited successfully")
        
    except Exception as e:
        print(f"   ✗ Context manager test failed: {e}")
    
    print("=" * 60)


def test_create_table_and_insert():
    """Test creating a table and inserting data"""
    print("\n" + "=" * 60)
    print("Testing DatabaseConnector - Table Operations")
    print("=" * 60)
    
    try:
        with DatabaseConnector() as db:
            # Create a test table
            print("\n1. Creating test table...")
            db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS test_connector (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                fetch=False
            )
            print("   ✓ Table created")
            
            # Insert data
            print("\n2. Inserting test data...")
            db.execute_query(
                "INSERT INTO test_connector (name) VALUES (%s)",
                ('Test User',),
                fetch=False
            )
            print("   ✓ Data inserted")
            
            # Select data
            print("\n3. Selecting data...")
            results = db.execute_query("SELECT * FROM test_connector WHERE name = %s", ('Test User',))
            print(f"   ✓ Found {len(results)} record(s)")
            if results:
                print(f"   Record: ID={results[0][0]}, Name={results[0][1]}")
            
            # Cleanup
            print("\n4. Cleaning up...")
            db.execute_query("DROP TABLE IF EXISTS test_connector", fetch=False)
            print("   ✓ Table dropped")
            
    except Exception as e:
        print(f"   ✗ Table operations failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)


if __name__ == "__main__":
    print("\nDatabaseConnector Manual Test Suite")
    print("=" * 60)
    
    # Run tests
    test_basic_operations()
    test_context_manager()
    test_create_table_and_insert()
    
    print("\n" + "=" * 60)
    print("All manual tests completed!")
    print("=" * 60)










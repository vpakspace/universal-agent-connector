"""
Check database permissions and available tables
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_connector.app.db.connector import DatabaseConnector

connector = DatabaseConnector(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    user=os.getenv('DB_USER', 'cloudbadal'),
    password=os.getenv('DB_PASSWORD', 'Home1234@'),
    database=os.getenv('DB_NAME', 'test_db')
)

try:
    connector.connect()
    print("Connected successfully!\n")
    
    # Check current user and database
    result = connector.execute_query("SELECT current_user, current_database()")
    print(f"Current user: {result[0][0]}")
    print(f"Current database: {result[0][1]}\n")
    
    # List all tables
    print("All tables in database:")
    print("-" * 60)
    tables = connector.execute_query("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
    """)
    
    for schema, table in tables:
        print(f"  {schema}.{table}")
    
    print("\n" + "=" * 60)
    print("Checking permissions on target tables:")
    print("=" * 60)
    
    target_tables = ['school', 'class', 'student', 'enrollment']
    for table in target_tables:
        try:
            # Try to query the table
            result = connector.execute_query(f"SELECT COUNT(*) FROM {table} LIMIT 1")
            print(f"✓ {table}: Has SELECT permission")
        except Exception as e:
            print(f"✗ {table}: {str(e)}")
            
        # Check if table exists
        exists = connector.execute_query("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, (table,))
        if exists and exists[0][0]:
            print(f"  → Table exists but no permission")
        else:
            print(f"  → Table might not exist or in different schema")
    
finally:
    connector.disconnect()







"""
List all tables in the public schema using pg_catalog
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
    print("=" * 70)
    print("Listing all tables in public schema")
    print("=" * 70)
    print(f"\nConnected as user: {connector.user}")
    print(f"Database: {connector.database}\n")
    
    # Query to list all tables
    results = connector.execute_query("""
        SELECT tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    
    if results:
        print(f"Found {len(results)} table(s) in public schema:\n")
        for row in results:
            print(f"  - {row[0]}")
    else:
        print("No tables found in public schema")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    connector.disconnect()







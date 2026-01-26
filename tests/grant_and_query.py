"""
Script to grant permissions and then query tables
Note: This requires admin privileges to grant permissions
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_connector.app.db.connector import DatabaseConnector

# Try to connect as postgres user (admin) to grant permissions
# If this doesn't work, you'll need to run the SQL manually

admin_connector = DatabaseConnector(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    user=os.getenv('DB_ADMIN_USER', 'postgres'),  # Try postgres user
    password=os.getenv('DB_ADMIN_PASSWORD', ''),  # Admin password
    database=os.getenv('DB_NAME', 'test_db')
)

user_connector = DatabaseConnector(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    user=os.getenv('DB_USER', 'cloudbadal'),
    password=os.getenv('DB_PASSWORD', 'Home1234@'),
    database=os.getenv('DB_NAME', 'test_db')
)

tables = ['school', 'class', 'student', 'enrollment']

def grant_permissions():
    """Try to grant permissions as admin"""
    try:
        admin_connector.connect()
        print("Connected as admin user. Granting permissions...\n")
        
        for table in tables:
            try:
                admin_connector.execute_query(
                    f"GRANT SELECT ON TABLE public.{table} TO cloudbadal",
                    fetch=False
                )
                print(f"✓ Granted SELECT permission on {table}")
            except Exception as e:
                print(f"✗ Failed to grant permission on {table}: {e}")
        
        admin_connector.disconnect()
        return True
    except Exception as e:
        print(f"Could not connect as admin user: {e}")
        print("\nPlease run the SQL commands manually:")
        print("  See: tests/grant_permissions.sql")
        return False

def query_tables():
    """Query all tables"""
    try:
        user_connector.connect()
        print("\n" + "=" * 80)
        print("Querying Tables from test_db Database")
        print("=" * 80)
        print(f"\nConnected as user: {user_connector.user}")
        print(f"Database: {user_connector.database}\n")
        
        for table in tables:
            print(f"\n{'=' * 80}")
            print(f"Table: {table}")
            print('=' * 80)
            
            try:
                # Get column information
                column_info = user_connector.execute_query("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = [col[0] for col in column_info] if column_info else []
                
                # Query all data
                results = user_connector.execute_query(f"SELECT * FROM {table}")
                
                if not results:
                    print("Table exists but contains no data.")
                    continue
                
                # Display information
                if columns:
                    print(f"\nColumns ({len(columns)}): {', '.join(columns)}")
                print(f"Total rows: {len(results)}\n")
                
                if not columns:
                    columns = [f"col_{i+1}" for i in range(len(results[0]))]
                
                # Calculate column widths
                col_widths = {}
                for col in columns:
                    col_widths[col] = max(len(col), 12)
                
                for row in results:
                    for i, val in enumerate(row):
                        if i < len(columns):
                            col_name = columns[i]
                            val_str = str(val) if val is not None else 'NULL'
                            col_widths[col_name] = max(col_widths[col_name], min(len(val_str), 40))
                
                # Print header
                header = " | ".join(f"{col:{col_widths[col]}}" for col in columns)
                print("Data:")
                print("-" * len(header))
                print(header)
                print("-" * len(header))
                
                # Print all rows
                for row in results:
                    row_str = " | ".join(
                        f"{str(val) if val is not None else 'NULL':{col_widths[columns[i]]}}" 
                        for i, val in enumerate(row) if i < len(columns)
                    )
                    print(row_str)
                    
            except Exception as e:
                error_msg = str(e)
                if "permission denied" in error_msg.lower():
                    print(f"✗ Permission denied!")
                    print(f"  Please grant SELECT permission on {table}")
                else:
                    print(f"✗ Error: {error_msg}")
        
        print("\n" + "=" * 80)
        print("All queries completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Connection error: {e}")
    finally:
        user_connector.disconnect()

# Main execution
if __name__ == "__main__":
    print("=" * 80)
    print("Grant Permissions and Query Tables")
    print("=" * 80)
    
    # Try to grant permissions first
    granted = grant_permissions()
    
    if not granted:
        print("\n⚠ Could not grant permissions automatically.")
        print("Please run the SQL commands from tests/grant_permissions.sql")
        print("as a database administrator, then run this script again.\n")
    
    # Query tables
    query_tables()







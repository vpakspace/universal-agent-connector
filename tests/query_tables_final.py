"""
Query all tables: school, class, student, enrollment
Run this after granting SELECT permissions to cloudbadal user
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

tables = ['school', 'class', 'student', 'enrollment']

def query_table(connector, table_name):
    """Query and display a table"""
    print(f"\n{'=' * 80}")
    print(f"Table: {table_name}")
    print('=' * 80)
    
    try:
        # Get column information first
        column_info = connector.execute_query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        if not column_info:
            # Try without schema specification
            column_info = connector.execute_query("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
        
        columns = [col[0] for col in column_info] if column_info else []
        
        # Query all data
        results = connector.execute_query(f"SELECT * FROM {table_name}")
        
        if not results:
            print("Table exists but contains no data.")
            return
        
        # Display information
        if columns:
            print(f"\nColumns ({len(columns)}): {', '.join(columns)}")
        print(f"Total rows: {len(results)}\n")
        
        if not columns:
            # If we couldn't get column names, infer from first row
            columns = [f"col_{i+1}" for i in range(len(results[0]))]
        
        # Calculate column widths
        col_widths = {}
        for col in columns:
            col_widths[col] = max(len(col), 12)
        
        # Adjust widths based on data
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
            print(f"\n  Please run these SQL commands as a database admin:")
            print(f"  GRANT SELECT ON TABLE public.{table_name} TO cloudbadal;")
        else:
            print(f"✗ Error: {error_msg}")

try:
    connector.connect()
    print("=" * 80)
    print("Querying Tables from test_db Database")
    print("=" * 80)
    print(f"\nConnected as user: {connector.user}")
    print(f"Database: {connector.database}")
    
    for table in tables:
        query_table(connector, table)
    
    print("\n" + "=" * 80)
    print("All queries completed!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Connection error: {e}")
    import traceback
    traceback.print_exc()
finally:
    connector.disconnect()
    print("\nDisconnected from database.")







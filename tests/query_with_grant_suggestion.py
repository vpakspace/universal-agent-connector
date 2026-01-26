"""
Query tables with permission check and grant suggestions
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

try:
    connector.connect()
    print("=" * 70)
    print("Querying Tables from test_db Database")
    print("=" * 70)
    print(f"\nConnected as user: {connector.user}")
    print(f"Database: {connector.database}\n")
    
    for table in tables:
        print(f"\n{'=' * 70}")
        print(f"Table: {table}")
        print('=' * 70)
        
        # Check if table exists
        try:
            exists = connector.execute_query("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            
            if not exists or not exists[0][0]:
                print(f"⚠ Table '{table}' does not exist in 'public' schema")
                print(f"  You may need to create it or check other schemas")
                continue
        except Exception as e:
            print(f"⚠ Could not check if table exists: {e}")
            continue
        
        # Try to query the table
        try:
            results = connector.execute_query(f"SELECT * FROM {table}")
            
            if not results:
                print("✓ Table exists but contains no data")
                continue
            
            # Get column info
            column_info = connector.execute_query("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            if column_info:
                columns = [col[0] for col in column_info]
                print(f"\nColumns ({len(columns)}): {', '.join(columns)}")
                print(f"Total rows: {len(results)}\n")
                
                # Display data
                print("Data:")
                print("-" * 70)
                
                # Calculate column widths
                col_widths = {col: max(len(col), 12) for col in columns}
                for row in results:
                    for i, val in enumerate(row):
                        if i < len(columns):
                            col_name = columns[i]
                            val_str = str(val) if val is not None else 'NULL'
                            col_widths[col_name] = max(col_widths[col_name], min(len(val_str), 30))
                
                # Print header
                header = " | ".join(f"{col:{col_widths[col]}}" for col in columns)
                print(header)
                print("-" * len(header))
                
                # Print rows (limit to 20 for display)
                for i, row in enumerate(results[:20], 1):
                    row_str = " | ".join(
                        f"{str(val) if val is not None else 'NULL':{col_widths[columns[j]]}}" 
                        for j, val in enumerate(row) if j < len(columns)
                    )
                    print(row_str)
                
                if len(results) > 20:
                    print(f"\n... and {len(results) - 20} more rows")
            else:
                print(f"✓ Found {len(results)} rows")
                for i, row in enumerate(results[:10], 1):
                    print(f"  Row {i}: {row}")
                if len(results) > 10:
                    print(f"  ... and {len(results) - 10} more rows")
                    
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Permission denied or error: {error_msg}")
            print(f"\n  To grant permissions, run this SQL as a database admin:")
            print(f"  GRANT SELECT ON TABLE public.{table} TO {connector.user};")
            print(f"  -- Or for all privileges:")
            print(f"  GRANT ALL PRIVILEGES ON TABLE public.{table} TO {connector.user};")
    
    print("\n" + "=" * 70)
    print("Query completed!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Connection error: {e}")
finally:
    connector.disconnect()







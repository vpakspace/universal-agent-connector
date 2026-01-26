"""
Query tables from all schemas in test_db
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
    
    # First, list all schemas
    print("Available schemas:")
    print("-" * 70)
    schemas = connector.execute_query("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name
    """)
    for schema_row in schemas:
        print(f"  - {schema_row[0]}")
    print()
    
    # Check tables in all schemas
    print("Searching for tables in all schemas:")
    print("-" * 70)
    all_tables = connector.execute_query("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY table_schema, table_name
    """)
    
    if all_tables:
        print(f"Found {len(all_tables)} table(s):")
        for schema, table in all_tables:
            print(f"  {schema}.{table}")
    else:
        print("No tables found in any schema")
    print()
    
    # Try to query each table directly (will show actual error)
    for table in tables:
        print(f"\n{'=' * 70}")
        print(f"Attempting to query: {table}")
        print('=' * 70)
        
        # Try without schema first
        try:
            results = connector.execute_query(f"SELECT * FROM {table} LIMIT 5")
            print(f"✓ Success! Found {len(results)} row(s) (showing first 5)")
            
            # Get column names
            try:
                # Try to get columns by describing the result
                if results:
                    print(f"\nColumns: {len(results[0])} column(s)")
                    print("\nFirst few rows:")
                    for i, row in enumerate(results[:5], 1):
                        print(f"  Row {i}: {row}")
            except:
                pass
                
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Error: {error_msg}")
            
            # Try with public schema
            try:
                print(f"\nTrying with 'public' schema...")
                results = connector.execute_query(f"SELECT * FROM public.{table} LIMIT 5")
                print(f"✓ Success with public schema! Found {len(results)} row(s)")
                if results:
                    print("\nFirst few rows:")
                    for i, row in enumerate(results[:5], 1):
                        print(f"  Row {i}: {row}")
            except Exception as e2:
                print(f"✗ Also failed with public schema: {e2}")
    
    # Now try full queries
    print("\n" + "=" * 70)
    print("Full Table Queries")
    print("=" * 70)
    
    for table in tables:
        print(f"\n{'=' * 70}")
        print(f"Table: {table}")
        print('=' * 70)
        
        try:
            # Try direct query first
            results = connector.execute_query(f"SELECT * FROM {table}")
            
            if not results:
                print("Table exists but contains no data")
                continue
            
            # Get column info
            try:
                column_info = connector.execute_query("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
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
                    col_widths = {col: max(len(col), 10) for col in columns}
                    for row in results:
                        for i, val in enumerate(row):
                            if i < len(columns):
                                col_name = columns[i]
                                val_str = str(val) if val is not None else 'NULL'
                                col_widths[col_name] = max(col_widths[col_name], min(len(val_str), 25))
                    
                    # Print header
                    header = " | ".join(f"{col:{col_widths[col]}}" for col in columns)
                    print(header)
                    print("-" * len(header))
                    
                    # Print all rows
                    for row in results:
                        row_str = " | ".join(
                            f"{str(val) if val is not None else 'NULL':{col_widths[columns[j]]}}" 
                            for j, val in enumerate(row) if j < len(columns)
                        )
                        print(row_str)
                else:
                    print(f"Found {len(results)} rows")
                    for row in results:
                        print(f"  {row}")
                        
            except Exception as col_error:
                print(f"Could not get column info: {col_error}")
                print(f"Found {len(results)} rows")
                for i, row in enumerate(results[:10], 1):
                    print(f"  Row {i}: {row}")
                if len(results) > 10:
                    print(f"  ... and {len(results) - 10} more rows")
                    
        except Exception as e:
            # Try with public schema
            try:
                results = connector.execute_query(f"SELECT * FROM public.{table}")
                
                if not results:
                    print("Table exists but contains no data")
                    continue
                
                print(f"✓ Found {len(results)} row(s) in public.{table}")
                
                # Get column info
                column_info = connector.execute_query("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                if column_info:
                    columns = [col[0] for col in column_info]
                    print(f"\nColumns: {', '.join(columns)}")
                    print(f"Total rows: {len(results)}\n")
                    
                    # Display data
                    print("Data:")
                    print("-" * 70)
                    
                    # Calculate column widths
                    col_widths = {col: max(len(col), 10) for col in columns}
                    for row in results:
                        for i, val in enumerate(row):
                            if i < len(columns):
                                col_name = columns[i]
                                val_str = str(val) if val is not None else 'NULL'
                                col_widths[col_name] = max(col_widths[col_name], min(len(val_str), 25))
                    
                    # Print header
                    header = " | ".join(f"{col:{col_widths[col]}}" for col in columns)
                    print(header)
                    print("-" * len(header))
                    
                    # Print all rows
                    for row in results:
                        row_str = " | ".join(
                            f"{str(val) if val is not None else 'NULL':{col_widths[columns[j]]}}" 
                            for j, val in enumerate(row) if j < len(columns)
                        )
                        print(row_str)
                        
            except Exception as e2:
                print(f"✗ Could not query table: {e2}")
                print(f"\n  This might be a permission issue.")
                print(f"  Try running as a database admin:")
                print(f"  GRANT SELECT ON TABLE {table} TO {connector.user};")
                print(f"  -- Or:")
                print(f"  GRANT SELECT ON TABLE public.{table} TO {connector.user};")
    
    print("\n" + "=" * 70)
    print("Query completed!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Connection error: {e}")
    import traceback
    traceback.print_exc()
finally:
    connector.disconnect()







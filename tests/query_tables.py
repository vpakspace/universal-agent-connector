"""
Script to query tables from test_db database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_connector.app.db.connector import DatabaseConnector


def query_table(connector, table_name, schema='public'):
    """Query and display data from a table"""
    full_table_name = f"{schema}.{table_name}" if schema else table_name
    print(f"\n{'=' * 60}")
    print(f"Table: {full_table_name}")
    print('=' * 60)
    
    try:
        results = connector.execute_query(f"SELECT * FROM {full_table_name}")
        
        if not results:
            print("No data found in table.")
            return
        
        # Get column names by querying information_schema
        column_info = connector.execute_query(
            f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table_name)
        )
        
        if column_info:
            columns = [col[0] for col in column_info]
            print(f"\nColumns: {', '.join(columns)}")
            print(f"\nTotal rows: {len(results)}")
            print("\nData:")
            print("-" * 80)
            
            # Calculate column widths
            col_widths = {}
            for col in columns:
                col_widths[col] = max(len(col), 15)
            
            # Adjust widths based on data
            for row in results:
                for i, val in enumerate(row):
                    col_name = columns[i]
                    val_str = str(val) if val is not None else 'NULL'
                    col_widths[col_name] = max(col_widths[col_name], len(val_str))
            
            # Print header
            header = " | ".join(f"{col:{col_widths[col]}}" for col in columns)
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in results:
                row_str = " | ".join(
                    f"{str(val) if val is not None else 'NULL':{col_widths[columns[i]]}}" 
                    for i, val in enumerate(row)
                )
                print(row_str)
        else:
            # Fallback: just print rows
            print(f"\nTotal rows: {len(results)}")
            for i, row in enumerate(results, 1):
                print(f"Row {i}: {row}")
                
    except Exception as e:
        print(f"Error querying {full_table_name}: {e}")


def list_available_tables(connector):
    """List all available tables in the database"""
    try:
        tables = connector.execute_query("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """)
        
        if tables:
            print("\nAvailable tables in database:")
            print("-" * 60)
            for schema, table in tables:
                print(f"  {schema}.{table}")
            print()
    except Exception as e:
        print(f"Error listing tables: {e}")


def main():
    """Main function to query all tables"""
    print("\n" + "=" * 60)
    print("Querying PostgreSQL Database: test_db")
    print("=" * 60)
    
    # Set database connection parameters
    connector = DatabaseConnector(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'cloudbadal'),
        password=os.getenv('DB_PASSWORD', 'Home1234@'),
        database=os.getenv('DB_NAME', 'test_db')
    )
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        connector.connect()
        print("✓ Connected successfully!")
        
        # List available tables first
        list_available_tables(connector)
        
        # Try querying tables - try both with and without schema
        tables = ['school', 'class', 'student', 'enrollment']
        schemas_to_try = ['public', None]  # Try public schema first, then no schema
        
        for table in tables:
            queried = False
            for schema in schemas_to_try:
                try:
                    query_table(connector, table, schema)
                    queried = True
                    break
                except Exception as e:
                    if schema is None:  # Last attempt
                        print(f"\n{'=' * 60}")
                        print(f"Table: {table}")
                        print('=' * 60)
                        print(f"Error: {e}")
                    continue
        
        print("\n" + "=" * 60)
        print("All queries completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connector.disconnect()
        print("\nDisconnected from database.")


if __name__ == "__main__":
    main()

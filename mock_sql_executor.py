"""
Mock SQL Executor for Self-Healing Query System Testing
Simulates SQL execution with configurable failures
"""

from typing import Dict, Any, Optional, List
from ontology_matcher import ColumnNotFoundError, TableNotFoundError, TypeMismatchError


class MockSQLExecutor:
    """
    Mock SQL executor that simulates database queries.
    Can be configured to fail for specific columns/tables.
    """
    
    def __init__(self):
        """Initialize mock executor"""
        # Track which columns exist in which tables
        # Format: table_name -> set of column_names
        self.table_schemas: Dict[str, set] = {
            "customers": {
                "id", "vat_number", "name", "email", "phone", "address",
                "created_at", "updated_at"
            },
            "orders": {
                "id", "customer_id", "order_date", "total_amount", "status",
                "shipping_address"
            },
            "products": {
                "id", "product_name", "price", "category", "description",
                "in_stock"
            }
        }
        
        # Track which columns should fail (for testing)
        self.failing_columns: Dict[str, List[str]] = {}  # table -> [columns]
        
        # Mock data for successful queries
        self.mock_data: Dict[str, List[Dict[str, Any]]] = {
            "customers": [
                {"id": 1, "vat_number": "VAT123", "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "vat_number": "VAT456", "name": "Jane Smith", "email": "jane@example.com"}
            ],
            "orders": [
                {"id": 1, "customer_id": 1, "order_date": "2024-01-01", "total_amount": 99.99},
                {"id": 2, "customer_id": 2, "order_date": "2024-01-02", "total_amount": 149.50}
            ],
            "products": [
                {"id": 1, "product_name": "Widget", "price": 29.99, "category": "Electronics"},
                {"id": 2, "product_name": "Gadget", "price": 49.99, "category": "Electronics"}
            ]
        }
    
    def set_failing_column(self, table: str, column: str) -> None:
        """
        Configure a column to fail (for testing)
        
        Args:
            table: Table name
            column: Column name that should fail
        """
        if table not in self.failing_columns:
            self.failing_columns[table] = []
        
        if column not in self.failing_columns[table]:
            self.failing_columns[table].append(column)
    
    def clear_failing_column(self, table: str, column: str) -> None:
        """
        Clear a failing column (for testing)
        
        Args:
            table: Table name
            column: Column name to clear
        """
        if table in self.failing_columns:
            if column in self.failing_columns[table]:
                self.failing_columns[table].remove(column)
    
    def add_column_to_schema(self, table: str, column: str) -> None:
        """
        Add a column to a table schema (simulate schema change)
        
        Args:
            table: Table name
            column: Column name to add
        """
        if table not in self.table_schemas:
            self.table_schemas[table] = set()
        
        self.table_schemas[table].add(column)
        
        # Also add to mock data if table exists
        if table in self.mock_data and self.mock_data[table]:
            for row in self.mock_data[table]:
                row[column] = f"mock_{column}_value"
    
    def execute(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query (mock implementation)
        
        This is a simplified SQL parser that:
        - Extracts table name from FROM clause
        - Extracts column names from SELECT clause
        - Checks if table and columns exist
        - Returns mock data if valid
        
        Args:
            query: SQL query string
        
        Returns:
            List of dictionaries (rows)
        
        Raises:
            TableNotFoundError: If table doesn't exist
            ColumnNotFoundError: If column doesn't exist
            TypeMismatchError: If there's a type mismatch (not implemented in mock)
        """
        query_lower = query.lower().strip()
        
        # Extract table name (simple parsing)
        table = None
        if "from" in query_lower:
            parts = query_lower.split("from")
            if len(parts) > 1:
                table_part = parts[1].split()[0].strip().rstrip(';')
                table = table_part
        
        if not table:
            raise ValueError("Could not extract table name from query")
        
        # Check if table exists
        if table not in self.table_schemas:
            raise TableNotFoundError(f"Table '{table}' not found")
        
        # Extract columns (simple parsing)
        columns = []
        if query_lower.startswith("select"):
            select_part = query_lower.split("from")[0].replace("select", "").strip()
            if "*" in select_part:
                # SELECT * - use all columns
                columns = list(self.table_schemas[table])
            else:
                # Extract individual columns
                column_names = [col.strip().rstrip(',') for col in select_part.split(",")]
                columns = column_names
        
        # Check if columns exist (and not in failing list)
        available_columns = self.table_schemas[table]
        failing_cols = self.failing_columns.get(table, [])
        
        for col in columns:
            # Remove aliases (AS clause)
            col_clean = col.split()[0].strip()
            
            # Check if column should fail
            if col_clean in failing_cols:
                raise ColumnNotFoundError(
                    f"Column '{col_clean}' not found in table '{table}'. "
                    f"Available columns: {sorted(available_columns)}"
                )
            
            # Check if column exists
            if col_clean not in available_columns and col_clean != "*":
                raise ColumnNotFoundError(
                    f"Column '{col_clean}' not found in table '{table}'. "
                    f"Available columns: {sorted(available_columns)}"
                )
        
        # Return mock data (filtered by requested columns)
        if table not in self.mock_data:
            return []
        
        result = []
        for row in self.mock_data[table]:
            if "*" in query_lower:
                result.append(row.copy())
            else:
                filtered_row = {col: row.get(col, None) for col in columns}
                result.append(filtered_row)
        
        return result
    
    def get_table_schema(self, table: str) -> set:
        """
        Get schema for a table
        
        Args:
            table: Table name
        
        Returns:
            Set of column names
        """
        return self.table_schemas.get(table, set())
    
    def reset(self) -> None:
        """Reset executor state (for testing)"""
        self.failing_columns.clear()
        # Reset to default schemas
        self.table_schemas = {
            "customers": {
                "id", "vat_number", "name", "email", "phone", "address",
                "created_at", "updated_at"
            },
            "orders": {
                "id", "customer_id", "order_date", "total_amount", "status",
                "shipping_address"
            },
            "products": {
                "id", "product_name", "price", "category", "description",
                "in_stock"
            }
        }


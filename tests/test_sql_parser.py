"""
Unit tests for SQL parser utilities
"""

import pytest
from ai_agent_connector.app.utils.sql_parser import (
    extract_tables_from_query,
    get_query_type,
    requires_read_permission,
    requires_write_permission,
    QueryType
)


class TestSQLParser:
    """Test cases for SQL parsing utilities"""
    
    def test_extract_tables_simple_select(self):
        """Test extracting table from simple SELECT"""
        query = "SELECT * FROM users"
        tables = extract_tables_from_query(query)
        assert 'users' in tables
    
    def test_extract_tables_schema_table(self):
        """Test extracting schema.table format"""
        query = "SELECT * FROM public.orders"
        tables = extract_tables_from_query(query)
        assert 'public.orders' in tables
    
    def test_extract_tables_multiple_from_join(self):
        """Test extracting tables from JOIN queries"""
        query = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        tables = extract_tables_from_query(query)
        assert 'users' in tables
        assert 'orders' in tables
    
    def test_extract_tables_insert(self):
        """Test extracting table from INSERT"""
        query = "INSERT INTO products (name, price) VALUES ('Test', 10)"
        tables = extract_tables_from_query(query)
        assert 'products' in tables
    
    def test_extract_tables_update(self):
        """Test extracting table from UPDATE"""
        query = "UPDATE users SET name = 'John' WHERE id = 1"
        tables = extract_tables_from_query(query)
        assert 'users' in tables
    
    def test_extract_tables_delete(self):
        """Test extracting table from DELETE"""
        query = "DELETE FROM orders WHERE status = 'cancelled'"
        tables = extract_tables_from_query(query)
        assert 'orders' in tables
    
    def test_extract_tables_case_insensitive(self):
        """Test case-insensitive table extraction"""
        query = "select * from USERS"
        tables = extract_tables_from_query(query)
        assert 'users' in tables
    
    def test_get_query_type_select(self):
        """Test query type detection for SELECT"""
        assert get_query_type("SELECT * FROM users") == QueryType.SELECT
        assert get_query_type("select id from table") == QueryType.SELECT
    
    def test_get_query_type_insert(self):
        """Test query type detection for INSERT"""
        assert get_query_type("INSERT INTO users VALUES (1)") == QueryType.INSERT
        assert get_query_type("insert into table values (1)") == QueryType.INSERT
    
    def test_get_query_type_update(self):
        """Test query type detection for UPDATE"""
        assert get_query_type("UPDATE users SET name = 'test'") == QueryType.UPDATE
    
    def test_get_query_type_delete(self):
        """Test query type detection for DELETE"""
        assert get_query_type("DELETE FROM users") == QueryType.DELETE
    
    def test_requires_read_permission(self):
        """Test read permission requirement check"""
        assert requires_read_permission("SELECT * FROM users") is True
        assert requires_read_permission("INSERT INTO users VALUES (1)") is False
    
    def test_requires_write_permission(self):
        """Test write permission requirement check"""
        assert requires_write_permission("INSERT INTO users VALUES (1)") is True
        assert requires_write_permission("UPDATE users SET name = 'test'") is True
        assert requires_write_permission("DELETE FROM users") is True
        assert requires_write_permission("SELECT * FROM users") is False
    
    def test_extract_tables_with_comments(self):
        """Test table extraction with SQL comments"""
        query = """
        -- This is a comment
        SELECT * FROM users
        /* Multi-line comment */
        WHERE id = 1
        """
        tables = extract_tables_from_query(query)
        assert 'users' in tables
    
    def test_extract_tables_empty_query(self):
        """Test handling of empty query"""
        assert extract_tables_from_query("") == set()
        assert extract_tables_from_query(None) == set()







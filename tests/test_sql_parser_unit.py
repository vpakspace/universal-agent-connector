"""Unit tests for SQL parser utilities."""

import pytest
from ai_agent_connector.app.utils.sql_parser import (
    extract_tables_from_query,
    get_query_type,
    requires_write_permission,
    requires_read_permission,
    QueryType,
)


class TestGetQueryType:
    def test_select(self):
        assert get_query_type("SELECT * FROM users") == QueryType.SELECT

    def test_insert(self):
        assert get_query_type("INSERT INTO users VALUES (1)") == QueryType.INSERT

    def test_update(self):
        assert get_query_type("UPDATE users SET name='a'") == QueryType.UPDATE

    def test_delete(self):
        assert get_query_type("DELETE FROM users WHERE id=1") == QueryType.DELETE

    def test_unknown(self):
        assert get_query_type("CREATE TABLE foo (id INT)") == QueryType.UNKNOWN

    def test_empty(self):
        assert get_query_type("") == QueryType.UNKNOWN

    def test_none(self):
        assert get_query_type(None) == QueryType.UNKNOWN

    def test_case_insensitive(self):
        assert get_query_type("select * from t") == QueryType.SELECT

    def test_leading_whitespace(self):
        assert get_query_type("   SELECT 1") == QueryType.SELECT

    def test_with_comment(self):
        assert get_query_type("-- comment\nSELECT 1") == QueryType.SELECT


class TestExtractTables:
    def test_select_from(self):
        assert extract_tables_from_query("SELECT * FROM users") == {"users"}

    def test_insert_into(self):
        assert extract_tables_from_query("INSERT INTO orders VALUES (1)") == {"orders"}

    def test_update(self):
        assert extract_tables_from_query("UPDATE products SET price=10") == {"products"}

    def test_delete_from(self):
        assert extract_tables_from_query("DELETE FROM logs WHERE id=1") == {"logs"}

    def test_join(self):
        tables = extract_tables_from_query(
            "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        )
        assert tables == {"users", "orders"}

    def test_schema_dot_table(self):
        tables = extract_tables_from_query("SELECT * FROM public.users")
        assert "public.users" in tables

    def test_multiple_tables(self):
        tables = extract_tables_from_query(
            "SELECT * FROM users JOIN orders ON 1=1 JOIN products ON 1=1"
        )
        assert {"users", "orders", "products"} == tables

    def test_empty(self):
        assert extract_tables_from_query("") == set()

    def test_none(self):
        assert extract_tables_from_query(None) == set()

    def test_comment_only(self):
        assert extract_tables_from_query("-- just a comment") == set()


class TestPermissions:
    def test_write_insert(self):
        assert requires_write_permission("INSERT INTO t VALUES (1)") is True

    def test_write_update(self):
        assert requires_write_permission("UPDATE t SET a=1") is True

    def test_write_delete(self):
        assert requires_write_permission("DELETE FROM t") is True

    def test_write_select(self):
        assert requires_write_permission("SELECT 1") is False

    def test_read_select(self):
        assert requires_read_permission("SELECT * FROM t") is True

    def test_read_insert(self):
        assert requires_read_permission("INSERT INTO t VALUES (1)") is False

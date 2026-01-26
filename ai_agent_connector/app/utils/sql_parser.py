"""
SQL query parser utilities for extracting table and dataset names
"""

import re
from typing import List, Set, Optional
from enum import Enum


class QueryType(Enum):
    """SQL query operation types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UNKNOWN = "UNKNOWN"


def extract_tables_from_query(query: str) -> Set[str]:
    """
    Extract table/dataset names from a SQL query.
    
    Supports:
    - SELECT FROM table
    - SELECT FROM schema.table
    - INSERT INTO table
    - UPDATE table
    - DELETE FROM table
    - JOIN operations
    
    Args:
        query: SQL query string
        
    Returns:
        Set[str]: Set of table identifiers (e.g., 'table', 'schema.table')
    """
    if not query or not isinstance(query, str):
        return set()
    
    # Normalize query - remove comments and extra whitespace
    normalized = _normalize_query(query)
    
    tables = set()
    
    # Extract FROM clauses
    from_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
    from_matches = re.finditer(from_pattern, normalized, re.IGNORECASE)
    for match in from_matches:
        table = match.group(1).strip()
        if table:
            tables.add(table.lower())
    
    # Extract JOIN clauses
    join_pattern = r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
    join_matches = re.finditer(join_pattern, normalized, re.IGNORECASE)
    for match in join_matches:
        table = match.group(1).strip()
        if table:
            tables.add(table.lower())
    
    # Extract INSERT INTO
    insert_pattern = r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
    insert_matches = re.finditer(insert_pattern, normalized, re.IGNORECASE)
    for match in insert_matches:
        table = match.group(1).strip()
        if table:
            tables.add(table.lower())
    
    # Extract UPDATE
    update_pattern = r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
    update_matches = re.finditer(update_pattern, normalized, re.IGNORECASE)
    for match in update_matches:
        table = match.group(1).strip()
        if table:
            tables.add(table.lower())
    
    # Extract DELETE FROM
    delete_pattern = r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
    delete_matches = re.finditer(delete_pattern, normalized, re.IGNORECASE)
    for match in delete_matches:
        table = match.group(1).strip()
        if table:
            tables.add(table.lower())
    
    return tables


def get_query_type(query: str) -> QueryType:
    """
    Determine the type of SQL query.
    
    Args:
        query: SQL query string
        
    Returns:
        QueryType: Type of query operation
    """
    if not query or not isinstance(query, str):
        return QueryType.UNKNOWN
    
    normalized = _normalize_query(query)
    
    if re.match(r'^\s*SELECT\b', normalized, re.IGNORECASE):
        return QueryType.SELECT
    elif re.match(r'^\s*INSERT\b', normalized, re.IGNORECASE):
        return QueryType.INSERT
    elif re.match(r'^\s*UPDATE\b', normalized, re.IGNORECASE):
        return QueryType.UPDATE
    elif re.match(r'^\s*DELETE\b', normalized, re.IGNORECASE):
        return QueryType.DELETE
    
    return QueryType.UNKNOWN


def _normalize_query(query: str) -> str:
    """
    Normalize SQL query by removing comments and extra whitespace.
    
    Args:
        query: Raw SQL query
        
    Returns:
        str: Normalized query
    """
    # Remove single-line comments
    query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    
    # Remove multi-line comments
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    
    # Normalize whitespace
    query = re.sub(r'\s+', ' ', query)
    
    return query.strip()


def requires_write_permission(query: str) -> bool:
    """
    Check if a query requires write permission.
    
    Args:
        query: SQL query string
        
    Returns:
        bool: True if query requires write permission
    """
    query_type = get_query_type(query)
    return query_type in (QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE)


def requires_read_permission(query: str) -> bool:
    """
    Check if a query requires read permission.
    
    Args:
        query: SQL query string
        
    Returns:
        bool: True if query requires read permission
    """
    return get_query_type(query) == QueryType.SELECT







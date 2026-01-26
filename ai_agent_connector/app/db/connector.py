# app/db/connector.py

"""
Multi-Database Connector
Provides unified interface for connecting to multiple database types:
PostgreSQL, MySQL, MongoDB, BigQuery, Snowflake, etc.
"""

import os
from typing import Optional, Dict, Any, List, Tuple, Union

from .factory import DatabaseConnectorFactory
from .base_connector import BaseDatabaseConnector


class DatabaseConnector:
    """
    Multi-database connector with support for connect, disconnect, and query execution.
    
    Supports PostgreSQL, MySQL, MongoDB, BigQuery, and Snowflake.
    Can be used as a context manager for automatic connection handling.
    
    This class provides backward compatibility with the original PostgreSQL-only interface
    while adding support for multiple database types.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        connection_string: Optional[str] = None,
        database_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize database connector.
        
        Args:
            host: Database host (defaults to DB_HOST env var)
            port: Database port (defaults to DB_PORT env var or 5432 for PostgreSQL)
            user: Database user (defaults to DB_USER env var)
            password: Database password (defaults to DB_PASSWORD env var)
            database: Database name (defaults to DB_NAME env var)
            connection_string: Connection string (database-specific format)
            database_type: Type of database (postgresql, mysql, mongodb, bigquery, snowflake)
                          If not provided, will be detected from connection_string or default to postgresql
            **kwargs: Additional database-specific parameters
        """
        # Build config dictionary
        config: Dict[str, Any] = {}
        
        if connection_string:
            config['connection_string'] = connection_string
        else:
            config['host'] = host or os.getenv('DB_HOST')
            config['port'] = port or int(os.getenv('DB_PORT', 5432))
            config['user'] = user or os.getenv('DB_USER')
            config['password'] = password or os.getenv('DB_PASSWORD')
            config['database'] = database or os.getenv('DB_NAME')
        
        # Add any additional kwargs
        config.update(kwargs)
        
        # Determine database type
        if database_type:
            self.database_type = database_type.lower()
        else:
            self.database_type = DatabaseConnectorFactory.detect_database_type(config) or 'postgresql'
        
        # Store config for reference
        self.config = config
        
        # Create the appropriate connector
        self._connector: BaseDatabaseConnector = DatabaseConnectorFactory.create_connector(
            self.database_type,
            config
        )
    
    def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            ValueError: If required connection parameters are missing
        """
        return self._connector.connect()
    
    def disconnect(self) -> None:
        """
        Close the database connection.
        
        Safe to call even if not connected.
        """
        self._connector.disconnect()
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """
        Execute a query against the database.
        
        Args:
            query: Query string (SQL for SQL databases, JSON for MongoDB, etc.)
            params: Query parameters (dict, tuple, or list)
            fetch: Whether to fetch results (False for INSERT/UPDATE/DELETE)
            as_dict: Return results as list of dicts instead of tuples
            
        Returns:
            Query results as list of tuples or dicts, or None if fetch=False
            
        Raises:
            ConnectionError: If not connected to database
            Exception: If query execution fails
        """
        return self._connector.execute_query(query, params, fetch, as_dict)
    
    def execute_many(
        self,
        query: str,
        params_list: List[Union[Dict[str, Any], Tuple]]
    ) -> None:
        """
        Execute a query multiple times with different parameters (bulk insert/update).
        
        Note: This method is primarily for SQL databases. MongoDB and other NoSQL
        databases may have different bulk operation patterns.
        
        Args:
            query: Query string
            params_list: List of parameter sets to execute
            
        Raises:
            ConnectionError: If not connected to database
            Exception: If query execution fails
        """
        if not self._connector.is_connected:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        # For SQL databases, execute each query
        for params in params_list:
            self._connector.execute_query(query, params, fetch=False)
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected to database."""
        return self._connector.is_connected
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the connected database.
        
        Returns:
            Dict containing database metadata (type, version, name, etc.)
        """
        return self._connector.get_database_info()
    
    def __enter__(self):
        """Context manager entry - automatically connects."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically disconnects."""
        self.disconnect()
    
    def __repr__(self) -> str:
        """String representation of the connector."""
        status = "connected" if self.is_connected else "disconnected"
        db_name = self.config.get('database', 'unknown')
        return f"DatabaseConnector(type={self.database_type}, database={db_name}, status={status})"


"""
Base database connector interface
Defines the common interface for all database connectors
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple, Union


class BaseDatabaseConnector(ABC):
    """
    Abstract base class for database connectors.
    All database connectors must implement these methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the database connector.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self._is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the database connection.
        
        Safe to call even if not connected.
        """
        pass
    
    @abstractmethod
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
            query: Query string (SQL, MongoDB query, etc.)
            params: Query parameters
            fetch: Whether to fetch results
            as_dict: Return results as list of dicts instead of tuples
            
        Returns:
            Query results or None if fetch=False
            
        Raises:
            ConnectionError: If not connected
            Exception: If query execution fails
        """
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to database."""
        pass
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the connected database.
        
        Returns:
            Dict containing database metadata (version, name, etc.)
        """
        pass
    
    def __enter__(self):
        """Context manager entry - automatically connects."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically disconnects."""
        self.disconnect()


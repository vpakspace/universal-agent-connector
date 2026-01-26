"""
Example Custom Database Plugin
This demonstrates how to create a custom database driver plugin.

To use this plugin:
1. Copy this file to your plugins directory
2. Register it using the plugin registry
3. Use 'custom_db' as the database_type in your configuration
"""

from typing import Dict, Any, List, Tuple, Optional, Union
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector


class ExampleCustomConnector(BaseDatabaseConnector):
    """
    Example custom database connector implementation.
    This is a minimal example - replace with your actual database logic.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.host = config.get('host')
        self.port = config.get('port', 5432)
        self.user = config.get('user')
        self.password = config.get('password')
        self.database = config.get('database')
        self.connection_string = config.get('connection_string')
    
    def connect(self) -> bool:
        """
        Establish connection to the custom database.
        
        In a real implementation, you would:
        1. Import your database client library
        2. Create a connection using the config
        3. Store the connection object
        4. Set self._is_connected = True on success
        """
        try:
            # Example: Using a hypothetical custom_db library
            # import custom_db
            # self.connection = custom_db.connect(
            #     host=self.host,
            #     port=self.port,
            #     user=self.user,
            #     password=self.password,
            #     database=self.database
            # )
            
            # For this example, we'll simulate a connection
            if not all([self.host, self.user, self.database]):
                raise ConnectionError("Missing required connection parameters")
            
            # Simulate connection
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to custom database: {e}")
    
    def disconnect(self) -> None:
        """Close the database connection."""
        if self.connection:
            # In real implementation: self.connection.close()
            self.connection = None
        self._is_connected = False
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """
        Execute a query against the custom database.
        
        In a real implementation, you would:
        1. Validate the connection
        2. Execute the query using your database client
        3. Format results according to as_dict parameter
        4. Return the results
        """
        if not self._is_connected:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        try:
            # Example query execution
            # cursor = self.connection.cursor()
            # cursor.execute(query, params)
            # 
            # if fetch:
            #     if as_dict:
            #         columns = [desc[0] for desc in cursor.description]
            #         results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            #     else:
            #         results = cursor.fetchall()
            #     return results
            # return None
            
            # For this example, return empty results
            if fetch:
                if as_dict:
                    return []
                else:
                    return []
            return None
            
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected to database."""
        return self._is_connected
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the connected database.
        
        Returns:
            Dict containing database metadata
        """
        return {
            'type': 'custom_db',
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'version': '1.0.0'  # Replace with actual version detection
        }


class ExampleCustomDatabasePlugin(DatabasePlugin):
    """
    Example plugin for a custom database.
    
    This plugin demonstrates:
    - Required plugin properties
    - Configuration validation
    - Connector creation
    - Database type detection
    """
    
    @property
    def plugin_name(self) -> str:
        return "example_custom_db"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    @property
    def database_type(self) -> str:
        return "custom_db"
    
    @property
    def display_name(self) -> str:
        return "Example Custom Database"
    
    @property
    def description(self) -> str:
        return "Example plugin demonstrating how to create a custom database driver"
    
    @property
    def author(self) -> str:
        return "AI Agent Connector Team"
    
    @property
    def required_config_keys(self) -> List[str]:
        """
        Define required configuration keys.
        These will be validated before connector creation.
        """
        return ['host', 'user', 'database']
    
    @property
    def optional_config_keys(self) -> List[str]:
        """
        Define optional configuration keys.
        """
        return ['port', 'password', 'connection_string', 'timeout', 'ssl_mode']
    
    def create_connector(self, config: Dict[str, Any]) -> BaseDatabaseConnector:
        """
        Create a connector instance for this database type.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            BaseDatabaseConnector: Instance of the connector
        """
        # Validation is automatically called by the factory,
        # but you can add additional validation here if needed
        
        return ExampleCustomConnector(config)
    
    def detect_database_type(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Attempt to detect if this plugin should handle the given configuration.
        
        This method allows automatic detection based on connection patterns.
        """
        # Check explicit type
        if 'type' in config and config['type'].lower() == 'custom_db':
            return self.database_type
        
        # Check connection string pattern
        connection_string = config.get('connection_string', '')
        if connection_string and connection_string.startswith('customdb://'):
            return self.database_type
        
        # Check for custom database-specific config keys
        if 'custom_db_api_key' in config or 'custom_db_endpoint' in config:
            return self.database_type
        
        return None


# Plugin instance - this will be automatically discovered if the file is loaded
PLUGIN = ExampleCustomDatabasePlugin()







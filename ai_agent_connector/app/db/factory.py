"""
Database connector factory
Creates appropriate connector instances based on database type
"""

from typing import Dict, Any, Optional

from .base_connector import BaseDatabaseConnector
from .connectors import (
    PostgreSQLConnector,
    MySQLConnector,
    MongoDBConnector,
    BigQueryConnector,
    SnowflakeConnector
)
from .plugin import get_plugin_registry


class DatabaseConnectorFactory:
    """Factory for creating database connectors"""
    
    # Supported database types
    SUPPORTED_TYPES = {
        'postgresql': PostgreSQLConnector,
        'mysql': MySQLConnector,
        'mongodb': MongoDBConnector,
        'bigquery': BigQueryConnector,
        'snowflake': SnowflakeConnector
    }
    
    @classmethod
    def create_connector(
        cls,
        database_type: str,
        config: Dict[str, Any]
    ) -> BaseDatabaseConnector:
        """
        Create a database connector instance.
        
        Args:
            database_type: Type of database (postgresql, mysql, mongodb, bigquery, snowflake, or custom plugin)
            config: Database configuration dictionary
            
        Returns:
            BaseDatabaseConnector: Appropriate connector instance
            
        Raises:
            ValueError: If database type is not supported
        """
        db_type = database_type.lower()
        
        # First check built-in types
        if db_type in cls.SUPPORTED_TYPES:
            connector_class = cls.SUPPORTED_TYPES[db_type]
            return connector_class(config)
        
        # Then check plugins
        plugin_registry = get_plugin_registry()
        plugin = plugin_registry.get_plugin(db_type)
        if plugin:
            # Validate config
            is_valid, error_msg = plugin.validate_config(config)
            if not is_valid:
                raise ValueError(f"Invalid configuration for plugin '{db_type}': {error_msg}")
            return plugin.create_connector(config)
        
        # Not found in built-in or plugins
        supported = ', '.join(cls.get_supported_types())
        raise ValueError(
            f"Unsupported database type: {database_type}. "
            f"Supported types: {supported}"
        )
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        Get list of supported database types (including plugins).
        
        Returns:
            List of supported database type strings
        """
        built_in_types = list(cls.SUPPORTED_TYPES.keys())
        plugin_registry = get_plugin_registry()
        plugin_types = plugin_registry.get_supported_types()
        
        # Combine and deduplicate
        all_types = list(set(built_in_types + plugin_types))
        return sorted(all_types)
    
    @classmethod
    def detect_database_type(cls, config: Dict[str, Any]) -> Optional[str]:
        """
        Attempt to detect database type from configuration.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            Optional[str]: Detected database type or None
        """
        # Explicit type in config
        if 'type' in config:
            return config['type'].lower()
        
        # Detect from connection string - check plugins first
        connection_string = config.get('connection_string', '')
        if connection_string:
            plugin_registry = get_plugin_registry()
            for plugin in plugin_registry._plugins.values():
                detected = plugin.detect_database_type(config)
                if detected:
                    return detected
        
        # Then check built-in types
        if connection_string:
            if connection_string.startswith('postgresql://') or connection_string.startswith('postgres://'):
                return 'postgresql'
            elif connection_string.startswith('mysql://'):
                return 'mysql'
            elif connection_string.startswith('mongodb://') or connection_string.startswith('mongodb+srv://'):
                return 'mongodb'
            elif 'bigquery' in connection_string.lower():
                return 'bigquery'
            elif 'snowflake' in connection_string.lower():
                return 'snowflake'
        
        # Default to PostgreSQL for backward compatibility
        return 'postgresql'


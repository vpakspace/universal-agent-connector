"""
Plugin SDK for Custom Database Drivers
Allows developers to create custom database connectors as plugins
"""

import importlib
import importlib.util
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Type
import json

from .base_connector import BaseDatabaseConnector


class DatabasePlugin(ABC):
    """
    Base class for database driver plugins.
    
    All custom database plugins must extend this class and implement
    the required methods.
    """
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """
        Unique name identifier for the plugin.
        Should be lowercase, alphanumeric with underscores.
        Example: 'custom_db', 'proprietary_db'
        """
        pass
    
    @property
    @abstractmethod
    def plugin_version(self) -> str:
        """
        Plugin version string (semantic versioning recommended).
        Example: '1.0.0'
        """
        pass
    
    @property
    @abstractmethod
    def database_type(self) -> str:
        """
        Database type identifier that this plugin handles.
        This is the value used in database_type configuration.
        Example: 'custom_db', 'proprietary_db'
        """
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable display name for the database.
        Example: 'Custom Database', 'Proprietary DB'
        """
        pass
    
    @property
    def description(self) -> str:
        """
        Optional description of the plugin.
        Override this to provide plugin documentation.
        """
        return ""
    
    @property
    def author(self) -> str:
        """Plugin author name."""
        return ""
    
    @property
    def required_config_keys(self) -> List[str]:
        """
        List of required configuration keys for this plugin.
        These will be validated before connector creation.
        
        Returns:
            List of required config key names
        """
        return []
    
    @property
    def optional_config_keys(self) -> List[str]:
        """
        List of optional configuration keys for this plugin.
        
        Returns:
            List of optional config key names
        """
        return []
    
    @abstractmethod
    def create_connector(self, config: Dict[str, Any]) -> BaseDatabaseConnector:
        """
        Create a connector instance for this database type.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            BaseDatabaseConnector: Instance of the connector
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> tuple:
        """
        Validate configuration before creating connector.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            If valid, returns (True, None)
            If invalid, returns (False, error_message)
        """
        # Check required keys
        for key in self.required_config_keys:
            if key not in config or config[key] is None:
                return False, f"Missing required configuration key: {key}"
        
        return True, None
    
    def detect_database_type(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Attempt to detect if this plugin should handle the given configuration.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            Database type string if this plugin should handle it, None otherwise
        """
        # Default: check if database_type matches
        if 'type' in config and config['type'].lower() == self.database_type.lower():
            return self.database_type
        
        # Check connection string patterns
        connection_string = config.get('connection_string', '')
        if connection_string:
            # Override this method in your plugin to implement custom detection
            pass
        
        return None
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get metadata about this plugin.
        
        Returns:
            Dictionary containing plugin metadata
        """
        return {
            'name': self.plugin_name,
            'version': self.plugin_version,
            'database_type': self.database_type,
            'display_name': self.display_name,
            'description': self.description,
            'author': self.author,
            'required_config_keys': self.required_config_keys,
            'optional_config_keys': self.optional_config_keys
        }


class PluginRegistry:
    """
    Registry for managing database driver plugins.
    """
    
    def __init__(self):
        self._plugins: Dict[str, DatabasePlugin] = {}
        self._plugin_paths: Dict[str, str] = {}
    
    def register(self, plugin: DatabasePlugin) -> bool:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration successful, False if plugin with same name already exists
        """
        plugin_id = plugin.database_type.lower()
        
        if plugin_id in self._plugins:
            return False
        
        self._plugins[plugin_id] = plugin
        return True
    
    def unregister(self, database_type: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            database_type: Database type identifier
            
        Returns:
            True if unregistered, False if not found
        """
        plugin_id = database_type.lower()
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            if plugin_id in self._plugin_paths:
                del self._plugin_paths[plugin_id]
            return True
        return False
    
    def get_plugin(self, database_type: str) -> Optional[DatabasePlugin]:
        """
        Get a plugin by database type.
        
        Args:
            database_type: Database type identifier
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(database_type.lower())
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all registered plugins.
        
        Returns:
            List of plugin metadata dictionaries
        """
        return [plugin.get_plugin_info() for plugin in self._plugins.values()]
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of supported database types (including plugins).
        
        Returns:
            List of database type strings
        """
        return list(self._plugins.keys())
    
    def load_plugin_from_file(self, file_path: str) -> Optional[DatabasePlugin]:
        """
        Load a plugin from a Python file.
        
        Args:
            file_path: Path to the plugin Python file
            
        Returns:
            Plugin instance or None if loading failed
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return None
            
            module_name = file_path_obj.stem
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class (should be a subclass of DatabasePlugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, DatabasePlugin) and 
                    attr != DatabasePlugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                return None
            
            # Instantiate plugin
            plugin = plugin_class()
            
            # Register it
            if self.register(plugin):
                self._plugin_paths[plugin.database_type.lower()] = file_path
                return plugin
            
            return None
            
        except Exception as e:
            print(f"Error loading plugin from {file_path}: {e}")
            return None
    
    def load_plugins_from_directory(self, directory: str) -> List[DatabasePlugin]:
        """
        Load all plugins from a directory.
        
        Args:
            directory: Directory path containing plugin files
            
        Returns:
            List of successfully loaded plugin instances
        """
        loaded = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return loaded
        
        # Look for Python files in the directory
        for file_path in directory_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue
            
            plugin = self.load_plugin_from_file(str(file_path))
            if plugin:
                loaded.append(plugin)
        
        return loaded


# Global plugin registry instance
_global_registry = PluginRegistry()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    return _global_registry


def register_plugin(plugin: DatabasePlugin) -> bool:
    """Register a plugin in the global registry."""
    return _global_registry.register(plugin)


def get_plugin(database_type: str) -> Optional[DatabasePlugin]:
    """Get a plugin from the global registry."""
    return _global_registry.get_plugin(database_type)


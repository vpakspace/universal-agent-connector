"""
Tests for Database Plugin SDK
Validates plugin registration, loading, and integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Tuple, Optional, Union
import tempfile
import os
from pathlib import Path

from ai_agent_connector.app.db.plugin import (
    DatabasePlugin,
    PluginRegistry,
    get_plugin_registry,
    register_plugin
)
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector
from ai_agent_connector.app.db.factory import DatabaseConnectorFactory


class MockConnector(BaseDatabaseConnector):
    """Mock connector for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.config = config
    
    def connect(self) -> bool:
        self._is_connected = True
        return True
    
    def disconnect(self) -> None:
        self._is_connected = False
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        if not self._is_connected:
            raise ConnectionError("Not connected")
        return [] if fetch else None
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    def get_database_info(self) -> Dict[str, Any]:
        return {'type': 'test_db', 'version': '1.0.0'}


class TestPlugin(DatabasePlugin):
    """Test plugin implementation"""
    
    @property
    def plugin_name(self) -> str:
        return "test_plugin"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    @property
    def database_type(self) -> str:
        return "test_db"
    
    @property
    def display_name(self) -> str:
        return "Test Database"
    
    @property
    def description(self) -> str:
        return "Test plugin for validation"
    
    @property
    def author(self) -> str:
        return "Test Author"
    
    @property
    def required_config_keys(self) -> List[str]:
        return ['host', 'database']
    
    @property
    def optional_config_keys(self) -> List[str]:
        return ['port', 'user']
    
    def create_connector(self, config: Dict[str, Any]) -> BaseDatabaseConnector:
        return MockConnector(config)
    
    def detect_database_type(self, config: Dict[str, Any]) -> Optional[str]:
        if 'type' in config and config['type'].lower() == 'test_db':
            return self.database_type
        return None


class TestPluginSDK(unittest.TestCase):
    """Test cases for Plugin SDK"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = PluginRegistry()
        self.test_plugin = TestPlugin()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear registry
        self.registry.unregister('test_db')
    
    def test_plugin_properties(self):
        """Test that plugin exposes required properties"""
        self.assertEqual(self.test_plugin.plugin_name, "test_plugin")
        self.assertEqual(self.test_plugin.plugin_version, "1.0.0")
        self.assertEqual(self.test_plugin.database_type, "test_db")
        self.assertEqual(self.test_plugin.display_name, "Test Database")
        self.assertIn('host', self.test_plugin.required_config_keys)
        self.assertIn('database', self.test_plugin.required_config_keys)
    
    def test_plugin_info(self):
        """Test plugin info retrieval"""
        info = self.test_plugin.get_plugin_info()
        self.assertEqual(info['name'], "test_plugin")
        self.assertEqual(info['version'], "1.0.0")
        self.assertEqual(info['database_type'], "test_db")
        self.assertEqual(info['display_name'], "Test Database")
        self.assertIn('host', info['required_config_keys'])
    
    def test_plugin_registration(self):
        """Test plugin registration"""
        success = self.registry.register(self.test_plugin)
        self.assertTrue(success)
        
        # Try to register again - should fail
        success = self.registry.register(self.test_plugin)
        self.assertFalse(success)
    
    def test_plugin_retrieval(self):
        """Test retrieving registered plugin"""
        self.registry.register(self.test_plugin)
        
        plugin = self.registry.get_plugin('test_db')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.database_type, 'test_db')
        
        # Case insensitive
        plugin = self.registry.get_plugin('TEST_DB')
        self.assertIsNotNone(plugin)
    
    def test_plugin_unregistration(self):
        """Test plugin unregistration"""
        self.registry.register(self.test_plugin)
        self.assertIsNotNone(self.registry.get_plugin('test_db'))
        
        success = self.registry.unregister('test_db')
        self.assertTrue(success)
        self.assertIsNone(self.registry.get_plugin('test_db'))
        
        # Unregister again - should fail
        success = self.registry.unregister('test_db')
        self.assertFalse(success)
    
    def test_list_plugins(self):
        """Test listing registered plugins"""
        self.registry.register(self.test_plugin)
        
        plugins = self.registry.list_plugins()
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]['database_type'], 'test_db')
    
    def test_get_supported_types(self):
        """Test getting supported database types"""
        self.registry.register(self.test_plugin)
        
        types = self.registry.get_supported_types()
        self.assertIn('test_db', types)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        valid_config = {'host': 'localhost', 'database': 'testdb'}
        is_valid, error = self.test_plugin.validate_config(valid_config)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Missing required key
        invalid_config = {'host': 'localhost'}
        is_valid, error = self.test_plugin.validate_config(invalid_config)
        self.assertFalse(is_valid)
        self.assertIn('database', error)
        
        # Missing another required key
        invalid_config = {'database': 'testdb'}
        is_valid, error = self.test_plugin.validate_config(invalid_config)
        self.assertFalse(is_valid)
        self.assertIn('host', error)
    
    def test_detect_database_type(self):
        """Test database type detection"""
        # Explicit type
        config = {'type': 'test_db'}
        detected = self.test_plugin.detect_database_type(config)
        self.assertEqual(detected, 'test_db')
        
        # Case insensitive
        config = {'type': 'TEST_DB'}
        detected = self.test_plugin.detect_database_type(config)
        self.assertEqual(detected, 'test_db')
        
        # No match
        config = {'type': 'other_db'}
        detected = self.test_plugin.detect_database_type(config)
        self.assertIsNone(detected)
    
    def test_create_connector(self):
        """Test connector creation"""
        config = {'host': 'localhost', 'database': 'testdb'}
        connector = self.test_plugin.create_connector(config)
        
        self.assertIsInstance(connector, BaseDatabaseConnector)
        self.assertIsInstance(connector, MockConnector)
    
    def test_connector_functionality(self):
        """Test that created connector works correctly"""
        config = {'host': 'localhost', 'database': 'testdb'}
        connector = self.test_plugin.create_connector(config)
        
        # Test connection
        self.assertFalse(connector.is_connected)
        result = connector.connect()
        self.assertTrue(result)
        self.assertTrue(connector.is_connected)
        
        # Test query execution
        results = connector.execute_query("SELECT * FROM test")
        self.assertIsNotNone(results)
        
        # Test disconnection
        connector.disconnect()
        self.assertFalse(connector.is_connected)
    
    def test_plugin_from_file(self):
        """Test loading plugin from file"""
        # Create a temporary plugin file
        plugin_code = '''
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector
from typing import Dict, Any, List, Optional, Union, Tuple

class FileTestConnector(BaseDatabaseConnector):
    def __init__(self, config):
        super().__init__(config)
    
    def connect(self):
        self._is_connected = True
        return True
    
    def disconnect(self):
        self._is_connected = False
    
    def execute_query(self, query, params=None, fetch=True, as_dict=False):
        return [] if fetch else None
    
    @property
    def is_connected(self):
        return self._is_connected
    
    def get_database_info(self):
        return {'type': 'file_test'}

class FileTestPlugin(DatabasePlugin):
    @property
    def plugin_name(self):
        return "file_test_plugin"
    
    @property
    def plugin_version(self):
        return "1.0.0"
    
    @property
    def database_type(self):
        return "file_test"
    
    @property
    def display_name(self):
        return "File Test Database"
    
    @property
    def required_config_keys(self):
        return ['host']
    
    def create_connector(self, config):
        return FileTestConnector(config)
    
    def detect_database_type(self, config):
        if config.get('type') == 'file_test':
            return 'file_test'
        return None
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(plugin_code)
            temp_file = f.name
        
        try:
            plugin = self.registry.load_plugin_from_file(temp_file)
            self.assertIsNotNone(plugin)
            self.assertEqual(plugin.database_type, 'file_test')
            
            # Verify it's registered
            retrieved = self.registry.get_plugin('file_test')
            self.assertIsNotNone(retrieved)
            
        finally:
            os.unlink(temp_file)
            self.registry.unregister('file_test')
    
    def test_plugin_from_directory(self):
        """Test loading plugins from directory"""
        # Create temporary directory with plugin files
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_code = '''
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector
from typing import Dict, Any, List, Optional, Union, Tuple

class DirTestConnector(BaseDatabaseConnector):
    def __init__(self, config):
        super().__init__(config)
    
    def connect(self):
        self._is_connected = True
        return True
    
    def disconnect(self):
        self._is_connected = False
    
    def execute_query(self, query, params=None, fetch=True, as_dict=False):
        return [] if fetch else None
    
    @property
    def is_connected(self):
        return self._is_connected
    
    def get_database_info(self):
        return {'type': 'dir_test'}

class DirTestPlugin(DatabasePlugin):
    @property
    def plugin_name(self):
        return "dir_test_plugin"
    
    @property
    def plugin_version(self):
        return "1.0.0"
    
    @property
    def database_type(self):
        return "dir_test"
    
    @property
    def display_name(self):
        return "Directory Test Database"
    
    @property
    def required_config_keys(self):
        return ['host']
    
    def create_connector(self, config):
        return DirTestConnector(config)
    
    def detect_database_type(self, config):
        if config.get('type') == 'dir_test':
            return 'dir_test'
        return None
'''
            
            plugin_file = Path(temp_dir) / 'dir_test_plugin.py'
            plugin_file.write_text(plugin_code)
            
            # Load plugins from directory
            loaded = self.registry.load_plugins_from_directory(temp_dir)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].database_type, 'dir_test')
            
            # Clean up
            self.registry.unregister('dir_test')
    
    def test_global_registry(self):
        """Test global registry functions"""
        # Get global registry
        registry = get_plugin_registry()
        self.assertIsInstance(registry, PluginRegistry)
        
        # Register plugin
        success = register_plugin(self.test_plugin)
        self.assertTrue(success)
        
        # Clean up
        registry.unregister('test_db')
    
    def test_factory_integration(self):
        """Test integration with DatabaseConnectorFactory"""
        # Register plugin in global registry (factory uses global registry)
        global_registry = get_plugin_registry()
        global_registry.register(self.test_plugin)
        
        try:
            # Factory should now support the plugin type
            supported_types = DatabaseConnectorFactory.get_supported_types()
            self.assertIn('test_db', supported_types)
            
            # Create connector via factory
            config = {'host': 'localhost', 'database': 'testdb', 'type': 'test_db'}
            connector = DatabaseConnectorFactory.create_connector('test_db', config)
            self.assertIsNotNone(connector)
            self.assertIsInstance(connector, BaseDatabaseConnector)
        finally:
            # Clean up
            global_registry.unregister('test_db')
    
    def test_factory_validation(self):
        """Test that factory validates plugin config"""
        # Register plugin in global registry (factory uses global registry)
        global_registry = get_plugin_registry()
        global_registry.register(self.test_plugin)
        
        try:
            # Invalid config (missing required keys)
            invalid_config = {'host': 'localhost'}  # Missing 'database'
            
            with self.assertRaises(ValueError) as context:
                DatabaseConnectorFactory.create_connector('test_db', invalid_config)
            
            self.assertIn('Missing required configuration', str(context.exception))
        finally:
            # Clean up
            global_registry.unregister('test_db')
    
    def test_factory_detection_with_plugin(self):
        """Test database type detection with plugins"""
        # Register plugin in global registry (factory uses global registry)
        global_registry = get_plugin_registry()
        global_registry.register(self.test_plugin)
        
        try:
            # Detection should work with plugin
            config = {'type': 'test_db', 'host': 'localhost', 'database': 'testdb'}
            detected = DatabaseConnectorFactory.detect_database_type(config)
            self.assertEqual(detected, 'test_db')
        finally:
            # Clean up
            global_registry.unregister('test_db')


if __name__ == '__main__':
    unittest.main()







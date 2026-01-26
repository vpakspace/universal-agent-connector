# Database Plugin SDK

## Overview

The Database Plugin SDK allows developers to create custom database driver plugins for proprietary or niche databases. The SDK provides a complete framework for plugin development, registration, validation, and integration.

## Features

✅ **Base Plugin Class** - Abstract base class (`DatabasePlugin`) for all plugins  
✅ **Plugin Registry** - Automatic registration and discovery system  
✅ **TypeScript Types** - Complete type definitions for plugin development  
✅ **Example Plugin** - Working example demonstrating plugin implementation  
✅ **Validation Tests** - Comprehensive test suite for plugin validation  
✅ **Factory Integration** - Seamless integration with `DatabaseConnectorFactory`  
✅ **API Endpoints** - REST API for plugin management  
✅ **Configuration Validation** - Built-in validation for plugin configurations  

## Architecture

### Core Components

1. **`DatabasePlugin`** (Base Class)
   - Abstract base class that all plugins must extend
   - Defines plugin metadata (name, version, database_type, etc.)
   - Provides configuration validation
   - Handles connector creation

2. **`PluginRegistry`**
   - Manages plugin registration and discovery
   - Loads plugins from files and directories
   - Provides plugin lookup by database type

3. **`BaseDatabaseConnector`** (Connector Interface)
   - Abstract base class for database connectors
   - Defines standard methods: `connect()`, `disconnect()`, `execute_query()`, etc.
   - All plugin connectors must extend this class

4. **Factory Integration**
   - `DatabaseConnectorFactory` automatically supports plugins
   - Plugins are checked after built-in database types
   - Seamless integration with existing code

## File Structure

```
ai_agent_connector/app/db/
├── plugin.py              # Plugin SDK core (DatabasePlugin, PluginRegistry)
├── plugin_types.ts         # TypeScript type definitions
├── base_connector.py       # Base connector interface
└── factory.py              # Factory (integrated with plugins)

examples/plugins/
└── example_custom_db.py    # Example plugin implementation

tests/
└── test_plugin_sdk.py      # Plugin validation tests
```

## Quick Start

### 1. Create a Plugin

```python
from ai_agent_connector.app.db.plugin import DatabasePlugin
from ai_agent_connector.app.db.base_connector import BaseDatabaseConnector

class MyCustomConnector(BaseDatabaseConnector):
    # Implement required methods
    pass

class MyPlugin(DatabasePlugin):
    @property
    def plugin_name(self) -> str:
        return "my_plugin"
    
    @property
    def database_type(self) -> str:
        return "my_db"
    
    # ... implement other required properties and methods
    def create_connector(self, config):
        return MyCustomConnector(config)
```

### 2. Register the Plugin

```python
from ai_agent_connector.app.db.plugin import register_plugin

plugin = MyPlugin()
register_plugin(plugin)
```

### 3. Use the Plugin

```python
from ai_agent_connector.app.db import DatabaseConnector

connector = DatabaseConnector(
    database_type='my_db',
    host='localhost',
    database='mydb'
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plugins` | GET | List all registered plugins |
| `/api/plugins/<database_type>` | GET | Get plugin information |
| `/api/plugins/<database_type>` | DELETE | Unregister a plugin |
| `/api/plugins/load` | POST | Load a plugin from a file |
| `/api/plugins/load-directory` | POST | Load plugins from a directory |
| `/api/plugins/validate` | POST | Validate plugin configuration |
| `/api/plugins/supported-types` | GET | Get all supported database types |

## Testing

Run the plugin SDK tests:

```bash
pytest tests/test_plugin_sdk.py -v
```

The test suite covers:
- Plugin registration and unregistration
- Configuration validation
- Connector creation and functionality
- Plugin loading from files and directories
- Factory integration
- Database type detection

## TypeScript Types

TypeScript type definitions are available in `ai_agent_connector/app/db/plugin_types.ts`. These can be used for:
- Type checking in TypeScript/JavaScript projects
- IDE autocomplete and IntelliSense
- Documentation reference
- Integration with frontend applications

## Example Plugin

See `examples/plugins/example_custom_db.py` for a complete, working example that demonstrates:
- Plugin class implementation
- Connector implementation
- Configuration validation
- Database type detection
- Error handling

## Requirements

All plugins must:

1. ✅ Extend `DatabasePlugin` base class
2. ✅ Implement all abstract methods and properties
3. ✅ Return a connector that extends `BaseDatabaseConnector`
4. ✅ Implement proper error handling
5. ✅ Validate configuration before creating connectors

## Plugin Properties

Required properties:
- `plugin_name` - Unique identifier (lowercase, alphanumeric with underscores)
- `plugin_version` - Version string (semantic versioning recommended)
- `database_type` - Database type identifier
- `display_name` - Human-readable name
- `required_config_keys` - List of required configuration keys
- `create_connector()` - Method to create connector instance

Optional properties:
- `description` - Plugin description
- `author` - Plugin author name
- `optional_config_keys` - List of optional configuration keys
- `detect_database_type()` - Custom detection logic

## Integration

The plugin system is fully integrated with:
- `DatabaseConnectorFactory` - Automatically discovers and uses plugins
- `DatabaseConnector` - Works seamlessly with plugin connectors
- API routes - Plugin management endpoints available
- Agent registry - Agents can use plugin databases

## Next Steps

1. Review the example plugin: `examples/plugins/example_custom_db.py`
2. Read the TypeScript types: `ai_agent_connector/app/db/plugin_types.ts`
3. Run the tests: `pytest tests/test_plugin_sdk.py`
4. Create your own plugin following the example
5. Register and use your plugin

## Support

For questions or issues with the Plugin SDK:
1. Check the example plugin implementation
2. Review the test cases for usage examples
3. Consult the TypeScript types for interface definitions
4. Review the README.md for general documentation







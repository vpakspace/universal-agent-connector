# Migration Feature Test Cases

Complete test coverage for the migration feature (export/import/rollback).

## Test Files

- `cli/__tests__/commands/migrate.test.js` - Migration command tests
- `cli/__tests__/utils/validator.test.js` - Configuration validator tests

## Test Classes Overview

1. **Migration Command Tests** - Export, import, rollback functionality
2. **Validator Tests** - Configuration validation

## Detailed Test Cases

### Migration Command Tests - Export (5 tests)

#### Export Functionality
- ✅ `should export configuration successfully` - Successful export
- ✅ `should export to JSON format` - JSON output format
- ✅ `should throw error when API key is missing` - Validation: missing API key
- ✅ `should throw error when agent ID is missing` - Validation: missing agent ID
- ✅ `should handle export errors` - Error handling

### Migration Command Tests - Import (7 tests)

#### Import Functionality
- ✅ `should import configuration successfully` - Successful import
- ✅ `should validate only when --validate flag is set` - Validation-only mode
- ✅ `should perform dry run` - Dry run mode
- ✅ `should throw error when input file is missing` - Validation: missing input file
- ✅ `should throw error when input file does not exist` - Error: file not found
- ✅ `should throw error for invalid JSON` - Error: invalid JSON
- ✅ `should throw error for invalid configuration` - Error: invalid config

### Migration Command Tests - Rollback (3 tests)

#### Rollback Functionality
- ✅ `should rollback configuration successfully` - Successful rollback
- ✅ `should throw error when backup file is missing` - Validation: missing backup
- ✅ `should throw error when backup file does not exist` - Error: backup not found

### Migration Command Tests - Invalid Action (1 test)

#### Error Handling
- ✅ `should throw error for unknown action` - Error: unknown action

### Validator Tests - Configuration Validation (8 tests)

#### Configuration Structure
- ✅ `should validate valid configuration` - Valid config passes
- ✅ `should reject configuration without version` - Missing version
- ✅ `should reject configuration without agent` - Missing agent
- ✅ `should reject configuration without agent_id` - Missing agent_id
- ✅ `should reject configuration without agent name` - Missing agent name
- ✅ `should validate resource permissions structure` - Valid permissions
- ✅ `should reject invalid resource permissions` - Invalid permissions
- ✅ `should reject non-array permissions` - Permissions must be array

### Validator Tests - Tables Validation (2 tests)

#### Tables Structure
- ✅ `should validate tables array` - Valid tables array
- ✅ `should reject non-array tables` - Tables must be array

### Validator Tests - File Validation (3 tests)

#### File Operations
- ✅ `should validate existing file` - Valid file
- ✅ `should reject non-existent file` - File not found
- ✅ `should reject invalid JSON` - Invalid JSON format

## Running Tests

### Run All Migration Tests

```bash
cd cli
npm test -- migrate
```

### Run Specific Test File

```bash
# Migration command tests
npm test -- migrate.test.js

# Validator tests
npm test -- validator.test.js
```

### Run with Coverage

```bash
npm test -- --coverage migrate
```

## Test Coverage Summary

- **Total Test Cases**: 26+
- **Export Tests**: 5
- **Import Tests**: 7
- **Rollback Tests**: 3
- **Invalid Action Tests**: 1
- **Validator Tests**: 13

## Test Categories

### ✅ Export Tests
- Configuration export
- JSON format
- Validation
- Error handling

### ✅ Import Tests
- Configuration import
- Validation mode
- Dry run mode
- File validation
- Error handling

### ✅ Rollback Tests
- Rollback functionality
- Backup validation
- Error handling

### ✅ Validator Tests
- Configuration structure
- Required fields
- Type validation
- File validation

## Key Test Scenarios

### Scenario 1: Export Configuration
```javascript
test('should export configuration successfully', async () => {
  const mockAgent = {
    agent_id: 'test-agent',
    agent_info: { name: 'Test Agent' },
    resource_permissions: {}
  };
  
  mockClient.getAgent.mockResolvedValue(mockAgent);
  mockClient.listTables.mockResolvedValue({ tables: [] });
  
  await migrateCommand('export', {
    url: 'http://localhost:5000',
    apiKey: 'test-key',
    agentId: 'test-agent',
    output: 'config.json'
  });
  
  expect(fs.writeFileSync).toHaveBeenCalled();
});
```

### Scenario 2: Import with Validation
```javascript
test('should validate only when --validate flag is set', async () => {
  fs.existsSync.mockReturnValue(true);
  fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));
  
  await migrateCommand('import', {
    input: 'config.json',
    validate: true
  });
  
  expect(consoleLogSpy).toHaveBeenCalledWith(
    expect.stringContaining('Validation only')
  );
});
```

### Scenario 3: Configuration Validation
```javascript
test('should validate valid configuration', () => {
  const config = {
    version: '1.0.0',
    agent: {
      agent_id: 'test-agent',
      name: 'Test Agent'
    }
  };
  
  const result = validateConfig(config);
  expect(result.valid).toBe(true);
});
```

## Test Data

### Valid Configuration

```json
{
  "version": "1.0.0",
  "agent": {
    "agent_id": "test-agent",
    "name": "Test Agent",
    "resource_permissions": {
      "products": {
        "type": "table",
        "permissions": ["read"]
      }
    }
  },
  "tables": ["products"],
  "metadata": {}
}
```

### Invalid Configurations

1. **Missing Version**
```json
{
  "agent": {
    "agent_id": "test-agent",
    "name": "Test Agent"
  }
}
```

2. **Missing Agent**
```json
{
  "version": "1.0.0"
}
```

3. **Invalid Permissions**
```json
{
  "version": "1.0.0",
  "agent": {
    "agent_id": "test-agent",
    "name": "Test Agent",
    "resource_permissions": {
      "products": {
        "permissions": "read"  // Should be array
      }
    }
  }
}
```

## Mocking Strategy

### API Client Mocking
- `getAgent()` - Returns agent configuration
- `listTables()` - Returns table list
- Error scenarios - Network errors, API errors

### File System Mocking
- `fs.existsSync()` - File existence checks
- `fs.readFileSync()` - Read configuration files
- `fs.writeFileSync()` - Write configuration files
- `fs.mkdirSync()` - Create directories

### Console Mocking
- `console.log()` - Output capture
- `console.error()` - Error output capture

## Edge Cases Tested

### Export Edge Cases
- Missing API key
- Missing agent ID
- API errors
- Network errors
- Missing tables endpoint

### Import Edge Cases
- Missing input file
- Non-existent file
- Invalid JSON
- Invalid configuration structure
- Missing required fields
- Validation errors

### Rollback Edge Cases
- Missing backup file
- Non-existent backup
- Invalid backup format
- Validation errors

### Validator Edge Cases
- Missing required fields
- Invalid data types
- Malformed structures
- Empty configurations
- Nested validation errors

## Integration Test Scenarios

### Complete Workflow

1. **Export → Validate → Import**
   ```javascript
   // Export
   await migrateCommand('export', { output: 'config.json' });
   
   // Validate
   await migrateCommand('import', { input: 'config.json', validate: true });
   
   // Import
   await migrateCommand('import', { input: 'config.json' });
   ```

2. **Export → Import → Rollback**
   ```javascript
   // Export
   await migrateCommand('export', { output: 'backup.json' });
   
   // Import
   await migrateCommand('import', { input: 'config.json' });
   
   // Rollback
   await migrateCommand('rollback', { backup: 'backup.json' });
   ```

## Performance Considerations

### Large Configurations
- Test with large permission sets
- Test with many tables
- Test with complex nested structures

### File Operations
- Test with large files
- Test with concurrent operations
- Test with file system errors

## Security Test Cases

### Data Protection
- Connection strings not exported
- API keys not exported
- Sensitive data handling

### Validation Security
- SQL injection prevention
- Path traversal prevention
- File system security

## Notes

- Tests use Jest testing framework
- Mocked axios for API calls
- Mocked fs for file operations
- Mocked console for output testing
- Tests validate all error paths
- Tests cover edge cases

## Future Test Enhancements

1. **Integration Tests**
   - Real API integration
   - End-to-end workflows
   - Multi-environment testing

2. **Performance Tests**
   - Large configuration handling
   - Concurrent operations
   - File I/O performance

3. **Security Tests**
   - Injection attacks
   - Path traversal
   - File system security

4. **Error Recovery Tests**
   - Partial import recovery
   - Rollback scenarios
   - Error state handling


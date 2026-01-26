# CLI Tool Test Cases

Complete test coverage for the aidb CLI tool.

## Test Files

- `cli/__tests__/commands/query.test.js` - Query command tests
- `cli/__tests__/commands/explain.test.js` - Explain command tests
- `cli/__tests__/commands/test.test.js` - Test command tests
- `cli/__tests__/commands/config.test.js` - Config command tests
- `cli/__tests__/api/client.test.js` - API client tests
- `cli/__tests__/utils/formatter.test.js` - Formatter tests

## Test Classes Overview

1. **Query Command Tests** - Query execution and options
2. **Explain Command Tests** - Query explanation
3. **Test Command Tests** - Connection testing
4. **Config Command Tests** - Configuration management
5. **API Client Tests** - API client functionality
6. **Formatter Tests** - Output formatting

## Detailed Test Cases

### Query Command Tests (8 tests)

#### Query Execution
- ✅ `should execute query successfully` - Successful query execution
- ✅ `should output JSON format` - JSON output format
- ✅ `should handle preview mode` - Preview SQL without executing
- ✅ `should handle cache option` - Cache control
- ✅ `should throw error when API key is missing` - Validation: missing API key
- ✅ `should throw error when agent ID is missing` - Validation: missing agent ID
- ✅ `should handle API errors` - Error handling
- ✅ `should show verbose output` - Verbose mode

### Explain Command Tests (6 tests)

#### Query Explanation
- ✅ `should explain query successfully` - Successful explanation
- ✅ `should output JSON format` - JSON output format
- ✅ `should handle missing explanation` - Missing explanation handling
- ✅ `should throw error when API key is missing` - Validation: missing API key
- ✅ `should throw error when agent ID is missing` - Validation: missing agent ID
- ✅ `should handle API errors` - Error handling

### Test Command Tests (6 tests)

#### Connection Testing
- ✅ `should test connection successfully` - Successful connection test
- ✅ `should output JSON format` - JSON output format
- ✅ `should handle connection failure` - Connection failure handling
- ✅ `should throw error when API key is missing` - Validation: missing API key
- ✅ `should throw error when agent ID is missing` - Validation: missing agent ID
- ✅ `should handle API errors` - Error handling

### Config Command Tests (7 tests)

#### Configuration Management
- ✅ `should list configuration` - List all configuration
- ✅ `should get configuration value` - Get specific value
- ✅ `should mask sensitive values when getting` - Security: mask sensitive values
- ✅ `should set configuration value` - Set configuration value
- ✅ `should handle invalid set format` - Validation: invalid format
- ✅ `should handle missing configuration key` - Error: missing key
- ✅ `should handle empty configuration` - Empty configuration handling

### API Client Tests (8 tests)

#### API Client Functionality
- ✅ `should create client with correct configuration` - Client creation
- ✅ `should remove trailing slash from URL` - URL normalization
- ✅ `should execute query` - Query execution
- ✅ `should execute explain` - Explain execution
- ✅ `should test connection` - Connection testing
- ✅ `should handle API errors` - API error handling
- ✅ `should handle network errors` - Network error handling

### Formatter Tests (8 tests)

#### Output Formatting
- ✅ `should format preview results` - Preview mode formatting
- ✅ `should format query results with rows` - Results table formatting
- ✅ `should format empty results` - Empty results handling
- ✅ `should show SQL in verbose mode` - Verbose mode formatting
- ✅ `should format results with explanation` - Explanation formatting
- ✅ `should format results with statistics` - Statistics formatting
- ✅ `should handle null values` - Null value handling
- ✅ `should handle missing columns` - Missing columns handling

## Running Tests

### Run All Tests

```bash
cd cli
npm test
```

### Run Specific Test File

```bash
# Query command tests
npm test -- query.test.js

# API client tests
npm test -- client.test.js

# Formatter tests
npm test -- formatter.test.js
```

### Run with Coverage

```bash
npm test -- --coverage
```

## Test Coverage Summary

- **Total Test Cases**: 43+
- **Query Command Tests**: 8
- **Explain Command Tests**: 6
- **Test Command Tests**: 6
- **Config Command Tests**: 7
- **API Client Tests**: 8
- **Formatter Tests**: 8

## Test Categories

### ✅ Command Tests
- Query execution
- Explain functionality
- Connection testing
- Configuration management

### ✅ API Client Tests
- Client creation
- Request/response handling
- Error handling
- Network error handling

### ✅ Formatter Tests
- Table formatting
- JSON formatting
- Preview mode
- Error formatting

## Key Test Scenarios

### Scenario 1: Query Execution
```javascript
test('should execute query successfully', async () => {
  const result = await queryCommand('What are the products?', {
    url: 'http://localhost:5000',
    apiKey: 'test-key',
    agentId: 'test-agent'
  });
  
  expect(result).toBeDefined();
});
```

### Scenario 2: JSON Output
```javascript
test('should output JSON format', async () => {
  await queryCommand('Get products', {
    json: true
  });
  
  const output = JSON.parse(consoleLogSpy.mock.calls[0][0]);
  expect(output.sql).toBeDefined();
});
```

### Scenario 3: Error Handling
```javascript
test('should handle API errors', async () => {
  mockClient.query.mockRejectedValue(
    new Error('API Error (401): Invalid API key')
  );
  
  await expect(queryCommand('test')).rejects.toThrow('Invalid API key');
});
```

## Notes

- Tests use Jest testing framework
- Mocked axios for API calls
- Mocked console for output testing
- Mocked fs for config tests
- Mocked inquirer for interactive tests

## Future Enhancements

- Integration tests with real API
- E2E tests for complete workflows
- Performance tests
- Load tests for concurrent queries


# Universal Agent Connector SDK - Test Suite

Comprehensive test suite for the JavaScript/TypeScript SDK covering all functionality, error handling, and edge cases.

## Test Structure

### Test Files

- **`client.test.ts`** - Main client functionality tests (100+ tests)
  - Client initialization
  - Request handling and error management
  - All API methods
  - Edge cases
  - Integration scenarios

- **`exceptions.test.ts`** - Exception class tests
  - Exception hierarchy
  - Exception usage patterns
  - Error handling scenarios

## Running Tests

### Install Dependencies

```bash
cd sdk-js
npm install
```

### Run All Tests

```bash
npm test
```

### Run with Watch Mode

```bash
npm run test:watch
```

### Run with Coverage

```bash
npm run test:coverage
```

### Run Specific Test File

```bash
npm test -- client.test.ts
npm test -- exceptions.test.ts
```

## Test Categories

### 1. Client Initialization
- Default initialization
- Custom parameters
- URL handling
- API key configuration

### 2. Request Handling
- Successful requests
- Authentication errors (401)
- Not found errors (404)
- Validation errors (400)
- Rate limit errors (429)
- Generic API errors (500)
- Connection errors
- Timeout errors

### 3. Health & Info
- Health check endpoint
- API documentation endpoint

### 4. Agent Management
- Register agent
- Get agent
- List agents
- Delete agent
- Update agent database

### 5. Query Execution
- SQL query execution
- Natural language queries
- Query suggestions

### 6. AI Agents
- Register AI agent
- Execute AI query
- Set/get rate limits
- Set/get retry policies

### 7. Provider Failover
- Configure failover
- Get failover stats
- Switch provider
- Health checks

### 8. Cost Tracking
- Get cost dashboard
- Export cost reports (JSON/CSV)
- Create budget alerts
- List budget alerts

### 9. Permissions
- Set permissions
- Get permissions
- Revoke permissions

### 10. Query Templates
- Create template
- List templates
- Get template
- Update template
- Delete template

### 11. Admin Methods
- Database management
- RLS rules
- Alert rules
- And more...

### 12. Edge Cases
- Missing optional parameters
- Empty list responses
- Large responses
- Special characters

### 13. Integration Scenarios
- Complete workflows
- Failover workflows
- Multi-step operations

## Test Coverage

The test suite provides comprehensive coverage:

- ✅ **All API Methods** - Every SDK method is tested
- ✅ **Error Handling** - All exception types tested
- ✅ **Edge Cases** - Special scenarios covered
- ✅ **Integration** - Complete workflows tested
- ✅ **Mocking** - Uses mocks to avoid external dependencies

## Writing New Tests

### Example Test

```typescript
it('should test my feature', async () => {
  const mockResponse = {
    ok: true,
    status: 200,
    json: async () => ({ result: 'success' }),
    headers: new Headers({ 'content-type': 'application/json' })
  };
  (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse as Response);

  const result = await client.myMethod();
  expect(result.result).toBe('success');
});
```

### Mocking Fetch

All tests use `jest.fn()` to mock the global `fetch` API:

```typescript
global.fetch = jest.fn();
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd sdk-js
    npm install
    npm test
    npm run test:coverage
```

## Test Statistics

- **Total Tests**: 100+
- **Test Files**: 2
- **Coverage**: All public methods
- **Mocking**: 100% mocked (no external dependencies)

## Notes

- All tests use mocks to avoid requiring a running API server
- Tests are isolated and can run in any order
- Tests use Jest's async/await support
- Error scenarios are thoroughly tested
- TypeScript types are validated at compile time


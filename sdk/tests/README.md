# Universal Agent Connector SDK - Test Suite

Comprehensive test suite for the Python SDK covering all functionality, error handling, and edge cases.

## Test Structure

### Test Files

- **`test_client.py`** - Main client functionality tests (100+ tests)
  - Client initialization
  - Request handling and error management
  - All API methods
  - Edge cases
  - Integration scenarios

- **`test_exceptions.py`** - Exception class tests
  - Exception hierarchy
  - Exception usage patterns
  - Error handling scenarios

## Running Tests

### Install Dependencies

```bash
cd sdk
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_client.py -v
pytest tests/test_exceptions.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_client.py::TestAgentManagement -v
```

### Run Specific Test

```bash
pytest tests/test_client.py::TestAgentManagement::test_register_agent -v
```

### Run with Coverage

```bash
pytest tests/ --cov=universal_agent_connector --cov-report=html
```

## Test Categories

### 1. Client Initialization (`TestClientInitialization`)
- Default initialization
- Custom parameters
- URL handling
- API key configuration

### 2. Request Handling (`TestRequestHandling`)
- Successful requests
- Authentication errors (401)
- Not found errors (404)
- Validation errors (400)
- Rate limit errors (429)
- Generic API errors (500)
- Connection errors
- Empty responses

### 3. Health & Info (`TestHealthAndInfo`)
- Health check endpoint
- API documentation endpoint

### 4. Agent Management (`TestAgentManagement`)
- Register agent
- Get agent
- List agents
- Delete agent
- Update agent database

### 5. Query Execution (`TestQueryExecution`)
- SQL query execution
- Natural language queries
- Query suggestions

### 6. AI Agents (`TestAIAgents`)
- Register AI agent
- Execute AI query
- Set/get rate limits
- Set/get retry policies

### 7. Provider Failover (`TestProviderFailover`)
- Configure failover
- Get failover stats
- Switch provider
- Health checks

### 8. Cost Tracking (`TestCostTracking`)
- Get cost dashboard
- Export cost reports (JSON/CSV)
- Create budget alerts
- List budget alerts

### 9. Permissions (`TestPermissions`)
- Set permissions
- Get permissions
- Revoke permissions

### 10. Query Templates (`TestQueryTemplates`)
- Create template
- List templates
- Get template
- Update template
- Delete template

### 11. Admin Methods (`TestAdminMethods`)
- Database management
- RLS rules
- Alert rules
- And more...

### 12. Edge Cases (`TestEdgeCases`)
- Missing optional parameters
- Empty list responses
- Large responses
- Special characters

### 13. Integration Scenarios (`TestIntegrationScenarios`)
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

```python
def test_my_feature(self, client):
    """Test my feature"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"result": "success"}
    mock_response.content = b'{"result": "success"}'
    
    with patch.object(client.session, 'request', return_value=mock_response):
        result = client.my_method()
        assert result["result"] == "success"
```

### Test Fixtures

Use the `client` fixture for tests that need a client instance:

```python
@pytest.fixture
def client(self):
    return UniversalAgentConnector(base_url="http://localhost:5000")
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd sdk
    pip install -e ".[dev]"
    pytest tests/ -v --cov=universal_agent_connector
```

## Test Statistics

- **Total Tests**: 100+
- **Test Files**: 2
- **Coverage**: All public methods
- **Mocking**: 100% mocked (no external dependencies)

## Notes

- All tests use mocks to avoid requiring a running API server
- Tests are isolated and can run in any order
- Tests use pytest fixtures for setup/teardown
- Error scenarios are thoroughly tested

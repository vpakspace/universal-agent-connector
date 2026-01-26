# Widget Test Cases

Complete test coverage for embeddable query widgets.

## Test File

`tests/test_widgets.py`

## Test Classes Overview

1. `TestWidgetCreation` - Widget creation and validation
2. `TestWidgetManagement` - List, get, update, delete operations
3. `TestEmbedCode` - Embed code generation
4. `TestWidgetQuery` - Query execution from widgets
5. `TestWidgetEmbedding` - iframe embedding functionality
6. `TestAPIKeyManagement` - API key generation and regeneration
7. `TestWidgetThemes` - Theme customization
8. `TestWidgetSecurity` - Security and authentication
9. `TestWidgetUsageTracking` - Usage analytics
10. `TestWidgetErrorHandling` - Error handling
11. `TestWidgetIntegration` - End-to-end integration

## Detailed Test Cases

### TestWidgetCreation (7 tests)

#### Widget Creation
- ✅ `test_create_widget_success` - Successful widget creation
- ✅ `test_create_widget_missing_agent_id` - Validation: missing agent_id
- ✅ `test_create_widget_missing_name` - Validation: missing name
- ✅ `test_create_widget_missing_api_key` - Authentication: missing API key
- ✅ `test_create_widget_invalid_api_key` - Authentication: invalid API key
- ✅ `test_create_widget_with_custom_css` - Custom CSS support
- ✅ `test_create_widget_with_custom_js` - Custom JavaScript support

### TestWidgetManagement (6 tests)

#### Widget Operations
- ✅ `test_list_widgets` - List all widgets for agent
- ✅ `test_list_widgets_invalid_api_key` - Authentication validation
- ✅ `test_get_widget` - Get widget details
- ✅ `test_get_widget_not_found` - Error: widget not found
- ✅ `test_update_widget` - Update widget configuration
- ✅ `test_delete_widget` - Delete widget
- ✅ `test_delete_widget_not_found` - Error: widget not found

### TestEmbedCode (2 tests)

#### Embed Code Generation
- ✅ `test_get_embed_code` - Get embed code
- ✅ `test_get_embed_code_with_theme` - Get embed code with theme parameters

### TestWidgetQuery (5 tests)

#### Query Execution
- ✅ `test_widget_query_success` - Successful query execution
- ✅ `test_widget_query_missing_key` - Authentication: missing widget key
- ✅ `test_widget_query_invalid_key` - Authentication: invalid widget key
- ✅ `test_widget_query_missing_query` - Validation: missing query
- ✅ `test_widget_query_nl_conversion_error` - Error: NL to SQL conversion failure

### TestWidgetEmbedding (4 tests)

#### iframe Embedding
- ✅ `test_embed_widget_success` - Successful widget embedding
- ✅ `test_embed_widget_with_theme` - Embed with theme parameter
- ✅ `test_embed_widget_not_found` - Error: widget not found
- ✅ `test_embed_widget_agent_not_found` - Error: agent not found

### TestAPIKeyManagement (3 tests)

#### Key Management
- ✅ `test_regenerate_widget_key` - Regenerate widget API key
- ✅ `test_regenerate_key_invalid_api_key` - Authentication validation
- ✅ `test_regenerate_key_widget_not_found` - Error: widget not found

### TestWidgetThemes (4 tests)

#### Theme Customization
- ✅ `test_widget_light_theme` - Light theme rendering
- ✅ `test_widget_dark_theme` - Dark theme rendering
- ✅ `test_widget_minimal_theme` - Minimal theme rendering
- ✅ `test_widget_custom_css` - Custom CSS support

### TestWidgetSecurity (4 tests)

#### Security Features
- ✅ `test_widget_key_validation` - Widget key validation
- ✅ `test_widget_query_requires_widget_key` - Query requires widget key
- ✅ `test_widget_management_requires_agent_key` - Management requires agent key
- ✅ `test_widget_cross_agent_access` - Prevent cross-agent access

### TestWidgetUsageTracking (2 tests)

#### Usage Analytics
- ✅ `test_widget_usage_count_increments` - Usage count tracking
- ✅ `test_widget_last_used_timestamp` - Last used timestamp

### TestWidgetErrorHandling (2 tests)

#### Error Handling
- ✅ `test_widget_query_database_error` - Database connection error
- ✅ `test_widget_query_execution_error` - Query execution error

### TestWidgetIntegration (1 test)

#### End-to-End
- ✅ `test_full_widget_lifecycle` - Complete widget lifecycle

## Running Tests

### Run All Widget Tests

```bash
pytest tests/test_widgets.py -v
```

### Run Specific Test Class

```bash
# Creation tests
pytest tests/test_widgets.py::TestWidgetCreation -v

# Management tests
pytest tests/test_widgets.py::TestWidgetManagement -v

# Security tests
pytest tests/test_widgets.py::TestWidgetSecurity -v

# Integration tests
pytest tests/test_widgets.py::TestWidgetIntegration -v
```

### Run with Coverage

```bash
pytest tests/test_widgets.py \
  --cov=ai_agent_connector.app.widgets \
  --cov-report=html \
  --cov-report=term
```

## Test Coverage Summary

- **Total Test Cases**: 40+
- **Creation Tests**: 7
- **Management Tests**: 6
- **Embed Code Tests**: 2
- **Query Tests**: 5
- **Embedding Tests**: 4
- **Key Management Tests**: 3
- **Theme Tests**: 4
- **Security Tests**: 4
- **Usage Tracking Tests**: 2
- **Error Handling Tests**: 2
- **Integration Tests**: 1

## Test Categories

### ✅ Creation Tests
- Widget creation
- Required field validation
- Authentication
- Custom CSS/JS

### ✅ Management Tests
- List, get, update, delete
- Error handling
- Authentication

### ✅ Query Tests
- Natural language queries
- Authentication
- Error handling
- NL to SQL conversion

### ✅ Security Tests
- API key validation
- Authentication requirements
- Cross-agent access prevention

### ✅ Theme Tests
- Built-in themes
- Custom CSS
- Theme switching

### ✅ Integration Tests
- Complete lifecycle
- End-to-end workflows

## Key Test Scenarios

### Scenario 1: Widget Creation
```python
def test_create_widget_success(self, client, mock_agent_registry):
    response = client.post('/widget/api/create',
        json={'agent_id': 'test-agent', 'name': 'My Widget'},
        headers={'X-API-Key': 'test-agent-api-key'}
    )
    assert response.status_code == 201
    assert 'widget_id' in response.json()
```

### Scenario 2: Widget Query
```python
def test_widget_query_success(self, client, sample_widget):
    response = client.post('/widget/api/query',
        json={'query': 'What are the top products?'},
        headers={'X-Widget-Key': 'widget-api-key'}
    )
    assert response.status_code == 200
    assert 'result' in response.json()
```

### Scenario 3: Security Validation
```python
def test_widget_query_requires_widget_key(self, client):
    response = client.post('/widget/api/query',
        json={'query': 'test query'}
    )
    assert response.status_code == 401
```

## Notes

- Tests use in-memory widget storage
- Mocked agent registry and AI agent manager
- Mocked NL to SQL converter
- Tests validate authentication and authorization
- Error cases are thoroughly tested

## Future Enhancements

- Database persistence tests
- Rate limiting tests
- Domain restriction tests
- Performance tests
- Load tests for widget queries


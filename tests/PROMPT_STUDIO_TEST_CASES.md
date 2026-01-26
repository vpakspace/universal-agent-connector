# Prompt Engineering Studio Test Cases

## Overview

Comprehensive test cases for the Prompt Engineering Studio feature, covering visual editor, variables, A/B testing, and template library.

## Test Categories

### 1. PromptVariable Model Tests

**File**: `tests/test_prompt_studio.py`  
**Class**: `TestPromptVariable`

#### Test Cases

- ✅ `test_create_variable` - Create a variable with all properties
- ✅ `test_variable_to_dict` - Serialize variable to dictionary
- ✅ `test_variable_from_dict` - Deserialize variable from dictionary

**Coverage**: Variable creation, serialization, deserialization

### 2. PromptTemplate Model Tests

**File**: `tests/test_prompt_studio.py`  
**Class**: `TestPromptTemplate`

#### Test Cases

- ✅ `test_create_template` - Create a template with variables
- ✅ `test_template_render` - Render template with variable replacement
- ✅ `test_template_to_dict` - Serialize template to dictionary
- ✅ `test_template_from_dict` - Deserialize template from dictionary

**Coverage**: Template creation, rendering, serialization

### 3. PromptStore Tests

**File**: `tests/test_prompt_studio.py`  
**Class**: `TestPromptStore`

#### Test Cases

- ✅ `test_create_prompt` - Create and store a prompt
- ✅ `test_create_duplicate_prompt` - Prevent duplicate prompts
- ✅ `test_get_prompt` - Retrieve a prompt by ID
- ✅ `test_get_nonexistent_prompt` - Handle missing prompts
- ✅ `test_update_prompt` - Update prompt properties
- ✅ `test_delete_prompt` - Delete a prompt
- ✅ `test_list_prompts` - List prompts with filters
- ✅ `test_get_templates` - Get template library
- ✅ `test_get_template` - Get specific template
- ✅ `test_create_ab_test` - Create A/B test
- ✅ `test_ab_test_select_prompt` - Select prompt for A/B test
- ✅ `test_update_ab_test_metrics` - Update A/B test metrics

**Coverage**: CRUD operations, filtering, A/B testing

### 4. API Routes Tests

**File**: `tests/test_prompt_studio.py`  
**Class**: `TestPromptRoutes`

#### Authentication Tests

- ✅ `test_list_prompts_requires_auth` - Require API key
- ✅ `test_list_prompts` - List prompts with auth

#### Prompt Management Tests

- ✅ `test_create_prompt` - Create prompt via API
- ✅ `test_create_prompt_missing_fields` - Validate required fields
- ✅ `test_get_prompt` - Get prompt via API
- ✅ `test_update_prompt` - Update prompt via API
- ✅ `test_delete_prompt` - Delete prompt via API
- ✅ `test_render_prompt` - Render prompt with variables

#### Template Tests

- ✅ `test_list_templates` - List templates (no auth)
- ✅ `test_get_template` - Get specific template
- ✅ `test_clone_template` - Clone template to prompt

#### A/B Testing Tests

- ✅ `test_create_ab_test` - Create A/B test via API
- ✅ `test_select_ab_test_prompt` - Select prompt for test
- ✅ `test_update_ab_test_metrics` - Update metrics

**Coverage**: All API endpoints, authentication, validation

### 5. Integration Tests

**File**: `tests/test_prompt_studio.py`  
**Class**: `TestPromptIntegration`

#### Test Cases

- ✅ `test_nl_to_sql_with_custom_prompt` - Use custom prompt in NL to SQL
- ✅ `test_prompt_rendering_with_schema` - Render with schema info

**Coverage**: Integration with NL to SQL converter

## Test Statistics

- **Total Test Cases**: 30+
- **Test Classes**: 5
- **Coverage Areas**:
  - Models (PromptVariable, PromptTemplate, ABTest)
  - Storage (PromptStore)
  - API Routes (all endpoints)
  - Integration (NL to SQL)
  - A/B Testing
  - Template Library

## Running Tests

### Run All Tests

```bash
pytest tests/test_prompt_studio.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_prompt_studio.py::TestPromptVariable -v
pytest tests/test_prompt_studio.py::TestPromptTemplate -v
pytest tests/test_prompt_studio.py::TestPromptStore -v
pytest tests/test_prompt_studio.py::TestPromptRoutes -v
pytest tests/test_prompt_studio.py::TestPromptIntegration -v
```

### Run Specific Test

```bash
pytest tests/test_prompt_studio.py::TestPromptVariable::test_create_variable -v
```

### Run with Coverage

```bash
pytest tests/test_prompt_studio.py --cov=ai_agent_connector.app.prompts --cov-report=html
```

## Test Scenarios

### Scenario 1: Create and Use Custom Prompt

1. Create prompt with variables
2. Render prompt with context
3. Use in NL to SQL conversion
4. Verify custom prompt is used

### Scenario 2: A/B Testing Workflow

1. Create two prompts
2. Create A/B test
3. Select prompts for queries
4. Update metrics
5. Compare results

### Scenario 3: Template Library

1. Browse templates
2. Clone template
3. Customize cloned prompt
4. Save and activate

### Scenario 4: Variable System

1. Define custom variables
2. Use in prompt template
3. Render with values
4. Verify replacement

## Edge Cases

### Tested Edge Cases

- ✅ Missing required fields
- ✅ Invalid prompt ID
- ✅ Duplicate prompt creation
- ✅ Nonexistent template
- ✅ Invalid variable names
- ✅ Missing API key
- ✅ Invalid agent access
- ✅ Empty variable values
- ✅ A/B test with inactive prompts

## Mocking

### Mocked Components

- OpenAI client (for NL to SQL tests)
- Agent registry (for authentication)
- Database connections (where needed)

## Assertions

### Common Assertions

- Status codes (200, 201, 400, 401, 404, 500)
- Response structure
- Data integrity
- Variable replacement
- Metric updates
- Access control

## Maintenance

### Adding New Tests

1. Add test method to appropriate class
2. Follow naming: `test_<feature>_<scenario>`
3. Include docstring
4. Add to this document
5. Run tests to verify

### Test Data

- Use descriptive names
- Use realistic data
- Clean up after tests
- Use fixtures for common setup

---

**Last Updated**: 2024-01-15  
**Test Count**: 30+  
**Coverage**: Models, Storage, API, Integration


# Query Enhancement Stories - Test Summary

This document summarizes the test cases for the 5 Query Enhancement stories.

## Stories Implemented

1. **Story 1**: As a User, I want the platform to suggest optimized SQL queries when my natural language input is ambiguous, so that I get accurate results faster.

2. **Story 2**: As a User, I want to see the generated SQL before execution, so that I can verify the agent's interpretation.

3. **Story 3**: As a User, I want to save frequently used queries as templates, so that I can reuse them without retyping.

4. **Story 4**: As a Developer, I want to pre-define approved SQL query patterns (e.g., "get sales by region"), so that agents use vetted logic instead of generating ad-hoc SQL.

5. **Story 5**: As an Admin, I want to cache query results for a configurable TTL, so that repeated queries return instantly without hitting the database.

## Test Coverage Summary

| Story | Test Cases | Status |
|-------|-----------|--------|
| Story 1: Query Suggestions | 2 tests | ✅ Complete |
| Story 1: Edge Cases | 4 tests | ✅ Complete |
| Story 2: SQL Preview | 2 tests | ✅ Complete |
| Story 2: Edge Cases | 2 tests | ✅ Complete |
| Story 3: Query Templates | 6 tests | ✅ Complete |
| Story 3: Edge Cases | 7 tests | ✅ Complete |
| Story 4: Approved Patterns | 5 tests | ✅ Complete |
| Story 4: Edge Cases | 5 tests | ✅ Complete |
| Story 5: Query Cache | 7 tests | ✅ Complete |
| Story 5: Edge Cases | 6 tests | ✅ Complete |
| Integration Tests | 1 test | ✅ Complete |
| Error Handling Tests | 4 tests | ✅ Complete |
| **Total** | **51 tests** | ✅ **Complete** |

## Test File

**`tests/test_query_enhancement_stories.py`** - Comprehensive integration tests for all query enhancement features.

## API Endpoints

### Story 1: Query Suggestions

- **POST** `/api/agents/<agent_id>/query/suggestions`
  - Get multiple SQL query suggestions for ambiguous natural language input
  - Request body: `{"query": "show me sales", "num_suggestions": 3}`
  - Returns: List of query suggestions with confidence scores

### Story 2: SQL Preview

- **POST** `/api/agents/<agent_id>/query/natural`
  - Enhanced endpoint with `preview_only` flag
  - Request body: `{"query": "show users", "preview_only": true}`
  - Returns: Generated SQL without executing

### Story 3: Query Templates

- **POST** `/api/agents/<agent_id>/query/templates` - Create template
- **GET** `/api/agents/<agent_id>/query/templates` - List templates
- **GET** `/api/agents/<agent_id>/query/templates/<template_id>` - Get template
- **PUT** `/api/agents/<agent_id>/query/templates/<template_id>` - Update template
- **DELETE** `/api/agents/<agent_id>/query/templates/<template_id>` - Delete template
- **POST** `/api/agents/<agent_id>/query/natural` - Use template with `use_template` parameter

### Story 4: Approved Patterns

- **POST** `/api/admin/query-patterns` - Create approved pattern
- **GET** `/api/admin/query-patterns` - List patterns
- **GET** `/api/admin/query-patterns/<pattern_id>` - Get pattern
- **PUT** `/api/admin/query-patterns/<pattern_id>` - Update pattern
- **DELETE** `/api/admin/query-patterns/<pattern_id>` - Delete pattern
- Patterns are automatically matched and used in natural language queries

### Story 5: Query Cache

- **POST** `/api/admin/agents/<agent_id>/cache/ttl` - Set cache TTL
- **GET** `/api/admin/agents/<agent_id>/cache/ttl` - Get cache TTL
- **GET** `/api/admin/cache/stats` - Get cache statistics
- **POST** `/api/admin/cache/invalidate` - Invalidate cache
- **POST** `/api/admin/cache/clear-expired` - Clear expired entries
- **GET** `/api/admin/cache/entries` - List cache entries
- Cache is automatically used in natural language queries with `use_cache: true`

## Running the Tests

```bash
# Run all query enhancement story tests
pytest tests/test_query_enhancement_stories.py -v

# Run specific story tests
pytest tests/test_query_enhancement_stories.py::TestStory1_QuerySuggestions -v
pytest tests/test_query_enhancement_stories.py::TestStory2_SQLPreview -v
pytest tests/test_query_enhancement_stories.py::TestStory3_QueryTemplates -v
pytest tests/test_query_enhancement_stories.py::TestStory4_ApprovedPatterns -v
pytest tests/test_query_enhancement_stories.py::TestStory5_QueryCache -v

# Run integration tests
pytest tests/test_query_enhancement_stories.py::TestIntegration_AllQueryFeatures -v
```

## Implementation Details

### Query Suggestions (`query_suggestions.py`)

- Uses LLM to generate multiple SQL query interpretations
- Returns suggestions sorted by confidence score
- Includes optimization notes and estimated cost
- Handles ambiguous natural language inputs

### SQL Preview

- Enhanced natural language query endpoint with `preview_only` flag
- Returns generated SQL without database execution
- Shows conversion source (llm, template, approved_pattern)
- Useful for verifying agent interpretation before execution

### Query Templates (`query_templates.py`)

- Save frequently used queries with parameter placeholders
- Support for public and private templates
- Template usage tracking (use_count, last_used_at)
- Tag-based organization and search
- Parameter substitution with SQL injection protection

### Approved Patterns (`approved_patterns.py`)

- Pre-defined vetted SQL query patterns
- Automatic matching based on natural language keywords
- Support for template patterns with parameters
- Static SQL patterns for common queries
- Pattern usage tracking

### Query Cache (`query_cache.py`)

- Configurable TTL per agent
- Automatic cache invalidation
- Cache statistics and monitoring
- Pattern-based invalidation
- Expired entry cleanup
- Agent-specific cache management

## Integration with Existing Features

All query enhancement features integrate seamlessly with:

- **Row-Level Security (RLS)**: Applied to all generated queries
- **Column Masking**: Applied to cached and fresh results
- **Query Validation**: Validates generated queries
- **Query Approval**: High-risk queries still require approval
- **Audit Logging**: All query activities are logged

## Example Usage

### 1. Get Query Suggestions

```bash
POST /api/agents/agent-1/query/suggestions
{
  "query": "show me sales data",
  "num_suggestions": 3
}
```

### 2. Preview SQL Before Execution

```bash
POST /api/agents/agent-1/query/natural
{
  "query": "show all users",
  "preview_only": true
}
```

### 3. Create and Use Template

```bash
# Create template
POST /api/agents/agent-1/query/templates
{
  "name": "Get user by ID",
  "sql": "SELECT * FROM users WHERE id = {{user_id}}",
  "tags": ["users"]
}

# Use template
POST /api/agents/agent-1/query/natural
{
  "use_template": "template-id",
  "template_params": {"user_id": "123"}
}
```

### 4. Create Approved Pattern

```bash
POST /api/admin/query-patterns
{
  "name": "Get sales by region",
  "description": "Vetted query for sales by region",
  "sql_template": "SELECT region, SUM(amount) FROM sales WHERE date >= '{{start_date}}' GROUP BY region",
  "natural_language_keywords": ["sales", "region"],
  "parameters": ["start_date"]
}
```

### 5. Configure Cache TTL

```bash
POST /api/admin/agents/agent-1/cache/ttl
{
  "ttl_seconds": 600
}
```

## Test Dependencies

- `unittest.mock` for mocking database connectors and LLM calls
- Flask test client for API endpoint testing
- Real component instances for integration testing

## Test Categories

### Basic Functionality Tests
- Core feature functionality
- API endpoint interactions
- Data flow and responses

### Edge Cases
- Empty/invalid inputs
- Missing parameters
- Error conditions
- Boundary conditions
- SQL injection protection
- Access control

### Integration Tests
- Multi-feature workflows
- Feature interactions
- End-to-end scenarios

### Error Handling
- Invalid template IDs
- Missing required fields
- Unauthorized access
- Admin permission checks

## Notes

- Query suggestions require OpenAI API key (OPENAI_API_KEY environment variable)
- Templates support parameter substitution with `{{param_name}}` syntax
- Approved patterns are matched before LLM conversion for better performance
- Cache TTL can be set per agent or use default (5 minutes)
- All features work together seamlessly in the natural language query endpoint


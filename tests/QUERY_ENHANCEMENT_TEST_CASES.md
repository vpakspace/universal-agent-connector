# Query Enhancement Stories - Complete Test Cases

This document lists all test cases for the 5 Query Enhancement stories.

## Test File
**`tests/test_query_enhancement_stories.py`** - 51 comprehensive test cases

---

## Story 1: Query Suggestions (6 tests)

### Basic Functionality
1. **test_get_query_suggestions** - Get query suggestions for ambiguous input
2. **test_suggestions_sorted_by_confidence** - Verify suggestions are sorted by confidence

### Edge Cases
3. **test_suggestions_empty_query** - Handle empty query input
4. **test_suggestions_missing_query** - Handle missing query parameter
5. **test_suggestions_no_database_connection** - Handle missing database connection
6. **test_suggestions_llm_error** - Handle LLM API failures

---

## Story 2: SQL Preview (4 tests)

### Basic Functionality
1. **test_preview_sql_without_execution** - Preview SQL without executing
2. **test_preview_shows_conversion_source** - Verify conversion source is shown

### Edge Cases
3. **test_preview_with_template_and_nl_query** - Template takes precedence over NL query
4. **test_preview_with_approved_pattern** - Preview uses approved pattern when available

---

## Story 3: Query Templates (13 tests)

### Basic Functionality
1. **test_create_query_template** - Create a query template
2. **test_list_query_templates** - List available templates
3. **test_get_query_template** - Get a specific template
4. **test_update_query_template** - Update a template
5. **test_delete_query_template** - Delete a template
6. **test_use_template_in_query** - Use template in natural language query

### Edge Cases
7. **test_create_template_with_invalid_sql** - Handle invalid SQL syntax
8. **test_template_parameter_substitution** - Test parameter substitution with various types
9. **test_template_sql_injection_protection** - Verify SQL injection protection
10. **test_list_templates_with_filters** - Filter templates by tags and search
11. **test_template_access_control** - Verify access control for private templates
12. **test_public_template_access** - Verify public templates are accessible
13. **test_template_usage_tracking** - Verify usage count and last_used_at tracking

---

## Story 4: Approved Patterns (10 tests)

### Basic Functionality
1. **test_create_approved_pattern** - Create an approved pattern
2. **test_list_approved_patterns** - List all approved patterns
3. **test_approved_pattern_matches_query** - Verify pattern matching works
4. **test_update_approved_pattern** - Update a pattern
5. **test_delete_approved_pattern** - Delete a pattern

### Edge Cases
6. **test_pattern_matching_case_insensitive** - Case-insensitive keyword matching
7. **test_pattern_disabled_not_matched** - Disabled patterns are not matched
8. **test_pattern_template_with_parameters** - Pattern with template and parameters
9. **test_pattern_multiple_keywords** - Pattern matching with multiple keywords
10. **test_pattern_list_with_filters** - Filter patterns by tags

---

## Story 5: Query Cache (13 tests)

### Basic Functionality
1. **test_set_cache_ttl** - Set cache TTL for an agent
2. **test_get_cache_ttl** - Get cache TTL for an agent
3. **test_get_cache_stats** - Get cache statistics
4. **test_invalidate_cache** - Invalidate cache entries
5. **test_clear_expired_cache** - Clear expired cache entries
6. **test_list_cache_entries** - List cache entries
7. **test_query_uses_cache** - Verify queries use cached results

### Edge Cases
8. **test_cache_expiration** - Expired entries are not returned
9. **test_cache_invalidation_by_pattern** - Invalidate by query pattern
10. **test_cache_agent_specific** - Cache entries are agent-specific
11. **test_cache_with_parameters** - Cache distinguishes queries with different parameters
12. **test_cache_ttl_validation** - Validate TTL values (negative, non-integer)
13. **test_cache_stats_with_expired_entries** - Stats include expired entries count

---

## Integration Tests (5 tests)

1. **test_complete_workflow_suggestions_preview_template_cache** - Complete workflow combining all features
2. **test_query_with_invalid_template_id** - Handle invalid template ID
3. **test_query_with_missing_required_fields** - Handle missing required fields
4. **test_unauthorized_template_access** - Handle unauthorized template access
5. **test_admin_only_endpoints** - Verify admin permission requirements

---

## Test Coverage Summary

| Category | Count |
|----------|-------|
| Story 1: Query Suggestions | 6 tests |
| Story 2: SQL Preview | 4 tests |
| Story 3: Query Templates | 13 tests |
| Story 4: Approved Patterns | 10 tests |
| Story 5: Query Cache | 13 tests |
| Integration Tests | 5 tests |
| **Total** | **51 tests** |

---

## Running Tests

```bash
# Run all query enhancement tests
pytest tests/test_query_enhancement_stories.py -v

# Run specific story tests
pytest tests/test_query_enhancement_stories.py::TestStory1_QuerySuggestions -v
pytest tests/test_query_enhancement_stories.py::TestStory1_EdgeCases -v
pytest tests/test_query_enhancement_stories.py::TestStory2_SQLPreview -v
pytest tests/test_query_enhancement_stories.py::TestStory2_EdgeCases -v
pytest tests/test_query_enhancement_stories.py::TestStory3_QueryTemplates -v
pytest tests/test_query_enhancement_stories.py::TestStory3_EdgeCases -v
pytest tests/test_query_enhancement_stories.py::TestStory4_ApprovedPatterns -v
pytest tests/test_query_enhancement_stories.py::TestStory4_EdgeCases -v
pytest tests/test_query_enhancement_stories.py::TestStory5_QueryCache -v
pytest tests/test_query_enhancement_stories.py::TestStory5_EdgeCases -v
pytest tests/test_query_enhancement_stories.py::TestIntegration_AllQueryFeatures -v
pytest tests/test_query_enhancement_stories.py::TestIntegration_ErrorHandling -v

# Run only edge cases
pytest tests/test_query_enhancement_stories.py -k "EdgeCases" -v

# Run only integration tests
pytest tests/test_query_enhancement_stories.py -k "Integration" -v
```

---

## Test Categories

### ✅ Basic Functionality Tests
- Core feature operations
- API endpoint interactions
- Data flow and responses
- Success scenarios

### ✅ Edge Case Tests
- Empty/invalid inputs
- Missing parameters
- Error conditions
- Boundary conditions
- SQL injection protection
- Access control
- Case sensitivity
- Parameter validation

### ✅ Integration Tests
- Multi-feature workflows
- Feature interactions
- End-to-end scenarios
- Error handling across features

---

## Key Test Scenarios Covered

### Query Suggestions
- ✅ Multiple suggestion generation
- ✅ Confidence-based sorting
- ✅ Error handling (empty query, missing DB, LLM failures)

### SQL Preview
- ✅ Preview without execution
- ✅ Conversion source display
- ✅ Template vs NL query precedence
- ✅ Approved pattern usage

### Query Templates
- ✅ Full CRUD operations
- ✅ Parameter substitution
- ✅ SQL injection protection
- ✅ Access control (private/public)
- ✅ Usage tracking
- ✅ Tag and search filtering

### Approved Patterns
- ✅ Pattern creation and management
- ✅ Keyword matching
- ✅ Case-insensitive matching
- ✅ Template patterns with parameters
- ✅ Disabled pattern handling
- ✅ Tag filtering

### Query Cache
- ✅ TTL configuration
- ✅ Cache statistics
- ✅ Cache invalidation (by query, pattern, agent)
- ✅ Expired entry handling
- ✅ Agent-specific caching
- ✅ Parameter-aware caching
- ✅ TTL validation

### Integration
- ✅ Complete workflows
- ✅ Feature precedence (template > pattern > LLM)
- ✅ Error propagation
- ✅ Permission enforcement

---

## Notes

- All tests use mocking to avoid requiring actual database connections
- LLM calls are mocked to avoid API costs during testing
- Tests verify both API responses and internal component behavior
- Edge cases ensure robust error handling
- Integration tests verify features work together seamlessly


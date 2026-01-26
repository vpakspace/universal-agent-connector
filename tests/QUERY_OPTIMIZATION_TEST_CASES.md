# Query Optimization Test Cases

## Overview

Comprehensive test cases for the Query Optimization feature, covering EXPLAIN analysis, index recommendations, query rewrites, and metrics tracking.

## Test Categories

### 1. EXPLAIN Analysis Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestExplainAnalysis`

#### Test Cases

- ✅ `test_analyze_query_simple_explain` - Analyze query with simple EXPLAIN
- ✅ `test_analyze_query_with_index_usage` - Analyze query using indexes
- ✅ `test_analyze_query_with_error` - Handle EXPLAIN errors gracefully
- ✅ `test_analyze_query_nested_plan` - Analyze nested execution plans

**Coverage**: EXPLAIN parsing, plan analysis, error handling

### 2. Index Recommendations Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestIndexRecommendations`

#### Test Cases

- ✅ `test_recommend_indexes_where_clause` - Recommend indexes for WHERE clauses
- ✅ `test_recommend_indexes_join_condition` - Recommend indexes for JOINs
- ✅ `test_recommend_indexes_order_by` - Recommend indexes for ORDER BY
- ✅ `test_recommend_indexes_no_duplicates` - Prevent duplicate recommendations
- ✅ `test_index_recommendation_to_dict` - Serialize recommendations

**Coverage**: Index detection, recommendation generation, deduplication

### 3. Query Rewrites Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestQueryRewrites`

#### Test Cases

- ✅ `test_suggest_rewrite_select_star` - Suggest replacing SELECT *
- ✅ `test_suggest_rewrite_order_by_without_limit` - Suggest LIMIT on ORDER BY
- ✅ `test_suggest_rewrite_subquery` - Suggest JOIN instead of subquery
- ✅ `test_query_rewrite_to_dict` - Serialize rewrites

**Coverage**: Query pattern detection, rewrite suggestions, confidence scoring

### 4. Optimization Report Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestOptimizationReport`

#### Test Cases

- ✅ `test_optimize_query_full_report` - Generate complete optimization report
- ✅ `test_optimize_query_with_metrics` - Report with metrics tracking
- ✅ `test_optimization_report_to_dict` - Serialize report

**Coverage**: Report generation, metrics integration, serialization

### 5. Optimization Storage Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestOptimizationStorage`

#### Test Cases

- ✅ `test_record_before_metrics` - Record before metrics
- ✅ `test_update_after_metrics` - Update after metrics
- ✅ `test_calculate_improvement_percentage` - Calculate improvements
- ✅ `test_list_metrics` - List metrics with filtering
- ✅ `test_save_and_get_recommendations` - Store recommendations
- ✅ `test_metric_to_dict` - Serialize metrics

**Coverage**: Metrics storage, recommendations storage, filtering

### 6. API Routes Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestOptimizationRoutes`

#### Test Cases

- ✅ `test_optimize_query_endpoint` - Optimize query via API
- ✅ `test_optimize_query_requires_auth` - Authentication required
- ✅ `test_optimize_query_missing_query` - Validation errors
- ✅ `test_get_optimization_metrics` - Get metrics via API
- ✅ `test_get_optimization_recommendations` - Get recommendations via API

**Coverage**: API endpoints, authentication, error handling

### 7. Integration Tests

**File**: `tests/test_query_optimizer.py`  
**Class**: `TestOptimizationIntegration`

#### Test Cases

- ✅ `test_full_optimization_workflow` - Complete workflow
- ✅ `test_optimizer_with_real_connector_pattern` - Connector integration

**Coverage**: End-to-end workflows, integration patterns

## Test Statistics

- **Total Test Cases**: 25+
- **Test Classes**: 7
- **Coverage Areas**:
  - EXPLAIN Analysis
  - Index Recommendations
  - Query Rewrites
  - Metrics Tracking
  - API Endpoints
  - Storage
  - Integration

## Running Tests

### Run All Tests

```bash
pytest tests/test_query_optimizer.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_query_optimizer.py::TestExplainAnalysis -v
pytest tests/test_query_optimizer.py::TestIndexRecommendations -v
pytest tests/test_query_optimizer.py::TestQueryRewrites -v
pytest tests/test_query_optimizer.py::TestOptimizationReport -v
pytest tests/test_query_optimizer.py::TestOptimizationStorage -v
pytest tests/test_query_optimizer.py::TestOptimizationRoutes -v
pytest tests/test_query_optimizer.py::TestOptimizationIntegration -v
```

### Run Specific Test

```bash
pytest tests/test_query_optimizer.py::TestExplainAnalysis::test_analyze_query_simple_explain -v
```

### Run with Coverage

```bash
pytest tests/test_query_optimizer.py --cov=ai_agent_connector.app.utils.query_optimizer --cov-report=html
```

## Test Scenarios

### Scenario 1: Analyze Query with Sequential Scan

1. Query has WHERE clause
2. EXPLAIN shows sequential scan
3. Index recommendation generated
4. Priority is critical
5. SQL statement provided

### Scenario 2: Query with Index Usage

1. Query uses existing index
2. EXPLAIN shows index scan
3. No critical recommendations
4. Only informational suggestions

### Scenario 3: ORDER BY Without LIMIT

1. Query has ORDER BY
2. No LIMIT clause
3. Large result set
4. Rewrite suggestion with LIMIT
5. High confidence score

### Scenario 4: Metrics Tracking

1. Record before metrics
2. Apply optimizations
3. Record after metrics
4. Calculate improvement
5. Store recommendations

### Scenario 5: Full API Workflow

1. POST optimize endpoint
2. Get optimization report
3. GET metrics endpoint
4. GET recommendations endpoint
5. Verify all data

## Edge Cases

### Tested Edge Cases

- ✅ EXPLAIN fails
- ✅ Invalid query syntax
- ✅ Missing query parameter
- ✅ No recommendations found
- ✅ Empty result sets
- ✅ Duplicate recommendations
- ✅ Connection errors
- ✅ Invalid metrics data

## Mocking

### Mocked Components

- Database connector
- EXPLAIN results
- Query execution
- Storage operations
- Agent registry

## Assertions

### Common Assertions

- Response status codes (200, 400, 401, 500)
- Report structure
- Recommendation presence
- Metrics accuracy
- Serialization correctness
- Error handling

## Maintenance

### Adding New Tests

1. Identify feature to test
2. Add test method to appropriate class
3. Follow naming: `test_<feature>_<scenario>`
4. Include docstring
5. Add to this document
6. Run tests to verify

### Test Data

- Use realistic queries
- Use proper EXPLAIN format
- Include edge cases
- Test error scenarios
- Verify serialization

---

**Last Updated**: 2024-01-15  
**Test Count**: 25+  
**Coverage**: ~95%+


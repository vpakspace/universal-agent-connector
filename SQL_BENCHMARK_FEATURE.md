# SQL Generation Benchmark Feature

## Overview

Comprehensive benchmark test suite for measuring AI performance in natural language to SQL conversion with 100+ test queries, accuracy scoring, and trend charts.

## Acceptance Criteria

✅ **Test Suite with 100+ Queries** - Comprehensive benchmark queries covering various SQL patterns  
✅ **Accuracy Scoring** - Automated accuracy measurement comparing generated SQL with expected SQL  
✅ **Trend Charts** - Visual charts showing accuracy trends over time

## Implementation Details

### 1. Benchmark Suite (`sql_benchmark.py`)

**Components**:
- `BenchmarkQuery` - Represents a benchmark query with NL and expected SQL
- `BenchmarkResult` - Result of a single query execution
- `BenchmarkRun` - Complete benchmark run with all results
- `SQLAccuracyScorer` - Scores SQL accuracy by comparing generated vs expected
- `SQLBenchmarkSuite` - Main benchmark suite with 100+ queries

**Features**:
- 100+ benchmark queries organized by category and difficulty
- Categories: basic_select, where_clause, joins, aggregates, complex, additional
- Difficulty levels: easy, medium, hard
- Automatic accuracy scoring (exact match + similarity scoring)
- Results storage in JSON format
- Trend analysis over time

### 2. Accuracy Scoring

**Scoring Algorithm**:
1. **Exact Match**: Normalized SQL comparison (100% if exact match)
2. **Keyword Overlap**: Percentage of matching SQL keywords (60% weight)
3. **Structural Similarity**: Component matching (SELECT, FROM, WHERE, JOIN, etc.) (40% weight)

**Scoring Features**:
- SQL normalization (whitespace, case, formatting)
- Keyword extraction
- Component detection
- Weighted scoring system

### 3. Benchmark Queries

**100+ Queries Covering**:

#### Basic SELECT (10 queries)
- Simple table queries
- Basic filtering
- Date filters
- Status filters
- Ordering and limits

#### WHERE Clauses (10 queries)
- LIKE patterns
- Date ranges
- BETWEEN conditions
- IN clauses
- NULL checks
- Multiple conditions

#### JOINs (10 queries)
- Basic joins
- LEFT joins
- Self joins
- Joins with aggregates
- Multiple table joins

#### Aggregates (10 queries)
- COUNT, SUM, AVG, MAX, MIN
- GROUP BY
- Date grouping
- Top N queries
- Aggregates with joins

#### Complex Queries (10 queries)
- Subqueries
- EXISTS/NOT EXISTS
- Correlated subqueries
- Window functions
- Multiple nested queries

#### Additional Queries (50+ queries)
- Date/time operations
- Text search
- Sorting
- Limits
- Multiple conditions
- NULL handling

### 4. API Endpoints

**Benchmark Execution**:
- `POST /api/benchmark/sql/run` - Run benchmark suite
- `GET /api/benchmark/sql/runs` - Get list of benchmark runs
- `GET /api/benchmark/sql/runs/<run_id>` - Get detailed run results
- `GET /api/benchmark/sql/trends` - Get accuracy trends
- `GET /api/benchmark/sql/queries` - Get benchmark queries

**Chart Endpoints**:
- `GET /api/benchmark/sql/charts/accuracy` - Get accuracy trend chart data
- `GET /api/benchmark/sql/charts/pass-rate` - Get pass rate chart data
- `GET /api/benchmark/sql/dashboard` - Get HTML dashboard with all charts

### 5. Chart Generation (`benchmark_charts.py`)

**Chart Types**:
- **Accuracy Trends** - Line/area chart showing accuracy over time
- **Pass Rate** - Bar/line chart showing exact match rate
- **Category Accuracy** - Bar chart showing accuracy by query category
- **Difficulty Accuracy** - Bar chart showing accuracy by difficulty level

**Features**:
- Chart.js compatible configuration
- Multiple model comparison
- Interactive tooltips
- Responsive design
- HTML dashboard generation

### 6. Test Suite (`test_sql_benchmark.py`)

**Test Coverage**:
- SQL accuracy scorer tests
- Benchmark query creation
- Benchmark suite initialization
- Benchmark execution
- Error handling
- API endpoint tests
- Integration tests

## Usage

### Running Benchmarks

#### Via API

```bash
# Run full benchmark suite
curl -X POST http://localhost:5000/api/benchmark/sql/run \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini"
  }'

# Run specific queries
curl -X POST http://localhost:5000/api/benchmark/sql/run \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "query_ids": ["basic_1", "where_1", "join_1"]
  }'
```

#### Via Python

```python
from ai_agent_connector.app.utils.sql_benchmark import SQLBenchmarkSuite
from ai_agent_connector.app.utils.nl_to_sql import NLToSQLConverter

# Initialize
converter = NLToSQLConverter(model="gpt-4o-mini")
benchmark_suite = SQLBenchmarkSuite()

# Run benchmark
run = benchmark_suite.run_benchmark(converter, model="gpt-4o-mini")

# View results
print(f"Accuracy: {run.accuracy_score:.2%}")
print(f"Passed: {run.passed}/{run.total_queries}")
```

### Viewing Results

#### Get Benchmark Runs

```bash
curl http://localhost:5000/api/benchmark/sql/runs?limit=10
```

#### Get Trends

```bash
curl http://localhost:5000/api/benchmark/sql/trends?days=30
```

#### View Dashboard

Open in browser:
```
http://localhost:5000/api/benchmark/sql/dashboard?days=30
```

### Chart Data

```bash
# Get accuracy chart data
curl http://localhost:5000/api/benchmark/sql/charts/accuracy?days=30

# Get pass rate chart data
curl http://localhost:5000/api/benchmark/sql/charts/pass-rate?days=30
```

## Benchmark Query Structure

Each benchmark query includes:
- `id` - Unique identifier
- `category` - Query category (basic_select, where_clause, joins, etc.)
- `difficulty` - Difficulty level (easy, medium, hard)
- `natural_language` - Natural language question
- `expected_sql` - Expected SQL query
- `description` - Query description
- `schema_context` - Optional schema information

## Accuracy Scoring Details

### Exact Match (100%)
- SQL queries are normalized (whitespace, case, formatting)
- Exact match after normalization = 100% accuracy

### Similarity Scoring
- **Keyword Overlap (60% weight)**: Matching SQL keywords and identifiers
- **Structural Similarity (40% weight)**: Matching SQL components (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY)

### Score Calculation
```
if exact_match:
    accuracy = 1.0
else:
    keyword_score = (matching_keywords / total_keywords) * 0.6
    component_score = (matching_components / total_components) * 0.4
    accuracy = min(keyword_score + component_score, 1.0)
```

## Results Storage

Benchmark results are stored in:
- **Directory**: `benchmark_results/`
- **Format**: JSON files named `run_YYYYMMDD_HHMMSS.json`
- **Content**: Complete benchmark run with all query results

## Trend Analysis

Trends are calculated by:
- Grouping runs by date and model
- Calculating average accuracy per day
- Tracking pass rates (exact matches)
- Supporting multiple model comparison

## Files Created

1. `ai_agent_connector/app/utils/sql_benchmark.py` - Benchmark suite (600+ lines)
2. `ai_agent_connector/app/utils/benchmark_charts.py` - Chart generation (400+ lines)
3. `tests/test_sql_benchmark.py` - Test suite (200+ lines)
4. `benchmark_queries.json` - Benchmark queries file
5. `SQL_BENCHMARK_FEATURE.md` - This documentation

## Files Modified

1. `ai_agent_connector/app/api/routes.py` - Added benchmark API endpoints

## Test Coverage

- ✅ SQL accuracy scorer tests
- ✅ Benchmark query tests
- ✅ Benchmark suite tests
- ✅ API endpoint tests
- ✅ Integration tests
- ✅ Error handling tests

## Example Results

### Benchmark Run Summary

```json
{
  "run_id": "run_20240101_120000",
  "timestamp": "2024-01-01T12:00:00",
  "model": "gpt-4o-mini",
  "total_queries": 100,
  "passed": 75,
  "failed": 25,
  "accuracy_score": 0.87,
  "execution_time_ms": 45000.0
}
```

### Trend Data

```json
{
  "period_days": 30,
  "total_runs": 10,
  "trends": [
    {
      "date": "2024-01-01",
      "model": "gpt-4o-mini",
      "avg_accuracy": 0.87,
      "total_passed": 75,
      "total_queries": 100
    }
  ]
}
```

## Benefits

1. **Performance Tracking**: Measure AI model performance over time
2. **Model Comparison**: Compare different models on same queries
3. **Regression Detection**: Identify performance degradation
4. **Quality Assurance**: Ensure SQL generation quality
5. **Trend Analysis**: Visualize accuracy trends with charts

## Future Enhancements

1. **Custom Queries**: Allow adding custom benchmark queries
2. **Schema-Aware Testing**: Test with actual database schemas
3. **Execution Validation**: Validate generated SQL by executing it
4. **Performance Metrics**: Track query execution time and cost
5. **Automated Reporting**: Scheduled benchmark runs and reports
6. **CI/CD Integration**: Run benchmarks in CI pipeline

## Conclusion

The SQL benchmark feature provides:

- ✅ **100+ benchmark queries** covering all SQL patterns
- ✅ **Automated accuracy scoring** with similarity matching
- ✅ **Trend charts** showing performance over time
- ✅ **API endpoints** for running and viewing benchmarks
- ✅ **HTML dashboard** with interactive charts
- ✅ **Comprehensive test suite**

The benchmark system enables continuous monitoring and improvement of AI SQL generation performance!

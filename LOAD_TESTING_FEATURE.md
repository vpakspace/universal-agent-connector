# Load Testing Feature - Implementation Summary

## Overview

Comprehensive load testing infrastructure for AI Agent Connector with support for 1000+ concurrent queries and performance baseline reporting.

## Acceptance Criteria

✅ **Load Test Scripts** - Scripts for running 1000 concurrent queries  
✅ **Performance Baseline Report** - Automated baseline generation and reporting

## Implementation Details

### 1. Load Testing Tools

#### Locust (Distributed Load Testing)

**File**: `load_tests/locustfile.py`

**Features**:
- Support for 1000+ concurrent users
- Realistic user behavior simulation
- Multiple endpoint testing
- Web UI for monitoring
- Distributed testing support

**Test Scenarios**:
- Health checks
- Agent registration
- Query execution
- Natural language queries
- Cost dashboard
- Failover stats
- GraphQL queries

#### Performance Test Script

**File**: `load_tests/performance_test.py`

**Features**:
- Python-based performance testing
- Concurrent request execution
- Performance metrics collection
- JSON result export
- Configurable test parameters

**Capabilities**:
- Total requests: Configurable (default: 1000)
- Concurrent users: Configurable (default: 100)
- Multiple endpoints: Test multiple endpoints simultaneously
- Error tracking: Track and report errors
- Response time metrics: P50, P95, P99 percentiles

### 2. Performance Baseline Generator

**File**: `ai_agent_connector/app/utils/performance_baseline.py`

**Components**:
- `PerformanceBaselineGenerator` - Main baseline generator
- `BaselineMetric` - Individual endpoint metrics
- `PerformanceBaseline` - Complete baseline report

**Features**:
- Load test results analysis
- Baseline metric calculation
- Performance recommendations
- Human-readable reports
- JSON export for programmatic access

**Metrics Calculated**:
- Response time percentiles (P50, P95, P99)
- Average, min, max response times
- Requests per second
- Error rates
- Per-endpoint statistics

### 3. API Endpoints

**Load Testing Endpoints**:
- `POST /api/load-test/baseline` - Generate performance baseline
- `GET /api/load-test/baselines` - List all baselines
- `GET /api/load-test/baselines/<baseline_id>` - Get baseline details
- `GET /api/load-test/info` - Get load testing information

### 4. Test Configuration

**Locust Configuration**:
- User wait time: 1-3 seconds between requests
- Task weights: Realistic endpoint distribution
- Fast HTTP user: For higher concurrency
- Event listeners: Test start/stop hooks

**Performance Test Configuration**:
- Thread pool executor: For concurrent requests
- Configurable endpoints: Test specific endpoints
- Error handling: Graceful error handling
- Result export: JSON format

## Usage

### Running Locust Tests

#### Web UI Mode

```bash
# Start Locust
locust -f load_tests/locustfile.py --host=http://localhost:5000

# Open browser: http://localhost:8089
# Configure: 1000 users, 10 spawn rate
# Start test
```

#### Headless Mode

```bash
# Run 1000 users for 5 minutes
locust -f load_tests/locustfile.py \
  --host=http://localhost:5000 \
  --users=1000 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless \
  --html=report.html
```

#### Distributed Mode

```bash
# Master
locust -f load_tests/locustfile.py --host=http://localhost:5000 --master

# Workers (on multiple machines)
locust -f load_tests/locustfile.py --host=http://localhost:5000 --worker
```

### Running Performance Tests

```bash
# Basic usage
python load_tests/performance_test.py http://localhost:5000 1000 100

# Parameters:
# 1. base_url: http://localhost:5000
# 2. total_requests: 1000
# 3. concurrent_users: 100
```

### Generating Baselines

#### Via API

```bash
curl -X POST http://localhost:5000/api/load-test/baseline \
  -H "Content-Type: application/json" \
  -d '{
    "test_results_file": "performance_report_20240101_120000.json",
    "baseline_name": "production_baseline_v1"
  }'
```

#### Via Python

```python
from ai_agent_connector.app.utils.performance_baseline import PerformanceBaselineGenerator

generator = PerformanceBaselineGenerator()
test_results = generator.load_test_results("performance_report_20240101_120000.json")
baseline = generator.generate_baseline(test_results, "production_baseline_v1")
generator.save_report(baseline)
```

## Performance Metrics

### Response Time Percentiles

- **P50 (Median)**: 50% of requests complete within this time
- **P95**: 95% of requests complete within this time
- **P99**: 99% of requests complete within this time

### Key Performance Indicators

- **Average Response Time**: Mean response time across all requests
- **Throughput**: Requests per second (RPS)
- **Error Rate**: Percentage of failed requests
- **Concurrent Users**: Number of simultaneous users

### Baseline Report Structure

```json
{
  "baseline_id": "production_baseline_v1",
  "timestamp": "2024-01-01T12:00:00",
  "test_duration_seconds": 300.0,
  "total_requests": 10000,
  "concurrent_users": 100,
  "summary": {
    "overall_avg_response_time": 45.23,
    "overall_p95_response_time": 125.50,
    "overall_error_rate": 0.0005,
    "total_requests_per_second": 33.33
  },
  "metrics": [
    {
      "endpoint": "/api/health",
      "method": "GET",
      "p50_response_time_ms": 10.0,
      "p95_response_time_ms": 25.0,
      "p99_response_time_ms": 50.0,
      "avg_response_time_ms": 12.5,
      "requests_per_second": 100.0,
      "error_rate": 0.0,
      "sample_size": 3000
    }
  ],
  "recommendations": [
    "Performance metrics are within acceptable ranges."
  ]
}
```

## Test Scenarios

### Scenario 1: Health Check Load

Test basic endpoint with maximum concurrency:

```bash
locust -f load_tests/locustfile.py \
  --host=http://localhost:5000 \
  --users=1000 \
  --spawn-rate=50 \
  --run-time=2m \
  --headless
```

### Scenario 2: Query Execution Load

Test query endpoints with realistic load:

```bash
locust -f load_tests/locustfile.py \
  --host=http://localhost:5000 \
  --users=500 \
  --spawn-rate=10 \
  --run-time=5m
```

### Scenario 3: Mixed Workload

Test all endpoints with realistic distribution:

```bash
locust -f load_tests/locustfile.py \
  --host=http://localhost:5000 \
  --users=1000 \
  --spawn-rate=10 \
  --run-time=10m
```

## Performance Recommendations

The baseline generator automatically provides recommendations based on:

- **Response Times**: Flags endpoints with P95 > 1 second
- **Error Rates**: Flags endpoints with error rate > 5%
- **Overall Health**: Provides system-wide recommendations

## Files Created

1. `load_tests/locustfile.py` - Locust load test configuration (200+ lines)
2. `load_tests/performance_test.py` - Performance testing script (400+ lines)
3. `load_tests/README.md` - Load testing documentation
4. `ai_agent_connector/app/utils/performance_baseline.py` - Baseline generator (500+ lines)
5. `LOAD_TESTING_FEATURE.md` - This document

## Files Modified

1. `requirements.txt` - Added locust and pytest-benchmark
2. `ai_agent_connector/app/api/routes.py` - Added load testing API endpoints

## Dependencies Added

- `locust==2.24.1` - Distributed load testing tool
- `pytest-benchmark==4.0.0` - Performance benchmarking

## Example Baseline Report

```
================================================================================
Performance Baseline Report
================================================================================
Baseline ID: production_baseline_v1
Generated: 2024-01-01T12:00:00
Test Duration: 300.00 seconds
Total Requests: 10,000
Concurrent Users: 100

Overall Summary
--------------------------------------------------------------------------------
Average Response Time: 45.23 ms
P95 Response Time: 125.50 ms
Error Rate: 0.05%
Requests per Second: 33.33

Endpoint Performance
--------------------------------------------------------------------------------
Method   Endpoint                                  P50        P95        P99        RPS        Errors
--------------------------------------------------------------------------------
GET      /api/health                               10         25         50         100.0      0.00%
POST     /api/agents/{id}/query                    50         150        300        20.0       0.10%
GET      /api/agents                               30         80         150        15.0       0.00%

Recommendations
--------------------------------------------------------------------------------
1. Performance metrics are within acceptable ranges.
```

## Benefits

1. **System Limits**: Identify maximum concurrent user capacity
2. **Performance Baselines**: Establish performance benchmarks
3. **Regression Detection**: Compare current performance to baselines
4. **Capacity Planning**: Plan for scaling based on load test results
5. **Optimization Targets**: Identify endpoints needing optimization

## Best Practices

1. **Warm-up Period**: Allow system to warm up before measuring
2. **Gradual Ramp-up**: Increase load gradually to avoid sudden spikes
3. **Multiple Runs**: Run tests multiple times for consistency
4. **Resource Monitoring**: Monitor CPU, memory, database during tests
5. **Baseline Comparison**: Compare results against established baselines
6. **Realistic Scenarios**: Test with realistic user behavior patterns

## Future Enhancements

1. **Automated Baseline Comparison**: Compare new tests to existing baselines
2. **Performance Regression Alerts**: Alert on performance degradation
3. **CI/CD Integration**: Run load tests in CI pipeline
4. **Real-time Monitoring**: Real-time performance dashboards
5. **Custom Test Scenarios**: User-defined test scenarios
6. **Database Load Testing**: Test database performance under load

## Conclusion

The load testing feature provides:

- ✅ **1000+ concurrent users** support via Locust
- ✅ **Performance testing scripts** for automated testing
- ✅ **Baseline generation** for performance tracking
- ✅ **API endpoints** for baseline management
- ✅ **Comprehensive reporting** with recommendations

The load testing infrastructure enables DevOps teams to identify system limits and ensure optimal performance!

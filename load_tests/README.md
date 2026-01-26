# Load Testing Guide

## Overview

Load testing infrastructure for AI Agent Connector with support for 1000+ concurrent queries and performance baseline reporting.

## Tools

### 1. Locust (Distributed Load Testing)

**Installation**:
```bash
pip install locust
```

**Usage**:
```bash
# Start Locust web UI
locust -f locustfile.py --host=http://localhost:5000

# Headless mode (1000 users, spawn rate 10/sec)
locust -f locustfile.py --host=http://localhost:5000 --users=1000 --spawn-rate=10 --headless --run-time=5m

# Distributed mode (master + workers)
locust -f locustfile.py --host=http://localhost:5000 --master
locust -f locustfile.py --host=http://localhost:5000 --worker
```

**Web UI**: http://localhost:8089

### 2. Performance Test Script

**Usage**:
```bash
# Basic usage
python performance_test.py http://localhost:5000 1000 100

# Parameters:
# 1. base_url: API base URL
# 2. total_requests: Total number of requests (default: 1000)
# 3. concurrent_users: Number of concurrent users (default: 100)
```

**Example**:
```bash
# Test with 1000 requests and 100 concurrent users
python performance_test.py http://localhost:5000 1000 100

# Test with 5000 requests and 200 concurrent users
python performance_test.py http://localhost:5000 5000 200
```

## Running Load Tests

### Quick Start

1. **Start the application**:
```bash
python main.py
```

2. **Run Locust**:
```bash
cd load_tests
locust -f locustfile.py --host=http://localhost:5000
```

3. **Open web UI**: http://localhost:8089

4. **Configure test**:
   - Number of users: 1000
   - Spawn rate: 10 users/second
   - Host: http://localhost:5000

5. **Start test**

### Command Line Testing

```bash
# Run 1000 concurrent users for 5 minutes
locust -f locustfile.py \
  --host=http://localhost:5000 \
  --users=1000 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless \
  --html=report.html
```

### Performance Test Script

```bash
# Run performance test
python load_tests/performance_test.py http://localhost:5000 1000 100

# Results saved to: performance_report_*.json
```

## Generating Performance Baselines

### Via API

```bash
# Generate baseline from test results
curl -X POST http://localhost:5000/api/load-test/baseline \
  -H "Content-Type: application/json" \
  -d '{
    "test_results_file": "performance_report_20240101_120000.json",
    "baseline_name": "production_baseline_v1"
  }'
```

### Via Python

```python
from ai_agent_connector.app.utils.performance_baseline import PerformanceBaselineGenerator

generator = PerformanceBaselineGenerator()
test_results = generator.load_test_results("performance_report_20240101_120000.json")
baseline = generator.generate_baseline(test_results, "production_baseline_v1")

# Generate report
generator.save_report(baseline)
```

## Viewing Baselines

### List Baselines

```bash
curl http://localhost:5000/api/load-test/baselines
```

### Get Baseline

```bash
curl http://localhost:5000/api/load-test/baselines/production_baseline_v1
```

## Test Scenarios

### Scenario 1: Health Check Load

Test basic health endpoint with high concurrency:

```bash
locust -f locustfile.py --host=http://localhost:5000 \
  --users=1000 --spawn-rate=50 --run-time=2m --headless
```

### Scenario 2: Query Execution Load

Test query execution endpoints:

```bash
# Focus on query endpoints
locust -f locustfile.py --host=http://localhost:5000 \
  --users=500 --spawn-rate=10 --run-time=5m
```

### Scenario 3: Mixed Workload

Test all endpoints with realistic distribution:

```bash
# Default task weights simulate realistic usage
locust -f locustfile.py --host=http://localhost:5000 \
  --users=1000 --spawn-rate=10 --run-time=10m
```

## Performance Metrics

### Key Metrics

- **Response Time**: P50, P95, P99 percentiles
- **Throughput**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Concurrent Users**: Number of simultaneous users
- **Total Requests**: Total number of requests processed

### Baseline Report Includes

- Overall performance summary
- Per-endpoint metrics
- Response time percentiles
- Error rates
- Performance recommendations

## Interpreting Results

### Response Times

- **< 100ms**: Excellent
- **100-500ms**: Good
- **500-1000ms**: Acceptable
- **> 1000ms**: Needs optimization

### Error Rates

- **< 0.1%**: Excellent
- **0.1-1%**: Good
- **1-5%**: Acceptable
- **> 5%**: Needs investigation

### Throughput

- **> 1000 RPS**: Excellent
- **500-1000 RPS**: Good
- **100-500 RPS**: Acceptable
- **< 100 RPS**: Needs scaling

## Best Practices

1. **Warm-up Period**: Allow system to warm up before measuring
2. **Gradual Ramp-up**: Increase load gradually
3. **Multiple Runs**: Run tests multiple times for consistency
4. **Monitor Resources**: Monitor CPU, memory, and database during tests
5. **Baseline Comparison**: Compare results against established baselines
6. **Realistic Scenarios**: Test with realistic user behavior patterns

## Troubleshooting

### High Error Rates

- Check application logs
- Monitor database connections
- Verify rate limiting settings
- Check resource utilization

### Slow Response Times

- Profile slow endpoints
- Check database query performance
- Review connection pooling settings
- Monitor external API calls

### Connection Issues

- Verify network connectivity
- Check firewall settings
- Review connection pool size
- Monitor connection timeouts

## Files

- `locustfile.py` - Locust load test configuration
- `performance_test.py` - Python performance testing script
- `README.md` - This file

## API Endpoints

- `POST /api/load-test/baseline` - Generate performance baseline
- `GET /api/load-test/baselines` - List all baselines
- `GET /api/load-test/baselines/<baseline_id>` - Get baseline details
- `GET /api/load-test/info` - Get load testing information

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

## Conclusion

The load testing infrastructure provides:

- ✅ **1000+ concurrent users** support via Locust
- ✅ **Performance testing scripts** for automated testing
- ✅ **Baseline generation** for performance tracking
- ✅ **API endpoints** for baseline management
- ✅ **Comprehensive reporting** with recommendations

Use these tools to identify system limits and ensure optimal performance!

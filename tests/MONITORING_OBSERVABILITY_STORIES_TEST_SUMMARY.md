# Monitoring & Observability Stories - Test Summary

This document summarizes the test cases for the 4 Monitoring & Observability stories.

## Stories Implemented

1. **Story 1**: As an Admin, I want real-time dashboards showing query volume, latency, and error rates per agent, so that I can monitor system health.

2. **Story 2**: As a User, I want to receive alerts when query execution times exceed a threshold, so that performance issues are caught early.

3. **Story 3**: As a Developer, I want integration with observability tools (Datadog, Grafana, CloudWatch), so that logs and metrics fit into existing workflows.

4. **Story 4**: As an Admin, I want to trace the full lifecycle of a query (input → SQL generation → execution → result), so that debugging is easier.

## Test Coverage Summary

| Story | Test Cases | Status |
|-------|-----------|--------|
| Story 1: Dashboard Metrics | 5 tests | ✅ Complete |
| Story 1: Edge Cases | 4 tests | ✅ Complete |
| Story 2: Alerting | 9 tests | ✅ Complete |
| Story 2: Edge Cases | 5 tests | ✅ Complete |
| Story 3: Observability | 4 tests | ✅ Complete |
| Story 3: Edge Cases | 3 tests | ✅ Complete |
| Story 4: Query Tracing | 8 tests | ✅ Complete |
| Story 4: Edge Cases | 7 tests | ✅ Complete |
| Integration Tests | 1 test | ✅ Complete |
| Error Handling Tests | 6 tests | ✅ Complete |
| **Total** | **52 tests** | ✅ **Complete** |

## Test File

**`tests/test_monitoring_observability_stories.py`** - Comprehensive integration tests for all monitoring and observability features.

## API Endpoints

### Story 1: Dashboard Metrics

- **GET** `/api/admin/dashboard/metrics`
  - Get real-time dashboard metrics for all agents
  - Query parameters: `window_seconds`, `agent_id`
  - Returns: System-wide and per-agent metrics

### Story 2: Alerting

- **POST** `/api/admin/alerts/rules` - Create alert rule
- **GET** `/api/admin/alerts/rules` - List alert rules
- **GET** `/api/admin/alerts/rules/<rule_id>` - Get alert rule
- **PUT** `/api/admin/alerts/rules/<rule_id>` - Update alert rule
- **DELETE** `/api/admin/alerts/rules/<rule_id>` - Delete alert rule
- **GET** `/api/admin/alerts` - List alerts (with filtering)
- **POST** `/api/admin/alerts/<alert_id>/acknowledge` - Acknowledge alert

### Story 3: Observability

- **GET** `/api/admin/observability/config` - Get observability configuration
- Metrics and logs are automatically sent to configured backend (Datadog, Grafana, CloudWatch)

### Story 4: Query Tracing

- **GET** `/api/admin/traces` - List query traces (with filtering)
- **GET** `/api/admin/traces/<trace_id>` - Get specific trace with full lifecycle

## Implementation Details

### Metrics Collector (`metrics_collector.py`)

- Real-time metrics collection per agent
- Tracks: query volume, latency (avg, p50, p95, p99, min, max), error rates
- Thread-safe for concurrent access
- Configurable time windows
- System-wide aggregations

### Alert Manager (`alerting.py`)

- Configurable alert rules with thresholds
- Per-agent or system-wide alerts
- Severity levels (info, warning, critical)
- Cooldown periods to prevent alert spam
- Alert acknowledgment workflow
- Custom alert handlers for external integrations

### Observability Manager (`observability.py`)

- Unified interface for multiple backends
- Supports: Datadog, Grafana (Prometheus/Loki), CloudWatch
- Automatic metric and log forwarding
- Environment variable configuration
- Graceful degradation if backend unavailable

### Query Tracer (`query_tracing.py`)

- Full lifecycle tracing: input → SQL generation → validation → approval → execution → result
- Span-based tracing with duration tracking
- Metadata capture at each stage
- Error tracking
- Trace filtering and search

## Running the Tests

```bash
# Run all monitoring/observability story tests
pytest tests/test_monitoring_observability_stories.py -v

# Run specific story tests
pytest tests/test_monitoring_observability_stories.py::TestStory1_DashboardMetrics -v
pytest tests/test_monitoring_observability_stories.py::TestStory2_Alerting -v
pytest tests/test_monitoring_observability_stories.py::TestStory3_Observability -v
pytest tests/test_monitoring_observability_stories.py::TestStory4_QueryTracing -v

# Run integration tests
pytest tests/test_monitoring_observability_stories.py::TestIntegration_MonitoringFeatures -v
```

## Configuration

### Observability Backend

Set environment variable:
```bash
export OBSERVABILITY_BACKEND=datadog  # or grafana, cloudwatch, none
```

### Datadog
```bash
export DATADOG_API_KEY=your-api-key
export DATADOG_APP_KEY=your-app-key
```

### Grafana
```bash
export PROMETHEUS_PUSHGATEWAY_URL=http://prometheus:9091
export GRAFANA_LOKI_URL=http://loki:3100
```

### CloudWatch
```bash
export CLOUDWATCH_LOG_GROUP=ai-agent-connector
# AWS credentials via boto3 (IAM role, credentials file, or env vars)
```

## Example Usage

### 1. Get Dashboard Metrics

```bash
# All agents
GET /api/admin/dashboard/metrics

# Specific agent
GET /api/admin/dashboard/metrics?agent_id=agent-1&window_seconds=300
```

### 2. Create Alert Rule

```bash
POST /api/admin/alerts/rules
{
  "name": "Slow Query Alert",
  "description": "Alert when queries exceed 5 seconds",
  "threshold_ms": 5000,
  "severity": "warning",
  "cooldown_seconds": 60
}
```

### 3. List Alerts

```bash
GET /api/admin/alerts?agent_id=agent-1&severity=warning&acknowledged=false
```

### 4. Get Query Trace

```bash
GET /api/admin/traces/<trace_id>
```

Returns full lifecycle:
- Input (natural language query)
- SQL generation (with conversion source)
- Validation
- Execution (with timing)
- Result (row count, success/failure)

## Integration with Query Execution

All monitoring features are automatically integrated into query execution:

1. **Metrics**: Automatically recorded for every query
2. **Alerts**: Automatically checked and triggered
3. **Observability**: Metrics and logs automatically sent
4. **Tracing**: Full lifecycle automatically traced

## Test Categories

### ✅ Basic Functionality Tests
- Core feature operations
- API endpoint interactions
- Data flow and responses

### ✅ Edge Cases
- Time window calculations
- Percentile calculations
- Error rate calculations
- Cooldown periods
- Filtering and search

### ✅ Integration Tests
- Multi-feature workflows
- Feature interactions
- End-to-end scenarios

## Notes

- Metrics are collected in real-time and aggregated on-demand
- Alert rules support both per-agent and system-wide scoping
- Observability integration is optional and gracefully degrades if backend unavailable
- Query traces are kept in memory (configurable max) for fast access
- All features are thread-safe for concurrent access
- Dashboard metrics include system-wide aggregations and per-agent breakdowns


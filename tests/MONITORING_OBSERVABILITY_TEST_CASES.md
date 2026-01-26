# Monitoring & Observability Stories - Complete Test Cases

This document lists all test cases for the 4 Monitoring & Observability stories.

## Test File
**`tests/test_monitoring_observability_stories.py`** - 52 comprehensive test cases

---

## Story 1: Real-Time Dashboards (9 tests)

### Basic Functionality
1. **test_get_dashboard_metrics_all_agents** - Get dashboard metrics for all agents
2. **test_get_dashboard_metrics_specific_agent** - Get metrics for specific agent
3. **test_dashboard_metrics_calculations** - Verify correct statistics calculations
4. **test_dashboard_error_rate_calculation** - Verify error rate calculation
5. **test_dashboard_window_parameter** - Test custom time window parameter

### Edge Cases
6. **test_dashboard_no_metrics** - Handle case when no metrics available
7. **test_dashboard_error_breakdown** - Verify error breakdown by error type
8. **test_dashboard_queries_per_second** - Verify queries per second calculation
9. **test_dashboard_percentile_calculations** - Verify percentile (p50, p95, p99) calculations

---

## Story 2: Alerting System (14 tests)

### Basic Functionality
1. **test_create_alert_rule** - Create an alert rule
2. **test_alert_rule_triggers_on_threshold** - Verify alert triggers when threshold exceeded
3. **test_alert_cooldown** - Verify cooldown period prevents spam
4. **test_list_alerts** - List all alerts
5. **test_filter_alerts_by_agent** - Filter alerts by agent ID
6. **test_acknowledge_alert** - Acknowledge an alert
7. **test_alert_rule_for_specific_agent** - Test agent-specific alert rules
8. **test_update_alert_rule** - Update an alert rule
9. **test_delete_alert_rule** - Delete an alert rule

### Edge Cases
10. **test_multiple_alert_rules** - Multiple rules can trigger independently
11. **test_disabled_alert_rule** - Disabled rules don't trigger
12. **test_alert_severity_filtering** - Filter alerts by severity
13. **test_alert_acknowledged_filtering** - Filter alerts by acknowledged status
14. **test_alert_rule_agent_specific_vs_global** - Agent-specific vs global rules

---

## Story 3: Observability Integration (7 tests)

### Basic Functionality
1. **test_get_observability_config** - Get observability configuration
2. **test_observability_sends_metrics** - Verify metrics are sent to backend
3. **test_observability_sends_logs** - Verify logs are sent to backend
4. **test_observability_alert_metric** - Verify alert metrics are sent

### Edge Cases
5. **test_observability_backend_none** - Handle disabled backend gracefully
6. **test_observability_missing_credentials** - Handle missing credentials gracefully
7. **test_observability_different_backends** - Test different backend configurations

---

## Story 4: Query Tracing (15 tests)

### Basic Functionality
1. **test_start_trace** - Start a query trace
2. **test_trace_full_lifecycle** - Trace complete query lifecycle
3. **test_trace_error_case** - Trace error scenarios
4. **test_list_traces** - List query traces
5. **test_filter_traces_by_agent** - Filter traces by agent ID
6. **test_filter_traces_by_success** - Filter traces by success status
7. **test_get_specific_trace** - Get specific trace details
8. **test_trace_span_durations** - Verify span duration calculations

### Edge Cases
9. **test_trace_missing_span** - Handle missing span gracefully
10. **test_trace_incomplete_span** - Handle incomplete spans
11. **test_trace_all_stages** - Test all trace stages (INPUT, SQL_GENERATION, VALIDATION, APPROVAL, EXECUTION, RESULT)
12. **test_trace_filter_by_query_type** - Filter traces by query type
13. **test_trace_metadata_preservation** - Verify metadata is preserved in spans
14. **test_trace_limit_enforcement** - Verify trace limit is enforced
15. **test_trace_error_in_span** - Test error tracking in spans

---

## Integration Tests (7 tests)

1. **test_complete_monitoring_workflow** - Complete workflow combining all features
2. **test_dashboard_unauthorized** - Dashboard requires admin permission
3. **test_alerts_unauthorized** - Alerts require admin permission
4. **test_traces_unauthorized** - Traces require admin permission
5. **test_alert_rule_not_found** - Handle non-existent alert rule
6. **test_trace_not_found** - Handle non-existent trace
7. **test_alert_acknowledge_not_found** - Handle non-existent alert acknowledgment

---

## Test Coverage Summary

| Category | Count |
|----------|-------|
| Story 1: Dashboard Metrics | 9 tests |
| Story 2: Alerting | 14 tests |
| Story 3: Observability | 7 tests |
| Story 4: Query Tracing | 15 tests |
| Integration Tests | 7 tests |
| **Total** | **52 tests** |

---

## Running Tests

```bash
# Run all monitoring/observability tests
pytest tests/test_monitoring_observability_stories.py -v

# Run specific story tests
pytest tests/test_monitoring_observability_stories.py::TestStory1_DashboardMetrics -v
pytest tests/test_monitoring_observability_stories.py::TestStory1_EdgeCases -v
pytest tests/test_monitoring_observability_stories.py::TestStory2_Alerting -v
pytest tests/test_monitoring_observability_stories.py::TestStory2_EdgeCases -v
pytest tests/test_monitoring_observability_stories.py::TestStory3_Observability -v
pytest tests/test_monitoring_observability_stories.py::TestStory3_EdgeCases -v
pytest tests/test_monitoring_observability_stories.py::TestStory4_QueryTracing -v
pytest tests/test_monitoring_observability_stories.py::TestStory4_EdgeCases -v

# Run integration tests
pytest tests/test_monitoring_observability_stories.py::TestIntegration_MonitoringFeatures -v
pytest tests/test_monitoring_observability_stories.py::TestIntegration_ErrorHandling -v

# Run only edge cases
pytest tests/test_monitoring_observability_stories.py -k "EdgeCases" -v

# Run only error handling
pytest tests/test_monitoring_observability_stories.py -k "ErrorHandling" -v
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
- Missing data scenarios
- Boundary conditions
- Error handling
- Filtering and search
- Multiple rules/agents
- Disabled features
- Missing credentials

### ✅ Integration Tests
- Multi-feature workflows
- Feature interactions
- End-to-end scenarios
- Permission enforcement
- Error propagation

---

## Key Test Scenarios Covered

### Dashboard Metrics
- ✅ System-wide aggregations
- ✅ Per-agent metrics
- ✅ Latency statistics (avg, p50, p95, p99, min, max)
- ✅ Error rate calculations
- ✅ Error breakdown by type
- ✅ Queries per second
- ✅ Time window filtering
- ✅ Empty metrics handling

### Alerting
- ✅ Rule creation and management
- ✅ Threshold-based triggering
- ✅ Cooldown periods
- ✅ Severity levels (info, warning, critical)
- ✅ Agent-specific vs global rules
- ✅ Alert acknowledgment
- ✅ Alert filtering (agent, severity, acknowledged)
- ✅ Multiple rules triggering
- ✅ Disabled rules

### Observability
- ✅ Backend configuration
- ✅ Metric forwarding
- ✅ Log forwarding
- ✅ Alert metric forwarding
- ✅ Graceful degradation
- ✅ Missing credentials handling
- ✅ Multiple backend support

### Query Tracing
- ✅ Full lifecycle tracking
- ✅ All trace stages
- ✅ Span duration calculations
- ✅ Metadata preservation
- ✅ Error tracking
- ✅ Trace filtering
- ✅ Incomplete span handling
- ✅ Trace limits

### Integration
- ✅ Complete workflows
- ✅ Permission enforcement
- ✅ Error handling
- ✅ Feature interactions

---

## Notes

- All tests use real component instances for integration testing
- Metrics are collected in real-time and tested with actual data
- Alert rules are tested with actual threshold checking
- Traces are tested with full lifecycle scenarios
- Observability tests verify graceful degradation when backends unavailable
- Permission tests ensure admin-only endpoints are protected
- Edge cases ensure robust error handling and boundary conditions


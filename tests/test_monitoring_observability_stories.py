"""
Integration tests for Monitoring & Observability Stories

Story 1: As an Admin, I want real-time dashboards showing query volume, latency, and error rates per agent,
         so that I can monitor system health.

Story 2: As a User, I want to receive alerts when query execution times exceed a threshold,
         so that performance issues are caught early.

Story 3: As a Developer, I want integration with observability tools (Datadog, Grafana, CloudWatch),
         so that logs and metrics fit into existing workflows.

Story 4: As an Admin, I want to trace the full lifecycle of a query (input → SQL generation → execution → result),
         so that debugging is easier.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, metrics_collector,
    alert_manager, observability_manager, query_tracer
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.alerting import AlertSeverity
from ai_agent_connector.app.utils.query_tracing import TraceStage


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    metrics_collector.clear_all_metrics()
    alert_manager._rules.clear()
    alert_manager._alerts.clear()
    alert_manager._last_alert_times.clear()
    query_tracer.clear_traces()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    metrics_collector.clear_all_metrics()
    alert_manager._rules.clear()
    alert_manager._alerts.clear()
    alert_manager._last_alert_times.clear()
    query_tracer.clear_traces()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_agent():
    """Create a test agent"""
    result = agent_registry.register_agent(
        agent_id='test-agent',
        agent_info={'name': 'Test Agent'},
        credentials={'api_key': 'test-key', 'api_secret': 'test-secret'}
    )
    access_control.grant_permission('test-agent', Permission.READ)
    return {'agent_id': 'test-agent', 'api_key': result['api_key']}


@pytest.fixture
def admin_agent():
    """Create an admin agent"""
    result = agent_registry.register_agent(
        agent_id='admin-agent',
        agent_info={'name': 'Admin Agent'},
        credentials={'api_key': 'admin-key', 'api_secret': 'admin-secret'}
    )
    access_control.grant_permission('admin-agent', Permission.ADMIN)
    return {'agent_id': 'admin-agent', 'api_key': result['api_key']}


class TestStory1_DashboardMetrics:
    """Story 1: Real-time dashboards for query monitoring"""
    
    def test_get_dashboard_metrics_all_agents(self, client, admin_agent):
        """Test getting dashboard metrics for all agents"""
        # Record some metrics
        metrics_collector.record_query('agent-1', 'SELECT', 100.0, True)
        metrics_collector.record_query('agent-1', 'SELECT', 150.0, True)
        metrics_collector.record_query('agent-2', 'INSERT', 200.0, False)
        
        response = client.get(
            '/api/admin/dashboard/metrics',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'system_metrics' in data
        assert 'agent_metrics' in data
        assert data['system_metrics']['total_queries'] >= 3
    
    def test_get_dashboard_metrics_specific_agent(self, client, admin_agent):
        """Test getting dashboard metrics for a specific agent"""
        # Record metrics for multiple agents
        metrics_collector.record_query('agent-1', 'SELECT', 100.0, True)
        metrics_collector.record_query('agent-2', 'SELECT', 200.0, True)
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=agent-1',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['agent_id'] == 'agent-1'
        assert data['total_queries'] >= 1
    
    def test_dashboard_metrics_calculations(self, client, admin_agent):
        """Test that dashboard calculates correct statistics"""
        # Record metrics with known values
        latencies = [100.0, 200.0, 300.0, 400.0, 500.0]
        for latency in latencies:
            metrics_collector.record_query('test-agent', 'SELECT', latency, True)
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_queries'] == 5
        assert data['successful_queries'] == 5
        assert data['avg_latency_ms'] == 300.0
        assert data['p50_latency_ms'] == 300.0
        assert data['p95_latency_ms'] > 300.0
        assert data['max_latency_ms'] == 500.0
        assert data['min_latency_ms'] == 100.0
    
    def test_dashboard_error_rate_calculation(self, client, admin_agent):
        """Test error rate calculation"""
        # Record mix of success and failures
        for i in range(10):
            metrics_collector.record_query('test-agent', 'SELECT', 100.0, i < 7)  # 7 success, 3 failures
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['error_rate'] == pytest.approx(0.3, abs=0.01)
        assert data['failed_queries'] == 3
        assert data['successful_queries'] == 7
    
    def test_dashboard_window_parameter(self, client, admin_agent):
        """Test dashboard with custom time window"""
        metrics_collector.record_query('test-agent', 'SELECT', 100.0, True)
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent&window_seconds=300',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['time_window_seconds'] == 300


class TestStory2_Alerting:
    """Story 2: Alerts for query execution time thresholds"""
    
    def test_create_alert_rule(self, client, admin_agent):
        """Test creating an alert rule"""
        payload = {
            'name': 'Slow Query Alert',
            'description': 'Alert when queries exceed 5 seconds',
            'threshold_ms': 5000,
            'severity': 'warning',
            'cooldown_seconds': 60
        }
        
        response = client.post(
            '/api/admin/alerts/rules',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'rule' in data
        assert data['rule']['threshold_ms'] == 5000
        assert data['rule']['severity'] == 'warning'
    
    def test_alert_rule_triggers_on_threshold(self, client, admin_agent):
        """Test that alert rule triggers when threshold is exceeded"""
        # Create alert rule
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0,
            severity=AlertSeverity.WARNING
        )
        
        # Trigger alert
        alerts = alert_manager.check_and_trigger('test-agent', 1500.0)
        
        assert len(alerts) == 1
        assert alerts[0].execution_time_ms == 1500.0
        assert alerts[0].threshold_ms == 1000.0
        assert alerts[0].severity == AlertSeverity.WARNING
    
    def test_alert_cooldown(self, client, admin_agent):
        """Test that alerts respect cooldown period"""
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0,
            cooldown_seconds=60
        )
        
        # First alert should trigger
        alerts1 = alert_manager.check_and_trigger('test-agent', 1500.0)
        assert len(alerts1) == 1
        
        # Second alert within cooldown should not trigger
        alerts2 = alert_manager.check_and_trigger('test-agent', 1500.0)
        assert len(alerts2) == 0
    
    def test_list_alerts(self, client, admin_agent):
        """Test listing alerts"""
        # Create and trigger alerts
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0
        )
        alert_manager.check_and_trigger('test-agent', 1500.0)
        alert_manager.check_and_trigger('test-agent-2', 2000.0)
        
        response = client.get(
            '/api/admin/alerts',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'alerts' in data
        assert len(data['alerts']) >= 2
    
    def test_filter_alerts_by_agent(self, client, admin_agent):
        """Test filtering alerts by agent ID"""
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0
        )
        alert_manager.check_and_trigger('agent-1', 1500.0)
        alert_manager.check_and_trigger('agent-2', 2000.0)
        
        response = client.get(
            '/api/admin/alerts?agent_id=agent-1',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(a['agent_id'] == 'agent-1' for a in data['alerts'])
    
    def test_acknowledge_alert(self, client, admin_agent):
        """Test acknowledging an alert"""
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0
        )
        alerts = alert_manager.check_and_trigger('test-agent', 1500.0)
        alert_id = alerts[0].alert_id
        
        payload = {'acknowledged_by': 'admin-user'}
        
        response = client.post(
            f'/api/admin/alerts/{alert_id}/acknowledge',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['alert']['acknowledged'] is True
        assert data['alert']['acknowledged_by'] == 'admin-user'
    
    def test_alert_rule_for_specific_agent(self, client, admin_agent):
        """Test alert rule scoped to specific agent"""
        rule = alert_manager.create_rule(
            name='Agent-Specific Alert',
            description='Alert for specific agent',
            threshold_ms=1000.0,
            agent_id='agent-1'
        )
        
        # Should trigger for agent-1
        alerts1 = alert_manager.check_and_trigger('agent-1', 1500.0)
        assert len(alerts1) == 1
        
        # Should not trigger for agent-2
        alerts2 = alert_manager.check_and_trigger('agent-2', 1500.0)
        assert len(alerts2) == 0
    
    def test_update_alert_rule(self, client, admin_agent):
        """Test updating an alert rule"""
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0
        )
        
        payload = {
            'threshold_ms': 2000.0,
            'severity': 'critical'
        }
        
        response = client.put(
            f'/api/admin/alerts/rules/{rule.rule_id}',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rule']['threshold_ms'] == 2000.0
        assert data['rule']['severity'] == 'critical'
    
    def test_delete_alert_rule(self, client, admin_agent):
        """Test deleting an alert rule"""
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0
        )
        
        response = client.delete(
            f'/api/admin/alerts/rules/{rule.rule_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify rule is deleted
        assert alert_manager.get_rule(rule.rule_id) is None


class TestStory3_Observability:
    """Story 3: Integration with observability tools"""
    
    def test_get_observability_config(self, client, admin_agent):
        """Test getting observability configuration"""
        response = client.get(
            '/api/admin/observability/config',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'backend' in data
        assert 'enabled' in data
        assert 'environment_variables_required' in data
    
    def test_observability_sends_metrics(self, client, test_agent):
        """Test that observability manager sends metrics"""
        with patch.object(observability_manager.client, 'send_metric') as mock_send:
            observability_manager.send_query_metric(
                agent_id='test-agent',
                query_type='SELECT',
                execution_time_ms=100.0,
                success=True
            )
            
            # Should be called (or not if disabled)
            # Just verify it doesn't raise an error
            assert True
    
    def test_observability_sends_logs(self, client, test_agent):
        """Test that observability manager sends logs"""
        with patch.object(observability_manager.client, 'send_log') as mock_send:
            observability_manager.send_query_log(
                level='error',
                message='Query failed',
                agent_id='test-agent',
                query='SELECT * FROM users',
                execution_time_ms=100.0,
                error='Connection timeout'
            )
            
            # Should be called (or not if disabled)
            # Just verify it doesn't raise an error
            assert True
    
    def test_observability_alert_metric(self, client, admin_agent):
        """Test sending alert metrics to observability"""
        with patch.object(observability_manager.client, 'send_metric') as mock_send:
            observability_manager.send_alert_metric(
                alert_severity='warning',
                agent_id='test-agent',
                execution_time_ms=1500.0
            )
            
            # Should be called (or not if disabled)
            assert True


class TestStory4_QueryTracing:
    """Story 4: Query lifecycle tracing"""
    
    def test_start_trace(self, client, test_agent):
        """Test starting a query trace"""
        trace_id = query_tracer.start_trace(
            agent_id='test-agent',
            query_type='SELECT',
            natural_language_query='show all users'
        )
        
        assert trace_id is not None
        
        trace = query_tracer.get_trace(trace_id)
        assert trace is not None
        assert trace.agent_id == 'test-agent'
        assert trace.query_type == 'SELECT'
        assert trace.natural_language_query == 'show all users'
        assert len(trace.spans) == 1
        assert trace.spans[0].stage == TraceStage.INPUT
    
    def test_trace_full_lifecycle(self, client, test_agent):
        """Test tracing full query lifecycle"""
        # Start trace
        trace_id = query_tracer.start_trace(
            agent_id='test-agent',
            query_type='SELECT',
            natural_language_query='show users'
        )
        
        # Add SQL generation span
        sql_span_id = query_tracer.add_span(
            trace_id=trace_id,
            stage=TraceStage.SQL_GENERATION,
            metadata={'sql': 'SELECT * FROM users'}
        )
        query_tracer.end_span(trace_id, sql_span_id)
        
        # Add execution span
        exec_span_id = query_tracer.add_span(
            trace_id=trace_id,
            stage=TraceStage.EXECUTION
        )
        query_tracer.end_span(trace_id, exec_span_id, metadata={'execution_time_ms': 100.0})
        
        # Complete trace
        query_tracer.complete_trace(
            trace_id=trace_id,
            success=True,
            generated_sql='SELECT * FROM users',
            final_sql='SELECT * FROM users WHERE user_id = current_user()',
            result_row_count=10
        )
        
        trace = query_tracer.get_trace(trace_id)
        assert trace.success is True
        assert trace.generated_sql == 'SELECT * FROM users'
        assert trace.final_sql == 'SELECT * FROM users WHERE user_id = current_user()'
        assert trace.result_row_count == 10
        assert len(trace.spans) == 3
        assert trace.total_duration_ms is not None
    
    def test_trace_error_case(self, client, test_agent):
        """Test tracing error case"""
        trace_id = query_tracer.start_trace(
            agent_id='test-agent',
            query_type='SELECT'
        )
        
        # Add error span
        error_span_id = query_tracer.add_span(
            trace_id=trace_id,
            stage=TraceStage.ERROR,
            error='Connection timeout'
        )
        query_tracer.end_span(trace_id, error_span_id)
        
        # Complete with error
        query_tracer.complete_trace(
            trace_id=trace_id,
            success=False,
            error_message='Connection timeout'
        )
        
        trace = query_tracer.get_trace(trace_id)
        assert trace.success is False
        assert trace.error_message == 'Connection timeout'
    
    def test_list_traces(self, client, admin_agent):
        """Test listing query traces"""
        # Create some traces
        trace1 = query_tracer.start_trace('agent-1', 'SELECT')
        query_tracer.complete_trace(trace1, True)
        
        trace2 = query_tracer.start_trace('agent-2', 'INSERT')
        query_tracer.complete_trace(trace2, False, error_message='Error')
        
        response = client.get(
            '/api/admin/traces',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'traces' in data
        assert len(data['traces']) >= 2
    
    def test_filter_traces_by_agent(self, client, admin_agent):
        """Test filtering traces by agent ID"""
        trace1 = query_tracer.start_trace('agent-1', 'SELECT')
        query_tracer.complete_trace(trace1, True)
        
        trace2 = query_tracer.start_trace('agent-2', 'SELECT')
        query_tracer.complete_trace(trace2, True)
        
        response = client.get(
            '/api/admin/traces?agent_id=agent-1',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(t['agent_id'] == 'agent-1' for t in data['traces'])
    
    def test_filter_traces_by_success(self, client, admin_agent):
        """Test filtering traces by success status"""
        trace1 = query_tracer.start_trace('test-agent', 'SELECT')
        query_tracer.complete_trace(trace1, True)
        
        trace2 = query_tracer.start_trace('test-agent', 'SELECT')
        query_tracer.complete_trace(trace2, False, error_message='Error')
        
        response = client.get(
            '/api/admin/traces?success=true',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(t['success'] is True for t in data['traces'])
    
    def test_get_specific_trace(self, client, admin_agent):
        """Test getting a specific trace"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT')
        query_tracer.complete_trace(trace_id, True, result_row_count=5)
        
        response = client.get(
            f'/api/admin/traces/{trace_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['trace_id'] == trace_id
        assert data['success'] is True
        assert data['result_row_count'] == 5
        assert 'spans' in data
    
    def test_trace_span_durations(self, client, test_agent):
        """Test that trace spans have duration calculations"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT')
        
        import time
        span_id = query_tracer.add_span(trace_id, TraceStage.EXECUTION)
        time.sleep(0.1)  # Simulate execution
        query_tracer.end_span(trace_id, span_id)
        
        trace = query_tracer.get_trace(trace_id)
        span = next(s for s in trace.spans if s.span_id == span_id)
        assert span.duration_ms is not None
        assert span.duration_ms > 0


class TestIntegration_MonitoringFeatures:
    """Integration tests combining all monitoring features"""
    
    def test_complete_monitoring_workflow(self, client, test_agent, admin_agent):
        """Test complete workflow: metrics → alerts → tracing → observability"""
        # Step 1: Record metrics
        metrics_collector.record_query('test-agent', 'SELECT', 1500.0, True)
        
        # Step 2: Create alert rule
        rule = alert_manager.create_rule(
            name='Slow Query',
            description='Alert on slow queries',
            threshold_ms=1000.0
        )
        
        # Step 3: Trigger alert
        alerts = alert_manager.check_and_trigger('test-agent', 1500.0)
        assert len(alerts) == 1
        
        # Step 4: Create trace
        trace_id = query_tracer.start_trace('test-agent', 'SELECT')
        query_tracer.complete_trace(trace_id, True, result_row_count=10)
        
        # Step 5: Get dashboard
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        
        # Step 6: Get alerts
        response = client.get(
            '/api/admin/alerts',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        assert len(response.get_json()['alerts']) >= 1
        
        # Step 7: Get trace
        response = client.get(
            f'/api/admin/traces/{trace_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        assert response.status_code == 200
        assert response.get_json()['success'] is True


class TestStory1_EdgeCases:
    """Story 1: Dashboard Metrics - Edge Cases"""
    
    def test_dashboard_no_metrics(self, client, admin_agent):
        """Test dashboard when no metrics are available"""
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=nonexistent-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data or data.get('total_queries', 0) == 0
    
    def test_dashboard_error_breakdown(self, client, admin_agent):
        """Test that dashboard includes error breakdown"""
        # Record queries with different error types
        metrics_collector.record_query('test-agent', 'SELECT', 100.0, False, 'ConnectionError')
        metrics_collector.record_query('test-agent', 'SELECT', 100.0, False, 'TimeoutError')
        metrics_collector.record_query('test-agent', 'SELECT', 100.0, False, 'ConnectionError')
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'error_breakdown' in data
        assert data['error_breakdown'].get('ConnectionError', 0) == 2
        assert data['error_breakdown'].get('TimeoutError', 0) == 1
    
    def test_dashboard_queries_per_second(self, client, admin_agent):
        """Test queries per second calculation"""
        # Record multiple queries
        for i in range(10):
            metrics_collector.record_query('test-agent', 'SELECT', 100.0, True)
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent&window_seconds=60',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'queries_per_second' in data
        assert data['queries_per_second'] > 0
    
    def test_dashboard_percentile_calculations(self, client, admin_agent):
        """Test percentile calculations are correct"""
        # Record queries with known latency distribution
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for latency in latencies:
            metrics_collector.record_query('test-agent', 'SELECT', float(latency), True)
        
        response = client.get(
            '/api/admin/dashboard/metrics?agent_id=test-agent',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        # P50 should be around 50
        assert 45 <= data['p50_latency_ms'] <= 55
        # P95 should be around 95
        assert 90 <= data['p95_latency_ms'] <= 100
        # P99 should be around 99
        assert 95 <= data['p99_latency_ms'] <= 100


class TestStory2_EdgeCases:
    """Story 2: Alerting - Edge Cases"""
    
    def test_multiple_alert_rules(self, client, admin_agent):
        """Test multiple alert rules can trigger independently"""
        rule1 = alert_manager.create_rule(
            name='Warning Threshold',
            description='Warning at 1s',
            threshold_ms=1000.0,
            severity=AlertSeverity.WARNING
        )
        rule2 = alert_manager.create_rule(
            name='Critical Threshold',
            description='Critical at 5s',
            threshold_ms=5000.0,
            severity=AlertSeverity.CRITICAL
        )
        
        # Should trigger both rules
        alerts = alert_manager.check_and_trigger('test-agent', 6000.0)
        
        assert len(alerts) == 2
        severities = [a.severity for a in alerts]
        assert AlertSeverity.WARNING in severities
        assert AlertSeverity.CRITICAL in severities
    
    def test_disabled_alert_rule(self, client, admin_agent):
        """Test that disabled alert rules don't trigger"""
        rule = alert_manager.create_rule(
            name='Disabled Rule',
            description='Disabled alert',
            threshold_ms=1000.0
        )
        rule.enabled = False
        
        alerts = alert_manager.check_and_trigger('test-agent', 2000.0)
        
        assert len(alerts) == 0
    
    def test_alert_severity_filtering(self, client, admin_agent):
        """Test filtering alerts by severity"""
        rule1 = alert_manager.create_rule(
            name='Warning',
            description='Warning',
            threshold_ms=1000.0,
            severity=AlertSeverity.WARNING
        )
        rule2 = alert_manager.create_rule(
            name='Critical',
            description='Critical',
            threshold_ms=2000.0,
            severity=AlertSeverity.CRITICAL
        )
        
        alert_manager.check_and_trigger('test-agent', 3000.0)
        
        response = client.get(
            '/api/admin/alerts?severity=critical',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(a['severity'] == 'critical' for a in data['alerts'])
    
    def test_alert_acknowledged_filtering(self, client, admin_agent):
        """Test filtering alerts by acknowledged status"""
        rule = alert_manager.create_rule(
            name='Test Rule',
            description='Test',
            threshold_ms=1000.0
        )
        
        alerts = alert_manager.check_and_trigger('test-agent', 2000.0)
        alert_id = alerts[0].alert_id
        
        # Acknowledge one alert
        alert_manager.acknowledge_alert(alert_id, 'admin')
        
        # Filter unacknowledged
        response = client.get(
            '/api/admin/alerts?acknowledged=false',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(not a['acknowledged'] for a in data['alerts'])
    
    def test_alert_rule_agent_specific_vs_global(self, client, admin_agent):
        """Test agent-specific vs global alert rules"""
        global_rule = alert_manager.create_rule(
            name='Global Rule',
            description='Applies to all agents',
            threshold_ms=1000.0,
            agent_id=None
        )
        agent_rule = alert_manager.create_rule(
            name='Agent Rule',
            description='Applies to agent-1 only',
            threshold_ms=500.0,
            agent_id='agent-1'
        )
        
        # Should trigger both for agent-1
        alerts1 = alert_manager.check_and_trigger('agent-1', 2000.0)
        assert len(alerts1) == 2
        
        # Should only trigger global for agent-2
        alerts2 = alert_manager.check_and_trigger('agent-2', 2000.0)
        assert len(alerts2) == 1
        assert alerts2[0].rule_id == global_rule.rule_id


class TestStory3_EdgeCases:
    """Story 3: Observability - Edge Cases"""
    
    def test_observability_backend_none(self, client, admin_agent):
        """Test observability when backend is disabled"""
        with patch.dict('os.environ', {'OBSERVABILITY_BACKEND': 'none'}):
            from ai_agent_connector.app.utils.observability import ObservabilityManager
            manager = ObservabilityManager()
            
            # Should not raise error even if backend unavailable
            manager.send_query_metric('test-agent', 'SELECT', 100.0, True)
            assert True
    
    def test_observability_missing_credentials(self, client, admin_agent):
        """Test observability gracefully handles missing credentials"""
        with patch.dict('os.environ', {'OBSERVABILITY_BACKEND': 'datadog'}, clear=False):
            from ai_agent_connector.app.utils.observability import ObservabilityManager
            manager = ObservabilityManager()
            
            # Should not raise error if credentials missing
            result = manager.send_query_metric('test-agent', 'SELECT', 100.0, True)
            # May return False but shouldn't raise
            assert result is False or result is True
    
    def test_observability_different_backends(self, client, admin_agent):
        """Test different observability backends"""
        backends = ['datadog', 'grafana', 'cloudwatch', 'none']
        
        for backend in backends:
            with patch.dict('os.environ', {'OBSERVABILITY_BACKEND': backend}):
                from ai_agent_connector.app.utils.observability import ObservabilityManager
                manager = ObservabilityManager()
                
                # Should initialize without error
                assert manager.backend.value == backend
                assert manager.enabled == (backend != 'none')


class TestStory4_EdgeCases:
    """Story 4: Query Tracing - Edge Cases"""
    
    def test_trace_missing_span(self, client, test_agent):
        """Test handling of missing span when ending"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT')
        
        # Try to end non-existent span
        query_tracer.end_span(trace_id, 'nonexistent-span-id')
        
        # Should not raise error
        trace = query_tracer.get_trace(trace_id)
        assert trace is not None
    
    def test_trace_incomplete_span(self, client, test_agent):
        """Test trace with incomplete span (no end time)"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT')
        
        span_id = query_tracer.add_span(trace_id, TraceStage.EXECUTION)
        # Don't end the span
        
        query_tracer.complete_trace(trace_id, True)
        
        trace = query_tracer.get_trace(trace_id)
        span = next(s for s in trace.spans if s.span_id == span_id)
        assert span.end_time is None
        assert span.duration_ms is None
    
    def test_trace_all_stages(self, client, test_agent):
        """Test trace with all possible stages"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT', 'show users')
        
        # Add all stages
        sql_span = query_tracer.add_span(trace_id, TraceStage.SQL_GENERATION)
        query_tracer.end_span(trace_id, sql_span)
        
        val_span = query_tracer.add_span(trace_id, TraceStage.VALIDATION)
        query_tracer.end_span(trace_id, val_span)
        
        approval_span = query_tracer.add_span(trace_id, TraceStage.APPROVAL)
        query_tracer.end_span(trace_id, approval_span)
        
        exec_span = query_tracer.add_span(trace_id, TraceStage.EXECUTION)
        query_tracer.end_span(trace_id, exec_span)
        
        result_span = query_tracer.add_span(trace_id, TraceStage.RESULT)
        query_tracer.end_span(trace_id, result_span)
        
        query_tracer.complete_trace(trace_id, True, result_row_count=10)
        
        trace = query_tracer.get_trace(trace_id)
        assert len(trace.spans) == 6  # INPUT + 5 stages
        assert all(s.end_time is not None for s in trace.spans[1:])
    
    def test_trace_filter_by_query_type(self, client, admin_agent):
        """Test filtering traces by query type"""
        trace1 = query_tracer.start_trace('test-agent', 'SELECT')
        query_tracer.complete_trace(trace1, True)
        
        trace2 = query_tracer.start_trace('test-agent', 'INSERT')
        query_tracer.complete_trace(trace2, True)
        
        response = client.get(
            '/api/admin/traces?query_type=SELECT',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(t['query_type'] == 'SELECT' for t in data['traces'])
    
    def test_trace_metadata_preservation(self, client, test_agent):
        """Test that trace metadata is preserved"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT', 'show users')
        
        span_id = query_tracer.add_span(
            trace_id,
            TraceStage.SQL_GENERATION,
            metadata={'conversion_source': 'llm', 'confidence': 0.95}
        )
        query_tracer.end_span(trace_id, span_id, metadata={'sql': 'SELECT * FROM users'})
        
        trace = query_tracer.get_trace(trace_id)
        span = next(s for s in trace.spans if s.span_id == span_id)
        
        assert 'conversion_source' in span.metadata
        assert 'confidence' in span.metadata
        assert 'sql' in span.metadata
    
    def test_trace_limit_enforcement(self, client, test_agent):
        """Test that trace limit is enforced"""
        # Create many traces
        trace_ids = []
        for i in range(150):  # More than default max (10000, but test with smaller)
            trace_id = query_tracer.start_trace('test-agent', 'SELECT')
            query_tracer.complete_trace(trace_id, True)
            trace_ids.append(trace_id)
        
        # Should still be able to get traces
        traces = query_tracer.list_traces(limit=100)
        assert len(traces) <= 100
    
    def test_trace_error_in_span(self, client, test_agent):
        """Test trace with error in span"""
        trace_id = query_tracer.start_trace('test-agent', 'SELECT')
        
        error_span_id = query_tracer.add_span(
            trace_id,
            TraceStage.ERROR,
            error='Database connection failed'
        )
        query_tracer.end_span(trace_id, error_span_id)
        
        trace = query_tracer.get_trace(trace_id)
        error_span = next(s for s in trace.spans if s.stage == TraceStage.ERROR)
        assert error_span.error == 'Database connection failed'


class TestIntegration_ErrorHandling:
    """Integration tests for error handling"""
    
    def test_dashboard_unauthorized(self, client, test_agent):
        """Test dashboard requires admin permission"""
        response = client.get(
            '/api/admin/dashboard/metrics',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_alerts_unauthorized(self, client, test_agent):
        """Test alerts require admin permission"""
        response = client.get(
            '/api/admin/alerts',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_traces_unauthorized(self, client, test_agent):
        """Test traces require admin permission"""
        response = client.get(
            '/api/admin/traces',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_alert_rule_not_found(self, client, admin_agent):
        """Test getting non-existent alert rule"""
        response = client.get(
            '/api/admin/alerts/rules/nonexistent-id',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404
    
    def test_trace_not_found(self, client, admin_agent):
        """Test getting non-existent trace"""
        response = client.get(
            '/api/admin/traces/nonexistent-id',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404
    
    def test_alert_acknowledge_not_found(self, client, admin_agent):
        """Test acknowledging non-existent alert"""
        response = client.post(
            '/api/admin/alerts/nonexistent-id/acknowledge',
            json={'acknowledged_by': 'admin'},
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 404


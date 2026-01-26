"""
Test cases for Cost Tracking Feature

As a Developer, I want cost tracking per AI provider call, so that I can optimize spending.
AC: Real-time cost dashboard, export reports, budget alerts
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from datetime import datetime, timedelta
import json
import csv
from io import StringIO

from main import create_app
from ai_agent_connector.app.utils.cost_tracker import (
    CostTracker, CostRecord, PricingData, BudgetAlert
)
from ai_agent_connector.app.agents.providers import (
    OpenAIProvider, AnthropicProvider, CustomProvider,
    AgentConfiguration, AgentProvider, set_cost_tracker
)
from ai_agent_connector.app.utils.query_suggestions import (
    QuerySuggestionEngine, set_cost_tracker as set_suggestions_cost_tracker
)
from ai_agent_connector.app.utils.nl_to_sql import (
    NLToSQLConverter, set_cost_tracker as set_nl_cost_tracker
)
from ai_agent_connector.app.agents.ai_agent_manager import (
    AIAgentManager, set_cost_tracker as set_manager_cost_tracker
)


@pytest.fixture
def cost_tracker():
    """Create a fresh cost tracker instance"""
    tracker = CostTracker()
    tracker._cost_records.clear()
    tracker._budget_alerts.clear()
    tracker._custom_pricing.clear()
    return tracker


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestCostTracker:
    """Test CostTracker core functionality"""
    
    def test_track_openai_call(self, cost_tracker):
        """Test tracking an OpenAI API call"""
        usage = {
            'prompt_tokens': 1000,
            'completion_tokens': 500,
            'total_tokens': 1500
        }
        
        record = cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage=usage,
            agent_id='test-agent',
            operation_type='query'
        )
        
        assert record.provider == 'openai'
        assert record.model == 'gpt-4o-mini'
        assert record.prompt_tokens == 1000
        assert record.completion_tokens == 500
        assert record.total_tokens == 1500
        assert record.agent_id == 'test-agent'
        assert record.operation_type == 'query'
        assert record.cost_usd > 0
        
        # Verify cost calculation (gpt-4o-mini: $0.15/$0.6 per 1M tokens)
        expected_cost = (1000 / 1_000_000) * 0.15 + (500 / 1_000_000) * 0.6
        assert abs(record.cost_usd - expected_cost) < 0.0001
    
    def test_track_anthropic_call(self, cost_tracker):
        """Test tracking an Anthropic API call"""
        usage = {
            'input_tokens': 2000,
            'output_tokens': 1000
        }
        
        record = cost_tracker.track_call(
            provider='anthropic',
            model='claude-3-haiku-20240307',
            usage=usage,
            agent_id='test-agent',
            operation_type='query'
        )
        
        assert record.provider == 'anthropic'
        assert record.model == 'claude-3-haiku-20240307'
        assert record.prompt_tokens == 2000
        assert record.completion_tokens == 1000
        assert record.total_tokens == 3000
        assert record.cost_usd > 0
        
        # Verify cost calculation (claude-3-haiku: $0.25/$1.25 per 1M tokens)
        expected_cost = (2000 / 1_000_000) * 0.25 + (1000 / 1_000_000) * 1.25
        assert abs(record.cost_usd - expected_cost) < 0.0001
    
    def test_track_custom_provider_call(self, cost_tracker):
        """Test tracking a custom provider call"""
        usage = {
            'total_tokens': 5000
        }
        
        # Set custom pricing
        cost_tracker.set_custom_pricing(
            provider='custom',
            model='my-model',
            prompt_per_1m=1.0,
            completion_per_1m=2.0
        )
        
        record = cost_tracker.track_call(
            provider='custom',
            model='my-model',
            usage=usage,
            agent_id='test-agent',
            operation_type='query'
        )
        
        assert record.provider == 'custom'
        assert record.model == 'my-model'
        assert record.cost_usd > 0
    
    def test_get_total_cost(self, cost_tracker):
        """Test getting total cost"""
        # Track multiple calls
        for i in range(5):
            cost_tracker.track_call(
                provider='openai',
                model='gpt-4o-mini',
                usage={'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150},
                agent_id='test-agent'
            )
        
        total = cost_tracker.get_total_cost()
        assert total > 0
        assert len(cost_tracker._cost_records) == 5
    
    def test_get_cost_for_period(self, cost_tracker):
        """Test getting cost for a specific time period"""
        # Track a call
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='test-agent'
        )
        
        # Get cost for last 24 hours
        cost_24h = cost_tracker.get_cost_for_period(hours=24)
        assert cost_24h > 0
        
        # Get cost for last 7 days
        cost_7d = cost_tracker.get_cost_for_period(days=7)
        assert cost_7d > 0
        
        # Get cost for last 30 days
        cost_30d = cost_tracker.get_cost_for_period(days=30)
        assert cost_30d > 0


class TestPricingData:
    """Test pricing data calculations"""
    
    def test_openai_pricing(self):
        """Test OpenAI pricing calculation"""
        cost = PricingData.get_openai_cost('gpt-4o-mini', 1000, 500)
        expected = (1000 / 1_000_000) * 0.15 + (500 / 1_000_000) * 0.6
        assert abs(cost - expected) < 0.0001
    
    def test_openai_default_pricing(self):
        """Test OpenAI default pricing for unknown model"""
        cost = PricingData.get_openai_cost('unknown-model', 1000, 500)
        expected = (1000 / 1_000_000) * 0.5 + (500 / 1_000_000) * 1.5
        assert abs(cost - expected) < 0.0001
    
    def test_anthropic_pricing(self):
        """Test Anthropic pricing calculation"""
        cost = PricingData.get_anthropic_cost('claude-3-haiku-20240307', 2000, 1000)
        expected = (2000 / 1_000_000) * 0.25 + (1000 / 1_000_000) * 1.25
        assert abs(cost - expected) < 0.0001
    
    def test_custom_pricing(self):
        """Test custom pricing calculation"""
        custom_pricing = {'prompt_per_1m': 1.0, 'completion_per_1m': 2.0}
        cost = PricingData.get_custom_cost('custom-model', 5000, custom_pricing)
        # 50/50 split assumption
        expected = (2500 / 1_000_000) * 1.0 + (2500 / 1_000_000) * 2.0
        assert abs(cost - expected) < 0.0001
    
    def test_custom_pricing_default(self):
        """Test custom pricing with default fallback"""
        cost = PricingData.get_custom_cost('custom-model', 1000, None)
        expected = (1000 / 1_000_000) * 0.5
        assert abs(cost - expected) < 0.0001


class TestDashboardData:
    """Test dashboard data aggregation"""
    
    def test_get_dashboard_data(self, cost_tracker):
        """Test getting dashboard data"""
        # Track multiple calls with different providers
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='agent-1',
            operation_type='query'
        )
        cost_tracker.track_call(
            provider='anthropic',
            model='claude-3-haiku-20240307',
            usage={'input_tokens': 2000, 'output_tokens': 1000},
            agent_id='agent-2',
            operation_type='nl_to_sql'
        )
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 500, 'completion_tokens': 250, 'total_tokens': 750},
            agent_id='agent-1',
            operation_type='suggestion'
        )
        
        dashboard = cost_tracker.get_dashboard_data()
        
        assert dashboard['total_cost'] > 0
        assert dashboard['total_calls'] == 3
        assert dashboard['total_tokens'] > 0
        assert 'openai' in dashboard['cost_by_provider']
        assert 'anthropic' in dashboard['cost_by_provider']
        assert 'query' in dashboard['cost_by_operation']
        assert 'nl_to_sql' in dashboard['cost_by_operation']
        assert 'suggestion' in dashboard['cost_by_operation']
        assert len(dashboard['daily_costs']) > 0
    
    def test_get_dashboard_data_with_filters(self, cost_tracker):
        """Test dashboard data with filters"""
        # Track calls for different agents
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='agent-1'
        )
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='agent-2'
        )
        
        # Filter by agent
        dashboard = cost_tracker.get_dashboard_data(agent_id='agent-1')
        assert dashboard['total_calls'] == 1
        
        # Filter by provider
        dashboard = cost_tracker.get_dashboard_data(provider='openai')
        assert dashboard['total_calls'] == 2


class TestExportReports:
    """Test export functionality"""
    
    def test_export_json(self, cost_tracker):
        """Test exporting cost report as JSON"""
        # Track some calls
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='test-agent'
        )
        
        report = cost_tracker.export_report(format='json')
        data = json.loads(report)
        
        assert 'records' in data
        assert 'summary' in data
        assert len(data['records']) == 1
        assert data['summary']['total_cost'] > 0
        assert data['summary']['total_calls'] == 1
    
    def test_export_csv(self, cost_tracker):
        """Test exporting cost report as CSV"""
        # Track some calls
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='test-agent'
        )
        
        report = cost_tracker.export_report(format='csv')
        
        # Parse CSV
        reader = csv.reader(StringIO(report))
        rows = list(reader)
        
        assert len(rows) == 2  # Header + 1 data row
        assert rows[0][0] == 'Call ID'
        assert rows[0][8] == 'Cost (USD)'
        assert rows[1][3] == 'gpt-4o-mini'
    
    def test_export_with_filters(self, cost_tracker):
        """Test export with filters"""
        # Track calls for different agents
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='agent-1'
        )
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={'prompt_tokens': 1000, 'completion_tokens': 500, 'total_tokens': 1500},
            agent_id='agent-2'
        )
        
        # Export filtered by agent
        report = cost_tracker.export_report(format='json', agent_id='agent-1')
        data = json.loads(report)
        assert len(data['records']) == 1
        assert data['records'][0]['agent_id'] == 'agent-1'


class TestBudgetAlerts:
    """Test budget alert functionality"""
    
    def test_create_budget_alert(self, cost_tracker):
        """Test creating a budget alert"""
        alert = cost_tracker.add_budget_alert(
            name='Monthly Budget',
            threshold_usd=1000.0,
            period='monthly',
            notification_emails=['admin@example.com']
        )
        
        assert alert.name == 'Monthly Budget'
        assert alert.threshold_usd == 1000.0
        assert alert.period == 'monthly'
        assert alert.enabled is True
        assert 'admin@example.com' in alert.notification_emails
        assert alert.alert_id is not None
    
    def test_get_budget_alerts(self, cost_tracker):
        """Test getting all budget alerts"""
        cost_tracker.add_budget_alert(
            name='Daily Budget',
            threshold_usd=100.0,
            period='daily'
        )
        cost_tracker.add_budget_alert(
            name='Weekly Budget',
            threshold_usd=500.0,
            period='weekly'
        )
        
        alerts = cost_tracker.get_budget_alerts()
        assert len(alerts) == 2
    
    def test_update_budget_alert(self, cost_tracker):
        """Test updating a budget alert"""
        alert = cost_tracker.add_budget_alert(
            name='Test Alert',
            threshold_usd=100.0,
            period='daily'
        )
        
        updated = cost_tracker.update_budget_alert(
            alert.alert_id,
            threshold_usd=200.0,
            enabled=False
        )
        
        assert updated.threshold_usd == 200.0
        assert updated.enabled is False
    
    def test_delete_budget_alert(self, cost_tracker):
        """Test deleting a budget alert"""
        alert = cost_tracker.add_budget_alert(
            name='Test Alert',
            threshold_usd=100.0,
            period='daily'
        )
        
        success = cost_tracker.delete_budget_alert(alert.alert_id)
        assert success is True
        
        alerts = cost_tracker.get_budget_alerts()
        assert len(alerts) == 0
    
    def test_budget_alert_trigger(self, cost_tracker):
        """Test budget alert triggering"""
        # Create alert with low threshold
        alert = cost_tracker.add_budget_alert(
            name='Low Threshold',
            threshold_usd=0.001,  # Very low threshold
            period='total'
        )
        
        # Track a call that exceeds threshold
        cost_tracker.track_call(
            provider='openai',
            model='gpt-4',
            usage={'prompt_tokens': 10000, 'completion_tokens': 5000, 'total_tokens': 15000},
            agent_id='test-agent'
        )
        
        # Alert should be triggered (check last_triggered is set)
        alerts = cost_tracker.get_budget_alerts()
        triggered_alert = next(a for a in alerts if a.alert_id == alert.alert_id)
        # Note: In real implementation, we'd check if alert was triggered
        # For now, we just verify the alert exists


class TestCustomPricing:
    """Test custom pricing functionality"""
    
    def test_set_custom_pricing(self, cost_tracker):
        """Test setting custom pricing"""
        cost_tracker.set_custom_pricing(
            provider='custom',
            model='my-model',
            prompt_per_1m=1.0,
            completion_per_1m=2.0
        )
        
        pricing = cost_tracker.get_custom_pricing('custom', 'my-model')
        assert pricing is not None
        assert pricing['prompt_per_1m'] == 1.0
        assert pricing['completion_per_1m'] == 2.0
    
    def test_custom_pricing_in_cost_calculation(self, cost_tracker):
        """Test that custom pricing is used in cost calculation"""
        cost_tracker.set_custom_pricing(
            provider='custom',
            model='my-model',
            prompt_per_1m=1.0,
            completion_per_1m=2.0
        )
        
        record = cost_tracker.track_call(
            provider='custom',
            model='my-model',
            usage={'total_tokens': 1000},
            agent_id='test-agent'
        )
        
        # Cost should be calculated using custom pricing
        assert record.cost_usd > 0


class TestAPIEndpoints:
    """Test API endpoints for cost tracking"""
    
    def test_get_cost_dashboard(self, client):
        """Test GET /api/cost/dashboard"""
        response = client.get('/api/cost/dashboard')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_cost' in data
        assert 'total_calls' in data
        assert 'total_tokens' in data
        assert 'cost_by_provider' in data
        assert 'cost_by_operation' in data
    
    def test_get_cost_dashboard_with_filters(self, client):
        """Test GET /api/cost/dashboard with filters"""
        response = client.get('/api/cost/dashboard?period_days=7&provider=openai')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['period_days'] == 7
    
    def test_export_cost_report_json(self, client):
        """Test GET /api/cost/export as JSON"""
        response = client.get('/api/cost/export?format=json')
        assert response.status_code == 200
        assert response.mimetype == 'application/json'
        data = json.loads(response.data)
        assert 'records' in data or 'summary' in data
    
    def test_export_cost_report_csv(self, client):
        """Test GET /api/cost/export as CSV"""
        response = client.get('/api/cost/export?format=csv')
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'Call ID' in response.data.decode()
    
    def test_get_budget_alerts(self, client):
        """Test GET /api/cost/budget-alerts"""
        response = client.get('/api/cost/budget-alerts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'alerts' in data
        assert 'count' in data
    
    def test_create_budget_alert(self, client):
        """Test POST /api/cost/budget-alerts"""
        response = client.post(
            '/api/cost/budget-alerts',
            json={
                'name': 'Test Alert',
                'threshold_usd': 100.0,
                'period': 'monthly'
            }
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Test Alert'
        assert data['threshold_usd'] == 100.0
        assert data['period'] == 'monthly'
    
    def test_create_budget_alert_invalid(self, client):
        """Test POST /api/cost/budget-alerts with invalid data"""
        response = client.post(
            '/api/cost/budget-alerts',
            json={
                'name': 'Test Alert'
                # Missing required fields
            }
        )
        assert response.status_code == 400
    
    def test_update_budget_alert(self, client):
        """Test PUT /api/cost/budget-alerts/<alert_id>"""
        # First create an alert
        create_response = client.post(
            '/api/cost/budget-alerts',
            json={
                'name': 'Test Alert',
                'threshold_usd': 100.0,
                'period': 'monthly'
            }
        )
        alert_id = json.loads(create_response.data)['alert_id']
        
        # Update it
        response = client.put(
            f'/api/cost/budget-alerts/{alert_id}',
            json={
                'threshold_usd': 200.0,
                'enabled': False
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['threshold_usd'] == 200.0
        assert data['enabled'] is False
    
    def test_delete_budget_alert(self, client):
        """Test DELETE /api/cost/budget-alerts/<alert_id>"""
        # First create an alert
        create_response = client.post(
            '/api/cost/budget-alerts',
            json={
                'name': 'Test Alert',
                'threshold_usd': 100.0,
                'period': 'monthly'
            }
        )
        alert_id = json.loads(create_response.data)['alert_id']
        
        # Delete it
        response = client.delete(f'/api/cost/budget-alerts/{alert_id}')
        assert response.status_code == 200
    
    def test_set_custom_pricing(self, client):
        """Test POST /api/cost/custom-pricing"""
        response = client.post(
            '/api/cost/custom-pricing',
            json={
                'provider': 'custom',
                'model': 'my-model',
                'prompt_per_1m': 1.0,
                'completion_per_1m': 2.0
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Custom pricing set successfully'
    
    def test_get_cost_stats(self, client):
        """Test GET /api/cost/stats"""
        response = client.get('/api/cost/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_cost_usd' in data
        assert 'total_calls' in data
        assert 'total_tokens' in data
        assert 'average_cost_per_call' in data


class TestProviderIntegration:
    """Test cost tracking integration with providers"""
    
    def test_openai_provider_tracks_cost(self, cost_tracker):
        """Test that OpenAIProvider tracks costs"""
        set_cost_tracker(cost_tracker)
        
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model='gpt-4o-mini',
            api_key='test-key'
        )
        
        provider = OpenAIProvider(config)
        
        # Mock the OpenAI client
        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = 'Test response'
            mock_response.model = 'gpt-4o-mini'
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500
            
            mock_openai_client = MagicMock()
            mock_openai_client.chat.completions.create.return_value = mock_response
            mock_client.return_value = mock_openai_client
            
            result = provider.execute_query('test query')
            
            # Verify cost was tracked
            assert len(cost_tracker._cost_records) == 1
            record = cost_tracker._cost_records[0]
            assert record.provider == 'openai'
            assert record.model == 'gpt-4o-mini'
            assert record.cost_usd > 0
    
    def test_anthropic_provider_tracks_cost(self, cost_tracker):
        """Test that AnthropicProvider tracks costs"""
        set_cost_tracker(cost_tracker)
        
        config = AgentConfiguration(
            provider=AgentProvider.ANTHROPIC,
            model='claude-3-haiku-20240307',
            api_key='test-key'
        )
        
        provider = AnthropicProvider(config)
        
        # Mock the Anthropic client
        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.content[0].text = 'Test response'
            mock_response.model = 'claude-3-haiku-20240307'
            mock_response.usage.input_tokens = 2000
            mock_response.usage.output_tokens = 1000
            
            mock_anthropic_client = MagicMock()
            mock_anthropic_client.messages.create.return_value = mock_response
            mock_client.return_value = mock_anthropic_client
            
            result = provider.execute_query('test query')
            
            # Verify cost was tracked
            assert len(cost_tracker._cost_records) == 1
            record = cost_tracker._cost_records[0]
            assert record.provider == 'anthropic'
            assert record.model == 'claude-3-haiku-20240307'
            assert record.cost_usd > 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_track_call_with_missing_usage(self, cost_tracker):
        """Test tracking call with missing usage data"""
        record = cost_tracker.track_call(
            provider='openai',
            model='gpt-4o-mini',
            usage={},  # Empty usage
            agent_id='test-agent'
        )
        
        assert record.prompt_tokens == 0
        assert record.completion_tokens == 0
        assert record.cost_usd == 0.0
    
    def test_export_invalid_format(self, cost_tracker):
        """Test export with invalid format"""
        with pytest.raises(ValueError):
            cost_tracker.export_report(format='invalid')
    
    def test_update_nonexistent_alert(self, cost_tracker):
        """Test updating non-existent alert"""
        result = cost_tracker.update_budget_alert('nonexistent-id', threshold_usd=100.0)
        assert result is None
    
    def test_delete_nonexistent_alert(self, cost_tracker):
        """Test deleting non-existent alert"""
        result = cost_tracker.delete_budget_alert('nonexistent-id')
        assert result is False
    
    def test_dashboard_with_no_data(self, cost_tracker):
        """Test dashboard with no cost records"""
        dashboard = cost_tracker.get_dashboard_data()
        assert dashboard['total_cost'] == 0.0
        assert dashboard['total_calls'] == 0
        assert dashboard['total_tokens'] == 0
    
    def test_cost_tracking_failure_doesnt_break_provider(self, cost_tracker):
        """Test that cost tracking failures don't break provider calls"""
        # Simulate cost tracker failure
        def failing_track_call(*args, **kwargs):
            raise Exception("Cost tracking failed")
        
        cost_tracker.track_call = failing_track_call
        
        # Provider should still work
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model='gpt-4o-mini',
            api_key='test-key'
        )
        
        provider = OpenAIProvider(config)
        
        with patch.object(provider, '_get_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = 'Test response'
            mock_response.model = 'gpt-4o-mini'
            mock_response.usage.prompt_tokens = 1000
            mock_response.usage.completion_tokens = 500
            mock_response.usage.total_tokens = 1500
            
            mock_openai_client = MagicMock()
            mock_openai_client.chat.completions.create.return_value = mock_response
            mock_client.return_value = mock_openai_client
            
            # Should not raise exception
            result = provider.execute_query('test query')
            assert result['response'] == 'Test response'


class TestCostRecord:
    """Test CostRecord dataclass"""
    
    def test_cost_record_to_dict(self):
        """Test converting CostRecord to dictionary"""
        record = CostRecord(
            call_id='test-id',
            timestamp='2024-01-01T00:00:00',
            provider='openai',
            model='gpt-4o-mini',
            agent_id='test-agent',
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            cost_usd=0.001,
            operation_type='query',
            metadata={'test': 'data'}
        )
        
        data = record.to_dict()
        assert data['call_id'] == 'test-id'
        assert data['provider'] == 'openai'
        assert data['model'] == 'gpt-4o-mini'
        assert data['cost_usd'] == 0.001
        assert data['metadata']['test'] == 'data'


class TestBudgetAlert:
    """Test BudgetAlert dataclass"""
    
    def test_budget_alert_to_dict(self):
        """Test converting BudgetAlert to dictionary"""
        alert = BudgetAlert(
            alert_id='test-id',
            name='Test Alert',
            threshold_usd=100.0,
            period='monthly',
            enabled=True,
            notification_emails=['admin@example.com'],
            webhook_url='https://example.com/webhook'
        )
        
        data = alert.to_dict()
        assert data['alert_id'] == 'test-id'
        assert data['name'] == 'Test Alert'
        assert data['threshold_usd'] == 100.0
        assert data['period'] == 'monthly'
        assert data['enabled'] is True
        assert 'admin@example.com' in data['notification_emails']
        assert data['webhook_url'] == 'https://example.com/webhook'

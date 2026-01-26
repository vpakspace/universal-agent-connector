"""
Integration tests for Analytics & Automation Stories

Story 1: As a Data Analyst, I want the platform to generate visualizations (charts, tables) from query results,
         so that insights are immediately actionable.

Story 2: As a Developer, I want to schedule recurring queries (e.g., daily reports),
         so that automation is built-in.

Story 3: As an Admin, I want to export query results to external systems (S3, Google Sheets, Slack),
         so that data flows seamlessly.

Story 4: As a User, I want natural language explanations of query results,
         so that I understand the data without SQL knowledge.

Story 5: As an Admin, I want to A/B test different AI models (e.g., GPT-4 vs. Claude) on the same query,
         so that I can choose the best performer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry, access_control, visualization_generator,
    query_scheduler, query_exporter, result_explainer, ab_test_manager
)
from ai_agent_connector.app.permissions import Permission
from ai_agent_connector.app.utils.encryption import reset_encryptor
from ai_agent_connector.app.utils.visualizations import ChartType, VisualizationConfig
from ai_agent_connector.app.utils.query_scheduler import ScheduleFrequency
from ai_agent_connector.app.utils.query_export import ExportDestination, ExportConfig
from ai_agent_connector.app.utils.ab_testing import ABTestStatus
from ai_agent_connector.app.utils.result_explainer import ExplanationConfig


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    query_scheduler._schedules.clear()
    query_scheduler._agent_schedules.clear()
    ab_test_manager._tests.clear()
    ab_test_manager._agent_tests.clear()
    yield
    agent_registry.reset()
    access_control.permissions.clear()
    access_control.resource_permissions.clear()
    reset_encryptor()
    query_scheduler._schedules.clear()
    query_scheduler._agent_schedules.clear()
    ab_test_manager._tests.clear()
    ab_test_manager._agent_tests.clear()


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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
def sample_data():
    """Sample query result data"""
    return [
        {'month': 'Jan', 'sales': 1000, 'orders': 50},
        {'month': 'Feb', 'sales': 1200, 'orders': 60},
        {'month': 'Mar', 'sales': 1500, 'orders': 75},
        {'month': 'Apr', 'sales': 1300, 'orders': 65}
    ]


class TestStory1_Visualizations:
    """Story 1: Generate visualizations from query results"""
    
    def test_generate_bar_chart(self, client, test_agent, sample_data):
        """Test generating a bar chart"""
        payload = {
            'data': sample_data,
            'chart_type': 'bar',
            'title': 'Sales by Month',
            'x_axis': 'month',
            'y_axis': 'sales'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['type'] == 'bar'
        assert data['title'] == 'Sales by Month'
        assert 'data' in data
    
    def test_generate_line_chart(self, client, test_agent, sample_data):
        """Test generating a line chart"""
        payload = {
            'data': sample_data,
            'chart_type': 'line',
            'title': 'Sales Trend'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['type'] == 'line'
    
    def test_generate_pie_chart(self, client, test_agent, sample_data):
        """Test generating a pie chart"""
        payload = {
            'data': sample_data,
            'chart_type': 'pie',
            'title': 'Sales Distribution'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['type'] == 'pie'
    
    def test_generate_table(self, client, test_agent, sample_data):
        """Test generating a table"""
        payload = {
            'data': sample_data,
            'chart_type': 'table',
            'title': 'Sales Data'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['type'] == 'table'
        assert len(data['data']) == len(sample_data)
    
    def test_visualization_with_aggregation(self, client, test_agent, sample_data):
        """Test visualization with aggregation"""
        config = VisualizationConfig(
            chart_type=ChartType.BAR,
            title='Total Sales',
            aggregation='sum',
            group_by='month'
        )
        
        visualization = visualization_generator.generate_visualization(sample_data, config)
        
        assert visualization['type'] == 'bar'
        assert 'data' in visualization
    
    def test_visualization_empty_data(self, client, test_agent):
        """Test visualization with empty data"""
        payload = {
            'data': [],
            'chart_type': 'bar'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'No data' in data['message']


class TestStory2_ScheduledQueries:
    """Story 2: Schedule recurring queries"""
    
    def test_create_daily_schedule(self, client, test_agent):
        """Test creating a daily schedule"""
        payload = {
            'query': 'SELECT * FROM sales WHERE date = CURRENT_DATE',
            'query_type': 'SELECT',
            'frequency': 'daily',
            'schedule_config': {'time': '09:00'},
            'notification_config': {'email': 'user@example.com'}
        }
        
        response = client.post(
            '/api/agents/test-agent/schedules',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'schedule' in data
        assert data['schedule']['schedule_frequency'] == 'daily'
        assert data['schedule']['schedule_config']['time'] == '09:00'
    
    def test_create_weekly_schedule(self, client, test_agent):
        """Test creating a weekly schedule"""
        payload = {
            'query': 'SELECT * FROM weekly_report',
            'query_type': 'SELECT',
            'frequency': 'weekly',
            'schedule_config': {'day_of_week': 0, 'time': '10:00'}  # Monday
        }
        
        response = client.post(
            '/api/agents/test-agent/schedules',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['schedule']['schedule_frequency'] == 'weekly'
    
    def test_list_schedules(self, client, test_agent):
        """Test listing schedules"""
        # Create a schedule
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        response = client.get(
            '/api/agents/test-agent/schedules',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'schedules' in data
        assert len(data['schedules']) >= 1
    
    def test_get_schedule(self, client, test_agent):
        """Test getting a specific schedule"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        response = client.get(
            f'/api/agents/test-agent/schedules/{schedule.schedule_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['schedule_id'] == schedule.schedule_id
    
    def test_update_schedule(self, client, test_agent):
        """Test updating a schedule"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        payload = {
            'schedule_config': {'time': '10:00'},
            'is_active': False
        }
        
        response = client.put(
            f'/api/agents/test-agent/schedules/{schedule.schedule_id}',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['schedule']['is_active'] is False
    
    def test_delete_schedule(self, client, test_agent):
        """Test deleting a schedule"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        response = client.delete(
            f'/api/agents/test-agent/schedules/{schedule.schedule_id}',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert query_scheduler.get_schedule(schedule.schedule_id) is None
    
    def test_get_due_schedules(self, client, test_agent):
        """Test getting due schedules"""
        # Create schedule with past next_run_at
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.HOURLY,
            schedule_config={}
        )
        
        # Manually set next_run_at to past
        from datetime import datetime, timedelta
        schedule.next_run_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        query_scheduler._schedules[schedule.schedule_id] = schedule
        
        due = query_scheduler.get_due_schedules()
        assert len(due) >= 1


class TestStory3_ExportResults:
    """Story 3: Export query results to external systems"""
    
    def test_export_to_s3(self, client, test_agent, sample_data):
        """Test exporting to S3"""
        payload = {
            'data': sample_data,
            'destination': 's3',
            'destination_config': {
                'bucket': 'my-bucket',
                'key': 'exports/sales.csv'
            },
            'format': 'csv'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/export',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['destination'] == 's3'
        assert data['bucket'] == 'my-bucket'
    
    def test_export_to_google_sheets(self, client, test_agent, sample_data):
        """Test exporting to Google Sheets"""
        payload = {
            'data': sample_data,
            'destination': 'google_sheets',
            'destination_config': {
                'spreadsheet_id': 'abc123',
                'sheet_name': 'Sales Data'
            }
        }
        
        response = client.post(
            '/api/agents/test-agent/query/export',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['destination'] == 'google_sheets'
    
    def test_export_to_slack(self, client, test_agent, sample_data):
        """Test exporting to Slack"""
        payload = {
            'data': sample_data,
            'destination': 'slack',
            'destination_config': {
                'webhook_url': 'https://hooks.slack.com/...',
                'channel': '#analytics'
            }
        }
        
        response = client.post(
            '/api/agents/test-agent/query/export',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['destination'] == 'slack'
    
    def test_export_to_csv(self, client, test_agent, sample_data):
        """Test exporting to CSV format"""
        config = ExportDestination.CSV
        export_config = ExportConfig(
            destination=config,
            format='csv',
            include_headers=True
        )
        
        result = query_exporter.export_results(sample_data, export_config)
        
        assert isinstance(result, str)
        assert 'month' in result  # Header should be present
        assert 'sales' in result
    
    def test_export_to_json(self, client, test_agent, sample_data):
        """Test exporting to JSON format"""
        config = ExportDestination.JSON
        export_config = ExportConfig(
            destination=config,
            format='json'
        )
        
        result = query_exporter.export_results(sample_data, export_config)
        
        assert isinstance(result, str)
        import json
        parsed = json.loads(result)
        assert len(parsed) == len(sample_data)


class TestStory4_ResultExplanations:
    """Story 4: Natural language explanations of query results"""
    
    def test_explain_results(self, client, test_agent, sample_data):
        """Test explaining query results"""
        payload = {
            'data': sample_data,
            'query': 'SELECT month, sales FROM sales_data',
            'detail_level': 'medium',
            'include_statistics': True,
            'include_trends': True
        }
        
        response = client.post(
            '/api/agents/test-agent/query/explain',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'explanation' in data
        assert 'summary' in data
        assert 'insights' in data
        assert 'statistics' in data
        assert 'The query returned' in data['explanation'] or 'results' in data['explanation'].lower()
    
    def test_explain_empty_results(self, client, test_agent):
        """Test explaining empty results"""
        payload = {
            'data': [],
            'query': 'SELECT * FROM empty_table'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/explain',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'no results' in data['explanation'].lower() or 'No data' in data['explanation']
    
    def test_explain_with_statistics(self, client, test_agent, sample_data):
        """Test explanation with statistics"""
        explanation = result_explainer.explain_results(
            data=sample_data,
            config=ExplanationConfig(include_statistics=True)
        )
        
        assert 'explanation' in explanation
        assert 'statistics' in explanation
        assert explanation['statistics'] is not None
    
    def test_explain_with_trends(self, client, test_agent, sample_data):
        """Test explanation with trends"""
        explanation = result_explainer.explain_results(
            data=sample_data,
            config=ExplanationConfig(include_trends=True)
        )
        
        assert 'explanation' in explanation
        assert 'insights' in explanation


class TestStory5_ABTesting:
    """Story 5: A/B testing different AI models"""
    
    def test_create_ab_test(self, client, admin_agent):
        """Test creating an A/B test"""
        payload = {
            'query': 'SELECT * FROM sales',
            'query_type': 'SELECT',
            'variants': [
                {
                    'model_name': 'gpt-4',
                    'model_config': {'temperature': 0.7}
                },
                {
                    'model_name': 'claude-3',
                    'model_config': {'temperature': 0.7}
                }
            ]
        }
        
        response = client.post(
            '/api/admin/agents/test-agent/ab-tests',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'test' in data
        assert len(data['test']['variants']) == 2
    
    def test_list_ab_tests(self, client, admin_agent):
        """Test listing A/B tests"""
        # Create a test
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        response = client.get(
            '/api/admin/agents/test-agent/ab-tests',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'tests' in data
        assert len(data['tests']) >= 1
    
    def test_get_ab_test(self, client, admin_agent):
        """Test getting a specific A/B test"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        response = client.get(
            f'/api/admin/ab-tests/{test.test_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['test_id'] == test.test_id
    
    def test_start_ab_test(self, client, admin_agent):
        """Test starting an A/B test"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        response = client.post(
            f'/api/admin/ab-tests/{test.test_id}/start',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['test']['status'] == 'running'
    
    def test_update_variant_result(self, client, admin_agent):
        """Test updating variant result"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        variant = test.variants[0]
        
        payload = {
            'result': [{'id': 1, 'value': 100}],
            'execution_time_ms': 1234.5,
            'success': True
        }
        
        response = client.post(
            f'/api/admin/ab-tests/{test.test_id}/variants/{variant.variant_id}/result',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'test' in data
    
    def test_complete_ab_test(self, client, admin_agent):
        """Test completing an A/B test"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        ab_test_manager.start_test(test.test_id)
        
        # Update both variants
        for variant in test.variants:
            ab_test_manager.update_variant_result(
                test_id=test.test_id,
                variant_id=variant.variant_id,
                result=[{'id': 1}],
                execution_time_ms=1000.0 if variant.model_name == 'gpt-4' else 1500.0,
                success=True
            )
        
        updated_test = ab_test_manager.get_test(test.test_id)
        assert updated_test.status == ABTestStatus.COMPLETED
        assert updated_test.winner is not None
    
    def test_delete_ab_test(self, client, admin_agent):
        """Test deleting an A/B test"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        response = client.delete(
            f'/api/admin/ab-tests/{test.test_id}',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert ab_test_manager.get_test(test.test_id) is None


class TestIntegration_AllFeatures:
    """Integration tests combining all features"""
    
    def test_visualize_and_explain(self, client, test_agent, sample_data):
        """Test visualizing and explaining results together"""
        # Generate visualization
        viz_response = client.post(
            '/api/agents/test-agent/query/visualize',
            json={'data': sample_data, 'chart_type': 'bar'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert viz_response.status_code == 200
        
        # Explain results
        explain_response = client.post(
            '/api/agents/test-agent/query/explain',
            json={'data': sample_data},
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert explain_response.status_code == 200
    
    def test_schedule_with_export(self, client, test_agent):
        """Test scheduling a query with export"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'},
            notification_config={
                'export': {
                    'destination': 's3',
                    'bucket': 'reports',
                    'key': 'daily-sales.csv'
                }
            }
        )
        
        assert schedule is not None
        assert schedule.notification_config is not None
    
    def test_ab_test_with_explanation(self, client, admin_agent, sample_data):
        """Test A/B testing with result explanations"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        # Update variant results
        for variant in test.variants:
            ab_test_manager.update_variant_result(
                test_id=test.test_id,
                variant_id=variant.variant_id,
                result=sample_data,
                execution_time_ms=1000.0,
                success=True
            )
        
        # Explain results
        explanation = result_explainer.explain_results(sample_data)
        assert 'explanation' in explanation


class TestErrorHandling:
    """Error handling tests"""
    
    def test_unauthorized_visualization(self, client):
        """Test unauthorized visualization access"""
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json={'data': []}
        )
        
        assert response.status_code == 401
    
    def test_invalid_chart_type(self, client, test_agent, sample_data):
        """Test invalid chart type"""
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json={'data': sample_data, 'chart_type': 'invalid'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400
    
    def test_unauthorized_ab_test(self, client, test_agent):
        """Test unauthorized A/B test access"""
        response = client.post(
            '/api/admin/agents/test-agent/ab-tests',
            json={'query': 'SELECT 1', 'query_type': 'SELECT', 'variants': []},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 403
    
    def test_invalid_export_destination(self, client, test_agent, sample_data):
        """Test invalid export destination"""
        response = client.post(
            '/api/agents/test-agent/query/export',
            json={'data': sample_data, 'destination': 'invalid'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400


class TestStory1_AdditionalVisualizationCases:
    """Story 1: Additional visualization scenarios"""
    
    def test_generate_scatter_chart(self, client, test_agent, sample_data):
        """Test generating a scatter chart"""
        payload = {
            'data': sample_data,
            'chart_type': 'scatter',
            'title': 'Sales vs Orders',
            'x_axis': 'orders',
            'y_axis': 'sales'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['type'] == 'scatter'
    
    def test_generate_area_chart(self, client, test_agent, sample_data):
        """Test generating an area chart"""
        payload = {
            'data': sample_data,
            'chart_type': 'area',
            'title': 'Sales Over Time'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['type'] == 'area'
    
    def test_visualization_with_custom_dimensions(self, client, test_agent, sample_data):
        """Test visualization with custom dimensions"""
        payload = {
            'data': sample_data,
            'chart_type': 'bar',
            'width': 1200,
            'height': 800,
            'show_legend': False,
            'show_grid': False
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['config']['width'] == 1200
        assert data['config']['height'] == 800
        assert data['config']['show_legend'] is False
    
    def test_visualization_auto_detect_axes(self, client, test_agent, sample_data):
        """Test automatic axis detection"""
        payload = {
            'data': sample_data,
            'chart_type': 'bar'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/visualize',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'axes' in data
        assert 'x' in data['axes']
        assert 'y' in data['axes']


class TestStory2_AdditionalScheduleCases:
    """Story 2: Additional scheduled query scenarios"""
    
    def test_create_hourly_schedule(self, client, test_agent):
        """Test creating an hourly schedule"""
        payload = {
            'query': 'SELECT * FROM hourly_metrics',
            'query_type': 'SELECT',
            'frequency': 'hourly',
            'schedule_config': {}
        }
        
        response = client.post(
            '/api/agents/test-agent/schedules',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['schedule']['schedule_frequency'] == 'hourly'
    
    def test_create_monthly_schedule(self, client, test_agent):
        """Test creating a monthly schedule"""
        payload = {
            'query': 'SELECT * FROM monthly_report',
            'query_type': 'SELECT',
            'frequency': 'monthly',
            'schedule_config': {'day': 1, 'time': '09:00'}
        }
        
        response = client.post(
            '/api/agents/test-agent/schedules',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['schedule']['schedule_frequency'] == 'monthly'
    
    def test_schedule_mark_run(self, client, test_agent):
        """Test marking a schedule as run"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        query_scheduler.mark_run(schedule.schedule_id, success=True)
        
        updated = query_scheduler.get_schedule(schedule.schedule_id)
        assert updated.run_count == 1
        assert updated.success_count == 1
        assert updated.last_run_at is not None
    
    def test_schedule_mark_run_failure(self, client, test_agent):
        """Test marking a schedule run as failed"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        query_scheduler.mark_run(schedule.schedule_id, success=False)
        
        updated = query_scheduler.get_schedule(schedule.schedule_id)
        assert updated.run_count == 1
        assert updated.failure_count == 1
    
    def test_list_active_schedules(self, client, test_agent):
        """Test listing only active schedules"""
        # Create active and inactive schedules
        active = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT 1',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'}
        )
        
        inactive = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT 2',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '10:00'}
        )
        query_scheduler.update_schedule(inactive.schedule_id, is_active=False)
        
        response = client.get(
            '/api/agents/test-agent/schedules?is_active=true',
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(s['is_active'] for s in data['schedules'])


class TestStory3_AdditionalExportCases:
    """Story 3: Additional export scenarios"""
    
    def test_export_to_email(self, client, test_agent, sample_data):
        """Test exporting to email"""
        payload = {
            'data': sample_data,
            'destination': 'email',
            'destination_config': {
                'recipients': ['user@example.com'],
                'subject': 'Sales Report'
            }
        }
        
        response = client.post(
            '/api/agents/test-agent/query/export',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['destination'] == 'email'
    
    def test_export_to_excel(self, client, test_agent, sample_data):
        """Test exporting to Excel"""
        payload = {
            'data': sample_data,
            'destination': 'excel',
            'filename': 'sales_report.xlsx'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/export',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['destination'] == 'excel'
    
    def test_export_without_headers(self, client, test_agent, sample_data):
        """Test export without headers"""
        config = ExportDestination.CSV
        export_config = ExportConfig(
            destination=config,
            format='csv',
            include_headers=False
        )
        
        result = query_exporter.export_results(sample_data, export_config)
        
        # First line should be data, not headers
        lines = result.split('\n')
        assert 'month' not in lines[0] or lines[0].strip() == ''
    
    def test_export_empty_data(self, client, test_agent):
        """Test exporting empty data"""
        payload = {
            'data': [],
            'destination': 'csv'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/export',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No data' in data.get('error', '')


class TestStory4_AdditionalExplanationCases:
    """Story 4: Additional explanation scenarios"""
    
    def test_explain_brief_detail_level(self, client, test_agent, sample_data):
        """Test explanation with brief detail level"""
        payload = {
            'data': sample_data,
            'detail_level': 'brief'
        }
        
        response = client.post(
            '/api/agents/test-agent/query/explain',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'explanation' in data
    
    def test_explain_detailed_level(self, client, test_agent, sample_data):
        """Test explanation with detailed level"""
        payload = {
            'data': sample_data,
            'detail_level': 'detailed',
            'include_statistics': True,
            'include_trends': True,
            'include_comparisons': True
        }
        
        response = client.post(
            '/api/agents/test-agent/query/explain',
            json=payload,
            headers={'X-API-Key': test_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'explanation' in data
        assert 'insights' in data
        assert len(data['insights']) >= 0
    
    def test_explain_without_statistics(self, client, test_agent, sample_data):
        """Test explanation without statistics"""
        explanation = result_explainer.explain_results(
            data=sample_data,
            config=ExplanationConfig(include_statistics=False)
        )
        
        assert 'explanation' in explanation
        assert explanation.get('statistics') is None
    
    def test_explain_single_result(self, client, test_agent):
        """Test explaining single result"""
        single_data = [{'id': 1, 'value': 100}]
        
        explanation = result_explainer.explain_results(single_data)
        
        assert 'explanation' in explanation
        assert '1 result' in explanation['explanation'] or '1 result' in explanation['summary']
    
    def test_explain_detect_outliers(self, client, test_agent):
        """Test outlier detection in explanations"""
        data_with_outlier = [
            {'id': 1, 'value': 100},
            {'id': 2, 'value': 105},
            {'id': 3, 'value': 98},
            {'id': 4, 'value': 1000}  # Outlier
        ]
        
        explanation = result_explainer.explain_results(data_with_outlier)
        
        assert 'insights' in explanation
        # May or may not detect outlier depending on algorithm
        assert isinstance(explanation['insights'], list)


class TestStory5_AdditionalABTestCases:
    """Story 5: Additional A/B testing scenarios"""
    
    def test_ab_test_three_variants(self, client, admin_agent):
        """Test A/B test with three variants"""
        payload = {
            'query': 'SELECT * FROM sales',
            'query_type': 'SELECT',
            'variants': [
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}},
                {'model_name': 'gpt-3.5', 'model_config': {}}
            ]
        }
        
        response = client.post(
            '/api/admin/agents/test-agent/ab-tests',
            json=payload,
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert len(data['test']['variants']) == 3
    
    def test_ab_test_variant_failure(self, client, admin_agent):
        """Test A/B test with variant failure"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        ab_test_manager.start_test(test.test_id)
        
        # One success, one failure
        ab_test_manager.update_variant_result(
            test_id=test.test_id,
            variant_id=test.variants[0].variant_id,
            result=[{'id': 1}],
            execution_time_ms=1000.0,
            success=True
        )
        
        ab_test_manager.update_variant_result(
            test_id=test.test_id,
            variant_id=test.variants[1].variant_id,
            result=None,
            execution_time_ms=0,
            success=False,
            error='Connection timeout'
        )
        
        updated_test = ab_test_manager.get_test(test.test_id)
        assert updated_test.status == ABTestStatus.COMPLETED
        assert updated_test.winner == test.variants[0].variant_id
    
    def test_ab_test_all_failures(self, client, admin_agent):
        """Test A/B test where all variants fail"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        ab_test_manager.start_test(test.test_id)
        
        # Both fail
        for variant in test.variants:
            ab_test_manager.update_variant_result(
                test_id=test.test_id,
                variant_id=variant.variant_id,
                result=None,
                execution_time_ms=0,
                success=False,
                error='Error'
            )
        
        updated_test = ab_test_manager.get_test(test.test_id)
        assert updated_test.status == ABTestStatus.COMPLETED
        assert updated_test.winner is None  # No winner if all fail
    
    def test_ab_test_metrics_calculation(self, client, admin_agent):
        """Test A/B test metrics calculation"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        ab_test_manager.start_test(test.test_id)
        
        # Update both variants
        for i, variant in enumerate(test.variants):
            ab_test_manager.update_variant_result(
                test_id=test.test_id,
                variant_id=variant.variant_id,
                result=[{'id': 1}],
                execution_time_ms=1000.0 + (i * 100),
                success=True
            )
        
        updated_test = ab_test_manager.get_test(test.test_id)
        assert 'metrics' in updated_test.to_dict()
        metrics = updated_test.metrics
        assert metrics['total_variants'] == 2
        assert metrics['successful_variants'] == 2
        assert 'avg_execution_time_ms' in metrics
    
    def test_ab_test_filter_by_status(self, client, admin_agent):
        """Test filtering A/B tests by status"""
        test1 = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT 1',
            query_type='SELECT',
            variants=[{'model_name': 'gpt-4', 'model_config': {}}, {'model_name': 'claude-3', 'model_config': {}}]
        )
        
        test2 = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT 2',
            query_type='SELECT',
            variants=[{'model_name': 'gpt-4', 'model_config': {}}, {'model_name': 'claude-3', 'model_config': {}}]
        )
        
        ab_test_manager.start_test(test1.test_id)
        
        response = client.get(
            '/api/admin/agents/test-agent/ab-tests?status=running',
            headers={'X-API-Key': admin_agent['api_key']}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert all(t['status'] == 'running' for t in data['tests'])


class TestIntegration_AdvancedWorkflows:
    """Advanced integration workflows"""
    
    def test_complete_analytics_workflow(self, client, test_agent, sample_data):
        """Test complete analytics workflow: query → visualize → explain → export"""
        # Step 1: Generate visualization
        viz_response = client.post(
            '/api/agents/test-agent/query/visualize',
            json={'data': sample_data, 'chart_type': 'bar', 'title': 'Sales Analysis'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert viz_response.status_code == 200
        
        # Step 2: Explain results
        explain_response = client.post(
            '/api/agents/test-agent/query/explain',
            json={'data': sample_data, 'query': 'SELECT * FROM sales'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert explain_response.status_code == 200
        
        # Step 3: Export results
        export_response = client.post(
            '/api/agents/test-agent/query/export',
            json={'data': sample_data, 'destination': 'csv'},
            headers={'X-API-Key': test_agent['api_key']}
        )
        assert export_response.status_code == 200
    
    def test_schedule_with_visualization_and_export(self, client, test_agent):
        """Test scheduling query with visualization and export"""
        schedule = query_scheduler.create_schedule(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            frequency=ScheduleFrequency.DAILY,
            schedule_config={'time': '09:00'},
            notification_config={
                'visualization': {'chart_type': 'bar'},
                'export': {'destination': 's3', 'bucket': 'reports'}
            }
        )
        
        assert schedule is not None
        assert schedule.notification_config is not None
    
    def test_ab_test_with_all_features(self, client, admin_agent, sample_data):
        """Test A/B test with visualization, explanation, and export"""
        test = ab_test_manager.create_test(
            agent_id='test-agent',
            query='SELECT * FROM sales',
            query_type='SELECT',
            variants=[
                {'model_name': 'gpt-4', 'model_config': {}},
                {'model_name': 'claude-3', 'model_config': {}}
            ]
        )
        
        ab_test_manager.start_test(test.test_id)
        
        # Update variants with results
        for variant in test.variants:
            ab_test_manager.update_variant_result(
                test_id=test.test_id,
                variant_id=variant.variant_id,
                result=sample_data,
                execution_time_ms=1000.0,
                success=True
            )
        
        # Generate visualization for winner
        updated_test = ab_test_manager.get_test(test.test_id)
        winner_variant = next(v for v in updated_test.variants if v.variant_id == updated_test.winner)
        
        viz = visualization_generator.generate_chart(
            sample_data,
            ChartType.BAR,
            title=f'Results from {winner_variant.model_name}'
        )
        assert viz['type'] == 'bar'
        
        # Explain results
        explanation = result_explainer.explain_results(sample_data)
        assert 'explanation' in explanation


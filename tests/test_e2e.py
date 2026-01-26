"""
End-to-end tests for AI Agent Connector
Tests complete user workflows from API to database
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry,
    ai_agent_manager,
    cost_tracker,
    audit_logger
)


@pytest.fixture
def app():
    """Create Flask app for E2E testing"""
    app = create_app('testing')
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    agent_registry.reset()
    cost_tracker._cost_records.clear()
    cost_tracker._budget_alerts.clear()
    audit_logger._logs.clear()
    yield
    agent_registry.reset()
    cost_tracker._cost_records.clear()
    cost_tracker._budget_alerts.clear()
    audit_logger._logs.clear()


@pytest.mark.e2e
class TestE2EAgentLifecycle:
    """E2E tests for complete agent lifecycle"""
    
    def test_agent_lifecycle_complete(self, client):
        """Test complete agent lifecycle: register -> use -> monitor -> delete"""
        agent_id = 'e2e-lifecycle-agent'
        
        # 1. Register agent
        response = client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {
                'api_key': 'test-key',
                'api_secret': 'test-secret'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_pass'
            }
        })
        assert response.status_code == 201
        api_key = response.get_json()['api_key']
        
        # 2. Get agent info
        response = client.get(f'/api/agents/{agent_id}')
        assert response.status_code == 200
        agent_data = response.get_json()
        assert agent_data['agent_id'] == agent_id
        
        # 3. List all agents
        response = client.get('/api/agents')
        assert response.status_code == 200
        agents = response.get_json()
        assert any(a['agent_id'] == agent_id for a in agents)
        
        # 4. Update agent database
        response = client.put(f'/api/agents/{agent_id}/database', json={
            'host': 'newhost',
            'database': 'newdb'
        })
        assert response.status_code == 200
        
        # 5. Delete agent
        response = client.delete(f'/api/agents/{agent_id}')
        assert response.status_code == 200
        
        # 6. Verify deletion
        response = client.get(f'/api/agents/{agent_id}')
        assert response.status_code == 404


@pytest.mark.e2e
class TestE2EQueryWorkflow:
    """E2E tests for query execution workflow"""
    
    def test_natural_language_query_workflow(self, client):
        """Test complete NL query workflow"""
        agent_id = 'e2e-nl-query-agent'
        
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Mock database connector
        with patch.object(agent_registry, 'get_database_connector') as mock_connector:
            mock_conn = Mock()
            mock_conn.connect = Mock()
            mock_conn.close = Mock()
            mock_conn.execute_query.return_value = {
                'data': [{'id': 1, 'name': 'John'}],
                'rows': 1,
                'columns': ['id', 'name'],
                'execution_time_ms': 50.0
            }
            mock_connector.return_value = mock_conn
            
            # Execute NL query
            response = client.post(f'/api/agents/{agent_id}/nl-query', json={
                'query': 'Show me all users'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
            assert 'sql' in data
            assert len(data['data']) > 0
    
    def test_sql_query_workflow(self, client):
        """Test SQL query execution workflow"""
        agent_id = 'e2e-sql-query-agent'
        
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Mock database connector
        with patch.object(agent_registry, 'get_database_connector') as mock_connector:
            mock_conn = Mock()
            mock_conn.connect = Mock()
            mock_conn.close = Mock()
            mock_conn.execute_query.return_value = {
                'data': [{'count': 100}],
                'rows': 1,
                'columns': ['count']
            }
            mock_connector.return_value = mock_conn
            
            # Execute SQL query
            response = client.post(f'/api/agents/{agent_id}/query', json={
                'query': 'SELECT COUNT(*) as count FROM users'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data
            assert data['rows'] == 1


@pytest.mark.e2e
class TestE2ECostTracking:
    """E2E tests for cost tracking"""
    
    def test_cost_tracking_workflow(self, client):
        """Test complete cost tracking workflow"""
        agent_id = 'e2e-cost-agent'
        
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Execute queries to generate costs
        with patch.object(ai_agent_manager, 'execute_query') as mock_exec:
            mock_exec.return_value = {
                'data': [],
                'rows': 0,
                'columns': [],
                'execution_time_ms': 100.0,
                'sql': 'SELECT * FROM users',
                'confidence': 0.95
            }
            
            for i in range(3):
                client.post(f'/api/agents/{agent_id}/nl-query', json={
                    'query': f'Query {i}'
                })
        
        # Get cost dashboard
        response = client.get(f'/api/cost/dashboard?agent_id={agent_id}')
        assert response.status_code == 200
        dashboard = response.get_json()
        assert 'total_cost' in dashboard
        assert 'total_calls' in dashboard
        
        # Create budget alert
        response = client.post('/api/cost/budget-alerts', json={
            'name': 'E2E Alert',
            'threshold_usd': 100.0,
            'period': 'daily'
        })
        assert response.status_code == 201
        
        # Get budget alerts
        response = client.get('/api/cost/budget-alerts')
        assert response.status_code == 200
        alerts = response.get_json()
        assert len(alerts) > 0
        
        # Export cost report
        response = client.get('/api/cost/export?format=csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv'


@pytest.mark.e2e
class TestE2EFailover:
    """E2E tests for provider failover"""
    
    def test_failover_workflow(self, client):
        """Test complete failover workflow"""
        agent_id = 'e2e-failover-agent'
        
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Configure failover
        response = client.post(f'/api/agents/{agent_id}/failover/configure', json={
            'primary_provider_id': 'openai-agent',
            'backup_provider_ids': ['anthropic-agent', 'custom-agent'],
            'health_check_enabled': True,
            'auto_failover_enabled': True
        })
        assert response.status_code == 200
        
        # Get failover stats
        response = client.get(f'/api/agents/{agent_id}/failover/stats')
        assert response.status_code == 200
        stats = response.get_json()
        assert 'active_provider' in stats
        assert 'total_switches' in stats
        
        # Check provider health
        response = client.get(f'/api/agents/{agent_id}/failover/health')
        assert response.status_code == 200
        
        # Manual switch
        response = client.post(f'/api/agents/{agent_id}/failover/switch', json={
            'provider_id': 'anthropic-agent'
        })
        assert response.status_code == 200


@pytest.mark.e2e
class TestE2EGraphQL:
    """E2E tests for GraphQL API"""
    
    def test_graphql_complete_workflow(self, client):
        """Test complete GraphQL workflow"""
        agent_id = 'e2e-graphql-agent'
        
        # Register agent via REST
        client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Query agent via GraphQL
        response = client.post('/graphql', json={
            'query': f'''
            query {{
                agent(agentId: "{agent_id}") {{
                    agentId
                    status
                }}
                costDashboard(agentId: "{agent_id}") {{
                    totalCost
                    totalCalls
                }}
                failoverStats(agentId: "{agent_id}") {{
                    activeProvider
                }}
            }}
            '''
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data']['agent']['agentId'] == agent_id
        
        # Mutation via GraphQL
        response = client.post('/graphql', json={
            'query': '''
            mutation {
                createBudgetAlert(input: {
                    name: "E2E GraphQL Alert"
                    thresholdUsd: 50.0
                    period: "monthly"
                }) {
                    success
                    alert {
                        alertId
                        name
                    }
                }
            }
            '''
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['createBudgetAlert']['success'] is True


@pytest.mark.e2e
class TestE2ECompleteScenario:
    """E2E tests for complete user scenarios"""
    
    def test_complete_user_scenario(self, client):
        """Test complete user scenario: setup -> query -> monitor -> optimize"""
        agent_id = 'e2e-complete-agent'
        
        # 1. Setup: Register agent
        response = client.post('/api/agents/register', json={
            'agent_id': agent_id,
            'agent_credentials': {
                'api_key': 'user-key',
                'api_secret': 'user-secret'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'analytics',
                'user': 'analyst',
                'password': 'secure-pass'
            }
        })
        assert response.status_code == 201
        
        # 2. Setup: Configure permissions
        response = client.post(f'/api/agents/{agent_id}/permissions', json={
            'permissions': [
                {
                    'resource_type': 'table',
                    'resource_id': 'users',
                    'permissions': ['read']
                },
                {
                    'resource_type': 'table',
                    'resource_id': 'orders',
                    'permissions': ['read']
                }
            ]
        })
        assert response.status_code == 200
        
        # 3. Setup: Configure failover
        response = client.post(f'/api/agents/{agent_id}/failover/configure', json={
            'primary_provider_id': 'openai-agent',
            'backup_provider_ids': ['anthropic-agent'],
            'health_check_enabled': True,
            'auto_failover_enabled': True
        })
        assert response.status_code == 200
        
        # 4. Usage: Execute queries
        with patch.object(agent_registry, 'get_database_connector') as mock_connector, \
             patch.object(ai_agent_manager, 'execute_query') as mock_exec:
            
            mock_conn = Mock()
            mock_conn.connect = Mock()
            mock_conn.close = Mock()
            mock_conn.execute_query.return_value = {
                'data': [{'id': 1, 'name': 'User'}],
                'rows': 1,
                'columns': ['id', 'name']
            }
            mock_connector.return_value = mock_conn
            
            mock_exec.return_value = {
                'data': [{'id': 1, 'name': 'User'}],
                'rows': 1,
                'columns': ['id', 'name'],
                'execution_time_ms': 50.0,
                'sql': 'SELECT * FROM users',
                'confidence': 0.95
            }
            
            # Execute multiple queries
            for query_text in ['Show me all users', 'Count orders', 'Recent activity']:
                response = client.post(f'/api/agents/{agent_id}/nl-query', json={
                    'query': query_text
                })
                assert response.status_code == 200
        
        # 5. Monitor: Check costs
        response = client.get(f'/api/cost/dashboard?agent_id={agent_id}')
        assert response.status_code == 200
        dashboard = response.get_json()
        assert dashboard['total_calls'] >= 3
        
        # 6. Monitor: Check audit logs
        response = client.get(f'/api/audit/logs?agent_id={agent_id}')
        assert response.status_code == 200
        logs = response.get_json()
        assert len(logs) >= 3
        
        # 7. Optimize: Create budget alert
        response = client.post('/api/cost/budget-alerts', json={
            'name': 'Monthly Budget',
            'threshold_usd': 1000.0,
            'period': 'monthly'
        })
        assert response.status_code == 201
        
        # 8. Optimize: Check failover stats
        response = client.get(f'/api/agents/{agent_id}/failover/stats')
        assert response.status_code == 200
        stats = response.get_json()
        assert 'active_provider' in stats

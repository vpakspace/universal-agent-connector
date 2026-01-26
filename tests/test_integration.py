"""
Integration tests for AI Agent Connector
Tests multiple components working together without external dependencies
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from main import create_app
from ai_agent_connector.app.api.routes import (
    agent_registry,
    ai_agent_manager,
    cost_tracker,
    audit_logger
)
from ai_agent_connector.app.agents.registry import AgentRegistry
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager
from ai_agent_connector.app.utils.cost_tracker import CostTracker
from ai_agent_connector.app.utils.audit_logger import AuditLogger
from ai_agent_connector.app.utils.provider_failover import ProviderFailoverManager


@pytest.fixture
def app():
    """Create Flask app for testing"""
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


@pytest.mark.integration
class TestAgentRegistrationIntegration:
    """Integration tests for agent registration flow"""
    
    def test_register_agent_via_api(self, client):
        """Test complete agent registration via API"""
        response = client.post('/api/agents/register', json={
            'agent_id': 'test-agent-integration',
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
        data = response.get_json()
        assert data['success'] is True
        assert 'api_key' in data
        
        # Verify agent exists
        agent = agent_registry.get_agent('test-agent-integration')
        assert agent is not None
    
    def test_register_and_query_flow(self, client):
        """Test agent registration followed by query execution"""
        # Register agent
        response = client.post('/api/agents/register', json={
            'agent_id': 'query-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        assert response.status_code == 201
        
        # Execute query (mocked)
        with patch.object(agent_registry, 'get_database_connector') as mock_connector:
            mock_conn = Mock()
            mock_conn.execute_query.return_value = {
                'data': [{'id': 1, 'name': 'Test'}],
                'rows': 1,
                'columns': ['id', 'name']
            }
            mock_connector.return_value = mock_conn
            
            response = client.post('/api/agents/query-agent/query', json={
                'query': 'SELECT * FROM users LIMIT 10'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'data' in data


@pytest.mark.integration
class TestCostTrackingIntegration:
    """Integration tests for cost tracking"""
    
    def test_cost_tracking_with_query_execution(self, client):
        """Test cost tracking integrated with query execution"""
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': 'cost-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Mock AI agent manager to track costs
        with patch.object(ai_agent_manager, 'execute_query') as mock_exec:
            mock_exec.return_value = {
                'data': [],
                'rows': 0,
                'columns': [],
                'execution_time_ms': 100.0,
                'sql': 'SELECT * FROM users',
                'confidence': 0.95
            }
            
            # Execute query
            response = client.post('/api/agents/cost-agent/nl-query', json={
                'query': 'Show me all users'
            })
            
            assert response.status_code == 200
            
            # Check cost was tracked
            dashboard = cost_tracker.get_dashboard_data()
            assert dashboard is not None
    
    def test_budget_alert_creation_and_triggering(self, client):
        """Test budget alert creation and triggering"""
        # Create budget alert
        response = client.post('/api/cost/budget-alerts', json={
            'name': 'Test Alert',
            'threshold_usd': 10.0,
            'period': 'daily'
        })
        
        assert response.status_code == 201
        alert_id = response.get_json()['alert']['alert_id']
        
        # Simulate cost accumulation
        for _ in range(5):
            cost_tracker.track_call(
                call_id=f'call-{_}',
                provider='openai',
                model='gpt-4',
                agent_id='test-agent',
                prompt_tokens=1000,
                completion_tokens=500,
                cost_usd=2.0
            )
        
        # Check alert status
        alerts = cost_tracker.get_budget_alerts()
        assert len(alerts) > 0


@pytest.mark.integration
class TestProviderFailoverIntegration:
    """Integration tests for provider failover"""
    
    def test_failover_configuration_and_switching(self, client):
        """Test failover configuration and automatic switching"""
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': 'failover-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Configure failover
        response = client.post('/api/agents/failover-agent/failover/configure', json={
            'primary_provider_id': 'openai-agent',
            'backup_provider_ids': ['anthropic-agent'],
            'health_check_enabled': True,
            'auto_failover_enabled': True
        })
        
        assert response.status_code == 200
        
        # Get failover stats
        response = client.get('/api/agents/failover-agent/failover/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'active_provider' in data


@pytest.mark.integration
class TestAuditLoggingIntegration:
    """Integration tests for audit logging"""
    
    def test_audit_logging_with_operations(self, client):
        """Test audit logging integrated with operations"""
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': 'audit-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Execute query
        with patch.object(agent_registry, 'get_database_connector') as mock_connector:
            mock_conn = Mock()
            mock_conn.execute_query.return_value = {'data': []}
            mock_connector.return_value = mock_conn
            
            response = client.post('/api/agents/audit-agent/query', json={
                'query': 'SELECT * FROM users'
            })
            
            assert response.status_code == 200
            
            # Check audit log
            logs = audit_logger.get_logs(agent_id='audit-agent')
            assert len(logs) > 0
    
    def test_audit_log_export(self, client):
        """Test audit log export functionality"""
        # Create some audit logs
        audit_logger.log(
            agent_id='export-agent',
            action_type='query_execution',
            details={'query': 'SELECT * FROM users'}
        )
        
        # Export logs
        response = client.get('/api/audit/export?format=json')
        assert response.status_code == 200


@pytest.mark.integration
class TestGraphQLIntegration:
    """Integration tests for GraphQL API"""
    
    def test_graphql_query_through_api(self, client):
        """Test GraphQL queries through API"""
        # Register agent first
        client.post('/api/agents/register', json={
            'agent_id': 'graphql-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # GraphQL query
        response = client.post('/graphql', json={
            'query': '''
            query {
                agent(agentId: "graphql-agent") {
                    agentId
                    status
                }
            }
            '''
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data']['agent']['agentId'] == 'graphql-agent'
    
    def test_graphql_mutation_through_api(self, client):
        """Test GraphQL mutations through API"""
        response = client.post('/graphql', json={
            'query': '''
            mutation {
                registerAgent(input: {
                    agentId: "graphql-mutation-agent"
                    agentCredentials: "{\\"api_key\\": \\"key\\"}"
                    database: "{\\"host\\": \\"localhost\\", \\"database\\": \\"test\\"}"
                }) {
                    success
                    agent {
                        agentId
                    }
                }
            }
            '''
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data']['registerAgent']['success'] is True


@pytest.mark.integration
class TestPermissionIntegration:
    """Integration tests for permissions"""
    
    def test_permission_setting_and_enforcement(self, client):
        """Test permission setting and enforcement"""
        from ai_agent_connector.app.permissions import AccessControl
        
        # Register agent
        client.post('/api/agents/register', json={
            'agent_id': 'perm-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        
        # Set permissions
        response = client.post('/api/agents/perm-agent/permissions', json={
            'permissions': [
                {
                    'resource_type': 'table',
                    'resource_id': 'users',
                    'permissions': ['read']
                }
            ]
        })
        
        assert response.status_code == 200
        
        # Verify permissions
        access_control = AccessControl()
        has_permission = access_control.has_resource_permission(
            'perm-agent',
            'users',
            'read'
        )
        assert has_permission is True


@pytest.mark.integration
class TestMultiComponentIntegration:
    """Integration tests involving multiple components"""
    
    def test_full_workflow(self, client):
        """Test complete workflow: register -> query -> track cost -> audit"""
        # 1. Register agent
        response = client.post('/api/agents/register', json={
            'agent_id': 'workflow-agent',
            'agent_credentials': {'api_key': 'key'},
            'database': {'host': 'localhost', 'database': 'test'}
        })
        assert response.status_code == 201
        
        # 2. Set permissions
        client.post('/api/agents/workflow-agent/permissions', json={
            'permissions': [{
                'resource_type': 'table',
                'resource_id': 'users',
                'permissions': ['read']
            }]
        })
        
        # 3. Execute query (mocked)
        with patch.object(agent_registry, 'get_database_connector') as mock_connector:
            mock_conn = Mock()
            mock_conn.execute_query.return_value = {
                'data': [{'id': 1}],
                'rows': 1
            }
            mock_connector.return_value = mock_conn
            
            response = client.post('/api/agents/workflow-agent/query', json={
                'query': 'SELECT * FROM users'
            })
            assert response.status_code == 200
        
        # 4. Check cost tracking
        dashboard = cost_tracker.get_dashboard_data(agent_id='workflow-agent')
        assert dashboard is not None
        
        # 5. Check audit logs
        logs = audit_logger.get_logs(agent_id='workflow-agent')
        assert len(logs) > 0

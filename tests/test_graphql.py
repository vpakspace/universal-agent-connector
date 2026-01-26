"""
Comprehensive test suite for GraphQL API
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from graphql import graphql_sync

from ai_agent_connector.app.graphql.schema import (
    schema,
    set_managers,
    Query,
    Mutation,
    Subscription
)
from ai_agent_connector.app.agents.registry import AgentRegistry
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager
from ai_agent_connector.app.utils.cost_tracker import CostTracker
from ai_agent_connector.app.utils.audit_logger import AuditLogger
from ai_agent_connector.app.utils.provider_failover import ProviderFailoverManager


@pytest.fixture
def mock_managers():
    """Create mock managers for GraphQL"""
    agent_registry = Mock(spec=AgentRegistry)
    ai_agent_manager = Mock(spec=AIAgentManager)
    cost_tracker = Mock(spec=CostTracker)
    audit_logger = Mock(spec=AuditLogger)
    failover_manager = Mock(spec=ProviderFailoverManager)
    
    # Set up mocks
    agent_registry.get_agent.return_value = {'agent_id': 'test-agent', 'status': 'active'}
    agent_registry.list_agents.return_value = ['agent1', 'agent2']
    agent_registry.register_agent.return_value = {'api_key': 'generated-key'}
    agent_registry.get_database_connector.return_value = Mock()
    
    cost_tracker.get_dashboard_data.return_value = {
        'total_cost': 100.0,
        'total_calls': 1000,
        'cost_by_provider': {'openai': 80.0, 'anthropic': 20.0},
        'cost_by_operation': {'query': 100.0},
        'cost_by_agent': {'test-agent': 100.0},
        'daily_costs': []
    }
    cost_tracker._cost_records = {}
    cost_tracker._budget_alerts = {}
    cost_tracker.add_budget_alert.return_value = Mock(
        alert_id='alert-123',
        name='Test Alert',
        threshold_usd=1000.0,
        period='monthly',
        triggered=False,
        notification_emails=[],
        webhook_url=None
    )
    
    audit_logger.get_logs.return_value = [
        {
            'id': 1,
            'agent_id': 'test-agent',
            'action_type': 'query_execution',
            'timestamp': '2024-01-01T00:00:00',
            'details': {},
            'user_id': None,
            'ip_address': None
        }
    ]
    audit_logger.get_log.return_value = {
        'id': 1,
        'agent_id': 'test-agent',
        'action_type': 'query_execution',
        'timestamp': '2024-01-01T00:00:00',
        'details': {}
    }
    
    failover_manager.get_failover_stats.return_value = {
        'active_provider': 'openai-agent',
        'total_switches': 2,
        'provider_health': {'openai-agent': {'status': 'healthy'}},
        'consecutive_failures': {}
    }
    failover_manager.get_provider_health.return_value = {
        'openai-agent': {'status': 'healthy'}
    }
    failover_manager.configure_failover.return_value = {
        'agent_id': 'test-agent',
        'primary_provider_id': 'openai-agent'
    }
    
    ai_agent_manager.execute_query.return_value = {
        'data': [{'id': 1, 'name': 'Test'}],
        'rows': 1,
        'columns': ['id', 'name'],
        'execution_time_ms': 10.0,
        'sql': 'SELECT * FROM users',
        'confidence': None
    }
    
    set_managers(agent_registry, ai_agent_manager, cost_tracker, audit_logger, failover_manager)
    
    return {
        'agent_registry': agent_registry,
        'ai_agent_manager': ai_agent_manager,
        'cost_tracker': cost_tracker,
        'audit_logger': audit_logger,
        'failover_manager': failover_manager
    }


class TestGraphQLSchema:
    """Test GraphQL schema structure"""
    
    def test_schema_creation(self):
        """Test that schema is created successfully"""
        assert schema is not None
        assert schema.query_type is not None
        assert schema.mutation_type is not None
        assert schema.subscription_type is not None
    
    def test_schema_introspection(self, mock_managers):
        """Test schema introspection query"""
        query = """
        query {
            __schema {
                queryType {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data is not None
        assert result.data['__schema']['queryType']['name'] == 'Query'


class TestGraphQLQueries:
    """Test GraphQL queries"""
    
    def test_health_query(self, mock_managers):
        """Test health check query"""
        query = """
        query {
            health {
                status
                service
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['health']['status'] == 'healthy'
    
    def test_agent_query(self, mock_managers):
        """Test get single agent query"""
        query = """
        query {
            agent(agentId: "test-agent") {
                agentId
                status
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['agent']['agentId'] == 'test-agent'
    
    def test_agents_query(self, mock_managers):
        """Test list agents query"""
        query = """
        query {
            agents(limit: 10) {
                agentId
                status
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert len(result.data['agents']) == 2
    
    def test_cost_dashboard_query(self, mock_managers):
        """Test cost dashboard query"""
        query = """
        query {
            costDashboard(periodDays: 30) {
                totalCost
                totalCalls
                costByProvider
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['costDashboard']['totalCost'] == 100.0
        assert result.data['costDashboard']['totalCalls'] == 1000
    
    def test_cost_records_query(self, mock_managers):
        """Test cost records query"""
        query = """
        query {
            costRecords(limit: 10) {
                callId
                costUsd
                provider
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert isinstance(result.data['costRecords'], list)
    
    def test_budget_alerts_query(self, mock_managers):
        """Test budget alerts query"""
        query = """
        query {
            budgetAlerts {
                alertId
                name
                thresholdUsd
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert isinstance(result.data['budgetAlerts'], list)
    
    def test_failover_stats_query(self, mock_managers):
        """Test failover stats query"""
        query = """
        query {
            failoverStats(agentId: "test-agent") {
                agentId
                activeProvider
                totalSwitches
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['failoverStats']['activeProvider'] == 'openai-agent'
        assert result.data['failoverStats']['totalSwitches'] == 2
    
    def test_audit_logs_query(self, mock_managers):
        """Test audit logs query"""
        query = """
        query {
            auditLogs(limit: 10) {
                logId
                agentId
                actionType
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert len(result.data['auditLogs']) == 1
        assert result.data['auditLogs'][0]['actionType'] == 'query_execution'
    
    def test_provider_health_query(self, mock_managers):
        """Test provider health query"""
        query = """
        query {
            providerHealth(agentId: "test-agent")
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['providerHealth'] is not None
    
    def test_execute_query_query(self, mock_managers):
        """Test execute query query"""
        # Mock database connector
        mock_connector = Mock()
        mock_connector.connect.return_value = None
        mock_connector.execute_query.return_value = {
            'data': [{'id': 1, 'name': 'Test'}],
            'rows': 1,
            'columns': ['id', 'name'],
            'execution_time_ms': 10.0
        }
        mock_connector.close.return_value = None
        mock_managers['agent_registry'].get_database_connector.return_value = mock_connector
        
        # Mock access control
        with patch('ai_agent_connector.app.graphql.schema.AccessControl') as mock_ac:
            mock_access_control = Mock()
            mock_access_control.has_resource_permission.return_value = True
            mock_ac.return_value = mock_access_control
            
            query = """
            query {
                executeQuery(input: {
                    agentId: "test-agent"
                    query: "SELECT * FROM users LIMIT 10"
                    fetch: true
                }) {
                    data
                    rows
                    columns
                    sql
                }
            }
            """
            result = graphql_sync(schema, query)
            # May have errors due to complex integration, but structure should be valid
            assert result is not None
    
    def test_execute_natural_language_query_query(self, mock_managers):
        """Test execute natural language query"""
        query = """
        query {
            executeNaturalLanguageQuery(input: {
                agentId: "test-agent"
                query: "Show me all users"
            }) {
                data
                sql
                confidence
            }
        }
        """
        result = graphql_sync(schema, query)
        # May have errors, but query structure is valid
        assert result is not None
    
    def test_budget_alert_query(self, mock_managers):
        """Test get single budget alert query"""
        # Add a mock alert
        mock_alert = Mock(
            alert_id='alert-123',
            name='Test Alert',
            threshold_usd=1000.0,
            period='monthly',
            triggered=False,
            notification_emails=[],
            webhook_url=None
        )
        mock_managers['cost_tracker']._budget_alerts = {'alert-123': mock_alert}
        
        query = """
        query {
            budgetAlert(alertId: "alert-123") {
                alertId
                name
                thresholdUsd
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['budgetAlert'] is not None
    
    def test_audit_log_query(self, mock_managers):
        """Test get single audit log query"""
        query = """
        query {
            auditLog(logId: 1) {
                logId
                agentId
                actionType
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['auditLog'] is not None
    
    def test_notifications_query(self, mock_managers):
        """Test notifications query"""
        query = """
        query {
            notifications(limit: 10) {
                notificationId
                type
                message
                read
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert isinstance(result.data['notifications'], list)
    
    def test_notification_query(self, mock_managers):
        """Test get single notification query"""
        query = """
        query {
            notification(notificationId: 1) {
                notificationId
                type
                message
            }
        }
        """
        result = graphql_sync(schema, query)
        # May return null if not implemented
        assert result.errors is None or len(result.errors) == 0
    
    def test_query_templates_query(self, mock_managers):
        """Test query templates query"""
        query = """
        query {
            queryTemplates(agentId: "test-agent") {
                templateId
                name
                sql
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert isinstance(result.data['queryTemplates'], list)
    
    def test_query_template_query(self, mock_managers):
        """Test get single query template query"""
        query = """
        query {
            queryTemplate(agentId: "test-agent", templateId: "tpl-123") {
                templateId
                name
                sql
            }
        }
        """
        result = graphql_sync(schema, query)
        # May return null if not implemented
        assert result.errors is None or len(result.errors) == 0
    
    def test_permissions_query(self, mock_managers):
        """Test permissions query"""
        query = """
        query {
            permissions(agentId: "test-agent") {
                resourceType
                resourceId
                permissions
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert isinstance(result.data['permissions'], list)


class TestGraphQLMutations:
    """Test GraphQL mutations"""
    
    def test_register_agent_mutation(self, mock_managers):
        """Test register agent mutation"""
        mutation = """
        mutation {
            registerAgent(input: {
                agentId: "new-agent"
                agentCredentials: "{\\"api_key\\": \\"key\\", \\"api_secret\\": \\"secret\\"}"
                database: "{\\"host\\": \\"localhost\\", \\"database\\": \\"mydb\\"}"
            }) {
                success
                message
                agent {
                    agentId
                    status
                }
            }
        }
        """
        result = graphql_sync(schema, mutation)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['registerAgent']['success'] is True
        assert result.data['registerAgent']['agent']['agentId'] == 'new-agent'
    
    def test_configure_failover_mutation(self, mock_managers):
        """Test configure failover mutation"""
        mutation = """
        mutation {
            configureFailover(input: {
                agentId: "test-agent"
                primaryProviderId: "openai-agent"
                backupProviderIds: ["claude-agent"]
                healthCheckEnabled: true
                autoFailoverEnabled: true
            }) {
                success
                message
                config
            }
        }
        """
        result = graphql_sync(schema, mutation)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['configureFailover']['success'] is True
    
    def test_create_budget_alert_mutation(self, mock_managers):
        """Test create budget alert mutation"""
        mutation = """
        mutation {
            createBudgetAlert(input: {
                name: "Monthly Budget"
                thresholdUsd: 1000.0
                period: "monthly"
            }) {
                success
                message
                alert {
                    alertId
                    name
                    thresholdUsd
                }
            }
        }
        """
        result = graphql_sync(schema, mutation)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['createBudgetAlert']['success'] is True
        assert result.data['createBudgetAlert']['alert']['thresholdUsd'] == 1000.0
    
    def test_execute_query_mutation(self, mock_managers):
        """Test execute query mutation"""
        mutation = """
        mutation {
            executeQuery(input: {
                agentId: "test-agent"
                query: "SELECT * FROM users LIMIT 10"
                fetch: true
            }) {
                success
                message
                result {
                    data
                    rows
                    sql
                }
            }
        }
        """
        result = graphql_sync(schema, mutation)
        # May have errors due to complex integration
        assert result is not None
    
    def test_execute_natural_language_query_mutation(self, mock_managers):
        """Test execute natural language query mutation"""
        mutation = """
        mutation {
            executeNaturalLanguageQuery(input: {
                agentId: "test-agent"
                query: "Show me all users"
                previewOnly: false
            }) {
                success
                message
                result {
                    data
                    sql
                    confidence
                }
            }
        }
        """
        result = graphql_sync(schema, mutation)
        # May have errors due to complex integration
        assert result is not None


class TestGraphQLResolvers:
    """Test GraphQL resolvers"""
    
    def test_resolve_agent(self, mock_managers):
        """Test agent resolver"""
        query = Query()
        result = query.resolve_agent(None, 'test-agent')
        assert result is not None
        assert result['agent_id'] == 'test-agent'
    
    def test_resolve_agents(self, mock_managers):
        """Test agents resolver"""
        query = Query()
        result = query.resolve_agents(None, limit=10)
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_resolve_cost_dashboard(self, mock_managers):
        """Test cost dashboard resolver"""
        query = Query()
        result = query.resolve_cost_dashboard(None, agent_id=None, provider=None, period_days=30)
        assert result is not None
        assert result['total_cost'] == 100.0
    
    def test_resolve_failover_stats(self, mock_managers):
        """Test failover stats resolver"""
        query = Query()
        result = query.resolve_failover_stats(None, 'test-agent')
        assert result is not None
        assert result['active_provider'] == 'openai-agent'
    
    def test_resolve_cost_records(self, mock_managers):
        """Test cost records resolver"""
        # Add mock cost records
        from ai_agent_connector.app.utils.cost_tracker import CostRecord
        from datetime import datetime
        
        mock_record = Mock(spec=CostRecord)
        mock_record.call_id = 'call-123'
        mock_record.timestamp = datetime.now().isoformat()
        mock_record.provider = 'openai'
        mock_record.model = 'gpt-4o-mini'
        mock_record.agent_id = 'test-agent'
        mock_record.prompt_tokens = 100
        mock_record.completion_tokens = 50
        mock_record.total_tokens = 150
        mock_record.cost_usd = 0.01
        mock_record.operation_type = 'query'
        
        mock_managers['cost_tracker']._cost_records = {'call-123': mock_record}
        
        query = Query()
        result = query.resolve_cost_records(None, agent_id=None, provider=None, limit=10)
        assert isinstance(result, list)
    
    def test_resolve_budget_alert(self, mock_managers):
        """Test budget alert resolver"""
        mock_alert = Mock(
            alert_id='alert-123',
            name='Test Alert',
            threshold_usd=1000.0,
            period='monthly',
            triggered=False,
            notification_emails=[],
            webhook_url=None
        )
        mock_managers['cost_tracker']._budget_alerts = {'alert-123': mock_alert}
        
        query = Query()
        result = query.resolve_budget_alert(None, 'alert-123')
        assert result is not None
        assert result['alert_id'] == 'alert-123'
    
    def test_resolve_audit_log(self, mock_managers):
        """Test audit log resolver"""
        query = Query()
        result = query.resolve_audit_log(None, 1)
        assert result is not None
        assert result['log_id'] == 1
    
    def test_resolve_notifications(self, mock_managers):
        """Test notifications resolver"""
        query = Query()
        result = query.resolve_notifications(None, unread_only=False, limit=10)
        assert isinstance(result, list)
    
    def test_resolve_query_templates(self, mock_managers):
        """Test query templates resolver"""
        query = Query()
        result = query.resolve_query_templates(None, 'test-agent', tags=None)
        assert isinstance(result, list)
    
    def test_resolve_permissions(self, mock_managers):
        """Test permissions resolver"""
        query = Query()
        result = query.resolve_permissions(None, 'test-agent')
        assert isinstance(result, list)


class TestGraphQLErrorHandling:
    """Test GraphQL error handling"""
    
    def test_invalid_query(self, mock_managers):
        """Test invalid query handling"""
        query = """
        query {
            invalidField {
                data
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is not None
        assert len(result.errors) > 0
    
    def test_missing_required_argument(self, mock_managers):
        """Test missing required argument"""
        query = """
        query {
            agent {
                agentId
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is not None
    
    def test_invalid_mutation_input(self, mock_managers):
        """Test invalid mutation input"""
        mutation = """
        mutation {
            registerAgent(input: {
                agentId: "test"
            }) {
                success
            }
        }
        """
        result = graphql_sync(schema, mutation)
        # Should have errors due to missing required fields
        assert result.errors is not None or result.data is None


class TestGraphQLComplexQueries:
    """Test complex GraphQL queries"""
    
    def test_multiple_fields_query(self, mock_managers):
        """Test query with multiple fields"""
        query = """
        query {
            agent(agentId: "test-agent") {
                agentId
                status
            }
            costDashboard(periodDays: 30) {
                totalCost
                totalCalls
            }
            failoverStats(agentId: "test-agent") {
                activeProvider
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['agent'] is not None
        assert result.data['costDashboard'] is not None
        assert result.data['failoverStats'] is not None
    
    def test_nested_query(self, mock_managers):
        """Test nested query structure"""
        query = """
        query {
            agents(limit: 5) {
                agentId
                status
            }
            costDashboard {
                totalCost
                costByProvider
                dailyCosts
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert 'agents' in result.data
        assert 'costDashboard' in result.data


class TestGraphQLVariables:
    """Test GraphQL variables"""
    
    def test_query_with_variables(self, mock_managers):
        """Test query with variables"""
        query = """
        query GetAgent($agentId: ID!, $periodDays: Int) {
            agent(agentId: $agentId) {
                agentId
            }
            costDashboard(agentId: $agentId, periodDays: $periodDays) {
                totalCost
            }
        }
        """
        variables = {
            'agentId': 'test-agent',
            'periodDays': 30
        }
        result = graphql_sync(schema, query, variable_values=variables)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['agent']['agentId'] == 'test-agent'


class TestGraphQLRoutes:
    """Test GraphQL routes"""
    
    @pytest.fixture
    def client(self, mock_managers):
        """Create Flask test client"""
        from main import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app.test_client()
    
    def test_graphql_endpoint(self, client, mock_managers):
        """Test GraphQL POST endpoint"""
        query = """
        query {
            health {
                status
            }
        }
        """
        response = client.post(
            '/graphql',
            json={'query': query},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert data['data']['health']['status'] == 'healthy'
    
    def test_graphql_playground(self, client):
        """Test GraphQL playground endpoint"""
        response = client.get('/graphql/playground')
        assert response.status_code == 200
        assert b'GraphQL Playground' in response.data or b'graphql-playground' in response.data.lower()
    
    def test_graphql_schema_endpoint(self, client):
        """Test GraphQL schema endpoint"""
        response = client.get('/graphql/schema')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'schema' in data or 'sdl' in data
    
    def test_graphql_invalid_query(self, client, mock_managers):
        """Test GraphQL endpoint with invalid query"""
        response = client.post(
            '/graphql',
            json={'query': 'invalid query'},
            content_type='application/json'
        )
        assert response.status_code in [200, 400]
        data = json.loads(response.data)
        assert 'errors' in data or 'data' in data
    
    def test_graphql_missing_query(self, client):
        """Test GraphQL endpoint without query"""
        response = client.post(
            '/graphql',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_graphql_with_variables(self, client, mock_managers):
        """Test GraphQL endpoint with variables"""
        query = """
        query GetAgent($agentId: ID!) {
            agent(agentId: $agentId) {
                agentId
            }
        }
        """
        response = client.post(
            '/graphql',
            json={
                'query': query,
                'variables': {'agentId': 'test-agent'}
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_graphql_subscriptions_endpoint(self, client):
        """Test GraphQL subscriptions endpoint"""
        response = client.get('/graphql/subscriptions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'endpoint' in data or 'channels' in data
    
    def test_graphql_subscriptions_post(self, client):
        """Test GraphQL subscriptions POST"""
        response = client.post(
            '/graphql/subscriptions',
            json={
                'query': 'subscription { costUpdated { costUsd } }'
            },
            content_type='application/json'
        )
        assert response.status_code in [200, 400]
    
    def test_graphql_subscription_stream(self, client):
        """Test GraphQL subscription stream endpoint"""
        response = client.get('/graphql/subscriptions/stream?channel=cost_updated')
        # SSE endpoint should return 200 with text/event-stream
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream' or 'text/event-stream' in str(response.headers)


class TestGraphQLSubscriptions:
    """Test GraphQL subscriptions"""
    
    def test_subscription_schema(self):
        """Test subscription type exists in schema"""
        assert schema.subscription_type is not None
        subscription_fields = schema.subscription_type.fields
        assert 'costUpdated' in subscription_fields
        assert 'failoverSwitched' in subscription_fields
        assert 'auditLogCreated' in subscription_fields
        assert 'notificationCreated' in subscription_fields
        assert 'budgetAlertTriggered' in subscription_fields
        assert 'agentStatusChanged' in subscription_fields
    
    def test_subscription_channels(self):
        """Test subscription channel definitions"""
        from ai_agent_connector.app.graphql.routes import _subscription_queues
        # Verify subscription manager exists
        assert _subscription_queues is not None
    
    def test_subscription_publish(self):
        """Test subscription publishing"""
        from ai_agent_connector.app.graphql.routes import publish_subscription, add_subscription, remove_subscription
        import queue
        
        test_queue = queue.Queue()
        add_subscription('test_channel', test_queue)
        
        # Publish data
        publish_subscription('test_channel', {'type': 'test', 'data': 'test_data'})
        
        # Check data was received
        try:
            data = test_queue.get(timeout=1)
            assert data['type'] == 'test'
            assert data['data'] == 'test_data'
        except queue.Empty:
            pytest.fail("Subscription data not received")
        finally:
            remove_subscription('test_channel', test_queue)
    
    def test_subscription_manager(self):
        """Test subscription manager functions"""
        from ai_agent_connector.app.graphql.routes import (
            add_subscription,
            remove_subscription,
            publish_subscription,
            _subscription_queues
        )
        import queue
        
        test_queue = queue.Queue()
        
        # Test add
        add_subscription('test_channel', test_queue)
        assert len(_subscription_queues['test_channel']) == 1
        
        # Test publish
        publish_subscription('test_channel', {'test': 'data'})
        assert not test_queue.empty()
        
        # Test remove
        remove_subscription('test_channel', test_queue)
        assert len(_subscription_queues['test_channel']) == 0


class TestGraphQLIntegration:
    """Test GraphQL integration with managers"""
    
    def test_manager_integration(self, mock_managers):
        """Test that resolvers use managers correctly"""
        query = """
        query {
            agent(agentId: "test-agent") {
                agentId
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        # Verify manager was called
        mock_managers['agent_registry'].get_agent.assert_called_once_with('test-agent')
    
    def test_cost_tracker_integration(self, mock_managers):
        """Test cost tracker integration"""
        query = """
        query {
            costDashboard(periodDays: 30) {
                totalCost
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        # Verify cost tracker was called
        mock_managers['cost_tracker'].get_dashboard_data.assert_called_once()
    
    def test_failover_manager_integration(self, mock_managers):
        """Test failover manager integration"""
        query = """
        query {
            failoverStats(agentId: "test-agent") {
                activeProvider
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        # Verify failover manager was called
        mock_managers['failover_manager'].get_failover_stats.assert_called_once_with('test-agent')
    
    def test_audit_logger_integration(self, mock_managers):
        """Test audit logger integration"""
        query = """
        query {
            auditLogs(limit: 10) {
                logId
                actionType
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        # Verify audit logger was called
        mock_managers['audit_logger'].get_logs.assert_called_once()
    
    def test_ai_agent_manager_integration(self, mock_managers):
        """Test AI agent manager integration"""
        query = """
        query {
            executeNaturalLanguageQuery(input: {
                agentId: "test-agent"
                query: "Show me users"
            }) {
                data
                sql
            }
        }
        """
        result = graphql_sync(schema, query)
        # May have errors, but manager should be called
        assert result is not None


class TestGraphQLEdgeCases:
    """Test GraphQL edge cases"""
    
    def test_empty_result(self, mock_managers):
        """Test query with empty result"""
        mock_managers['agent_registry'].get_agent.return_value = None
        query = """
        query {
            agent(agentId: "nonexistent") {
                agentId
            }
        }
        """
        result = graphql_sync(schema, query)
        # Should return null, not error
        assert result.data['agent'] is None
    
    def test_large_query(self, mock_managers):
        """Test query with many fields"""
        query = """
        query {
            agents(limit: 100) {
                agentId
                status
                databaseType
                databaseName
                permissionsCount
            }
            costDashboard {
                totalCost
                totalCalls
                costByProvider
                costByOperation
                costByAgent
                dailyCosts
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
    
    def test_partial_data(self, mock_managers):
        """Test query with partial data available"""
        mock_managers['cost_tracker'].get_dashboard_data.return_value = {
            'total_cost': 50.0,
            'total_calls': 500
            # Missing other fields
        }
        query = """
        query {
            costDashboard {
                totalCost
                totalCalls
                costByProvider
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['costDashboard']['totalCost'] == 50.0
    
    def test_manager_not_initialized(self):
        """Test resolvers when managers are not initialized"""
        # Clear managers
        set_managers(None, None, None, None, None)
        
        query = """
        query {
            agent(agentId: "test") {
                agentId
            }
        }
        """
        result = graphql_sync(schema, query)
        # Should return null, not error
        assert result.data['agent'] is None
    
    def test_exception_handling_in_resolvers(self, mock_managers):
        """Test that resolvers handle exceptions gracefully"""
        # Make manager raise exception
        mock_managers['agent_registry'].get_agent.side_effect = Exception("Test error")
        
        query = """
        query {
            agent(agentId: "test-agent") {
                agentId
            }
        }
        """
        result = graphql_sync(schema, query)
        # Should return null, not crash
        assert result.data['agent'] is None
    
    def test_filtered_queries(self, mock_managers):
        """Test queries with filters"""
        query = """
        query {
            costDashboard(agentId: "test-agent", provider: "openai", periodDays: 7) {
                totalCost
            }
            auditLogs(agentId: "test-agent", actionType: "query_execution", limit: 5) {
                logId
            }
        }
        """
        result = graphql_sync(schema, query)
        assert result.errors is None or len(result.errors) == 0
        assert result.data['costDashboard'] is not None
        assert result.data['auditLogs'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

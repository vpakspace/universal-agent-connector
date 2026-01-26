"""
Tests for AI agent management API endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.agents.ai_agent_manager import AIAgentManager
from ai_agent_connector.app.agents.providers import AgentProvider, AgentConfiguration
from ai_agent_connector.app.permissions import AccessControl, Permission


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(api_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_admin_auth():
    """Mock admin authentication"""
    with patch('ai_agent_connector.app.api.routes.authenticate_request') as mock_auth:
        mock_auth.return_value = ("admin_agent", None, 200)
        yield mock_auth


@pytest.fixture
def mock_admin_permission():
    """Mock admin permission check"""
    with patch('ai_agent_connector.app.api.routes.access_control') as mock_ac:
        mock_ac.has_permission.return_value = True
        yield mock_ac


@pytest.fixture
def mock_ai_agent_manager():
    """Mock AI agent manager"""
    with patch('ai_agent_connector.app.api.routes.ai_agent_manager') as mock_mgr:
        yield mock_mgr


class TestRegisterAIAgent:
    """Tests for registering AI agents"""
    
    def test_register_ai_agent_success(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test successful AI agent registration"""
        mock_mgr = mock_ai_agent_manager
        mock_mgr.register_ai_agent.return_value = {
            'agent_id': 'agent1',
            'provider': 'openai',
            'model': 'gpt-4',
            'version': 1
        }
        
        payload = {
            'agent_id': 'agent1',
            'provider': 'openai',
            'model': 'gpt-4',
            'api_key': 'test-key',
            'rate_limit': {
                'queries_per_minute': 60
            }
        }
        
        response = client.post(
            '/admin/ai-agents/register',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['agent_id'] == 'agent1'
        assert data['provider'] == 'openai'
    
    def test_register_ai_agent_missing_fields(self, client, mock_admin_auth, mock_admin_permission):
        """Test registration with missing required fields"""
        payload = {
            'agent_id': 'agent1'
            # Missing provider and model
        }
        
        response = client.post(
            '/admin/ai-agents/register',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 400
    
    def test_register_ai_agent_unauthorized(self, client):
        """Test registration without admin permission"""
        with patch('ai_agent_connector.app.api.routes.authenticate_request') as mock_auth:
            mock_auth.return_value = ("user_agent", None, 200)
            
            with patch('ai_agent_connector.app.api.routes.access_control') as mock_ac:
                mock_ac.has_permission.return_value = False
                
                response = client.post(
                    '/admin/ai-agents/register',
                    json={'agent_id': 'agent1', 'provider': 'openai', 'model': 'gpt-4'},
                    headers={'X-API-Key': 'test-key'}
                )
                
                assert response.status_code == 403


class TestListAIAgents:
    """Tests for listing AI agents"""
    
    def test_list_ai_agents(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test listing all AI agents"""
        mock_mgr = mock_ai_agent_manager
        mock_mgr.list_agents.return_value = ['agent1', 'agent2']
        mock_mgr.get_agent.side_effect = [
            {'agent_id': 'agent1', 'configuration': {'model': 'gpt-4'}},
            {'agent_id': 'agent2', 'configuration': {'model': 'claude-3'}}
        ]
        
        response = client.get(
            '/admin/ai-agents',
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['agents']) == 2


class TestExecuteQuery:
    """Tests for executing AI agent queries"""
    
    def test_execute_query_success(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test successful query execution"""
        mock_mgr = mock_ai_agent_manager
        mock_mgr.execute_query.return_value = {
            'response': 'Test response',
            'model': 'gpt-4'
        }
        
        payload = {'query': 'What is AI?'}
        
        response = client.post(
            '/admin/ai-agents/agent1/query',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['response'] == 'Test response'
    
    def test_execute_query_rate_limited(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test query execution with rate limit exceeded"""
        mock_mgr = mock_ai_agent_manager
        mock_mgr.execute_query.side_effect = RuntimeError("Rate limit exceeded: 60 queries per minute")
        
        payload = {'query': 'Test query'}
        
        response = client.post(
            '/admin/ai-agents/agent1/query',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 429


class TestRateLimitEndpoints:
    """Tests for rate limit endpoints"""
    
    def test_set_rate_limit(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test setting rate limit"""
        payload = {
            'queries_per_minute': 100,
            'queries_per_hour': 1000
        }
        
        response = client.post(
            '/admin/ai-agents/agent1/rate-limit',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rate_limit']['queries_per_minute'] == 100
    
    def test_get_rate_limit(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test getting rate limit"""
        from ai_agent_connector.app.utils.rate_limiter import RateLimitConfig
        
        mock_mgr = mock_ai_agent_manager
        mock_mgr.get_rate_limit.return_value = RateLimitConfig(queries_per_minute=60)
        mock_mgr.get_rate_limit_usage.return_value = {
            'rate_limits_configured': True,
            'current_usage': {'queries_last_minute': 5}
        }
        
        response = client.get(
            '/admin/ai-agents/agent1/rate-limit',
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'rate_limit' in data
        assert 'usage' in data


class TestRetryPolicyEndpoints:
    """Tests for retry policy endpoints"""
    
    def test_set_retry_policy(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test setting retry policy"""
        payload = {
            'enabled': True,
            'max_retries': 5,
            'strategy': 'exponential'
        }
        
        response = client.post(
            '/admin/ai-agents/agent1/retry-policy',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['retry_policy']['max_retries'] == 5
    
    def test_get_retry_policy(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test getting retry policy"""
        from ai_agent_connector.app.utils.retry_policy import RetryPolicy, RetryStrategy
        
        mock_mgr = mock_ai_agent_manager
        mock_mgr.get_retry_policy.return_value = RetryPolicy(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL
        )
        
        response = client.get(
            '/admin/ai-agents/agent1/retry-policy',
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['retry_policy']['max_retries'] == 3


class TestVersionControlEndpoints:
    """Tests for version control endpoints"""
    
    def test_list_versions(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test listing configuration versions"""
        from ai_agent_connector.app.utils.version_control import ConfigurationVersion
        
        mock_mgr = mock_ai_agent_manager
        version1 = ConfigurationVersion(
            version=1,
            timestamp='2024-01-01T00:00:00Z',
            config={'model': 'gpt-4'}
        )
        version2 = ConfigurationVersion(
            version=2,
            timestamp='2024-01-02T00:00:00Z',
            config={'model': 'gpt-3.5'}
        )
        mock_mgr.list_configuration_versions.return_value = [version2, version1]
        
        response = client.get(
            '/admin/ai-agents/agent1/versions',
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['versions']) == 2
    
    def test_rollback_configuration(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test rolling back configuration"""
        from ai_agent_connector.app.utils.version_control import ConfigurationVersion
        
        mock_mgr = mock_ai_agent_manager
        rollback_version = ConfigurationVersion(
            version=3,
            timestamp='2024-01-03T00:00:00Z',
            config={'model': 'gpt-4'},
            tags=['rollback']
        )
        mock_mgr.rollback_configuration.return_value = rollback_version
        
        payload = {'version': 1, 'description': 'Rolling back'}
        
        response = client.post(
            '/admin/ai-agents/agent1/rollback',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['rollback_to_version'] == 1
        assert data['new_version']['version'] == 3


class TestWebhookEndpoints:
    """Tests for webhook endpoints"""
    
    def test_register_webhook(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test registering a webhook"""
        mock_mgr = mock_ai_agent_manager
        mock_mgr.register_webhook.return_value = "webhook_123"
        
        payload = {
            'url': 'https://example.com/webhook',
            'events': ['query_success', 'query_failure']
        }
        
        response = client.post(
            '/admin/ai-agents/agent1/webhooks',
            json=payload,
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['webhook_id'] == 'webhook_123'
    
    def test_list_webhooks(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test listing webhooks"""
        from ai_agent_connector.app.utils.webhooks import WebhookConfig, WebhookEvent
        
        mock_mgr = mock_ai_agent_manager
        webhook = WebhookConfig(
            url='https://example.com/webhook',
            events=[WebhookEvent.QUERY_SUCCESS]
        )
        mock_mgr.get_webhooks.return_value = [webhook]
        
        response = client.get(
            '/admin/ai-agents/agent1/webhooks',
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['webhooks']) == 1
    
    def test_get_webhook_history(self, client, mock_admin_auth, mock_admin_permission, mock_ai_agent_manager):
        """Test getting webhook delivery history"""
        mock_mgr = mock_ai_agent_manager
        mock_mgr.get_webhook_delivery_history.return_value = [
            {'status': 'success', 'timestamp': '2024-01-01T00:00:00Z'}
        ]
        mock_mgr.get_webhook_stats.return_value = {
            'total_deliveries': 10,
            'successful': 9,
            'failed': 1
        }
        
        response = client.get(
            '/admin/ai-agents/agent1/webhooks/history',
            headers={'X-API-Key': 'test-key'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'history' in data
        assert 'statistics' in data


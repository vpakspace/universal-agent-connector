"""
Comprehensive test suite for Universal Agent Connector SDK
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, ConnectionError as RequestsConnectionError

from universal_agent_connector import (
    UniversalAgentConnector,
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ConnectionError
)


class TestClientInitialization:
    """Test client initialization"""
    
    def test_default_initialization(self):
        """Test client with default parameters"""
        client = UniversalAgentConnector()
        assert client.base_url == "http://localhost:5000"
        assert client.api_url == "http://localhost:5000/api"
        assert client.api_key is None
        assert client.timeout == 30
        assert client.verify_ssl is True
    
    def test_custom_initialization(self):
        """Test client with custom parameters"""
        client = UniversalAgentConnector(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=60,
            verify_ssl=False
        )
        assert client.base_url == "https://api.example.com"
        assert client.api_url == "https://api.example.com/api"
        assert client.api_key == "test-key"
        assert client.timeout == 60
        assert client.verify_ssl is False
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slashes are removed from base_url"""
        client = UniversalAgentConnector(base_url="http://localhost:5000/")
        assert client.base_url == "http://localhost:5000"
    
    def test_api_key_in_headers(self):
        """Test that API key is set in session headers"""
        client = UniversalAgentConnector(api_key="test-key")
        assert client.session.headers.get('Authorization') == 'Bearer test-key'


class TestRequestHandling:
    """Test request handling and error management"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_successful_request(self, client):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": {"id": "123"}}
        mock_response.content = b'{"status": "success"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client._request('GET', '/test')
            assert result == {"status": "success", "data": {"id": "123"}}
    
    def test_authentication_error(self, client):
        """Test 401 authentication error"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_response.content = b'{"message": "Unauthorized"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            with pytest.raises(AuthenticationError) as exc_info:
                client._request('GET', '/test')
            assert exc_info.value.status_code == 401
            assert "Authentication failed" in str(exc_info.value)
    
    def test_not_found_error(self, client):
        """Test 404 not found error"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not found"}
        mock_response.content = b'{"message": "Not found"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            with pytest.raises(NotFoundError) as exc_info:
                client._request('GET', '/test')
            assert exc_info.value.status_code == 404
    
    def test_validation_error(self, client):
        """Test 400 validation error"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid input"}
        mock_response.content = b'{"message": "Invalid input"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            with pytest.raises(ValidationError) as exc_info:
                client._request('POST', '/test', json_data={"invalid": "data"})
            assert exc_info.value.status_code == 400
    
    def test_rate_limit_error(self, client):
        """Test 429 rate limit error"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_response.content = b'{"message": "Rate limit exceeded"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            with pytest.raises(RateLimitError) as exc_info:
                client._request('GET', '/test')
            assert exc_info.value.status_code == 429
    
    def test_generic_api_error(self, client):
        """Test generic API error (500)"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_response.content = b'{"message": "Internal server error"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client._request('GET', '/test')
            assert exc_info.value.status_code == 500
    
    def test_connection_error(self, client):
        """Test connection error"""
        with patch.object(client.session, 'request', side_effect=RequestsConnectionError("Connection failed")):
            with pytest.raises(ConnectionError) as exc_info:
                client._request('GET', '/test')
            assert "Connection failed" in str(exc_info.value)
    
    def test_empty_response(self, client):
        """Test empty response handling"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.content = b''
        mock_response.json.side_effect = ValueError("No JSON")
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client._request('DELETE', '/test')
            assert result == {}


class TestHealthAndInfo:
    """Test health check and API docs"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "healthy", "service": "AI Agent Connector"}
        mock_response.content = b'{"status": "healthy"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.health_check()
            assert result["status"] == "healthy"
    
    def test_get_api_docs(self, client):
        """Test API documentation endpoint"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"openapi": "3.0.0", "info": {"title": "API"}}
        mock_response.content = b'{"openapi": "3.0.0"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_api_docs()
            assert result["openapi"] == "3.0.0"


class TestAgentManagement:
    """Test agent management methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_register_agent(self, client):
        """Test agent registration"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "agent_id": "test-agent",
            "api_key": "generated-key"
        }
        mock_response.content = b'{"agent_id": "test-agent"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.register_agent(
                agent_id="test-agent",
                agent_credentials={"api_key": "key", "api_secret": "secret"},
                database={"host": "localhost", "database": "testdb"}
            )
            assert result["agent_id"] == "test-agent"
            assert result["api_key"] == "generated-key"
    
    def test_get_agent(self, client):
        """Test get agent"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "agent_id": "test-agent",
            "status": "active"
        }
        mock_response.content = b'{"agent_id": "test-agent"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_agent("test-agent")
            assert result["agent_id"] == "test-agent"
    
    def test_list_agents(self, client):
        """Test list agents"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "agents": [
                {"agent_id": "agent1"},
                {"agent_id": "agent2"}
            ]
        }
        mock_response.content = b'{"agents": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.list_agents()
            assert len(result) == 2
            assert result[0]["agent_id"] == "agent1"
    
    def test_delete_agent(self, client):
        """Test delete agent"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"message": "Agent deleted"}
        mock_response.content = b'{"message": "Agent deleted"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.delete_agent("test-agent")
            assert result["message"] == "Agent deleted"
    
    def test_update_agent_database(self, client):
        """Test update agent database"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"message": "Database updated"}
        mock_response.content = b'{"message": "Database updated"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.update_agent_database(
                "test-agent",
                {"host": "newhost", "database": "newdb"}
            )
            assert result["message"] == "Database updated"


class TestQueryExecution:
    """Test query execution methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_execute_query(self, client):
        """Test SQL query execution"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": [{"id": 1, "name": "Test"}],
            "rows": 1
        }
        mock_response.content = b'{"data": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.execute_query("test-agent", "SELECT * FROM users")
            assert "data" in result
            assert len(result["data"]) == 1
    
    def test_execute_natural_language_query(self, client):
        """Test natural language query"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "sql": "SELECT * FROM users",
            "data": [{"id": 1}],
            "confidence": 0.95
        }
        mock_response.content = b'{"sql": "SELECT * FROM users"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.execute_natural_language_query(
                "test-agent",
                "Show me all users"
            )
            assert result["sql"] == "SELECT * FROM users"
            assert result["confidence"] == 0.95
    
    def test_get_query_suggestions(self, client):
        """Test query suggestions"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "suggestions": [
                {"sql": "SELECT * FROM users", "confidence": 0.9},
                {"sql": "SELECT * FROM customers", "confidence": 0.7}
            ]
        }
        mock_response.content = b'{"suggestions": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_query_suggestions("test-agent", "show users")
            assert len(result) == 2
            assert result[0]["confidence"] == 0.9


class TestAIAgents:
    """Test AI agent management"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_register_ai_agent(self, client):
        """Test register AI agent"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "agent_id": "gpt-agent",
            "provider": "openai",
            "model": "gpt-4o-mini"
        }
        mock_response.content = b'{"agent_id": "gpt-agent"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.register_ai_agent(
                agent_id="gpt-agent",
                provider="openai",
                model="gpt-4o-mini",
                api_key="sk-..."
            )
            assert result["agent_id"] == "gpt-agent"
            assert result["provider"] == "openai"
    
    def test_execute_ai_query(self, client):
        """Test execute AI query"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "response": "AI response text",
            "model": "gpt-4o-mini"
        }
        mock_response.content = b'{"response": "AI response"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.execute_ai_query("gpt-agent", "What is AI?")
            assert result["response"] == "AI response text"
    
    def test_set_rate_limit(self, client):
        """Test set rate limit"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"message": "Rate limit updated"}
        mock_response.content = b'{"message": "Rate limit updated"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.set_rate_limit(
                "gpt-agent",
                queries_per_minute=60,
                queries_per_hour=1000
            )
            assert result["message"] == "Rate limit updated"
    
    def test_get_rate_limit(self, client):
        """Test get rate limit"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "queries_per_minute": 60,
            "queries_per_hour": 1000
        }
        mock_response.content = b'{"queries_per_minute": 60}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_rate_limit("gpt-agent")
            assert result["queries_per_minute"] == 60
    
    def test_set_retry_policy(self, client):
        """Test set retry policy"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"message": "Retry policy updated"}
        mock_response.content = b'{"message": "Retry policy updated"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.set_retry_policy(
                "gpt-agent",
                enabled=True,
                max_retries=3,
                strategy="exponential"
            )
            assert result["message"] == "Retry policy updated"


class TestProviderFailover:
    """Test provider failover methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_configure_failover(self, client):
        """Test configure failover"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "agent_id": "test-agent",
            "primary_provider_id": "openai-agent",
            "backup_provider_ids": ["claude-agent"]
        }
        mock_response.content = b'{"agent_id": "test-agent"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.configure_failover(
                "test-agent",
                primary_provider_id="openai-agent",
                backup_provider_ids=["claude-agent"]
            )
            assert result["primary_provider_id"] == "openai-agent"
    
    def test_get_failover_stats(self, client):
        """Test get failover stats"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "active_provider": "openai-agent",
            "total_switches": 2,
            "provider_health": {
                "openai-agent": {"status": "healthy"}
            }
        }
        mock_response.content = b'{"active_provider": "openai-agent"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_failover_stats("test-agent")
            assert result["active_provider"] == "openai-agent"
            assert result["total_switches"] == 2
    
    def test_switch_provider(self, client):
        """Test switch provider"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "message": "Provider switched",
            "new_provider": "claude-agent"
        }
        mock_response.content = b'{"message": "Provider switched"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.switch_provider("test-agent", "claude-agent")
            assert result["new_provider"] == "claude-agent"


class TestCostTracking:
    """Test cost tracking methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_get_cost_dashboard(self, client):
        """Test get cost dashboard"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "total_cost": 123.45,
            "total_calls": 1000,
            "cost_by_provider": {"openai": 100.0, "anthropic": 23.45}
        }
        mock_response.content = b'{"total_cost": 123.45}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_cost_dashboard(period_days=30)
            assert result["total_cost"] == 123.45
            assert result["total_calls"] == 1000
    
    def test_export_cost_report_json(self, client):
        """Test export cost report as JSON"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "records": [{"cost": 10.0, "provider": "openai"}]
        }
        mock_response.content = b'{"records": []}'
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.export_cost_report(format="json")
            assert isinstance(result, dict)
            assert "records" in result
    
    def test_export_cost_report_csv(self, client):
        """Test export cost report as CSV"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "timestamp,provider,cost\n2024-01-01,openai,10.0"
        mock_response.content = b"timestamp,provider,cost"
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.export_cost_report(format="csv")
            assert isinstance(result, str)
            assert "timestamp" in result
    
    def test_create_budget_alert(self, client):
        """Test create budget alert"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "alert_id": "alert-123",
            "name": "Monthly Budget",
            "threshold_usd": 1000.0
        }
        mock_response.content = b'{"alert_id": "alert-123"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.create_budget_alert(
                name="Monthly Budget",
                threshold_usd=1000.0,
                period="monthly"
            )
            assert result["alert_id"] == "alert-123"
            assert result["threshold_usd"] == 1000.0


class TestPermissions:
    """Test permissions methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_set_permissions(self, client):
        """Test set permissions"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"message": "Permissions updated"}
        mock_response.content = b'{"message": "Permissions updated"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.set_permissions(
                "test-agent",
                permissions=[
                    {"resource_type": "table", "resource_id": "users", "permissions": ["read"]}
                ]
            )
            assert result["message"] == "Permissions updated"
    
    def test_get_permissions(self, client):
        """Test get permissions"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "permissions": [
                {"resource_type": "table", "resource_id": "users", "permissions": ["read"]}
            ]
        }
        mock_response.content = b'{"permissions": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.get_permissions("test-agent")
            assert len(result) == 1
            assert result[0]["resource_id"] == "users"


class TestQueryTemplates:
    """Test query template methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_create_query_template(self, client):
        """Test create query template"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "template_id": "tpl-123",
            "name": "Top Users",
            "sql": "SELECT * FROM users LIMIT {{limit}}"
        }
        mock_response.content = b'{"template_id": "tpl-123"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.create_query_template(
                "test-agent",
                name="Top Users",
                sql="SELECT * FROM users LIMIT {{limit}}"
            )
            assert result["template_id"] == "tpl-123"
    
    def test_list_query_templates(self, client):
        """Test list query templates"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "templates": [
                {"template_id": "tpl-1", "name": "Template 1"},
                {"template_id": "tpl-2", "name": "Template 2"}
            ]
        }
        mock_response.content = b'{"templates": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.list_query_templates("test-agent")
            assert len(result) == 2


class TestAdminMethods:
    """Test admin methods"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_list_databases(self, client):
        """Test list databases"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "databases": [
                {"name": "db1", "type": "postgresql"},
                {"name": "db2", "type": "mysql"}
            ]
        }
        mock_response.content = b'{"databases": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.list_databases()
            assert len(result) == 2
    
    def test_create_rls_rule(self, client):
        """Test create RLS rule"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "rule_id": "rls-123",
            "table_name": "users",
            "rule_type": "filter"
        }
        mock_response.content = b'{"rule_id": "rls-123"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.create_rls_rule(
                "test-agent",
                table_name="users",
                rule_type="filter",
                condition="user_id = current_user_id()"
            )
            assert result["rule_id"] == "rls-123"
    
    def test_create_alert_rule(self, client):
        """Test create alert rule"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "rule_id": "alert-rule-123",
            "name": "High Cost Alert",
            "severity": "high"
        }
        mock_response.content = b'{"rule_id": "alert-rule-123"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.create_alert_rule(
                name="High Cost Alert",
                condition="cost > 1000",
                severity="high"
            )
            assert result["rule_id"] == "alert-rule-123"


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_missing_optional_parameters(self, client):
        """Test methods with missing optional parameters"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"result": "success"}
        mock_response.content = b'{"result": "success"}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            # Should not raise error when optional params are None
            result = client.get_cost_dashboard()
            assert result["result"] == "success"
    
    def test_empty_list_responses(self, client):
        """Test methods returning empty lists"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"agents": []}
        mock_response.content = b'{"agents": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client.list_agents()
            assert result == []
    
    def test_large_response_handling(self, client):
        """Test handling of large responses"""
        large_data = {"items": [{"id": i} for i in range(1000)]}
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = large_data
        mock_response.content = json.dumps(large_data).encode()
        
        with patch.object(client.session, 'request', return_value=mock_response):
            result = client._request('GET', '/large-data')
            assert len(result["items"]) == 1000
    
    def test_special_characters_in_queries(self, client):
        """Test handling of special characters in queries"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        
        with patch.object(client.session, 'request', return_value=mock_response):
            # Query with special characters
            query = "SELECT * FROM users WHERE name = 'O''Brien'"
            result = client.execute_query("test-agent", query)
            assert "data" in result


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    @pytest.fixture
    def client(self):
        return UniversalAgentConnector(base_url="http://localhost:5000")
    
    def test_complete_workflow(self, client):
        """Test complete workflow: register -> query -> check costs"""
        # Register agent
        register_response = Mock()
        register_response.ok = True
        register_response.json.return_value = {
            "agent_id": "workflow-agent",
            "api_key": "key-123"
        }
        register_response.content = b'{"agent_id": "workflow-agent"}'
        
        # Execute query
        query_response = Mock()
        query_response.ok = True
        query_response.json.return_value = {"data": [{"id": 1}]}
        query_response.content = b'{"data": []}'
        
        # Get costs
        cost_response = Mock()
        cost_response.ok = True
        cost_response.json.return_value = {"total_cost": 5.0}
        cost_response.content = b'{"total_cost": 5.0}'
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.side_effect = [register_response, query_response, cost_response]
            
            # Register
            agent = client.register_agent(
                agent_id="workflow-agent",
                agent_credentials={"api_key": "key", "api_secret": "secret"},
                database={"host": "localhost", "database": "testdb"}
            )
            assert agent["agent_id"] == "workflow-agent"
            
            # Query
            result = client.execute_query("workflow-agent", "SELECT 1")
            assert "data" in result
            
            # Costs
            costs = client.get_cost_dashboard()
            assert costs["total_cost"] == 5.0
    
    def test_failover_workflow(self, client):
        """Test failover configuration and monitoring"""
        # Configure failover
        config_response = Mock()
        config_response.ok = True
        config_response.json.return_value = {
            "agent_id": "failover-agent",
            "primary_provider_id": "openai-agent"
        }
        config_response.content = b'{"agent_id": "failover-agent"}'
        
        # Get stats
        stats_response = Mock()
        stats_response.ok = True
        stats_response.json.return_value = {
            "active_provider": "openai-agent",
            "total_switches": 0
        }
        stats_response.content = b'{"active_provider": "openai-agent"}'
        
        with patch.object(client.session, 'request') as mock_request:
            mock_request.side_effect = [config_response, stats_response]
            
            # Configure
            config = client.configure_failover(
                "failover-agent",
                primary_provider_id="openai-agent",
                backup_provider_ids=["claude-agent"]
            )
            assert config["primary_provider_id"] == "openai-agent"
            
            # Check stats
            stats = client.get_failover_stats("failover-agent")
            assert stats["active_provider"] == "openai-agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

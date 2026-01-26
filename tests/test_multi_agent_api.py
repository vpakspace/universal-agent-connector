"""
Integration tests for multi-agent collaboration API endpoints
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import json

from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.agents.registry import AgentRegistry
from ai_agent_connector.app.utils.agent_orchestrator import (
    AgentOrchestrator,
    CollaborationSession,
    AgentTrace,
    AgentMessage
)
from datetime import datetime


class TestMultiAgentAPI(unittest.TestCase):
    """Test cases for multi-agent collaboration API"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock API key
        self.api_key = "test-api-key-123"
        
        # Mock agent registry
        self.mock_registry = Mock(spec=AgentRegistry)
        self.mock_registry.authenticate_agent.return_value = "test-agent-id"
        self.mock_registry.get_agent.return_value = {
            "agent_id": "test-agent-id",
            "name": "Test Agent"
        }
    
    def _authenticated_request(self, method, url, **kwargs):
        """Helper to make authenticated request"""
        headers = kwargs.get('headers', {})
        headers['X-API-Key'] = self.api_key
        kwargs['headers'] = headers
        return getattr(self.client, method.lower())(url, **kwargs)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_create_collaboration_session(self, mock_orchestrator, mock_registry):
        """Test creating collaboration session"""
        # Setup mocks
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_registry.get_agent.return_value = {"agent_id": "schema-agent"}
        
        mock_session = Mock(spec=CollaborationSession)
        mock_session.session_id = "session-123"
        mock_session.query = "Find all users"
        mock_session.agents = ["schema-agent", "sql-agent"]
        mock_session.roles = {
            "schema-agent": "schema_researcher",
            "sql-agent": "sql_generator"
        }
        mock_session.status = "pending"
        mock_session.created_at = "2024-01-01T00:00:00Z"
        
        mock_orchestrator.create_session.return_value = mock_session
        
        # Make request
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate',
            json={
                "query": "Find all users",
                "agents": [
                    {"agent_id": "schema-agent", "role": "schema_researcher"},
                    {"agent_id": "sql-agent", "role": "sql_generator"}
                ]
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn("session_id", data)
        self.assertEqual(data["query"], "Find all users")
        mock_orchestrator.create_session.assert_called_once()
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    def test_create_session_missing_query(self, mock_registry):
        """Test creating session without query"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate',
            json={"agents": []}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("query", data["error"])
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    def test_create_session_missing_agents(self, mock_registry):
        """Test creating session without agents"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate',
            json={"query": "Test query"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    def test_create_session_invalid_agent(self, mock_registry):
        """Test creating session with invalid agent ID"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_registry.get_agent.return_value = None
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate',
            json={
                "query": "Test query",
                "agents": [{"agent_id": "invalid-agent", "role": "schema_researcher"}]
            }
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    def test_create_session_invalid_role(self, mock_registry):
        """Test creating session with invalid role"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_registry.get_agent.return_value = {"agent_id": "agent-1"}
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate',
            json={
                "query": "Test query",
                "agents": [{"agent_id": "agent-1", "role": "invalid_role"}]
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_execute_collaboration(self, mock_orchestrator, mock_registry):
        """Test executing collaboration"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        mock_session = Mock(spec=CollaborationSession)
        mock_session.session_id = "session-123"
        mock_session.status = "completed"
        mock_session.traces = []
        mock_session.messages = []
        mock_session.state = {"generated_sql": "SELECT * FROM users"}
        mock_session.result = {"success": True}
        mock_session.completed_at = "2024-01-01T00:01:00Z"
        
        mock_orchestrator.execute_collaboration.return_value = mock_session
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate/session-123/execute',
            json={}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "completed")
        self.assertIn("traces", data)
        self.assertIn("state", data)
        mock_orchestrator.execute_collaboration.assert_called_once()
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_execute_collaboration_custom_workflow(self, mock_orchestrator, mock_registry):
        """Test executing collaboration with custom workflow"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        mock_session = Mock(spec=CollaborationSession)
        mock_session.session_id = "session-123"
        mock_session.status = "completed"
        mock_session.traces = []
        mock_session.messages = []
        mock_session.state = {}
        mock_session.result = {}
        mock_session.completed_at = "2024-01-01T00:01:00Z"
        
        mock_orchestrator.execute_collaboration.return_value = mock_session
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate/session-123/execute',
            json={"workflow": ["agent-2", "agent-1"]}
        )
        
        self.assertEqual(response.status_code, 200)
        # Verify workflow was passed
        call_args = mock_orchestrator.execute_collaboration.call_args
        self.assertEqual(call_args[1]["workflow"], ["agent-2", "agent-1"])
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_execute_collaboration_session_not_found(self, mock_orchestrator, mock_registry):
        """Test executing collaboration with invalid session"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_orchestrator.execute_collaboration.side_effect = ValueError("Session not found")
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate/invalid-session/execute'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_get_collaboration_session(self, mock_orchestrator, mock_registry):
        """Test getting collaboration session"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        mock_session = Mock(spec=CollaborationSession)
        mock_session.to_dict.return_value = {
            "session_id": "session-123",
            "query": "Test query",
            "status": "completed"
        }
        
        mock_orchestrator.get_session.return_value = mock_session
        
        response = self._authenticated_request(
            'get',
            '/api/agents/collaborate/session-123'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["session_id"], "session-123")
        mock_orchestrator.get_session.assert_called_once_with("session-123")
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_get_session_not_found(self, mock_orchestrator, mock_registry):
        """Test getting non-existent session"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_orchestrator.get_session.return_value = None
        
        response = self._authenticated_request(
            'get',
            '/api/agents/collaborate/invalid-session'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_get_trace_visualization(self, mock_orchestrator, mock_registry):
        """Test getting trace visualization"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        visualization_data = {
            "session_id": "session-123",
            "query": "Test query",
            "timeline": [],
            "agents": {},
            "messages": []
        }
        
        mock_orchestrator.get_trace_visualization.return_value = visualization_data
        
        response = self._authenticated_request(
            'get',
            '/api/agents/collaborate/session-123/trace'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("session_id", data)
        self.assertIn("timeline", data)
        self.assertIn("agents", data)
        mock_orchestrator.get_trace_visualization.assert_called_once_with("session-123")
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_get_trace_visualization_error(self, mock_orchestrator, mock_registry):
        """Test getting trace visualization with error"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_orchestrator.get_trace_visualization.side_effect = ValueError("Session not found")
        
        response = self._authenticated_request(
            'get',
            '/api/agents/collaborate/invalid-session/trace'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_send_agent_message(self, mock_orchestrator, mock_registry):
        """Test sending message between agents"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        mock_message = Mock(spec=AgentMessage)
        mock_message.to_dict.return_value = {
            "id": "msg-1",
            "from_agent": "agent-1",
            "to_agent": "agent-2",
            "message_type": "data",
            "content": {"key": "value"},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        mock_orchestrator.send_message.return_value = mock_message
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate/session-123/message',
            json={
                "from_agent": "agent-1",
                "to_agent": "agent-2",
                "message_type": "data",
                "content": {"key": "value"}
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data["from_agent"], "agent-1")
        self.assertEqual(data["to_agent"], "agent-2")
        mock_orchestrator.send_message.assert_called_once()
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    def test_send_message_missing_fields(self, mock_registry):
        """Test sending message with missing fields"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate/session-123/message',
            json={
                "from_agent": "agent-1"
                # Missing to_agent and message_type
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    @patch('ai_agent_connector.app.api.routes.agent_orchestrator')
    def test_send_message_session_not_found(self, mock_orchestrator, mock_registry):
        """Test sending message to invalid session"""
        mock_registry.authenticate_agent.return_value = "test-agent-id"
        mock_orchestrator.send_message.side_effect = ValueError("Session not found")
        
        response = self._authenticated_request(
            'post',
            '/api/agents/collaborate/invalid-session/message',
            json={
                "from_agent": "agent-1",
                "to_agent": "agent-2",
                "message_type": "data",
                "content": {}
            }
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('ai_agent_connector.app.api.routes.agent_registry')
    def test_unauthenticated_request(self, mock_registry):
        """Test unauthenticated request"""
        mock_registry.authenticate_agent.return_value = None
        
        response = self.client.post(
            '/api/agents/collaborate',
            json={"query": "Test", "agents": []}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("error", data)


if __name__ == '__main__':
    unittest.main()


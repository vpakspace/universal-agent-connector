"""
Unit tests for multi-agent collaboration orchestrator
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
import uuid

from ai_agent_connector.app.utils.agent_orchestrator import (
    AgentOrchestrator,
    AgentRole,
    MessageType,
    AgentMessage,
    AgentTrace,
    CollaborationSession
)
from ai_agent_connector.app.agents.registry import AgentRegistry


class TestAgentOrchestrator(unittest.TestCase):
    """Test cases for AgentOrchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent_registry = Mock(spec=AgentRegistry)
        self.orchestrator = AgentOrchestrator(self.agent_registry)
    
    def test_create_session(self):
        """Test creating a collaboration session"""
        query = "Find all active users"
        agent_configs = [
            {"agent_id": "schema-agent", "role": "schema_researcher"},
            {"agent_id": "sql-agent", "role": "sql_generator"}
        ]
        
        session = self.orchestrator.create_session(
            query=query,
            agent_configs=agent_configs
        )
        
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.query, query)
        self.assertEqual(len(session.agents), 2)
        self.assertEqual(session.status, "pending")
        self.assertIn("schema-agent", session.agents)
        self.assertIn("sql-agent", session.agents)
        self.assertEqual(session.roles["schema-agent"], "schema_researcher")
        self.assertEqual(session.roles["sql-agent"], "sql_generator")
    
    def test_create_session_with_initial_state(self):
        """Test creating session with initial state"""
        query = "Find users"
        agent_configs = [{"agent_id": "agent-1", "role": "schema_researcher"}]
        initial_state = {"custom_key": "custom_value"}
        
        session = self.orchestrator.create_session(
            query=query,
            agent_configs=agent_configs,
            initial_state=initial_state
        )
        
        self.assertEqual(session.state, initial_state)
    
    def test_determine_workflow(self):
        """Test workflow determination based on roles"""
        query = "Test query"
        agent_configs = [
            {"agent_id": "validator", "role": "query_validator"},
            {"agent_id": "researcher", "role": "schema_researcher"},
            {"agent_id": "generator", "role": "sql_generator"},
            {"agent_id": "analyzer", "role": "result_analyzer"}
        ]
        
        session = self.orchestrator.create_session(query, agent_configs)
        workflow = self.orchestrator._determine_workflow(session)
        
        # Should be ordered by role priority
        self.assertEqual(workflow[0], "researcher")
        self.assertEqual(workflow[1], "generator")
        self.assertEqual(workflow[2], "validator")
        self.assertEqual(workflow[3], "analyzer")
    
    @patch('ai_agent_connector.app.utils.agent_orchestrator.NLToSQLConverter')
    def test_handle_schema_research(self, mock_converter_class):
        """Test schema research handler"""
        # Setup mock agent
        agent = {"agent_id": "schema-agent"}
        
        # Setup mock connector
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            ("users", "id", "integer"),
            ("users", "name", "varchar"),
            ("orders", "id", "integer"),
            ("orders", "user_id", "integer")
        ]
        
        self.agent_registry.get_database_connector.return_value = mock_connector
        
        input_data = {"query": "Find users"}
        session = Mock()
        
        result = self.orchestrator._handle_schema_research(
            agent, input_data, session
        )
        
        self.assertIn("schema_info", result)
        self.assertIn("tables", result)
        self.assertEqual(result["tables"], ["users", "orders"])
        self.assertEqual(result["researcher_agent"], "schema-agent")
        mock_connector.connect.assert_called_once()
        mock_connector.disconnect.assert_called_once()
    
    def test_handle_schema_research_no_connector(self):
        """Test schema research without database connector"""
        agent = {"agent_id": "schema-agent"}
        self.agent_registry.get_database_connector.return_value = None
        
        input_data = {"query": "Find users"}
        session = Mock()
        
        with self.assertRaises(ValueError) as context:
            self.orchestrator._handle_schema_research(agent, input_data, session)
        
        self.assertIn("database connection", str(context.exception))
    
    @patch('ai_agent_connector.app.utils.agent_orchestrator.NLToSQLConverter')
    def test_handle_sql_generation(self, mock_converter_class):
        """Test SQL generation handler"""
        # Setup mock converter
        mock_converter = Mock()
        mock_converter.convert_to_sql.return_value = {
            "sql": "SELECT * FROM users WHERE active = true",
            "model": "gpt-4"
        }
        mock_converter_class.return_value = mock_converter
        
        agent = {"agent_id": "sql-agent"}
        input_data = {
            "query": "Find active users",
            "state": {
                "schema_info": {
                    "users": {"columns": [{"name": "id"}, {"name": "active"}]}
                }
            }
        }
        session = Mock()
        
        result = self.orchestrator._handle_sql_generation(
            agent, input_data, session
        )
        
        self.assertIn("generated_sql", result)
        self.assertEqual(result["generated_sql"], "SELECT * FROM users WHERE active = true")
        self.assertEqual(result["generator_agent"], "sql-agent")
        mock_converter.convert_to_sql.assert_called_once()
    
    def test_handle_query_validation(self):
        """Test query validation handler"""
        agent = {"agent_id": "validator-agent"}
        input_data = {
            "state": {
                "generated_sql": "SELECT * FROM users WHERE id = 1"
            }
        }
        session = Mock()
        
        result = self.orchestrator._handle_query_validation(
            agent, input_data, session
        )
        
        self.assertIn("validation_results", result)
        self.assertTrue(result["validation_results"]["is_valid"])
        self.assertEqual(result["validator_agent"], "validator-agent")
        self.assertIn("validated_sql", result)
    
    def test_handle_query_validation_dangerous_query(self):
        """Test validation catches dangerous queries"""
        agent = {"agent_id": "validator-agent"}
        input_data = {
            "state": {
                "generated_sql": "DELETE FROM users"
            }
        }
        session = Mock()
        
        result = self.orchestrator._handle_query_validation(
            agent, input_data, session
        )
        
        self.assertFalse(result["validation_results"]["is_valid"])
        self.assertIn("DELETE without WHERE", str(result["validation_results"]["errors"]))
    
    def test_handle_result_analysis(self):
        """Test result analysis handler"""
        agent = {"agent_id": "analyzer-agent"}
        input_data = {
            "state": {
                "validated_sql": "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
            }
        }
        session = Mock()
        
        result = self.orchestrator._handle_result_analysis(
            agent, input_data, session
        )
        
        self.assertIn("analysis", result)
        self.assertEqual(result["analyzer_agent"], "analyzer-agent")
        self.assertIn("query_type", result["analysis"])
        self.assertIn("complexity", result["analysis"])
    
    def test_detect_query_type(self):
        """Test query type detection"""
        self.assertEqual(
            self.orchestrator._detect_query_type("SELECT * FROM users"),
            "SELECT"
        )
        self.assertEqual(
            self.orchestrator._detect_query_type("INSERT INTO users VALUES (1)"),
            "INSERT"
        )
        self.assertEqual(
            self.orchestrator._detect_query_type("UPDATE users SET name = 'test'"),
            "UPDATE"
        )
        self.assertEqual(
            self.orchestrator._detect_query_type("DELETE FROM users"),
            "DELETE"
        )
    
    def test_estimate_complexity(self):
        """Test query complexity estimation"""
        simple_query = "SELECT * FROM users"
        moderate_query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        complex_query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id GROUP BY users.id ORDER BY users.name"
        
        self.assertEqual(
            self.orchestrator._estimate_complexity(simple_query),
            "simple"
        )
        self.assertEqual(
            self.orchestrator._estimate_complexity(moderate_query),
            "moderate"
        )
        self.assertIn(
            self.orchestrator._estimate_complexity(complex_query),
            ["complex", "very_complex"]
        )
    
    def test_send_message(self):
        """Test sending message between agents"""
        session = self.orchestrator.create_session(
            query="Test",
            agent_configs=[
                {"agent_id": "agent-1", "role": "schema_researcher"},
                {"agent_id": "agent-2", "role": "sql_generator"}
            ]
        )
        
        message = self.orchestrator.send_message(
            session_id=session.session_id,
            from_agent="agent-1",
            to_agent="agent-2",
            message_type="data",
            content={"schema": "info"}
        )
        
        self.assertIsNotNone(message.id)
        self.assertEqual(message.from_agent, "agent-1")
        self.assertEqual(message.to_agent, "agent-2")
        self.assertEqual(message.message_type, "data")
        self.assertEqual(len(session.messages), 1)
    
    def test_send_message_invalid_session(self):
        """Test sending message to invalid session"""
        with self.assertRaises(ValueError) as context:
            self.orchestrator.send_message(
                session_id="invalid-id",
                from_agent="agent-1",
                to_agent="agent-2",
                message_type="data",
                content={}
            )
        
        self.assertIn("not found", str(context.exception))
    
    def test_get_session(self):
        """Test retrieving session"""
        session = self.orchestrator.create_session(
            query="Test",
            agent_configs=[{"agent_id": "agent-1", "role": "schema_researcher"}]
        )
        
        retrieved = self.orchestrator.get_session(session.session_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.session_id, session.session_id)
        self.assertEqual(retrieved.query, "Test")
    
    def test_get_session_not_found(self):
        """Test retrieving non-existent session"""
        result = self.orchestrator.get_session("non-existent")
        self.assertIsNone(result)
    
    @patch.object(AgentOrchestrator, '_execute_agent_task')
    def test_execute_collaboration(self, mock_execute_task):
        """Test executing collaboration workflow"""
        # Setup mock trace
        mock_trace = AgentTrace(
            agent_id="agent-1",
            role="schema_researcher",
            action="schema_researcher_task",
            input={},
            output={"schema_info": {}},
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=100.0,
            status="success"
        )
        mock_execute_task.return_value = mock_trace
        
        # Setup mock agent
        self.agent_registry.get_agent.return_value = {"agent_id": "agent-1"}
        
        session = self.orchestrator.create_session(
            query="Test query",
            agent_configs=[{"agent_id": "agent-1", "role": "schema_researcher"}]
        )
        
        result = self.orchestrator.execute_collaboration(session.session_id)
        
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.completed_at)
        self.assertEqual(len(result.traces), 1)
        mock_execute_task.assert_called_once()
    
    def test_execute_collaboration_custom_workflow(self):
        """Test executing collaboration with custom workflow"""
        session = self.orchestrator.create_session(
            query="Test",
            agent_configs=[
                {"agent_id": "agent-1", "role": "schema_researcher"},
                {"agent_id": "agent-2", "role": "sql_generator"}
            ]
        )
        
        # Mock agent registry
        self.agent_registry.get_agent.return_value = {"agent_id": "agent-1"}
        
        # Mock execute task to avoid actual execution
        with patch.object(self.orchestrator, '_execute_agent_task') as mock_execute:
            mock_trace = AgentTrace(
                agent_id="agent-2",
                role="sql_generator",
                action="sql_generator_task",
                input={},
                output={},
                timestamp=datetime.utcnow().isoformat(),
                status="success"
            )
            mock_execute.return_value = mock_trace
            
            result = self.orchestrator.execute_collaboration(
                session.session_id,
                workflow=["agent-2", "agent-1"]  # Custom order
            )
            
            # Should execute in custom order
            self.assertEqual(result.status, "completed")
            self.assertEqual(len(mock_execute.call_args_list), 2)
    
    def test_execute_collaboration_session_not_found(self):
        """Test executing collaboration with invalid session"""
        with self.assertRaises(ValueError) as context:
            self.orchestrator.execute_collaboration("invalid-session-id")
        
        self.assertIn("not found", str(context.exception))
    
    @patch.object(AgentOrchestrator, '_execute_agent_task')
    def test_execute_collaboration_error_handling(self, mock_execute_task):
        """Test error handling during collaboration"""
        mock_execute_task.side_effect = Exception("Test error")
        
        self.agent_registry.get_agent.return_value = {"agent_id": "agent-1"}
        
        session = self.orchestrator.create_session(
            query="Test",
            agent_configs=[{"agent_id": "agent-1", "role": "schema_researcher"}]
        )
        
        with self.assertRaises(Exception):
            self.orchestrator.execute_collaboration(session.session_id)
        
        # Check session status
        updated_session = self.orchestrator.get_session(session.session_id)
        self.assertEqual(updated_session.status, "failed")
        self.assertIsNotNone(updated_session.completed_at)
    
    def test_get_trace_visualization(self):
        """Test getting trace visualization"""
        session = self.orchestrator.create_session(
            query="Test query",
            agent_configs=[
                {"agent_id": "agent-1", "role": "schema_researcher"},
                {"agent_id": "agent-2", "role": "sql_generator"}
            ]
        )
        
        # Add some traces
        trace1 = AgentTrace(
            agent_id="agent-1",
            role="schema_researcher",
            action="schema_researcher_task",
            input={},
            output={},
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=100.0,
            status="success"
        )
        trace2 = AgentTrace(
            agent_id="agent-2",
            role="sql_generator",
            action="sql_generator_task",
            input={},
            output={},
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=200.0,
            status="success"
        )
        session.traces = [trace1, trace2]
        
        visualization = self.orchestrator.get_trace_visualization(session.session_id)
        
        self.assertIn("session_id", visualization)
        self.assertIn("timeline", visualization)
        self.assertIn("agents", visualization)
        self.assertIn("messages", visualization)
        self.assertEqual(len(visualization["timeline"]), 2)
        self.assertIn("agent-1", visualization["agents"])
        self.assertIn("agent-2", visualization["agents"])
    
    def test_get_trace_visualization_not_found(self):
        """Test getting visualization for non-existent session"""
        with self.assertRaises(ValueError) as context:
            self.orchestrator.get_trace_visualization("invalid-id")
        
        self.assertIn("not found", str(context.exception))


class TestAgentMessage(unittest.TestCase):
    """Test cases for AgentMessage"""
    
    def test_agent_message_creation(self):
        """Test creating agent message"""
        message = AgentMessage(
            id="msg-1",
            from_agent="agent-1",
            to_agent="agent-2",
            message_type="data",
            content={"key": "value"},
            timestamp="2024-01-01T00:00:00Z"
        )
        
        self.assertEqual(message.from_agent, "agent-1")
        self.assertEqual(message.to_agent, "agent-2")
        self.assertEqual(message.message_type, "data")
    
    def test_agent_message_to_dict(self):
        """Test converting message to dict"""
        message = AgentMessage(
            id="msg-1",
            from_agent="agent-1",
            to_agent="agent-2",
            message_type="request",
            content={},
            timestamp="2024-01-01T00:00:00Z"
        )
        
        data = message.to_dict()
        self.assertIn("id", data)
        self.assertIn("from_agent", data)
        self.assertIn("to_agent", data)
    
    def test_agent_message_from_dict(self):
        """Test creating message from dict"""
        data = {
            "id": "msg-1",
            "from_agent": "agent-1",
            "to_agent": "agent-2",
            "message_type": "response",
            "content": {"result": "success"},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        message = AgentMessage.from_dict(data)
        self.assertEqual(message.id, "msg-1")
        self.assertEqual(message.from_agent, "agent-1")


class TestAgentTrace(unittest.TestCase):
    """Test cases for AgentTrace"""
    
    def test_agent_trace_creation(self):
        """Test creating agent trace"""
        trace = AgentTrace(
            agent_id="agent-1",
            role="schema_researcher",
            action="research_schema",
            input={"query": "test"},
            output={"schema": "info"},
            timestamp="2024-01-01T00:00:00Z",
            duration_ms=150.5,
            status="success"
        )
        
        self.assertEqual(trace.agent_id, "agent-1")
        self.assertEqual(trace.role, "schema_researcher")
        self.assertEqual(trace.duration_ms, 150.5)
        self.assertEqual(trace.status, "success")
    
    def test_agent_trace_to_dict(self):
        """Test converting trace to dict"""
        trace = AgentTrace(
            agent_id="agent-1",
            role="sql_generator",
            action="generate_sql",
            input={},
            output={},
            timestamp="2024-01-01T00:00:00Z",
            status="success"
        )
        
        data = trace.to_dict()
        self.assertIn("agent_id", data)
        self.assertIn("role", data)
        self.assertIn("action", data)


class TestCollaborationSession(unittest.TestCase):
    """Test cases for CollaborationSession"""
    
    def test_session_creation(self):
        """Test creating collaboration session"""
        session = CollaborationSession(
            session_id="session-1",
            query="Test query",
            agents=["agent-1", "agent-2"],
            roles={"agent-1": "schema_researcher", "agent-2": "sql_generator"},
            messages=[],
            traces=[],
            state={},
            status="pending",
            created_at="2024-01-01T00:00:00Z"
        )
        
        self.assertEqual(session.session_id, "session-1")
        self.assertEqual(len(session.agents), 2)
        self.assertEqual(session.status, "pending")
    
    def test_session_to_dict(self):
        """Test converting session to dict"""
        session = CollaborationSession(
            session_id="session-1",
            query="Test",
            agents=["agent-1"],
            roles={"agent-1": "schema_researcher"},
            messages=[],
            traces=[],
            state={},
            status="completed",
            created_at="2024-01-01T00:00:00Z",
            completed_at="2024-01-01T00:01:00Z"
        )
        
        data = session.to_dict()
        self.assertIn("session_id", data)
        self.assertIn("query", data)
        self.assertIn("agents", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "completed")


if __name__ == '__main__':
    unittest.main()


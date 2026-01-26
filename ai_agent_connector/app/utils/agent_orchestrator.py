"""
Multi-Agent Collaboration System
Orchestrates multiple agents to collaborate on complex queries
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

from ..agents.registry import AgentRegistry
from ..db import DatabaseConnector


class AgentRole(Enum):
    """Agent roles in collaboration"""
    SCHEMA_RESEARCHER = "schema_researcher"
    SQL_GENERATOR = "sql_generator"
    QUERY_VALIDATOR = "query_validator"
    RESULT_ANALYZER = "result_analyzer"
    COORDINATOR = "coordinator"


class MessageType(Enum):
    """Message types in agent communication"""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"
    DATA = "data"


@dataclass
class AgentMessage:
    """Message between agents"""
    id: str
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        return cls(**data)


@dataclass
class AgentTrace:
    """Trace of agent activity"""
    agent_id: str
    role: str
    action: str
    input: Optional[Dict[str, Any]]
    output: Optional[Dict[str, Any]]
    timestamp: str
    duration_ms: Optional[float] = None
    status: str = "success"  # success, error, pending
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTrace':
        return cls(**data)


@dataclass
class CollaborationSession:
    """Multi-agent collaboration session"""
    session_id: str
    query: str
    agents: List[str]  # Agent IDs
    roles: Dict[str, str]  # agent_id -> role
    messages: List[AgentMessage]
    traces: List[AgentTrace]
    state: Dict[str, Any]
    status: str  # pending, in_progress, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'query': self.query,
            'agents': self.agents,
            'roles': self.roles,
            'messages': [m.to_dict() for m in self.messages],
            'traces': [t.to_dict() for t in self.traces],
            'state': self.state,
            'status': self.status,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'result': self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationSession':
        messages = [AgentMessage.from_dict(m) for m in data.get('messages', [])]
        traces = [AgentTrace.from_dict(t) for t in data.get('traces', [])]
        return cls(
            session_id=data['session_id'],
            query=data['query'],
            agents=data['agents'],
            roles=data['roles'],
            messages=messages,
            traces=traces,
            state=data.get('state', {}),
            status=data['status'],
            created_at=data['created_at'],
            completed_at=data.get('completed_at'),
            result=data.get('result')
        )


class AgentOrchestrator:
    """Orchestrates multi-agent collaboration"""
    
    def __init__(self, agent_registry: AgentRegistry):
        """
        Initialize orchestrator
        
        Args:
            agent_registry: Agent registry instance
        """
        self.agent_registry = agent_registry
        self.sessions: Dict[str, CollaborationSession] = {}
        self._agent_handlers: Dict[str, Callable] = {
            AgentRole.SCHEMA_RESEARCHER.value: self._handle_schema_research,
            AgentRole.SQL_GENERATOR.value: self._handle_sql_generation,
            AgentRole.QUERY_VALIDATOR.value: self._handle_query_validation,
            AgentRole.RESULT_ANALYZER.value: self._handle_result_analysis,
        }
    
    def create_session(
        self,
        query: str,
        agent_configs: List[Dict[str, str]],
        initial_state: Optional[Dict[str, Any]] = None
    ) -> CollaborationSession:
        """
        Create a new collaboration session
        
        Args:
            query: The query/problem to solve
            agent_configs: List of {agent_id, role} dicts
            initial_state: Initial collaboration state
            
        Returns:
            CollaborationSession
        """
        session_id = str(uuid.uuid4())
        
        agents = [config['agent_id'] for config in agent_configs]
        roles = {config['agent_id']: config['role'] for config in agent_configs}
        
        session = CollaborationSession(
            session_id=session_id,
            query=query,
            agents=agents,
            roles=roles,
            messages=[],
            traces=[],
            state=initial_state or {},
            status='pending',
            created_at=datetime.utcnow().isoformat()
        )
        
        self.sessions[session_id] = session
        return session
    
    def execute_collaboration(
        self,
        session_id: str,
        workflow: Optional[List[str]] = None
    ) -> CollaborationSession:
        """
        Execute agent collaboration workflow
        
        Args:
            session_id: Session ID
            workflow: Optional workflow sequence (agent IDs), defaults to role-based order
            
        Returns:
            Updated CollaborationSession
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = 'in_progress'
        
        # Default workflow: schema_researcher -> sql_generator -> query_validator -> result_analyzer
        if not workflow:
            workflow = self._determine_workflow(session)
        
        try:
            for agent_id in workflow:
                if agent_id not in session.agents:
                    continue
                
                role = session.roles[agent_id]
                handler = self._agent_handlers.get(role)
                
                if handler:
                    trace = self._execute_agent_task(
                        session=session,
                        agent_id=agent_id,
                        role=role,
                        handler=handler
                    )
                    session.traces.append(trace)
                    
                    # Update state with agent output
                    if trace.output:
                        session.state.update(trace.output)
            
            session.status = 'completed'
            session.completed_at = datetime.utcnow().isoformat()
            
        except Exception as e:
            session.status = 'failed'
            session.completed_at = datetime.utcnow().isoformat()
            session.result = {'error': str(e)}
            raise
        
        return session
    
    def _determine_workflow(self, session: CollaborationSession) -> List[str]:
        """Determine execution workflow based on roles"""
        # Map roles to execution order
        role_order = {
            AgentRole.SCHEMA_RESEARCHER.value: 1,
            AgentRole.SQL_GENERATOR.value: 2,
            AgentRole.QUERY_VALIDATOR.value: 3,
            AgentRole.RESULT_ANALYZER.value: 4,
        }
        
        # Sort agents by role order
        sorted_agents = sorted(
            session.agents,
            key=lambda agent_id: role_order.get(session.roles[agent_id], 99)
        )
        
        return sorted_agents
    
    def _execute_agent_task(
        self,
        session: CollaborationSession,
        agent_id: str,
        role: str,
        handler: Callable
    ) -> AgentTrace:
        """Execute a task for a specific agent"""
        start_time = datetime.utcnow()
        
        try:
            agent = self.agent_registry.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Prepare input from session state and query
            input_data = {
                'query': session.query,
                'state': session.state.copy(),
                'previous_traces': [t.to_dict() for t in session.traces]
            }
            
            # Execute handler
            output = handler(agent, input_data, session)
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentTrace(
                agent_id=agent_id,
                role=role,
                action=f"{role}_task",
                input=input_data,
                output=output,
                timestamp=start_time.isoformat(),
                duration_ms=duration,
                status='success'
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AgentTrace(
                agent_id=agent_id,
                role=role,
                action=f"{role}_task",
                input={'query': session.query, 'state': session.state},
                output={'error': str(e)},
                timestamp=start_time.isoformat(),
                duration_ms=duration,
                status='error'
            )
    
    def _handle_schema_research(
        self,
        agent: Dict[str, Any],
        input_data: Dict[str, Any],
        session: CollaborationSession
    ) -> Dict[str, Any]:
        """Handle schema research task"""
        query = input_data['query']
        
        # Get database connector
        agent_id = agent.get('agent_id')
        if not agent_id:
            agent_id = agent.get('id')
        
        connector = self.agent_registry.get_database_connector(agent_id)
        if not connector:
            raise ValueError("Agent does not have database connection")
        
        try:
            connector.connect()
            
            # Research schema - get relevant tables and columns
            schema_query = """
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type
                FROM information_schema.tables t
                JOIN information_schema.columns c 
                    ON t.table_schema = c.table_schema 
                    AND t.table_name = c.table_name
                WHERE t.table_type = 'BASE TABLE'
                    AND t.table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY t.table_name, c.ordinal_position
            """
            
            result = connector.execute_query(schema_query, fetch=True)
            
            # Organize schema info
            schema_info = {}
            for row in result:
                table, column, dtype = row
                if table not in schema_info:
                    schema_info[table] = []
                schema_info[table].append({'name': column, 'type': dtype})
            
            return {
                'schema_info': schema_info,
                'tables': list(schema_info.keys()),
                'researcher_agent': agent['agent_id']
            }
            
        finally:
            try:
                connector.disconnect()
            except Exception:
                pass
    
    def _handle_sql_generation(
        self,
        agent: Dict[str, Any],
        input_data: Dict[str, Any],
        session: CollaborationSession
    ) -> Dict[str, Any]:
        """Handle SQL generation task"""
        query = input_data['query']
        state = input_data.get('state', {})
        schema_info = state.get('schema_info', {})
        
        # Use NL to SQL converter
        from .nl_to_sql import NLToSQLConverter
        
        converter = NLToSQLConverter()
        
        # Format schema for NL to SQL
        formatted_schema = {}
        if schema_info:
            for table, columns in schema_info.items():
                formatted_schema[table] = {
                    'columns': columns
                }
        
        schema_dict = {
            'schema': formatted_schema,
            'tables': list(formatted_schema.keys())
        }
        
        # Convert to SQL
        result = converter.convert_to_sql(
            natural_language_query=query,
            schema_info=schema_dict,
            database_type="PostgreSQL"
        )
        
        sql_query = result.get('sql')
        if not sql_query:
            raise ValueError(f"Failed to generate SQL: {result.get('error', 'Unknown error')}")
        
        agent_id = agent.get('agent_id') or agent.get('id')
        return {
            'generated_sql': sql_query,
            'generator_agent': agent_id,
            'model_used': result.get('model')
        }
    
    def _handle_query_validation(
        self,
        agent: Dict[str, Any],
        input_data: Dict[str, Any],
        session: CollaborationSession
    ) -> Dict[str, Any]:
        """Handle query validation task"""
        state = input_data.get('state', {})
        sql_query = state.get('generated_sql')
        
        if not sql_query:
            raise ValueError("No SQL query to validate")
        
        # Basic validation
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check for common issues
        sql_lower = sql_query.lower()
        
        if 'drop' in sql_lower or 'truncate' in sql_lower:
            validation_results['warnings'].append("Query contains DROP or TRUNCATE statements")
        
        if 'delete' in sql_lower and 'where' not in sql_lower:
            validation_results['errors'].append("DELETE without WHERE clause")
            validation_results['is_valid'] = False
        
        if 'update' in sql_lower and 'where' not in sql_lower:
            validation_results['errors'].append("UPDATE without WHERE clause")
            validation_results['is_valid'] = False
        
        # Check syntax (basic)
        if not sql_query.strip().endswith(';'):
            validation_results['warnings'].append("Query missing semicolon")
        
        agent_id = agent.get('agent_id') or agent.get('id')
        return {
            'validation_results': validation_results,
            'validator_agent': agent_id,
            'validated_sql': sql_query if validation_results['is_valid'] else None
        }
    
    def _handle_result_analysis(
        self,
        agent: Dict[str, Any],
        input_data: Dict[str, Any],
        session: CollaborationSession
    ) -> Dict[str, Any]:
        """Handle result analysis task"""
        state = input_data.get('state', {})
        sql_query = state.get('validated_sql') or state.get('generated_sql')
        
        agent_id = agent.get('agent_id') or agent.get('id')
        if not sql_query:
            return {
                'analysis': 'No SQL query available for analysis',
                'analyzer_agent': agent_id
            }
        
        # Analyze query characteristics
        analysis = {
            'query_type': self._detect_query_type(sql_query),
            'complexity': self._estimate_complexity(sql_query),
            'estimated_rows': 'unknown',
            'notes': []
        }
        
        sql_lower = sql_query.lower()
        if 'join' in sql_lower:
            analysis['notes'].append("Query contains JOINs")
        if 'group by' in sql_lower:
            analysis['notes'].append("Query contains aggregations")
        if 'order by' in sql_lower:
            analysis['notes'].append("Query contains sorting")
        
        agent_id = agent.get('agent_id') or agent.get('id')
        return {
            'analysis': analysis,
            'analyzer_agent': agent_id,
            'final_sql': sql_query
        }
    
    def _detect_query_type(self, sql: str) -> str:
        """Detect SQL query type"""
        sql_lower = sql.strip().lower()
        if sql_lower.startswith('select'):
            return 'SELECT'
        elif sql_lower.startswith('insert'):
            return 'INSERT'
        elif sql_lower.startswith('update'):
            return 'UPDATE'
        elif sql_lower.startswith('delete'):
            return 'DELETE'
        else:
            return 'UNKNOWN'
    
    def _estimate_complexity(self, sql: str) -> str:
        """Estimate query complexity"""
        sql_lower = sql.lower()
        complexity_score = 0
        
        if 'join' in sql_lower:
            complexity_score += 2
        if 'group by' in sql_lower:
            complexity_score += 1
        if 'order by' in sql_lower:
            complexity_score += 1
        if 'union' in sql_lower:
            complexity_score += 2
        if 'subquery' in sql_lower or '(' in sql_lower and 'select' in sql_lower:
            complexity_score += 2
        
        if complexity_score == 0:
            return 'simple'
        elif complexity_score <= 2:
            return 'moderate'
        elif complexity_score <= 4:
            return 'complex'
        else:
            return 'very_complex'
    
    def send_message(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any]
    ) -> AgentMessage:
        """Send a message between agents"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        message = AgentMessage(
            id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        
        session.messages.append(message)
        return message
    
    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get collaboration session"""
        return self.sessions.get(session_id)
    
    def get_trace_visualization(self, session_id: str) -> Dict[str, Any]:
        """Get trace visualization data"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Build visualization structure
        visualization = {
            'session_id': session_id,
            'query': session.query,
            'timeline': [],
            'agents': {},
            'messages': [m.to_dict() for m in session.messages],
            'state_evolution': []
        }
        
        # Build timeline from traces
        for trace in session.traces:
            timeline_entry = {
                'timestamp': trace.timestamp,
                'agent_id': trace.agent_id,
                'role': trace.role,
                'action': trace.action,
                'duration_ms': trace.duration_ms,
                'status': trace.status
            }
            visualization['timeline'].append(timeline_entry)
            
            # Track agent activity
            if trace.agent_id not in visualization['agents']:
                visualization['agents'][trace.agent_id] = {
                    'role': trace.role,
                    'traces': [],
                    'total_duration_ms': 0
                }
            
            visualization['agents'][trace.agent_id]['traces'].append(trace.to_dict())
            if trace.duration_ms:
                visualization['agents'][trace.agent_id]['total_duration_ms'] += trace.duration_ms
        
        # Sort timeline by timestamp
        visualization['timeline'].sort(key=lambda x: x['timestamp'])
        
        return visualization


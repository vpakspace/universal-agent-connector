"""
Setup wizard for first-time database and agent connection
Guides users through connecting their first database and agent
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class SetupStep(Enum):
    """Setup wizard steps"""
    WELCOME = "welcome"
    DATABASE_TYPE = "database_type"
    DATABASE_CONNECTION = "database_connection"
    DATABASE_TEST = "database_test"
    AGENT_REGISTRATION = "agent_registration"
    AGENT_CREDENTIALS = "agent_credentials"
    COMPLETE = "complete"


@dataclass
class SetupSession:
    """A setup wizard session"""
    session_id: str
    current_step: SetupStep
    database_type: Optional[str] = None
    database_config: Dict[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None
    agent_info: Dict[str, Any] = field(default_factory=dict)
    agent_credentials: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'current_step': self.current_step.value,
            'database_type': self.database_type,
            'database_config': self.database_config,
            'agent_id': self.agent_id,
            'agent_info': self.agent_info,
            'agent_credentials': self.agent_credentials,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'errors': self.errors
        }


class SetupWizard:
    """
    Manages setup wizard sessions.
    """
    
    def __init__(self):
        """Initialize setup wizard"""
        # session_id -> SetupSession
        self._sessions: Dict[str, SetupSession] = {}
    
    def create_session(self) -> SetupSession:
        """
        Create a new setup session.
        
        Returns:
            SetupSession object
        """
        session_id = str(uuid.uuid4())
        
        session = SetupSession(
            session_id=session_id,
            current_step=SetupStep.WELCOME
        )
        
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SetupSession]:
        """Get a setup session"""
        return self._sessions.get(session_id)
    
    def update_step(
        self,
        session_id: str,
        step: SetupStep,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[SetupSession]:
        """
        Update setup session step.
        
        Args:
            session_id: Session ID
            step: New step
            data: Optional step data
            
        Returns:
            Updated SetupSession or None if not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        session.current_step = step
        
        if data:
            if step == SetupStep.DATABASE_TYPE:
                session.database_type = data.get('database_type')
            elif step == SetupStep.DATABASE_CONNECTION:
                session.database_config.update(data)
            elif step == SetupStep.AGENT_REGISTRATION:
                session.agent_id = data.get('agent_id')
                session.agent_info.update(data.get('agent_info', {}))
            elif step == SetupStep.AGENT_CREDENTIALS:
                session.agent_credentials.update(data)
            elif step == SetupStep.COMPLETE:
                session.completed_at = datetime.utcnow().isoformat()
        
        return session
    
    def add_error(self, session_id: str, error: str) -> bool:
        """Add an error to the session"""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.errors.append(error)
        return True
    
    def clear_errors(self, session_id: str) -> bool:
        """Clear errors from the session"""
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.errors.clear()
        return True
    
    def get_next_step(self, current_step: SetupStep) -> Optional[SetupStep]:
        """Get the next step in the wizard"""
        step_order = [
            SetupStep.WELCOME,
            SetupStep.DATABASE_TYPE,
            SetupStep.DATABASE_CONNECTION,
            SetupStep.DATABASE_TEST,
            SetupStep.AGENT_REGISTRATION,
            SetupStep.AGENT_CREDENTIALS,
            SetupStep.COMPLETE
        ]
        
        try:
            current_index = step_order.index(current_step)
            if current_index < len(step_order) - 1:
                return step_order[current_index + 1]
        except ValueError:
            pass
        
        return None
    
    def get_previous_step(self, current_step: SetupStep) -> Optional[SetupStep]:
        """Get the previous step in the wizard"""
        step_order = [
            SetupStep.WELCOME,
            SetupStep.DATABASE_TYPE,
            SetupStep.DATABASE_CONNECTION,
            SetupStep.DATABASE_TEST,
            SetupStep.AGENT_REGISTRATION,
            SetupStep.AGENT_CREDENTIALS,
            SetupStep.COMPLETE
        ]
        
        try:
            current_index = step_order.index(current_step)
            if current_index > 0:
                return step_order[current_index - 1]
        except ValueError:
            pass
        
        return None
    
    def get_step_instructions(self, step: SetupStep) -> Dict[str, Any]:
        """
        Get instructions for a setup step.
        
        Args:
            step: Setup step
            
        Returns:
            Dict with step instructions
        """
        instructions = {
            SetupStep.WELCOME: {
                'title': 'Welcome to the Setup Wizard',
                'description': 'This wizard will guide you through connecting your first database and registering your agent.',
                'estimated_time': '5 minutes',
                'fields': []
            },
            SetupStep.DATABASE_TYPE: {
                'title': 'Select Database Type',
                'description': 'Choose the type of database you want to connect.',
                'estimated_time': '30 seconds',
                'fields': [
                    {
                        'name': 'database_type',
                        'type': 'select',
                        'label': 'Database Type',
                        'options': ['postgresql', 'mysql', 'mongodb', 'bigquery', 'snowflake'],
                        'required': True
                    }
                ]
            },
            SetupStep.DATABASE_CONNECTION: {
                'title': 'Database Connection',
                'description': 'Enter your database connection details.',
                'estimated_time': '2 minutes',
                'fields': [
                    {
                        'name': 'connection_string',
                        'type': 'text',
                        'label': 'Connection String (optional)',
                        'placeholder': 'postgresql://user:pass@host:5432/db',
                        'required': False
                    },
                    {
                        'name': 'host',
                        'type': 'text',
                        'label': 'Host',
                        'placeholder': 'db.example.com',
                        'required': False
                    },
                    {
                        'name': 'port',
                        'type': 'number',
                        'label': 'Port',
                        'placeholder': '5432',
                        'required': False
                    },
                    {
                        'name': 'user',
                        'type': 'text',
                        'label': 'Username',
                        'required': False
                    },
                    {
                        'name': 'password',
                        'type': 'password',
                        'label': 'Password',
                        'required': False
                    },
                    {
                        'name': 'database',
                        'type': 'text',
                        'label': 'Database Name',
                        'required': False
                    }
                ]
            },
            SetupStep.DATABASE_TEST: {
                'title': 'Test Database Connection',
                'description': 'Testing your database connection...',
                'estimated_time': '30 seconds',
                'fields': []
            },
            SetupStep.AGENT_REGISTRATION: {
                'title': 'Register Your Agent',
                'description': 'Provide information about your agent.',
                'estimated_time': '1 minute',
                'fields': [
                    {
                        'name': 'agent_id',
                        'type': 'text',
                        'label': 'Agent ID',
                        'placeholder': 'my-agent',
                        'required': True
                    },
                    {
                        'name': 'name',
                        'type': 'text',
                        'label': 'Agent Name',
                        'placeholder': 'My AI Agent',
                        'required': False
                    },
                    {
                        'name': 'description',
                        'type': 'textarea',
                        'label': 'Description',
                        'placeholder': 'Describe your agent...',
                        'required': False
                    }
                ]
            },
            SetupStep.AGENT_CREDENTIALS: {
                'title': 'Agent Credentials',
                'description': 'Set up credentials for your agent.',
                'estimated_time': '30 seconds',
                'fields': [
                    {
                        'name': 'api_key',
                        'type': 'text',
                        'label': 'API Key (optional, will be generated if not provided)',
                        'required': False
                    },
                    {
                        'name': 'api_secret',
                        'type': 'password',
                        'label': 'API Secret (optional, will be generated if not provided)',
                        'required': False
                    }
                ]
            },
            SetupStep.COMPLETE: {
                'title': 'Setup Complete!',
                'description': 'Your database and agent have been successfully configured.',
                'estimated_time': '0 seconds',
                'fields': []
            }
        }
        
        return instructions.get(step, {
            'title': 'Unknown Step',
            'description': '',
            'estimated_time': '0 seconds',
            'fields': []
        })
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a setup session"""
        if session_id not in self._sessions:
            return False
        
        del self._sessions[session_id]
        return True


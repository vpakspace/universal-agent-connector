"""
Unit tests for credential rotation functionality
Tests zero-downtime credential updates
"""

import pytest
from unittest.mock import MagicMock, patch

from ai_agent_connector.app.agents.registry import AgentRegistry
from ai_agent_connector.app.utils.encryption import reset_encryptor


class TestCredentialRotation:
    """Test cases for credential rotation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset encryptor before each test"""
        reset_encryptor()
        yield
        reset_encryptor()
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_credentials_staging(self, mock_connector_cls):
        """Test staging new credentials for rotation"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register agent with initial credentials
        registry.register_agent(
            agent_id='agent-rotate',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldpass',
                'database': 'testdb'
            }
        )
        
        # Rotate to new credentials
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'testdb'
        }
        
        result = registry.rotate_database_credentials(
            agent_id='agent-rotate',
            new_database_config=new_config,
            validate_before_activate=True
        )
        
        assert result['status'] == 'staging'
        assert 'staged_at' in result
        assert 'agent-rotate' in registry._pending_database_configs
        
        # Check rotation status
        rotation_status = registry.get_credential_rotation_status('agent-rotate')
        assert rotation_status['status'] == 'staging'
        assert rotation_status['validated'] is True
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_credentials_validation_failure(self, mock_connector_cls):
        """Test that invalid credentials are rejected during rotation"""
        mock_connector = MagicMock()
        mock_connector.connect.side_effect = ConnectionError("Connection failed")
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register agent
        registry.register_agent(
            agent_id='agent-invalid',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db'
            }
        )
        
        # Try to rotate with invalid credentials
        invalid_config = {
            'type': 'postgresql',
            'host': 'invalid-host',
            'user': 'user',
            'password': 'wrongpass',
            'database': 'db'
        }
        
        with pytest.raises(ValueError, match="New credentials validation failed"):
            registry.rotate_database_credentials(
                agent_id='agent-invalid',
                new_database_config=invalid_config,
                validate_before_activate=True
            )
        
        # Should not have staged credentials
        assert 'agent-invalid' not in registry._pending_database_configs
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_credentials_type_mismatch(self, mock_connector_cls):
        """Test that rotating to different database type is rejected"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register with PostgreSQL
        registry.register_agent(
            agent_id='agent-type',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db'
            }
        )
        
        # Try to rotate to MySQL
        mysql_config = {
            'type': 'mysql',
            'host': 'localhost',
            'user': 'user',
            'password': 'pass',
            'database': 'db'
        }
        
        with pytest.raises(ValueError, match="database type mismatch"):
            registry.rotate_database_credentials(
                agent_id='agent-type',
                new_database_config=mysql_config
            )
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_activate_rotated_credentials(self, mock_connector_cls):
        """Test activating staged credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register and rotate
        registry.register_agent(
            agent_id='agent-activate',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldpass',
                'database': 'testdb'
            }
        )
        
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'testdb'
        }
        
        registry.rotate_database_credentials('agent-activate', new_config)
        
        # Activate
        result = registry.activate_rotated_credentials('agent-activate')
        
        assert result['status'] == 'active'
        assert 'activated_at' in result
        
        # Staged credentials should be removed
        assert 'agent-activate' not in registry._pending_database_configs
        
        # Active config should be updated
        active_config = registry._decrypt_database_config(
            registry._agent_database_configs['agent-activate']
        )
        assert active_config['user'] == 'newuser'
        assert active_config['password'] == 'newpass'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_activate_fails_if_validation_fails(self, mock_connector_cls):
        """Test that activation fails if staged credentials no longer work"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register and rotate
        registry.register_agent(
            agent_id='agent-activate-fail',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db'
            }
        )
        
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'db'
        }
        
        registry.rotate_database_credentials('agent-activate-fail', new_config)
        
        # Make staged credentials fail validation
        mock_connector.connect.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(ValueError, match="Cannot activate credentials"):
            registry.activate_rotated_credentials('agent-activate-fail')
        
        # Should still have staged credentials
        assert 'agent-activate-fail' in registry._pending_database_configs
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rollback_credential_rotation(self, mock_connector_cls):
        """Test rolling back credential rotation"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register and rotate
        registry.register_agent(
            agent_id='agent-rollback',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldpass',
                'database': 'testdb'
            }
        )
        
        old_config = registry._decrypt_database_config(
            registry._agent_database_configs['agent-rollback']
        )
        
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'testdb'
        }
        
        registry.rotate_database_credentials('agent-rollback', new_config)
        
        # Rollback
        result = registry.rollback_credential_rotation('agent-rollback')
        
        assert result['status'] == 'rolled_back'
        assert 'rolled_back_at' in result
        
        # Staged credentials should be removed
        assert 'agent-rollback' not in registry._pending_database_configs
        
        # Active config should remain unchanged
        current_config = registry._decrypt_database_config(
            registry._agent_database_configs['agent-rollback']
        )
        assert current_config['user'] == old_config['user']
        assert current_config['password'] == old_config['password']
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_get_connector_uses_staged_credentials(self, mock_connector_cls):
        """Test that get_database_connector uses staged credentials during rotation"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register and rotate
        registry.register_agent(
            agent_id='agent-staged',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldpass',
                'database': 'testdb'
            }
        )
        
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'testdb'
        }
        
        registry.rotate_database_credentials('agent-staged', new_config)
        
        # Get connector should use staged credentials if they work
        connector = registry.get_database_connector('agent-staged')
        assert connector is not None
        
        # Verify connector was built (will use staged if they work)
        assert mock_connector_cls.called
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_get_connector_fallback_to_active_on_staged_failure(self, mock_connector_cls):
        """Test that connector falls back to active credentials if staged fail"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register and rotate
        registry.register_agent(
            agent_id='agent-fallback',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldpass',
                'database': 'testdb'
            }
        )
        
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'testdb'
        }
        
        registry.rotate_database_credentials('agent-fallback', new_config)
        
        # Make staged credentials fail
        call_count = 0
        def connect_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call (staged) fails
                raise ConnectionError("Staged credentials failed")
            return True
        
        mock_connector.connect.side_effect = connect_side_effect
        
        # Get connector should fallback to active
        connector = registry.get_database_connector('agent-fallback')
        assert connector is not None
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_without_validation(self, mock_connector_cls):
        """Test rotating credentials without validation"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        registry.register_agent(
            agent_id='agent-no-validate',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db'
            }
        )
        
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'db'
        }
        
        result = registry.rotate_database_credentials(
            agent_id='agent-no-validate',
            new_database_config=new_config,
            validate_before_activate=False
        )
        
        assert result['status'] == 'staging'
        rotation_status = registry.get_credential_rotation_status('agent-no-validate')
        assert rotation_status['validated'] is False
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_get_rotation_status_no_rotation(self, mock_connector_cls):
        """Test getting rotation status when no rotation in progress"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        registry.register_agent(
            agent_id='agent-no-rotation',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': 'pass',
                'database': 'db'
            }
        )
        
        status = registry.get_credential_rotation_status('agent-no-rotation')
        assert status is None


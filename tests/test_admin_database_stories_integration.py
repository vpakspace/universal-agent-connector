"""
Integration tests for Admin database management stories:
1. Connection pooling and timeout configuration
2. Encrypted credentials at rest
3. Credential rotation without breaking connections

These tests verify all three features work together correctly.
"""

import pytest
from unittest.mock import MagicMock, patch
import os

from ai_agent_connector.app.agents.registry import AgentRegistry
from ai_agent_connector.app.utils.encryption import reset_encryptor, get_encryptor
from ai_agent_connector.app.db.pooling import PoolingConfig, TimeoutConfig


@pytest.fixture(autouse=True)
def setup():
    """Reset encryptor before each test"""
    reset_encryptor()
    yield
    reset_encryptor()


class TestStory1_ConnectionPoolingAndTimeouts:
    """
    Story 1: As an Admin, I want to configure connection pooling and timeout settings 
    per database, so that performance is optimized for different workloads.
    """
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_with_pooling_and_timeouts(self, mock_connector_cls):
        """Test registering agent with pooling and timeout configuration"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        database_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb',
            'pooling': {
                'enabled': True,
                'min_size': 5,
                'max_size': 20,
                'max_overflow': 10,
                'pool_timeout': 60,
                'pool_recycle': 7200,
                'pool_pre_ping': True
            },
            'timeouts': {
                'connect_timeout': 15,
                'query_timeout': 60,
                'read_timeout': 45,
                'write_timeout': 45
            }
        }
        
        payload = registry.register_agent(
            agent_id='agent-pooling',
            agent_info={'name': 'High Performance Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        assert payload['credentials_stored'] is True
        assert payload['database']['status'] == 'connected'
        
        # Verify pooling config is stored
        stored_config = registry._decrypt_database_config(
            registry._agent_database_configs['agent-pooling']
        )
        assert stored_config['pooling']['enabled'] is True
        assert stored_config['pooling']['min_size'] == 5
        assert stored_config['pooling']['max_size'] == 20
        assert stored_config['timeouts']['connect_timeout'] == 15
        assert stored_config['timeouts']['query_timeout'] == 60
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_update_pooling_settings_for_existing_agent(self, mock_connector_cls):
        """Test updating pooling settings for an existing agent"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register with default settings
        registry.register_agent(
            agent_id='agent-update-pool',
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
        
        # Update with pooling configuration
        updated_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'password': 'pass',
            'database': 'db',
            'pooling': {
                'enabled': True,
                'min_size': 10,
                'max_size': 50
            },
            'timeouts': {
                'query_timeout': 120
            }
        }
        
        result = registry.update_agent_database('agent-update-pool', updated_config)
        
        # Verify updated config
        stored_config = registry._decrypt_database_config(
            registry._agent_database_configs['agent-update-pool']
        )
        assert stored_config['pooling']['enabled'] is True
        assert stored_config['pooling']['min_size'] == 10
        assert stored_config['timeouts']['query_timeout'] == 120
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_pooling_config_validation(self, mock_connector_cls):
        """Test that invalid pooling configurations are rejected"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Invalid: min_size > max_size
        invalid_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'password': 'pass',
            'database': 'db',
            'pooling': {
                'enabled': True,
                'min_size': 20,
                'max_size': 10  # Invalid
            }
        }
        
        with pytest.raises(ValueError, match="max_size must be >= min_size"):
            registry.register_agent(
                agent_id='agent-invalid-pool',
                agent_info={'name': 'Test Agent'},
                credentials={'api_key': 'key', 'api_secret': 'secret'},
                database_config=invalid_config
            )
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_timeout_config_validation(self, mock_connector_cls):
        """Test that invalid timeout configurations are rejected"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Invalid: timeout < 1
        invalid_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'password': 'pass',
            'database': 'db',
            'timeouts': {
                'connect_timeout': 0  # Invalid
            }
        }
        
        with pytest.raises(ValueError, match="connect_timeout must be at least 1"):
            registry.register_agent(
                agent_id='agent-invalid-timeout',
                agent_info={'name': 'Test Agent'},
                credentials={'api_key': 'key', 'api_secret': 'secret'},
                database_config=invalid_config
            )


class TestStory2_EncryptedCredentials:
    """
    Story 2: As an Admin, I want to store database credentials securely (encrypted at rest), 
    so that sensitive information is protected.
    """
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_credentials_encrypted_at_rest(self, mock_connector_cls):
        """Test that credentials are encrypted when stored"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        database_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'secretpassword123',
            'database': 'testdb',
            'connection_string': 'postgresql://user:secret@host/db'
        }
        
        registry.register_agent(
            agent_id='agent-encrypted',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        # Get stored config (should be encrypted)
        stored_config = registry._agent_database_configs['agent-encrypted']
        
        # Verify sensitive fields are encrypted
        assert stored_config['password'] != 'secretpassword123'
        assert stored_config['connection_string'] != 'postgresql://user:secret@host/db'
        assert stored_config.get('_encrypted') is True
        
        # Verify non-sensitive fields are not encrypted
        assert stored_config['host'] == 'localhost'
        assert stored_config['user'] == 'testuser'
        assert stored_config['database'] == 'testdb'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_credentials_decrypted_when_retrieved(self, mock_connector_cls):
        """Test that credentials are decrypted when retrieved for use"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        original_password = 'mysecretpassword'
        database_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': original_password,
            'database': 'testdb'
        }
        
        registry.register_agent(
            agent_id='agent-decrypt',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        # Get connector (should decrypt automatically)
        connector = registry.get_database_connector('agent-decrypt')
        assert connector is not None
        
        # Verify the connector was built with decrypted password
        # (The connector should have access to the original password)
        stored_encrypted = registry._agent_database_configs['agent-decrypt']
        decrypted_config = registry._decrypt_database_config(stored_encrypted)
        assert decrypted_config['password'] == original_password
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_encryption_with_different_master_keys(self, mock_connector_cls):
        """Test that encryption is key-specific (different keys produce different ciphertext)"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        # Register with first key
        reset_encryptor()
        encryptor1 = get_encryptor()
        encryptor1.master_key = 'key1'
        encryptor1.fernet_key = encryptor1._derive_fernet_key('key1')
        encryptor1.cipher = encryptor1.cipher.__class__(encryptor1.fernet_key)
        
        registry1 = AgentRegistry()
        config1 = {'password': 'secret'}
        encrypted1 = registry1._encrypt_database_config(config1)['password']
        
        # Register with second key
        reset_encryptor()
        encryptor2 = get_encryptor()
        encryptor2.master_key = 'key2'
        encryptor2.fernet_key = encryptor2._derive_fernet_key('key2')
        encryptor2.cipher = encryptor2.cipher.__class__(encryptor2.fernet_key)
        
        registry2 = AgentRegistry()
        config2 = {'password': 'secret'}
        encrypted2 = registry2._encrypt_database_config(config2)['password']
        
        # Encrypted values should be different (different keys)
        assert encrypted1 != encrypted2
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_bigquery_credentials_json_encrypted(self, mock_connector_cls):
        """Test that BigQuery credentials JSON is encrypted"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        credentials_json = {
            'type': 'service_account',
            'project_id': 'test-project',
            'private_key_id': 'key123',
            'private_key': '-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----'
        }
        
        database_config = {
            'type': 'bigquery',
            'project_id': 'test-project',
            'credentials_json': credentials_json
        }
        
        registry.register_agent(
            agent_id='agent-bq-encrypt',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        # Verify credentials_json is encrypted
        stored_config = registry._agent_database_configs['agent-bq-encrypt']
        assert stored_config['credentials_json'] != credentials_json
        assert isinstance(stored_config['credentials_json'], str)
        assert stored_config.get('_encrypted') is True
        
        # Verify it can be decrypted
        decrypted_config = registry._decrypt_database_config(stored_config)
        assert decrypted_config['credentials_json'] == credentials_json


class TestStory3_CredentialRotation:
    """
    Story 3: As an Admin, I want to update or rotate database credentials without breaking 
    active agent connections, so that security practices don't disrupt operations.
    """
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_credentials_without_breaking_connections(self, mock_connector_cls):
        """Test that credential rotation doesn't break active connections"""
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
                'password': 'oldpassword',
                'database': 'testdb'
            }
        )
        
        # Get initial connector (simulating active connection)
        initial_connector = registry.get_database_connector('agent-rotate')
        assert initial_connector is not None
        
        # Rotate credentials
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpassword',
            'database': 'testdb'
        }
        
        rotation_result = registry.rotate_database_credentials(
            agent_id='agent-rotate',
            new_database_config=new_config,
            validate_before_activate=True
        )
        
        assert rotation_result['status'] == 'staging'
        
        # Initial connector should still work (old credentials)
        # New connections should use staged credentials
        new_connector = registry.get_database_connector('agent-rotate')
        assert new_connector is not None
        
        # Activate new credentials
        activation_result = registry.activate_rotated_credentials('agent-rotate')
        assert activation_result['status'] == 'active'
        
        # After activation, all new connections use new credentials
        final_connector = registry.get_database_connector('agent-rotate')
        assert final_connector is not None
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_credentials_with_pooling_config(self, mock_connector_cls):
        """Test rotating credentials while preserving pooling configuration"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register with pooling config
        registry.register_agent(
            agent_id='agent-pool-rotate',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldpass',
                'database': 'testdb',
                'pooling': {
                    'enabled': True,
                    'min_size': 5,
                    'max_size': 20
                },
                'timeouts': {
                    'query_timeout': 60
                }
            }
        )
        
        # Rotate credentials (keep pooling config)
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newpass',
            'database': 'testdb',
            'pooling': {
                'enabled': True,
                'min_size': 5,
                'max_size': 20
            },
            'timeouts': {
                'query_timeout': 60
            }
        }
        
        registry.rotate_database_credentials('agent-pool-rotate', new_config)
        registry.activate_rotated_credentials('agent-pool-rotate')
        
        # Verify pooling config is preserved
        stored_config = registry._decrypt_database_config(
            registry._agent_database_configs['agent-pool-rotate']
        )
        assert stored_config['pooling']['enabled'] is True
        assert stored_config['pooling']['min_size'] == 5
        assert stored_config['timeouts']['query_timeout'] == 60
        assert stored_config['user'] == 'newuser'  # Credentials updated
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotate_encrypted_credentials(self, mock_connector_cls):
        """Test that credential rotation works with encrypted storage"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register with encrypted credentials
        registry.register_agent(
            agent_id='agent-encrypt-rotate',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'olduser',
                'password': 'oldencryptedpass',
                'database': 'testdb'
            }
        )
        
        # Verify old credentials are encrypted
        old_stored = registry._agent_database_configs['agent-encrypt-rotate']
        assert old_stored.get('_encrypted') is True
        assert old_stored['password'] != 'oldencryptedpass'
        
        # Rotate to new credentials
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'newuser',
            'password': 'newencryptedpass',
            'database': 'testdb'
        }
        
        registry.rotate_database_credentials('agent-encrypt-rotate', new_config)
        
        # Verify new credentials are also encrypted in staging
        staged_config = registry._pending_database_configs['agent-encrypt-rotate']
        assert staged_config.get('_encrypted') is True
        assert staged_config['password'] != 'newencryptedpass'
        
        # Activate
        registry.activate_rotated_credentials('agent-encrypt-rotate')
        
        # Verify new credentials are encrypted and active
        new_stored = registry._agent_database_configs['agent-encrypt-rotate']
        assert new_stored.get('_encrypted') is True
        assert new_stored['password'] != 'newencryptedpass'
        
        # Verify decryption works
        decrypted = registry._decrypt_database_config(new_stored)
        assert decrypted['password'] == 'newencryptedpass'
        assert decrypted['user'] == 'newuser'
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rollback_preserves_encryption(self, mock_connector_cls):
        """Test that rollback preserves encrypted credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        original_password = 'originalpass'
        registry.register_agent(
            agent_id='agent-rollback-encrypt',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user',
                'password': original_password,
                'database': 'testdb'
            }
        )
        
        # Get original encrypted config
        original_encrypted = registry._agent_database_configs['agent-rollback-encrypt'].copy()
        
        # Rotate
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user',
            'password': 'newpass',
            'database': 'testdb'
        }
        
        registry.rotate_database_credentials('agent-rollback-encrypt', new_config)
        
        # Rollback
        registry.rollback_credential_rotation('agent-rollback-encrypt')
        
        # Verify original credentials are still encrypted and active
        current_encrypted = registry._agent_database_configs['agent-rollback-encrypt']
        assert current_encrypted.get('_encrypted') is True
        
        # Verify original password is still correct
        decrypted = registry._decrypt_database_config(current_encrypted)
        assert decrypted['password'] == original_password


class TestAllStoriesIntegration:
    """
    Integration tests combining all three stories to ensure they work together
    """
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_full_workflow_pooling_encryption_rotation(self, mock_connector_cls):
        """Test complete workflow: register with pooling -> encrypt -> rotate"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Step 1: Register with pooling, timeouts, and credentials (encrypted)
        database_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user1',
            'password': 'password1',
            'database': 'testdb',
            'pooling': {
                'enabled': True,
                'min_size': 5,
                'max_size': 20
            },
            'timeouts': {
                'connect_timeout': 10,
                'query_timeout': 30
            }
        }
        
        registry.register_agent(
            agent_id='agent-full',
            agent_info={'name': 'Full Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        # Verify encryption
        stored = registry._agent_database_configs['agent-full']
        assert stored.get('_encrypted') is True
        assert stored['password'] != 'password1'
        
        # Verify pooling config stored
        decrypted = registry._decrypt_database_config(stored)
        assert decrypted['pooling']['enabled'] is True
        assert decrypted['timeouts']['query_timeout'] == 30
        
        # Step 2: Rotate credentials (with same pooling config)
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user2',
            'password': 'password2',
            'database': 'testdb',
            'pooling': {
                'enabled': True,
                'min_size': 10,  # Updated pooling
                'max_size': 30
            },
            'timeouts': {
                'connect_timeout': 15,
                'query_timeout': 60  # Updated timeout
            }
        }
        
        registry.rotate_database_credentials('agent-full', new_config)
        
        # Verify staged credentials are encrypted
        staged = registry._pending_database_configs['agent-full']
        assert staged.get('_encrypted') is True
        
        # Step 3: Activate
        registry.activate_rotated_credentials('agent-full')
        
        # Verify final state: new credentials, updated pooling, all encrypted
        final = registry._agent_database_configs['agent-full']
        assert final.get('_encrypted') is True
        
        final_decrypted = registry._decrypt_database_config(final)
        assert final_decrypted['user'] == 'user2'
        assert final_decrypted['password'] == 'password2'
        assert final_decrypted['pooling']['min_size'] == 10
        assert final_decrypted['timeouts']['query_timeout'] == 60
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_rotation_status_tracks_all_changes(self, mock_connector_cls):
        """Test that rotation status tracks all configuration changes"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {'type': 'postgresql'}
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Register
        registry.register_agent(
            agent_id='agent-status',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user1',
                'password': 'pass1',
                'database': 'db',
                'pooling': {'enabled': False}
            }
        )
        
        # Rotate
        new_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'user2',
            'password': 'pass2',
            'database': 'db',
            'pooling': {'enabled': True, 'min_size': 5}
        }
        
        registry.rotate_database_credentials('agent-status', new_config)
        
        # Check status
        status = registry.get_credential_rotation_status('agent-status')
        assert status is not None
        assert status['status'] == 'staging'
        assert 'staged_at' in status
        assert 'current_config_hash' in status
        assert 'new_config_hash' in status
        
        # Activate
        registry.activate_rotated_credentials('agent-status')
        
        # Check updated status
        status = registry.get_credential_rotation_status('agent-status')
        assert status['status'] == 'active'
        assert 'activated_at' in status
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_test_connection_with_pooling_and_encryption(self, mock_connector_cls):
        """Test that connection testing works with pooling config and encrypted credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.is_connected = True
        mock_connector.execute_query.return_value = [(1,)]
        mock_connector.get_database_info.return_value = {
            'type': 'postgresql',
            'version': '15.0',
            'database': 'testdb'
        }
        mock_connector_cls.return_value = mock_connector
        
        registry = AgentRegistry()
        
        # Test connection with pooling and timeouts
        test_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb',
            'pooling': {
                'enabled': True,
                'min_size': 2,
                'max_size': 10
            },
            'timeouts': {
                'connect_timeout': 5,
                'query_timeout': 30
            }
        }
        
        result = registry.test_database_connection(test_config)
        
        assert result['status'] == 'success'
        assert result['test_results']['connection_established'] is True
        assert result['connection_quality'] in ['excellent', 'good', 'fair']
        
        # Verify test was successful with pooling config
        assert result['status'] == 'success'
        assert 'database_info' in result


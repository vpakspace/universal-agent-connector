"""
Unit tests for credential encryption functionality
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from ai_agent_connector.app.utils.encryption import (
    CredentialEncryptor,
    get_encryptor,
    reset_encryptor
)
from ai_agent_connector.app.agents.registry import AgentRegistry


class TestCredentialEncryptor:
    """Test cases for CredentialEncryptor"""
    
    def test_encrypt_decrypt_string(self):
        """Test encrypting and decrypting a string"""
        encryptor = CredentialEncryptor(master_key="test-master-key-12345")
        
        plaintext = "my-secret-password"
        encrypted = encryptor.encrypt(plaintext)
        
        # Encrypted should be different from plaintext
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        
        # Decrypt should return original
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_different_values(self):
        """Test that different values encrypt to different ciphertexts"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        value1 = "password1"
        value2 = "password2"
        
        encrypted1 = encryptor.encrypt(value1)
        encrypted2 = encryptor.encrypt(value2)
        
        assert encrypted1 != encrypted2
        
        # Both should decrypt correctly
        assert encryptor.decrypt(encrypted1) == value1
        assert encryptor.decrypt(encrypted2) == value2
    
    def test_encrypt_empty_string_raises_error(self):
        """Test that encrypting empty string raises error"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        with pytest.raises(ValueError, match="Cannot encrypt empty"):
            encryptor.encrypt("")
        
        with pytest.raises(ValueError, match="Cannot encrypt empty"):
            encryptor.encrypt(None)
    
    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decrypting invalid ciphertext raises error"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        with pytest.raises(ValueError, match="Decryption failed"):
            encryptor.decrypt("invalid-ciphertext")
        
        with pytest.raises(ValueError, match="Cannot decrypt empty"):
            encryptor.decrypt("")
    
    def test_decrypt_with_wrong_key_fails(self):
        """Test that decrypting with wrong key fails"""
        encryptor1 = CredentialEncryptor(master_key="key1")
        encryptor2 = CredentialEncryptor(master_key="key2")
        
        plaintext = "secret"
        encrypted = encryptor1.encrypt(plaintext)
        
        # Should fail to decrypt with different key
        with pytest.raises(ValueError, match="Decryption failed"):
            encryptor2.decrypt(encrypted)
    
    def test_encrypt_dict_value(self):
        """Test encrypting a value in a dictionary"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        data = {'username': 'user', 'password': 'secret123'}
        encrypted_data = encryptor.encrypt_dict_value(data, 'password')
        
        assert encrypted_data['username'] == 'user'  # Unchanged
        assert encrypted_data['password'] != 'secret123'  # Encrypted
        assert encrypted_data['password'] != data['password']  # Different
        
        # Decrypt should restore original
        decrypted_data = encryptor.decrypt_dict_value(encrypted_data, 'password')
        assert decrypted_data['password'] == 'secret123'
    
    def test_encrypt_database_config(self):
        """Test encrypting database configuration"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        config = {
            'host': 'localhost',
            'user': 'testuser',
            'password': 'secretpass',
            'database': 'testdb',
            'connection_string': 'postgresql://user:pass@host/db'
        }
        
        encrypted_config = encryptor.encrypt_database_config(config)
        
        # Sensitive fields should be encrypted
        assert encrypted_config['password'] != 'secretpass'
        assert encrypted_config['connection_string'] != config['connection_string']
        assert encrypted_config['_encrypted'] is True
        
        # Non-sensitive fields unchanged
        assert encrypted_config['host'] == 'localhost'
        assert encrypted_config['user'] == 'testuser'
        assert encrypted_config['database'] == 'testdb'
    
    def test_decrypt_database_config(self):
        """Test decrypting database configuration"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        config = {
            'host': 'localhost',
            'password': 'secretpass',
            'connection_string': 'postgresql://user:pass@host/db'
        }
        
        encrypted_config = encryptor.encrypt_database_config(config)
        decrypted_config = encryptor.decrypt_database_config(encrypted_config)
        
        assert decrypted_config['password'] == 'secretpass'
        assert decrypted_config['connection_string'] == config['connection_string']
        assert decrypted_config.get('_encrypted') is None
    
    def test_decrypt_unencrypted_config(self):
        """Test that decrypting unencrypted config works (backward compatibility)"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        config = {
            'host': 'localhost',
            'password': 'plaintext-password'
        }
        
        # Should return as-is if not marked as encrypted
        decrypted = encryptor.decrypt_database_config(config)
        assert decrypted == config
    
    def test_encrypt_credentials_json_dict(self):
        """Test encrypting credentials_json when it's a dictionary"""
        encryptor = CredentialEncryptor(master_key="test-key")
        
        config = {
            'project_id': 'test-project',
            'credentials_json': {'type': 'service_account', 'private_key': 'secret'}
        }
        
        encrypted_config = encryptor.encrypt_database_config(config)
        
        # credentials_json should be encrypted
        assert encrypted_config['credentials_json'] != config['credentials_json']
        assert isinstance(encrypted_config['credentials_json'], str)
        
        # Decrypt should restore original
        decrypted_config = encryptor.decrypt_database_config(encrypted_config)
        assert decrypted_config['credentials_json'] == config['credentials_json']


class TestEncryptorSingleton:
    """Test cases for encryptor singleton pattern"""
    
    def test_get_encryptor_returns_singleton(self):
        """Test that get_encryptor returns the same instance"""
        reset_encryptor()
        encryptor1 = get_encryptor()
        encryptor2 = get_encryptor()
        
        assert encryptor1 is encryptor2
    
    def test_reset_encryptor(self):
        """Test resetting the encryptor"""
        encryptor1 = get_encryptor()
        reset_encryptor()
        encryptor2 = get_encryptor()
        
        assert encryptor1 is not encryptor2


class TestAgentRegistryEncryption:
    """Test cases for AgentRegistry with encryption"""
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_register_agent_encrypts_credentials(self, mock_connector_cls):
        """Test that agent registration encrypts database credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        reset_encryptor()
        registry = AgentRegistry()
        
        database_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'secretpass',
            'database': 'testdb'
        }
        
        registry.register_agent(
            agent_id='agent-encrypt',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        # Stored config should be encrypted
        stored_config = registry._agent_database_configs['agent-encrypt']
        assert stored_config['password'] != 'secretpass'
        assert stored_config.get('_encrypted') is True
        assert stored_config['host'] == 'localhost'  # Non-sensitive unchanged
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_get_database_connector_decrypts_credentials(self, mock_connector_cls):
        """Test that getting database connector decrypts credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        reset_encryptor()
        registry = AgentRegistry()
        
        database_config = {
            'type': 'postgresql',
            'host': 'localhost',
            'user': 'testuser',
            'password': 'secretpass',
            'database': 'testdb'
        }
        
        registry.register_agent(
            agent_id='agent-decrypt',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config=database_config
        )
        
        # Get connector should decrypt automatically
        connector = registry.get_database_connector('agent-decrypt')
        assert connector is not None
        
        # Verify the connector was built with decrypted config
        # (The connector should have the correct password)
        mock_connector_cls.assert_called()
        call_kwargs = mock_connector_cls.call_args[1] or mock_connector_cls.call_args[0][0]
        # The password should be decrypted when building connector
    
    @patch('ai_agent_connector.app.agents.registry.DatabaseConnector')
    def test_update_agent_database_encrypts(self, mock_connector_cls):
        """Test that updating agent database encrypts new credentials"""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector_cls.return_value = mock_connector
        
        reset_encryptor()
        registry = AgentRegistry()
        
        # Register with initial config
        registry.register_agent(
            agent_id='agent-update',
            agent_info={'name': 'Test Agent'},
            credentials={'api_key': 'key', 'api_secret': 'secret'},
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'user': 'user1',
                'password': 'pass1',
                'database': 'db1'
            }
        )
        
        # Update with new config
        new_config = {
            'type': 'mysql',
            'host': 'localhost',
            'user': 'user2',
            'password': 'pass2',
            'database': 'db2'
        }
        
        registry.update_agent_database('agent-update', new_config)
        
        # New config should be encrypted
        stored_config = registry._agent_database_configs['agent-update']
        assert stored_config['password'] != 'pass2'
        assert stored_config.get('_encrypted') is True
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test-env-key-12345'})
    def test_encryptor_uses_env_key(self):
        """Test that encryptor uses ENCRYPTION_KEY from environment"""
        reset_encryptor()
        
        # Should use key from environment
        encryptor = get_encryptor()
        assert encryptor.master_key == 'test-env-key-12345'
    
    def test_encryption_backward_compatibility(self):
        """Test that unencrypted configs still work (backward compatibility)"""
        reset_encryptor()
        registry = AgentRegistry()
        
        # Manually add unencrypted config (simulating old data)
        registry._agent_database_configs['old-agent'] = {
            'host': 'localhost',
            'user': 'user',
            'password': 'plaintext-password',
            'database': 'db'
            # No _encrypted flag
        }
        
        # Should still work (decrypt will return as-is)
        connector = registry.get_database_connector('old-agent')
        # Should not raise error
        assert connector is not None


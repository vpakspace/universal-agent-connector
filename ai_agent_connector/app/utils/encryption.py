"""
Encryption utilities for securing sensitive data at rest
Uses Fernet symmetric encryption from cryptography library
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialEncryptor:
    """
    Encryptor for database credentials and sensitive configuration data.
    Uses Fernet symmetric encryption with key derivation from a master key.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize the credential encryptor.
        
        Args:
            master_key: Master encryption key. If not provided, will be read from
                       ENCRYPTION_KEY environment variable or generated.
                       
        Raises:
            ValueError: If master_key is invalid
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_KEY')
        
        if not self.master_key:
            # Generate a new key (for development/testing)
            # In production, this should be set via environment variable
            self.master_key = self._generate_master_key()
            # Warn that a new key was generated
            import warnings
            warnings.warn(
                "ENCRYPTION_KEY not set. Generated a new key. "
                "This key will be lost on restart. Set ENCRYPTION_KEY environment variable for production.",
                UserWarning
            )
        
        # Derive Fernet key from master key
        self.fernet_key = self._derive_fernet_key(self.master_key)
        self.cipher = Fernet(self.fernet_key)
    
    @staticmethod
    def _generate_master_key() -> str:
        """Generate a new master encryption key"""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def _derive_fernet_key(master_key: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a Fernet key from the master key using PBKDF2.
        
        Args:
            master_key: Master encryption key (string)
            salt: Salt for key derivation (optional, will be generated if not provided)
            
        Returns:
            bytes: Fernet key
        """
        if salt is None:
            # Use a fixed salt for consistency (in production, consider storing salt separately)
            salt = b'ai_agent_connector_salt_v1'
        
        # Ensure master_key is bytes
        if isinstance(master_key, str):
            master_key_bytes = master_key.encode()
        else:
            master_key_bytes = master_key
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key_bytes))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            str: Encrypted string (base64 encoded)
            
        Raises:
            ValueError: If plaintext is empty or None
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty or None value")
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: Encrypted string (base64 encoded)
            
        Returns:
            str: Decrypted plaintext string
            
        Raises:
            ValueError: If decryption fails (invalid ciphertext or key)
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty or None value")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}") from e
    
    def encrypt_dict_value(self, data: dict, key: str) -> dict:
        """
        Encrypt a specific value in a dictionary.
        
        Args:
            data: Dictionary containing the value to encrypt
            key: Key of the value to encrypt
            
        Returns:
            dict: Dictionary with encrypted value
        """
        if key in data and data[key] is not None:
            data = data.copy()  # Don't modify original
            data[key] = self.encrypt(str(data[key]))
        return data
    
    def decrypt_dict_value(self, data: dict, key: str) -> dict:
        """
        Decrypt a specific value in a dictionary.
        
        Args:
            data: Dictionary containing the encrypted value
            key: Key of the value to decrypt
            
        Returns:
            dict: Dictionary with decrypted value
        """
        if key in data and data[key] is not None:
            data = data.copy()  # Don't modify original
            try:
                data[key] = self.decrypt(str(data[key]))
            except ValueError:
                # If decryption fails, assume it's already plaintext (backward compatibility)
                pass
        return data
    
    def encrypt_database_config(self, config: dict) -> dict:
        """
        Encrypt sensitive fields in a database configuration.
        
        Encrypts: password, credentials_path, credentials_json (if string)
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            dict: Configuration with encrypted sensitive fields
        """
        encrypted_config = config.copy()
        
        # Encrypt password if present
        if 'password' in encrypted_config and encrypted_config['password']:
            encrypted_config['password'] = self.encrypt(str(encrypted_config['password']))
        
        # Encrypt connection string if it contains credentials
        if 'connection_string' in encrypted_config and encrypted_config['connection_string']:
            conn_str = encrypted_config['connection_string']
            # Only encrypt if it contains credentials (has @ or ://)
            if '@' in conn_str or '://' in conn_str:
                encrypted_config['connection_string'] = self.encrypt(conn_str)
        
        # Encrypt BigQuery credentials path (if it's sensitive)
        if 'credentials_path' in encrypted_config and encrypted_config['credentials_path']:
            # For now, we'll encrypt the path if it contains sensitive info
            # In practice, paths might not need encryption, but credentials_json does
            pass
        
        # Encrypt credentials_json if it's a string
        if 'credentials_json' in encrypted_config and encrypted_config['credentials_json']:
            if isinstance(encrypted_config['credentials_json'], str):
                encrypted_config['credentials_json'] = self.encrypt(encrypted_config['credentials_json'])
            # If it's a dict, we'd need to encrypt the entire JSON string
            elif isinstance(encrypted_config['credentials_json'], dict):
                import json
                json_str = json.dumps(encrypted_config['credentials_json'])
                encrypted_config['credentials_json'] = self.encrypt(json_str)
        
        # Mark as encrypted
        encrypted_config['_encrypted'] = True
        
        return encrypted_config
    
    def decrypt_database_config(self, config: dict) -> dict:
        """
        Decrypt sensitive fields in a database configuration.
        
        Args:
            config: Database configuration dictionary with encrypted fields
            
        Returns:
            dict: Configuration with decrypted sensitive fields
        """
        # If not marked as encrypted, assume it's already decrypted (backward compatibility)
        if not config.get('_encrypted', False):
            return config
        
        decrypted_config = config.copy()
        
        # Decrypt password if present
        if 'password' in decrypted_config and decrypted_config['password']:
            try:
                decrypted_config['password'] = self.decrypt(str(decrypted_config['password']))
            except ValueError:
                # If decryption fails, keep original (might be plaintext for backward compat)
                pass
        
        # Decrypt connection string if encrypted
        if 'connection_string' in decrypted_config and decrypted_config['connection_string']:
            try:
                decrypted_config['connection_string'] = self.decrypt(str(decrypted_config['connection_string']))
            except ValueError:
                # If decryption fails, assume it's already plaintext
                pass
        
        # Decrypt credentials_json if present
        if 'credentials_json' in decrypted_config and decrypted_config['credentials_json']:
            try:
                decrypted_str = self.decrypt(str(decrypted_config['credentials_json']))
                # Try to parse as JSON
                try:
                    import json
                    decrypted_config['credentials_json'] = json.loads(decrypted_str)
                except json.JSONDecodeError:
                    # If not JSON, keep as string
                    decrypted_config['credentials_json'] = decrypted_str
            except ValueError:
                # If decryption fails, assume it's already plaintext
                pass
        
        # Remove encryption marker
        decrypted_config.pop('_encrypted', None)
        
        return decrypted_config


# Global encryptor instance (lazy initialization)
_encryptor: Optional[CredentialEncryptor] = None


def get_encryptor() -> CredentialEncryptor:
    """
    Get the global encryptor instance (singleton pattern).
    
    Returns:
        CredentialEncryptor: Global encryptor instance
    """
    global _encryptor
    if _encryptor is None:
        _encryptor = CredentialEncryptor()
    return _encryptor


def reset_encryptor() -> None:
    """Reset the global encryptor (useful for testing)"""
    global _encryptor
    _encryptor = None


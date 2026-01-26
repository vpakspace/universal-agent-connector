"""
AI agent registry for registration and authentication
"""

from typing import Dict, Optional, List, Any
import hashlib
import secrets

from ..db import DatabaseConnector
from ..db.pooling import (
    extract_pooling_config,
    extract_timeout_config,
    validate_pooling_config,
    validate_timeout_config
)
from ..utils.helpers import get_timestamp
from ..utils.encryption import get_encryptor


class AgentRegistry:
    """Manages AI agent registration, credentials, and database linking"""
    
    def __init__(self):
        """Initialize the agent registry"""
        self.agents: Dict[str, Dict] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> agent_id
        self.agent_credentials: Dict[str, Dict[str, str]] = {}
        self.agent_database_links: Dict[str, Dict[str, Any]] = {}
        # Store original database configs (with passwords) for query execution
        self._agent_database_configs: Dict[str, Dict[str, Any]] = {}
        # Store pending/staging credentials for rotation (agent_id -> config)
        self._pending_database_configs: Dict[str, Dict[str, Any]] = {}
        # Track credential rotation status (agent_id -> rotation_info)
        self._credential_rotation_status: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(
        self,
        agent_id: str,
        agent_info: Dict,
        credentials: Optional[Dict[str, str]] = None,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new AI agent and optionally link credentials/database access.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_info: Dictionary containing agent metadata
            credentials: API credentials supplied by the admin
            database_config: Database configuration the agent should access
            
        Returns:
            Dict[str, Any]: Registration metadata containing issued API key and linked resources
        """
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        timestamp = get_timestamp()
        api_key = self._generate_api_key()
        
        agent_record = {
            **agent_info,
            'agent_id': agent_id,
            'api_key_hash': self._hash_secret(api_key),
            'registered_at': timestamp
        }
        
        if credentials:
            self.agent_credentials[agent_id] = self._secure_credentials(credentials, timestamp)
        elif database_config:
            raise ValueError("agent_credentials are required when linking a database")
        
        if database_config:
            db_link = self._link_database(agent_id, database_config)
            agent_record['database'] = db_link
            self.agent_database_links[agent_id] = db_link
            # Store original config for query execution (encrypted at rest)
            encrypted_config = self._encrypt_database_config(database_config.copy())
            self._agent_database_configs[agent_id] = encrypted_config
        
        self.agents[agent_id] = agent_record
        self.api_keys[api_key] = agent_id
        
        return {
            'agent_id': agent_id,
            'api_key': api_key,
            'database': self.agent_database_links.get(agent_id),
            'credentials_stored': agent_id in self.agent_credentials,
            'registered_at': timestamp
        }
    
    def authenticate_agent(self, api_key: str) -> Optional[str]:
        """
        Authenticate an agent using API key
        
        Args:
            api_key: API key to validate
            
        Returns:
            Optional[str]: Agent ID if authenticated, None otherwise
        """
        return self.api_keys.get(api_key)
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """
        Get agent information by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Optional[Dict]: Agent information or None if not found
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs
        
        Returns:
            List[str]: List of agent IDs
        """
        return list(self.agents.keys())
    
    def revoke_agent(self, agent_id: str) -> bool:
        """
        Revoke an agent's access
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            bool: True if agent was revoked, False if not found
        """
        if agent_id not in self.agents:
            return False
        
        # Remove agent and associated API keys
        self.agents.pop(agent_id)
        api_keys_to_remove = [
            key for key, aid in self.api_keys.items()
            if aid == agent_id
        ]
        for key in api_keys_to_remove:
            del self.api_keys[key]
        
        self.agent_credentials.pop(agent_id, None)
        self.agent_database_links.pop(agent_id, None)
        self._agent_database_configs.pop(agent_id, None)
        
        return True
    
    def reset(self) -> None:
        """Utility method for tests to clear registry state."""
        self.agents.clear()
        self.api_keys.clear()
        self.agent_credentials.clear()
        self.agent_database_links.clear()
        self._agent_database_configs.clear()
        self._pending_database_configs.clear()
        self._credential_rotation_status.clear()
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def _hash_secret(self, value: str) -> str:
        """Hash a secret for storage"""
        return hashlib.sha256(value.encode()).hexdigest()
    
    def _secure_credentials(self, credentials: Dict[str, str], timestamp: str) -> Dict[str, Any]:
        """Validate and securely store provided agent credentials"""
        required_fields = {'api_key', 'api_secret'}
        missing = required_fields - credentials.keys()
        if missing:
            raise ValueError(f"agent_credentials missing: {', '.join(sorted(missing))}")
        
        return {
            'api_key_hash': self._hash_secret(credentials['api_key']),
            'api_secret_hash': self._hash_secret(credentials['api_secret']),
            'stored_at': timestamp
        }
    
    def _link_database(self, agent_id: str, database_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and link a database configuration to an agent"""
        connector = self._build_database_connector(database_config)
        
        try:
            connector.connect()
        except Exception as exc:
            raise ValueError(f"Failed to connect to database for agent {agent_id}: {exc}") from exc
        finally:
            connector.disconnect()
        
        sanitized_config = self._sanitize_database_config(database_config)
        sanitized_config.update({
            'status': 'connected',
            'linked_at': get_timestamp()
        })
        return sanitized_config
    
    def _build_database_connector(self, database_config: Dict[str, Any]) -> DatabaseConnector:
        """Create a DatabaseConnector from configuration"""
        # Extract database type if specified
        database_type = database_config.get('type')
        
        # Build connector arguments
        connector_args = {}
        
        if database_config.get('connection_string'):
            connector_args['connection_string'] = database_config['connection_string']
        else:
            # For SQL databases, check required fields
            db_type = database_type or 'postgresql'
            if db_type in ('postgresql', 'mysql'):
                for field in ('host', 'user', 'database'):
                    if not database_config.get(field):
                        raise ValueError(f"database.{field} is required when connection_string is not provided")
            
            connector_args.update({
                'host': database_config.get('host'),
                'port': database_config.get('port'),
                'user': database_config.get('user'),
                'password': database_config.get('password'),
                'database': database_config.get('database')
            })
        
        # Add database type
        if database_type:
            connector_args['database_type'] = database_type
        
        # Add any additional database-specific parameters
        # (e.g., for BigQuery: project_id, credentials_path, etc.)
        excluded_keys = {'host', 'port', 'user', 'password', 'database', 
                        'connection_string', 'type', 'connection_name'}
        for key, value in database_config.items():
            if key not in excluded_keys:
                connector_args[key] = value
        
        return DatabaseConnector(**connector_args)
    
    def get_database_connector(self, agent_id: str) -> Optional[DatabaseConnector]:
        """
        Get a database connector for an agent.
        Uses active credentials (or pending if rotation is in progress).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Optional[DatabaseConnector]: Database connector instance or None if not configured
        """
        # Check if there's a rotation in progress
        rotation_status = self._credential_rotation_status.get(agent_id)
        
        if rotation_status and rotation_status.get('status') == 'staging':
            # During staging, try pending credentials first, fallback to active
            pending_config = self._pending_database_configs.get(agent_id)
            if pending_config:
                try:
                    decrypted_pending = self._decrypt_database_config(pending_config)
                    connector = self._build_database_connector(decrypted_pending)
                    # Test connection with pending credentials
                    connector.connect()
                    connector.disconnect()
                    # Pending credentials work, use them
                    return self._build_database_connector(decrypted_pending)
                except Exception:
                    # Pending credentials failed, fallback to active
                    pass
        
        # Use active credentials
        encrypted_config = self._agent_database_configs.get(agent_id)
        if not encrypted_config:
            return None
        
        # Decrypt configuration before use
        database_config = self._decrypt_database_config(encrypted_config)
        return self._build_database_connector(database_config)
    
    def test_database_connection(self, database_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a database connection without storing it.
        
        This method validates credentials, network access, and performs
        a basic connectivity test. It does not store the connection.
        
        Args:
            database_config: Database configuration to test
            
        Returns:
            Dict containing connection test results with detailed information:
            - status: 'success' or 'error'
            - message: Human-readable message
            - database_info: Sanitized connection info
            - connection_test: Results of connectivity test
            - error: Error details if failed
        """
        connector = None
        test_results = {
            'connection_established': False,
            'query_test': False,
            'database_info_retrieved': False
        }
        
        try:
            # Validate configuration before attempting connection
            database_type = database_config.get('type', 'postgresql')
            self._validate_database_config(database_config, database_type)
            
            # Build and test connection
            connector = self._build_database_connector(database_config)
            
            # Test 1: Establish connection
            try:
                connector.connect()
                test_results['connection_established'] = True
            except ConnectionError as e:
                return {
                    'status': 'error',
                    'message': f'Failed to establish connection: {str(e)}',
                    'error': str(e),
                    'error_type': 'connection_error',
                    'database_info': self._sanitize_database_config(database_config),
                    'test_results': test_results
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Connection error: {str(e)}',
                    'error': str(e),
                    'error_type': 'connection_error',
                    'database_info': self._sanitize_database_config(database_config),
                    'test_results': test_results
                }
            
            # Test 2: Execute a simple query (database-specific)
            query_test_passed = False
            try:
                query = self._get_test_query(database_type)
                if query:
                    result = connector.execute_query(query, fetch=True)
                    if result is not None:
                        query_test_passed = True
                        test_results['query_test'] = True
            except Exception as e:
                # Query test failure is not critical - connection is established
                test_results['query_test'] = False
                test_results['query_test_error'] = str(e)
            
            # Test 3: Get database information
            db_info = {}
            try:
                db_info = connector.get_database_info()
                test_results['database_info_retrieved'] = True
            except Exception:
                # Info retrieval failure is not critical
                pass
            
            # Disconnect
            connector.disconnect()
            
            # Prepare success response
            sanitized_config = self._sanitize_database_config(database_config)
            sanitized_config.update(db_info)
            
            return {
                'status': 'success',
                'message': 'Database connection test successful',
                'database_info': sanitized_config,
                'test_results': test_results,
                'connection_quality': self._assess_connection_quality(test_results)
            }
            
        except ValueError as e:
            # Configuration validation error
            return {
                'status': 'error',
                'message': f'Invalid database configuration: {str(e)}',
                'error': str(e),
                'error_type': 'validation_error',
                'database_info': self._sanitize_database_config(database_config),
                'test_results': test_results
            }
        except Exception as exc:
            # Unexpected error
            return {
                'status': 'error',
                'message': f'Database connection test failed: {str(exc)}',
                'error': str(exc),
                'error_type': 'unknown_error',
                'database_info': self._sanitize_database_config(database_config),
                'test_results': test_results
            }
        finally:
            # Ensure connection is closed
            if connector:
                try:
                    connector.disconnect()
                except Exception:
                    pass
    
    def _validate_database_config(self, config: Dict[str, Any], database_type: str) -> None:
        """
        Validate database configuration based on database type.
        Also validates pooling and timeout configurations.
        
        Args:
            config: Database configuration
            database_type: Type of database
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate pooling configuration if provided
        if 'pooling' in config:
            pooling_config = extract_pooling_config(config)
            validate_pooling_config(pooling_config)
        
        # Validate timeout configuration if provided
        if 'timeouts' in config:
            timeout_config = extract_timeout_config(config)
            validate_timeout_config(timeout_config)
        
        # Validate database-specific required fields
        if database_type == 'postgresql':
            if not config.get('connection_string'):
                required = ['host', 'user', 'database']
                missing = [field for field in required if not config.get(field)]
                if missing:
                    raise ValueError(f"Missing required fields for PostgreSQL: {', '.join(missing)}")
        
        elif database_type == 'mysql':
            if not config.get('connection_string'):
                required = ['host', 'user', 'database']
                missing = [field for field in required if not config.get(field)]
                if missing:
                    raise ValueError(f"Missing required fields for MySQL: {', '.join(missing)}")
        
        elif database_type == 'mongodb':
            if not config.get('connection_string'):
                required = ['host', 'database']
                missing = [field for field in required if not config.get(field)]
                if missing:
                    raise ValueError(f"Missing required fields for MongoDB: {', '.join(missing)}")
        
        elif database_type == 'bigquery':
            if not config.get('project_id'):
                raise ValueError("Missing required field for BigQuery: project_id")
            if not config.get('credentials_path') and not config.get('credentials_json'):
                raise ValueError("Missing required field for BigQuery: credentials_path or credentials_json")
        
        elif database_type == 'snowflake':
            required = ['account', 'user', 'password']
            missing = [field for field in required if not config.get(field)]
            if missing:
                raise ValueError(f"Missing required fields for Snowflake: {', '.join(missing)}")
    
    def _get_test_query(self, database_type: str) -> Optional[str]:
        """
        Get a simple test query for the database type.
        
        Args:
            database_type: Type of database
            
        Returns:
            Test query string or None if not applicable
        """
        queries = {
            'postgresql': 'SELECT 1',
            'mysql': 'SELECT 1',
            'snowflake': 'SELECT 1',
            'bigquery': 'SELECT 1',
            'mongodb': None  # MongoDB uses different query format
        }
        return queries.get(database_type.lower())
    
    def _assess_connection_quality(self, test_results: Dict[str, Any]) -> str:
        """
        Assess the quality of the connection based on test results.
        
        Args:
            test_results: Results from connection tests
            
        Returns:
            Quality assessment: 'excellent', 'good', 'fair', or 'poor'
        """
        if test_results.get('connection_established') and \
           test_results.get('query_test') and \
           test_results.get('database_info_retrieved'):
            return 'excellent'
        elif test_results.get('connection_established') and \
             test_results.get('query_test'):
            return 'good'
        elif test_results.get('connection_established'):
            return 'fair'
        else:
            return 'poor'
    
    def _encrypt_database_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in database configuration.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            dict: Configuration with encrypted sensitive fields
        """
        encryptor = get_encryptor()
        return encryptor.encrypt_database_config(config)
    
    def _decrypt_database_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in database configuration.
        
        Args:
            config: Database configuration dictionary (may be encrypted)
            
        Returns:
            dict: Configuration with decrypted sensitive fields
        """
        encryptor = get_encryptor()
        return encryptor.decrypt_database_config(config)
    
    def rotate_database_credentials(
        self,
        agent_id: str,
        new_database_config: Dict[str, Any],
        validate_before_activate: bool = True
    ) -> Dict[str, Any]:
        """
        Rotate database credentials for an agent without breaking active connections.
        
        This method supports zero-downtime credential rotation:
        1. Validates new credentials
        2. Stores new credentials in staging
        3. Tests new credentials work
        4. Activates new credentials (old ones remain as fallback)
        
        Args:
            agent_id: Agent identifier
            new_database_config: New database configuration with updated credentials
            validate_before_activate: If True, validate new credentials before activating
            
        Returns:
            Dict containing rotation status and information
            
        Raises:
            ValueError: If agent not found or new credentials are invalid
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Check if agent has existing database config
        if agent_id not in self._agent_database_configs:
            raise ValueError(f"Agent {agent_id} does not have a database configuration to rotate")
        
        # Get current config for reference
        current_encrypted = self._agent_database_configs[agent_id]
        current_config = self._decrypt_database_config(current_encrypted)
        
        # Validate new configuration structure matches current
        current_type = current_config.get('type', 'postgresql')
        new_type = new_database_config.get('type', current_type)
        
        if new_type != current_type:
            raise ValueError(
                f"Cannot rotate credentials: database type mismatch. "
                f"Current: {current_type}, New: {new_type}"
            )
        
        # Validate new credentials work
        if validate_before_activate:
            test_result = self.test_database_connection(new_database_config)
            if test_result['status'] != 'success':
                raise ValueError(
                    f"New credentials validation failed: {test_result.get('error', 'Unknown error')}"
                )
        
        # Store new credentials in staging (encrypted)
        encrypted_new_config = self._encrypt_database_config(new_database_config.copy())
        self._pending_database_configs[agent_id] = encrypted_new_config
        
        # Update rotation status
        self._credential_rotation_status[agent_id] = {
            'status': 'staging',
            'staged_at': get_timestamp(),
            'current_config_hash': self._hash_config(current_config),
            'new_config_hash': self._hash_config(new_database_config),
            'validated': validate_before_activate
        }
        
        return {
            'agent_id': agent_id,
            'status': 'staging',
            'message': 'New credentials staged. They will be used for new connections.',
            'staged_at': self._credential_rotation_status[agent_id]['staged_at'],
            'next_step': 'activate' if validate_before_activate else 'validate_and_activate'
        }
    
    def activate_rotated_credentials(self, agent_id: str) -> Dict[str, Any]:
        """
        Activate staged credentials, making them the active credentials.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict containing activation status
            
        Raises:
            ValueError: If agent not found or no staged credentials
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        if agent_id not in self._pending_database_configs:
            raise ValueError(f"Agent {agent_id} has no staged credentials to activate")
        
        # Get staged credentials
        staged_encrypted = self._pending_database_configs[agent_id]
        staged_config = self._decrypt_database_config(staged_encrypted)
        
        # Validate staged credentials one more time before activation
        test_result = self.test_database_connection(staged_config)
        if test_result['status'] != 'success':
            raise ValueError(
                f"Cannot activate credentials: validation failed. "
                f"Error: {test_result.get('error', 'Unknown error')}"
            )
        
        # Move staged to active
        old_encrypted = self._agent_database_configs.get(agent_id)
        self._agent_database_configs[agent_id] = staged_encrypted
        self._pending_database_configs.pop(agent_id, None)
        
        # Update database link
        db_link = self._link_database(agent_id, staged_config)
        self.agents[agent_id]['database'] = db_link
        self.agent_database_links[agent_id] = db_link
        
        # Update rotation status
        rotation_info = self._credential_rotation_status.get(agent_id, {})
        rotation_info.update({
            'status': 'active',
            'activated_at': get_timestamp(),
            'previous_config_hash': rotation_info.get('current_config_hash')
        })
        self._credential_rotation_status[agent_id] = rotation_info
        
        return {
            'agent_id': agent_id,
            'status': 'active',
            'message': 'Credentials successfully activated. Old credentials are no longer used.',
            'activated_at': rotation_info['activated_at']
        }
    
    def rollback_credential_rotation(self, agent_id: str) -> Dict[str, Any]:
        """
        Rollback credential rotation, removing staged credentials and keeping current active.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict containing rollback status
            
        Raises:
            ValueError: If agent not found or no rotation in progress
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        if agent_id not in self._pending_database_configs:
            raise ValueError(f"Agent {agent_id} has no staged credentials to rollback")
        
        # Remove staged credentials
        self._pending_database_configs.pop(agent_id, None)
        
        # Update rotation status
        rotation_info = self._credential_rotation_status.get(agent_id, {})
        rotation_info.update({
            'status': 'rolled_back',
            'rolled_back_at': get_timestamp()
        })
        self._credential_rotation_status[agent_id] = rotation_info
        
        return {
            'agent_id': agent_id,
            'status': 'rolled_back',
            'message': 'Credential rotation rolled back. Current credentials remain active.',
            'rolled_back_at': rotation_info['rolled_back_at']
        }
    
    def get_credential_rotation_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current credential rotation status for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict containing rotation status or None if no rotation in progress
        """
        return self._credential_rotation_status.get(agent_id)
    
    def _hash_config(self, config: Dict[str, Any]) -> str:
        """
        Create a hash of configuration for tracking changes.
        Excludes sensitive fields for comparison.
        
        Args:
            config: Database configuration
            
        Returns:
            str: Hash of configuration
        """
        import json
        # Create a copy without sensitive fields for hashing
        config_copy = config.copy()
        config_copy.pop('password', None)
        config_copy.pop('connection_string', None)
        config_copy.pop('credentials_json', None)
        config_copy.pop('credentials_path', None)
        
        config_str = json.dumps(config_copy, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def update_agent_database(
        self,
        agent_id: str,
        database_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update or add database connection for an existing agent.
        
        Args:
            agent_id: Agent identifier
            database_config: Database configuration
            
        Returns:
            Dict containing updated database link information
            
        Raises:
            ValueError: If agent not found or connection fails
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Test and link database
        db_link = self._link_database(agent_id, database_config)
        
        # Update agent record
        self.agents[agent_id]['database'] = db_link
        self.agent_database_links[agent_id] = db_link
        # Encrypt before storing
        encrypted_config = self._encrypt_database_config(database_config.copy())
        self._agent_database_configs[agent_id] = encrypted_config
        
        return {
            'agent_id': agent_id,
            'database': db_link,
            'updated_at': get_timestamp()
        }
    
    def _sanitize_database_config(self, database_config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data before storing database configuration"""
        allowed_fields = ('connection_name', 'host', 'port', 'database', 'schema', 'type')
        sanitized = {field: database_config[field] for field in allowed_fields if field in database_config}
        if database_config.get('connection_string'):
            sanitized['connection_string'] = '***'
        if 'connection_name' not in sanitized:
            sanitized['connection_name'] = 'default'
        if 'type' not in sanitized:
            sanitized['type'] = 'postgresql'
        return sanitized

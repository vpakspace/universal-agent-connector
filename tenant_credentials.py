"""
Tenant Credential Vault
Securely stores and retrieves tenant credentials from configuration files
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP errors"""
    def __init__(self, error_code: str, message: str = ""):
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")


class TenantCredentialVault:
    """
    Secure credential vault for tenant configurations.
    Reads tenant credentials from JSON configuration files.
    """
    
    def __init__(self, config_dir: str = "tenant_configs"):
        """
        Initialize credential vault
        
        Args:
            config_dir: Directory containing tenant configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for loaded credentials (in-memory, not persistent)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def _validate_tenant_id(self, tenant_id: str) -> None:
        """
        Validate tenant_id format
        
        Args:
            tenant_id: Tenant identifier
            
        Raises:
            MCPError: If tenant_id is invalid
        """
        if not tenant_id:
            raise MCPError("INVALID_TENANT", "Tenant ID cannot be empty")
        
        if not isinstance(tenant_id, str):
            raise MCPError("INVALID_TENANT", "Tenant ID must be a string")
        
        # Alphanumeric, 6-20 characters
        if not (6 <= len(tenant_id) <= 20):
            raise MCPError("INVALID_TENANT", f"Tenant ID must be 6-20 characters, got {len(tenant_id)}")
        
        if not tenant_id.isalnum():
            raise MCPError("INVALID_TENANT", "Tenant ID must be alphanumeric only")
    
    def _resolve_env_vars(self, value: Any) -> Any:
        """
        Resolve environment variable references in config values
        
        Supports format: ${ENV_VAR_NAME} or ${ENV_VAR_NAME:default_value}
        
        Args:
            value: Config value (may contain env var reference)
            
        Returns:
            Resolved value
        """
        if not isinstance(value, str):
            return value
        
        # Check for ${ENV_VAR} pattern
        if value.startswith("${") and value.endswith("}"):
            env_ref = value[2:-1]  # Remove ${ and }
            
            # Check for default value: ${VAR:default}
            if ":" in env_ref:
                var_name, default = env_ref.split(":", 1)
                var_name = var_name.strip()
                default = default.strip()
            else:
                var_name = env_ref.strip()
                default = None
            
            # Get from environment
            env_value = os.getenv(var_name)
            
            if env_value is not None:
                return env_value
            elif default is not None:
                return default
            else:
                # Log warning but return original value
                logger.warning(f"Environment variable {var_name} not found, using original value")
                return value
        
        return value
    
    def _resolve_config_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve environment variables in config
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Resolved configuration dictionary
        """
        resolved = {}
        for key, value in config.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_config_values(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_config_values(item) if isinstance(item, dict) else self._resolve_env_vars(item)
                    for item in value
                ]
            else:
                resolved[key] = self._resolve_env_vars(value)
        
        return resolved
    
    def _load_config_file(self, tenant_id: str) -> Dict[str, Any]:
        """
        Load configuration file for a tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Configuration dictionary
            
        Raises:
            MCPError: If config file doesn't exist or is invalid
        """
        config_path = self.config_dir / f"{tenant_id}.json"
        
        if not config_path.exists():
            raise MCPError("TENANT_NOT_CONFIGURED", f"Configuration file not found for tenant: {tenant_id}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate tenant_id matches
            if config.get("tenant_id") != tenant_id:
                raise MCPError("TENANT_NOT_CONFIGURED", f"Tenant ID mismatch in config file: {tenant_id}")
            
            # Resolve environment variables
            config = self._resolve_config_values(config)
            
            return config
            
        except json.JSONDecodeError as e:
            raise MCPError("TENANT_NOT_CONFIGURED", f"Invalid JSON in config file: {e}")
        except Exception as e:
            logger.error(f"Error loading config for tenant {tenant_id}: {e}")
            raise MCPError("TENANT_NOT_CONFIGURED", f"Failed to load configuration: {e}")
    
    def get_credentials(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get credentials for a tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary containing tenant credentials and configuration
            
        Raises:
            MCPError: If tenant_id is invalid or configuration is missing
        """
        # Validate tenant_id
        self._validate_tenant_id(tenant_id)
        
        # Check cache
        import time
        current_time = time.time()
        if tenant_id in self._cache:
            cache_time = self._cache_timestamp.get(tenant_id, 0)
            if (current_time - cache_time) < self._cache_ttl:
                # Return cached config (NEVER log credentials)
                return self._cache[tenant_id].copy()
        
        # Load from file
        config = self._load_config_file(tenant_id)
        
        # Cache it (without logging)
        self._cache[tenant_id] = config.copy()
        self._cache_timestamp[tenant_id] = current_time
        
        # Log access (without credentials)
        logger.info(f"Loaded credentials for tenant: {tenant_id}")
        
        return config.copy()
    
    def clear_cache(self, tenant_id: Optional[str] = None) -> None:
        """
        Clear credential cache
        
        Args:
            tenant_id: If provided, clear only this tenant's cache. Otherwise clear all.
        """
        if tenant_id:
            self._cache.pop(tenant_id, None)
            self._cache_timestamp.pop(tenant_id, None)
            logger.info(f"Cleared cache for tenant: {tenant_id}")
        else:
            self._cache.clear()
            self._cache_timestamp.clear()
            logger.info("Cleared all credential cache")
    
    def tenant_exists(self, tenant_id: str) -> bool:
        """
        Check if tenant configuration exists
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if tenant exists, False otherwise
        """
        try:
            self._validate_tenant_id(tenant_id)
            config_path = self.config_dir / f"{tenant_id}.json"
            return config_path.exists()
        except MCPError:
            return False
    
    def list_tenants(self) -> list[str]:
        """
        List all configured tenants
        
        Returns:
            List of tenant IDs
        """
        tenant_ids = []
        for config_file in self.config_dir.glob("*.json"):
            tenant_id = config_file.stem
            try:
                self._validate_tenant_id(tenant_id)
                tenant_ids.append(tenant_id)
            except MCPError:
                # Skip invalid tenant IDs
                continue
        
        return sorted(tenant_ids)


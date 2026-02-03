"""
Tenant Manager for Multi-tenancy Support
Manages tenant configurations, quotas, and features.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class TenantQuotas:
    """Quotas configuration for a tenant."""
    max_queries_per_hour: int = 1000
    max_queries_per_day: int = 10000
    max_concurrent_connections: int = 5
    max_agents: int = 100
    max_storage_mb: int = 1024


@dataclass
class TenantFeatures:
    """Feature flags for a tenant."""
    premium_support: bool = False
    advanced_analytics: bool = False
    custom_ontologies: bool = False
    audit_trail: bool = True
    alerting: bool = False
    schema_drift_detection: bool = True


@dataclass
class TenantDatabaseConfig:
    """Database configuration for a tenant."""
    host: str = "localhost"
    port: int = 5432
    name: str = ""
    user: str = ""
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 5


@dataclass
class TenantInfo:
    """Complete tenant information."""
    tenant_id: str
    name: str = ""
    plan: str = "basic"  # basic, professional, enterprise
    quotas: TenantQuotas = field(default_factory=TenantQuotas)
    features: TenantFeatures = field(default_factory=TenantFeatures)
    database: TenantDatabaseConfig = field(default_factory=TenantDatabaseConfig)
    api_keys: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "plan": self.plan,
            "quotas": {
                "max_queries_per_hour": self.quotas.max_queries_per_hour,
                "max_queries_per_day": self.quotas.max_queries_per_day,
                "max_concurrent_connections": self.quotas.max_concurrent_connections,
                "max_agents": self.quotas.max_agents,
                "max_storage_mb": self.quotas.max_storage_mb,
            },
            "features": {
                "premium_support": self.features.premium_support,
                "advanced_analytics": self.features.advanced_analytics,
                "custom_ontologies": self.features.custom_ontologies,
                "audit_trail": self.features.audit_trail,
                "alerting": self.features.alerting,
                "schema_drift_detection": self.features.schema_drift_detection,
            },
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
            },
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TenantManager:
    """
    Manages tenant configurations for multi-tenancy support.

    Loads tenant configs from JSON files and provides access to tenant information.
    Supports environment variable substitution in config values.
    """

    DEFAULT_TENANT_ID = "default"

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize TenantManager.

        Args:
            config_dir: Directory containing tenant config JSON files.
                       Defaults to 'tenant_configs/' relative to project root.
        """
        self.tenants: Dict[str, TenantInfo] = {}
        self.config_dir = config_dir or self._get_default_config_dir()
        self._load_tenant_configs()
        self._ensure_default_tenant()

    def _get_default_config_dir(self) -> str:
        """Get default config directory path."""
        # Try relative to this file first
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        config_dir = base_dir / "tenant_configs"
        if config_dir.exists():
            return str(config_dir)

        # Fallback to current working directory
        cwd_config = Path.cwd() / "tenant_configs"
        if cwd_config.exists():
            return str(cwd_config)

        return str(config_dir)

    def _resolve_env_vars(self, value: str) -> str:
        """
        Resolve environment variable placeholders in config values.

        Supports format: ${VAR_NAME:default_value}
        """
        if not isinstance(value, str):
            return value

        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default = match.group(2) or ""
            return os.environ.get(var_name, default)

        return re.sub(pattern, replacer, value)

    def _resolve_config_values(self, config: Dict) -> Dict:
        """Recursively resolve environment variables in config."""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_config_values(value)
            elif isinstance(value, str):
                resolved[key] = self._resolve_env_vars(value)
            else:
                resolved[key] = value
        return resolved

    def _load_tenant_configs(self) -> None:
        """Load all tenant configurations from JSON files."""
        config_path = Path(self.config_dir)

        if not config_path.exists():
            logger.warning(f"Tenant config directory not found: {self.config_dir}")
            return

        for config_file in config_path.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    raw_config = json.load(f)

                # Resolve environment variables
                config = self._resolve_config_values(raw_config)

                tenant_id = config.get("tenant_id")
                if not tenant_id:
                    logger.warning(f"Skipping config without tenant_id: {config_file}")
                    continue

                tenant_info = self._parse_tenant_config(config)
                self.tenants[tenant_id] = tenant_info
                logger.info(f"Loaded tenant config: {tenant_id}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {config_file}: {e}")
            except Exception as e:
                logger.error(f"Error loading {config_file}: {e}")

        logger.info(f"Loaded {len(self.tenants)} tenant configurations")

    def _parse_tenant_config(self, config: Dict) -> TenantInfo:
        """Parse raw config dict into TenantInfo."""
        quotas_data = config.get("quotas", {})
        quotas = TenantQuotas(
            max_queries_per_hour=quotas_data.get("max_queries_per_hour", 1000),
            max_queries_per_day=quotas_data.get("max_queries_per_day", 10000),
            max_concurrent_connections=quotas_data.get("max_concurrent_connections", 5),
            max_agents=quotas_data.get("max_agents", 100),
            max_storage_mb=quotas_data.get("max_storage_mb", 1024),
        )

        features_data = config.get("features", {})
        features = TenantFeatures(
            premium_support=features_data.get("premium_support", False),
            advanced_analytics=features_data.get("advanced_analytics", False),
            custom_ontologies=features_data.get("custom_ontologies", False),
            audit_trail=features_data.get("audit_trail", True),
            alerting=features_data.get("alerting", False),
            schema_drift_detection=features_data.get("schema_drift_detection", True),
        )

        database = TenantDatabaseConfig(
            host=config.get("db_host", "localhost"),
            port=config.get("db_port", 5432),
            name=config.get("db_name", ""),
            user=config.get("db_user", ""),
            password=config.get("db_password", ""),
        )

        # Determine plan based on features
        plan = "basic"
        if features.premium_support and features.advanced_analytics:
            plan = "enterprise"
        elif features.premium_support:
            plan = "professional"

        return TenantInfo(
            tenant_id=config["tenant_id"],
            name=config.get("name", config["tenant_id"]),
            plan=plan,
            quotas=quotas,
            features=features,
            database=database,
            api_keys=config.get("api_keys", {}),
            created_at=config.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=config.get("updated_at", datetime.now(timezone.utc).isoformat()),
            is_active=config.get("is_active", True),
            metadata=config.get("metadata", {}),
        )

    def _ensure_default_tenant(self) -> None:
        """Ensure a default tenant exists for backward compatibility."""
        if self.DEFAULT_TENANT_ID not in self.tenants:
            self.tenants[self.DEFAULT_TENANT_ID] = TenantInfo(
                tenant_id=self.DEFAULT_TENANT_ID,
                name="Default Tenant",
                plan="basic",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.info("Created default tenant for backward compatibility")

    def get_tenant(self, tenant_id: str) -> Optional[TenantInfo]:
        """
        Get tenant information by ID.

        Args:
            tenant_id: The tenant identifier.

        Returns:
            TenantInfo if found, None otherwise.
        """
        return self.tenants.get(tenant_id)

    def get_tenant_or_default(self, tenant_id: Optional[str]) -> TenantInfo:
        """
        Get tenant by ID, falling back to default tenant.

        Args:
            tenant_id: The tenant identifier (can be None).

        Returns:
            TenantInfo for the specified or default tenant.
        """
        if tenant_id and tenant_id in self.tenants:
            return self.tenants[tenant_id]
        return self.tenants[self.DEFAULT_TENANT_ID]

    def validate_tenant(self, tenant_id: str) -> bool:
        """
        Validate that a tenant exists and is active.

        Args:
            tenant_id: The tenant identifier.

        Returns:
            True if tenant exists and is active.
        """
        tenant = self.get_tenant(tenant_id)
        return tenant is not None and tenant.is_active

    def list_tenants(self, active_only: bool = True) -> List[TenantInfo]:
        """
        List all tenants.

        Args:
            active_only: If True, only return active tenants.

        Returns:
            List of TenantInfo objects.
        """
        tenants = list(self.tenants.values())
        if active_only:
            tenants = [t for t in tenants if t.is_active]
        return tenants

    def get_tenant_ids(self, active_only: bool = True) -> List[str]:
        """Get list of tenant IDs."""
        return [t.tenant_id for t in self.list_tenants(active_only)]

    def check_quota(self, tenant_id: str, quota_type: str, current_usage: int) -> bool:
        """
        Check if a tenant has exceeded a quota.

        Args:
            tenant_id: The tenant identifier.
            quota_type: Type of quota (queries_per_hour, queries_per_day, etc.)
            current_usage: Current usage count.

        Returns:
            True if within quota, False if exceeded.
        """
        tenant = self.get_tenant_or_default(tenant_id)

        quota_map = {
            "queries_per_hour": tenant.quotas.max_queries_per_hour,
            "queries_per_day": tenant.quotas.max_queries_per_day,
            "concurrent_connections": tenant.quotas.max_concurrent_connections,
            "agents": tenant.quotas.max_agents,
            "storage_mb": tenant.quotas.max_storage_mb,
        }

        max_allowed = quota_map.get(quota_type)
        if max_allowed is None:
            logger.warning(f"Unknown quota type: {quota_type}")
            return True

        return current_usage < max_allowed

    def has_feature(self, tenant_id: str, feature_name: str) -> bool:
        """
        Check if a tenant has a specific feature enabled.

        Args:
            tenant_id: The tenant identifier.
            feature_name: Name of the feature to check.

        Returns:
            True if feature is enabled.
        """
        tenant = self.get_tenant_or_default(tenant_id)
        return getattr(tenant.features, feature_name, False)

    def reload_configs(self) -> None:
        """Reload all tenant configurations from disk."""
        self.tenants.clear()
        self._load_tenant_configs()
        self._ensure_default_tenant()
        logger.info("Reloaded tenant configurations")

    def add_tenant(self, tenant_info: TenantInfo) -> None:
        """
        Add a new tenant (in-memory only).

        Args:
            tenant_info: TenantInfo object to add.
        """
        self.tenants[tenant_info.tenant_id] = tenant_info
        logger.info(f"Added tenant: {tenant_info.tenant_id}")

    def remove_tenant(self, tenant_id: str) -> bool:
        """
        Remove a tenant (in-memory only).

        Args:
            tenant_id: The tenant identifier.

        Returns:
            True if removed, False if not found.
        """
        if tenant_id == self.DEFAULT_TENANT_ID:
            logger.warning("Cannot remove default tenant")
            return False

        if tenant_id in self.tenants:
            del self.tenants[tenant_id]
            logger.info(f"Removed tenant: {tenant_id}")
            return True
        return False

    def get_database_config(self, tenant_id: str) -> TenantDatabaseConfig:
        """Get database configuration for a tenant."""
        tenant = self.get_tenant_or_default(tenant_id)
        return tenant.database


# Global instance
_tenant_manager: Optional[TenantManager] = None


def get_tenant_manager() -> TenantManager:
    """Get the global TenantManager instance."""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager()
    return _tenant_manager


def init_tenant_manager(config_dir: Optional[str] = None) -> TenantManager:
    """Initialize the global TenantManager."""
    global _tenant_manager
    _tenant_manager = TenantManager(config_dir)
    return _tenant_manager

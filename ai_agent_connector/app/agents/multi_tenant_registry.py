"""
Multi-tenant AI agent registry.
Extends AgentRegistry with tenant isolation and management.
"""

from typing import Dict, Optional, List, Any, Tuple
import logging

from .registry import AgentRegistry
from ..config.tenant_manager import (
    TenantManager,
    TenantInfo,
    get_tenant_manager,
)
# from ..utils.helpers import get_timestamp  # Available if needed

logger = logging.getLogger(__name__)


class MultiTenantAgentRegistry:
    """
    Multi-tenant wrapper for AgentRegistry.

    Provides tenant isolation for agent registration and authentication.
    Uses a separate AgentRegistry instance per tenant for data isolation.

    Structure:
        tenant_registries[tenant_id] -> AgentRegistry instance
        api_key_tenant_map[api_key] -> (tenant_id, agent_id)
    """

    DEFAULT_TENANT_ID = "default"

    def __init__(self, tenant_manager: Optional[TenantManager] = None):
        """
        Initialize multi-tenant registry.

        Args:
            tenant_manager: TenantManager instance. If None, uses global instance.
        """
        self.tenant_manager = tenant_manager or get_tenant_manager()

        # Per-tenant registries
        self.tenant_registries: Dict[str, AgentRegistry] = {}

        # Global API key -> (tenant_id, agent_id) mapping
        self.api_key_tenant_map: Dict[str, Tuple[str, str]] = {}

        # Ensure default tenant registry exists
        self._ensure_tenant_registry(self.DEFAULT_TENANT_ID)

    def _ensure_tenant_registry(self, tenant_id: str) -> AgentRegistry:
        """
        Ensure a registry exists for the given tenant.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            AgentRegistry for the tenant.
        """
        if tenant_id not in self.tenant_registries:
            self.tenant_registries[tenant_id] = AgentRegistry()
            logger.info(f"Created registry for tenant: {tenant_id}")
        return self.tenant_registries[tenant_id]

    def _validate_tenant(self, tenant_id: str) -> TenantInfo:
        """
        Validate tenant exists and is active.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            TenantInfo for the tenant.

        Raises:
            ValueError: If tenant is invalid or inactive.
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant is None:
            raise ValueError(f"Unknown tenant: {tenant_id}")
        if not tenant.is_active:
            raise ValueError(f"Tenant is inactive: {tenant_id}")
        return tenant

    def register_agent(
        self,
        tenant_id: str,
        agent_id: str,
        agent_info: Dict,
        credentials: Optional[Dict[str, str]] = None,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register an agent under a specific tenant.

        Args:
            tenant_id: Tenant identifier.
            agent_id: Unique agent identifier within the tenant.
            agent_info: Agent metadata.
            credentials: API credentials.
            database_config: Database configuration.

        Returns:
            Registration result with api_key and metadata.

        Raises:
            ValueError: If tenant is invalid or quota exceeded.
        """
        # Validate tenant
        tenant = self._validate_tenant(tenant_id)

        # Check agent quota
        registry = self._ensure_tenant_registry(tenant_id)
        current_agents = len(registry.list_agents())
        if not self.tenant_manager.check_quota(tenant_id, "agents", current_agents):
            raise ValueError(
                f"Agent quota exceeded for tenant {tenant_id}. "
                f"Max: {tenant.quotas.max_agents}, Current: {current_agents}"
            )

        # Register in tenant's registry
        result = registry.register_agent(
            agent_id=agent_id,
            agent_info={**agent_info, 'tenant_id': tenant_id},
            credentials=credentials,
            database_config=database_config
        )

        # Update global API key mapping
        api_key = result.get('api_key')
        if api_key:
            self.api_key_tenant_map[api_key] = (tenant_id, agent_id)

        # Add tenant info to result
        result['tenant_id'] = tenant_id
        result['tenant_plan'] = tenant.plan

        logger.info(f"Registered agent {agent_id} under tenant {tenant_id}")
        return result

    def authenticate_agent(self, api_key: str) -> Optional[Tuple[str, str]]:
        """
        Authenticate an agent by API key.

        Args:
            api_key: API key to validate.

        Returns:
            Tuple of (tenant_id, agent_id) if authenticated, None otherwise.
        """
        return self.api_key_tenant_map.get(api_key)

    def authenticate_agent_legacy(self, api_key: str) -> Optional[str]:
        """
        Legacy authentication returning only agent_id.
        For backward compatibility with existing code.

        Args:
            api_key: API key to validate.

        Returns:
            Agent ID if authenticated, None otherwise.
        """
        result = self.authenticate_agent(api_key)
        return result[1] if result else None

    def get_agent(self, tenant_id: str, agent_id: str) -> Optional[Dict]:
        """
        Get agent information.

        Args:
            tenant_id: Tenant identifier.
            agent_id: Agent identifier.

        Returns:
            Agent information or None if not found.
        """
        registry = self.tenant_registries.get(tenant_id)
        if registry is None:
            return None
        return registry.get_agent(agent_id)

    def get_agent_by_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Get agent information by API key.

        Args:
            api_key: API key.

        Returns:
            Agent information or None if not found.
        """
        auth_result = self.authenticate_agent(api_key)
        if auth_result is None:
            return None
        tenant_id, agent_id = auth_result
        return self.get_agent(tenant_id, agent_id)

    def list_agents(self, tenant_id: str) -> List[str]:
        """
        List all agents for a tenant.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            List of agent IDs.
        """
        registry = self.tenant_registries.get(tenant_id)
        if registry is None:
            return []
        return registry.list_agents()

    def list_all_agents(self) -> Dict[str, List[str]]:
        """
        List all agents grouped by tenant.

        Returns:
            Dict mapping tenant_id to list of agent_ids.
        """
        return {
            tenant_id: registry.list_agents()
            for tenant_id, registry in self.tenant_registries.items()
        }

    def revoke_agent(self, tenant_id: str, agent_id: str) -> bool:
        """
        Revoke an agent's access.

        Args:
            tenant_id: Tenant identifier.
            agent_id: Agent identifier.

        Returns:
            True if revoked, False if not found.
        """
        registry = self.tenant_registries.get(tenant_id)
        if registry is None:
            return False

        # Find and remove from global API key map
        keys_to_remove = [
            key for key, (tid, aid) in self.api_key_tenant_map.items()
            if tid == tenant_id and aid == agent_id
        ]
        for key in keys_to_remove:
            del self.api_key_tenant_map[key]

        result = registry.revoke_agent(agent_id)
        if result:
            logger.info(f"Revoked agent {agent_id} from tenant {tenant_id}")
        return result

    def get_database_connector(self, tenant_id: str, agent_id: str):
        """
        Get database connector for an agent.

        Args:
            tenant_id: Tenant identifier.
            agent_id: Agent identifier.

        Returns:
            DatabaseConnector or None.
        """
        registry = self.tenant_registries.get(tenant_id)
        if registry is None:
            return None
        return registry.get_database_connector(agent_id)

    def get_database_connector_by_api_key(self, api_key: str):
        """
        Get database connector by API key.

        Args:
            api_key: API key.

        Returns:
            DatabaseConnector or None.
        """
        auth_result = self.authenticate_agent(api_key)
        if auth_result is None:
            return None
        tenant_id, agent_id = auth_result
        return self.get_database_connector(tenant_id, agent_id)

    def get_tenant_for_agent(self, api_key: str) -> Optional[TenantInfo]:
        """
        Get tenant information for an agent by API key.

        Args:
            api_key: API key.

        Returns:
            TenantInfo or None.
        """
        auth_result = self.authenticate_agent(api_key)
        if auth_result is None:
            return None
        tenant_id, _ = auth_result
        return self.tenant_manager.get_tenant(tenant_id)

    def check_agent_quota(self, tenant_id: str, quota_type: str, usage: int) -> bool:
        """
        Check if an agent operation is within tenant quota.

        Args:
            tenant_id: Tenant identifier.
            quota_type: Type of quota to check.
            usage: Current usage count.

        Returns:
            True if within quota.
        """
        return self.tenant_manager.check_quota(tenant_id, quota_type, usage)

    def has_feature(self, tenant_id: str, feature_name: str) -> bool:
        """
        Check if tenant has a specific feature.

        Args:
            tenant_id: Tenant identifier.
            feature_name: Feature name.

        Returns:
            True if feature is enabled.
        """
        return self.tenant_manager.has_feature(tenant_id, feature_name)

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for a tenant.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            Dict with tenant statistics.
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if tenant is None:
            return {}

        registry = self.tenant_registries.get(tenant_id)
        agent_count = len(registry.list_agents()) if registry else 0

        return {
            'tenant_id': tenant_id,
            'tenant_name': tenant.name,
            'plan': tenant.plan,
            'agent_count': agent_count,
            'max_agents': tenant.quotas.max_agents,
            'features': {
                'premium_support': tenant.features.premium_support,
                'advanced_analytics': tenant.features.advanced_analytics,
                'audit_trail': tenant.features.audit_trail,
            },
            'quotas': {
                'queries_per_hour': tenant.quotas.max_queries_per_hour,
                'queries_per_day': tenant.quotas.max_queries_per_day,
            },
            'is_active': tenant.is_active,
        }

    def reset(self) -> None:
        """Clear all registry data (for testing)."""
        for registry in self.tenant_registries.values():
            registry.reset()
        self.tenant_registries.clear()
        self.api_key_tenant_map.clear()
        self._ensure_tenant_registry(self.DEFAULT_TENANT_ID)
        logger.info("Multi-tenant registry reset")

    # Backward compatibility methods

    def register_agent_legacy(
        self,
        agent_id: str,
        agent_info: Dict,
        credentials: Optional[Dict[str, str]] = None,
        database_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Legacy registration without tenant (uses default tenant).
        For backward compatibility.
        """
        return self.register_agent(
            tenant_id=self.DEFAULT_TENANT_ID,
            agent_id=agent_id,
            agent_info=agent_info,
            credentials=credentials,
            database_config=database_config
        )

    def get_agent_legacy(self, agent_id: str) -> Optional[Dict]:
        """
        Legacy get_agent without tenant (searches all tenants).
        For backward compatibility.
        """
        # First check default tenant
        agent = self.get_agent(self.DEFAULT_TENANT_ID, agent_id)
        if agent:
            return agent

        # Search all tenants
        for tenant_id, registry in self.tenant_registries.items():
            agent = registry.get_agent(agent_id)
            if agent:
                return agent
        return None

    def list_agents_legacy(self) -> List[str]:
        """
        Legacy list_agents (returns all agents from all tenants).
        For backward compatibility.
        """
        all_agents = []
        for registry in self.tenant_registries.values():
            all_agents.extend(registry.list_agents())
        return all_agents


# Global instance
_multi_tenant_registry: Optional[MultiTenantAgentRegistry] = None


def get_multi_tenant_registry() -> MultiTenantAgentRegistry:
    """Get the global MultiTenantAgentRegistry instance."""
    global _multi_tenant_registry
    if _multi_tenant_registry is None:
        _multi_tenant_registry = MultiTenantAgentRegistry()
    return _multi_tenant_registry


def init_multi_tenant_registry(
    tenant_manager: Optional[TenantManager] = None
) -> MultiTenantAgentRegistry:
    """Initialize the global MultiTenantAgentRegistry."""
    global _multi_tenant_registry
    _multi_tenant_registry = MultiTenantAgentRegistry(tenant_manager)
    return _multi_tenant_registry

"""Unit tests for MultiTenantAgentRegistry."""

import pytest
import tempfile
import json
from pathlib import Path

from ai_agent_connector.app.config.tenant_manager import (
    TenantManager,
    TenantInfo,
    TenantQuotas,
    TenantFeatures,
)
from ai_agent_connector.app.agents.multi_tenant_registry import (
    MultiTenantAgentRegistry,
    get_multi_tenant_registry,
    init_multi_tenant_registry,
)


class TestMultiTenantAgentRegistry:
    """Tests for MultiTenantAgentRegistry."""

    @pytest.fixture
    def tenant_manager(self):
        """Create TenantManager with test tenants."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Tenant 1: Basic plan
            tenant_001 = {
                "tenant_id": "tenant_001",
                "quotas": {
                    "max_queries_per_hour": 100,
                    "max_agents": 5,
                },
                "features": {
                    "premium_support": False,
                },
            }
            with open(Path(tmpdir) / "tenant_001.json", 'w') as f:
                json.dump(tenant_001, f)

            # Tenant 2: Enterprise plan
            tenant_002 = {
                "tenant_id": "tenant_002",
                "quotas": {
                    "max_queries_per_hour": 10000,
                    "max_agents": 100,
                },
                "features": {
                    "premium_support": True,
                    "advanced_analytics": True,
                },
            }
            with open(Path(tmpdir) / "tenant_002.json", 'w') as f:
                json.dump(tenant_002, f)

            # Inactive tenant
            tenant_inactive = {
                "tenant_id": "tenant_inactive",
                "is_active": False,
            }
            with open(Path(tmpdir) / "tenant_inactive.json", 'w') as f:
                json.dump(tenant_inactive, f)

            manager = TenantManager(config_dir=tmpdir)
            yield manager

    @pytest.fixture
    def registry(self, tenant_manager):
        """Create MultiTenantAgentRegistry with test tenant manager."""
        return MultiTenantAgentRegistry(tenant_manager=tenant_manager)

    def test_register_agent_with_tenant(self, registry):
        """Test registering agent under a tenant."""
        result = registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent", "role": "Doctor"},
        )

        assert result["agent_id"] == "agent-1"
        assert result["tenant_id"] == "tenant_001"
        assert "api_key" in result

    def test_register_agent_adds_tenant_to_info(self, registry):
        """Test that tenant_id is added to agent info."""
        registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )

        agent = registry.get_agent("tenant_001", "agent-1")
        assert agent is not None
        assert agent.get("tenant_id") == "tenant_001"

    def test_register_agent_unknown_tenant(self, registry):
        """Test registering agent with unknown tenant raises error."""
        with pytest.raises(ValueError, match="Unknown tenant"):
            registry.register_agent(
                tenant_id="nonexistent",
                agent_id="agent-1",
                agent_info={"name": "Test"},
            )

    def test_register_agent_inactive_tenant(self, registry):
        """Test registering agent with inactive tenant raises error."""
        with pytest.raises(ValueError, match="Tenant is inactive"):
            registry.register_agent(
                tenant_id="tenant_inactive",
                agent_id="agent-1",
                agent_info={"name": "Test"},
            )

    def test_register_agent_quota_exceeded(self, registry):
        """Test that agent quota is enforced."""
        # tenant_001 has max_agents=5
        for i in range(5):
            registry.register_agent(
                tenant_id="tenant_001",
                agent_id=f"agent-{i}",
                agent_info={"name": f"Agent {i}"},
            )

        # 6th agent should fail
        with pytest.raises(ValueError, match="Agent quota exceeded"):
            registry.register_agent(
                tenant_id="tenant_001",
                agent_id="agent-6",
                agent_info={"name": "Agent 6"},
            )

    def test_authenticate_agent(self, registry):
        """Test agent authentication returns tenant and agent ID."""
        result = registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )
        api_key = result["api_key"]

        auth_result = registry.authenticate_agent(api_key)
        assert auth_result is not None
        tenant_id, agent_id = auth_result
        assert tenant_id == "tenant_001"
        assert agent_id == "agent-1"

    def test_authenticate_agent_invalid_key(self, registry):
        """Test authentication with invalid key returns None."""
        assert registry.authenticate_agent("invalid-key") is None

    def test_authenticate_agent_legacy(self, registry):
        """Test legacy authentication returns only agent_id."""
        result = registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )
        api_key = result["api_key"]

        agent_id = registry.authenticate_agent_legacy(api_key)
        assert agent_id == "agent-1"

    def test_get_agent(self, registry):
        """Test getting agent by tenant and agent ID."""
        registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent", "role": "Doctor"},
        )

        agent = registry.get_agent("tenant_001", "agent-1")
        assert agent is not None
        assert agent["name"] == "Test Agent"
        assert agent["role"] == "Doctor"

    def test_get_agent_wrong_tenant(self, registry):
        """Test getting agent with wrong tenant returns None."""
        registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )

        # Agent exists in tenant_001, not tenant_002
        agent = registry.get_agent("tenant_002", "agent-1")
        assert agent is None

    def test_get_agent_by_api_key(self, registry):
        """Test getting agent by API key."""
        result = registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )
        api_key = result["api_key"]

        agent = registry.get_agent_by_api_key(api_key)
        assert agent is not None
        assert agent["name"] == "Test Agent"

    def test_list_agents_by_tenant(self, registry):
        """Test listing agents for a specific tenant."""
        # Register agents in different tenants
        registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Agent 1"},
        )
        registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-2",
            agent_info={"name": "Agent 2"},
        )
        registry.register_agent(
            tenant_id="tenant_002",
            agent_id="agent-3",
            agent_info={"name": "Agent 3"},
        )

        # List agents per tenant
        tenant_001_agents = registry.list_agents("tenant_001")
        tenant_002_agents = registry.list_agents("tenant_002")

        assert len(tenant_001_agents) == 2
        assert "agent-1" in tenant_001_agents
        assert "agent-2" in tenant_001_agents
        assert len(tenant_002_agents) == 1
        assert "agent-3" in tenant_002_agents

    def test_list_all_agents(self, registry):
        """Test listing all agents grouped by tenant."""
        registry.register_agent("tenant_001", "agent-1", {"name": "A1"})
        registry.register_agent("tenant_001", "agent-2", {"name": "A2"})
        registry.register_agent("tenant_002", "agent-3", {"name": "A3"})

        all_agents = registry.list_all_agents()

        assert "tenant_001" in all_agents
        assert "tenant_002" in all_agents
        assert len(all_agents["tenant_001"]) == 2
        assert len(all_agents["tenant_002"]) == 1

    def test_revoke_agent(self, registry):
        """Test revoking an agent."""
        result = registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )
        api_key = result["api_key"]

        # Verify agent exists
        assert registry.get_agent("tenant_001", "agent-1") is not None
        assert registry.authenticate_agent(api_key) is not None

        # Revoke
        assert registry.revoke_agent("tenant_001", "agent-1") is True

        # Verify agent is gone
        assert registry.get_agent("tenant_001", "agent-1") is None
        assert registry.authenticate_agent(api_key) is None

    def test_revoke_agent_wrong_tenant(self, registry):
        """Test revoking agent with wrong tenant returns False."""
        registry.register_agent(
            tenant_id="tenant_001",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )

        # Try to revoke from wrong tenant
        assert registry.revoke_agent("tenant_002", "agent-1") is False

        # Agent should still exist
        assert registry.get_agent("tenant_001", "agent-1") is not None

    def test_tenant_isolation(self, registry):
        """Test that agents are isolated between tenants."""
        # Same agent_id in different tenants
        result1 = registry.register_agent(
            tenant_id="tenant_001",
            agent_id="shared-id",
            agent_info={"name": "Tenant 1 Agent"},
        )
        result2 = registry.register_agent(
            tenant_id="tenant_002",
            agent_id="shared-id",
            agent_info={"name": "Tenant 2 Agent"},
        )

        # Different API keys
        assert result1["api_key"] != result2["api_key"]

        # Get correct agent per tenant
        agent1 = registry.get_agent("tenant_001", "shared-id")
        agent2 = registry.get_agent("tenant_002", "shared-id")

        assert agent1["name"] == "Tenant 1 Agent"
        assert agent2["name"] == "Tenant 2 Agent"

    def test_get_tenant_for_agent(self, registry):
        """Test getting tenant info for an agent."""
        result = registry.register_agent(
            tenant_id="tenant_002",
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )
        api_key = result["api_key"]

        tenant = registry.get_tenant_for_agent(api_key)
        assert tenant is not None
        assert tenant.tenant_id == "tenant_002"
        assert tenant.plan == "enterprise"  # tenant_002 has both premium features

    def test_check_agent_quota(self, registry):
        """Test quota checking for agents."""
        # tenant_001 has max_queries_per_hour=100
        assert registry.check_agent_quota("tenant_001", "queries_per_hour", 50) is True
        assert registry.check_agent_quota("tenant_001", "queries_per_hour", 100) is False

    def test_has_feature(self, registry):
        """Test feature checking for tenants."""
        # tenant_001 is basic (no premium)
        assert registry.has_feature("tenant_001", "premium_support") is False
        assert registry.has_feature("tenant_001", "advanced_analytics") is False

        # tenant_002 is enterprise
        assert registry.has_feature("tenant_002", "premium_support") is True
        assert registry.has_feature("tenant_002", "advanced_analytics") is True

    def test_get_tenant_stats(self, registry):
        """Test getting tenant statistics."""
        registry.register_agent("tenant_001", "agent-1", {"name": "A1"})
        registry.register_agent("tenant_001", "agent-2", {"name": "A2"})

        stats = registry.get_tenant_stats("tenant_001")

        assert stats["tenant_id"] == "tenant_001"
        assert stats["agent_count"] == 2
        assert stats["max_agents"] == 5
        assert stats["plan"] == "basic"

    def test_reset(self, registry):
        """Test registry reset."""
        registry.register_agent("tenant_001", "agent-1", {"name": "A1"})
        registry.register_agent("tenant_002", "agent-2", {"name": "A2"})

        registry.reset()

        assert registry.list_agents("tenant_001") == []
        assert registry.list_agents("tenant_002") == []
        assert len(registry.api_key_tenant_map) == 0


class TestLegacyCompatibility:
    """Tests for backward compatibility methods."""

    @pytest.fixture
    def registry(self):
        """Create registry with default tenant manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TenantManager(config_dir=tmpdir)
            return MultiTenantAgentRegistry(tenant_manager=manager)

    def test_register_agent_legacy(self, registry):
        """Test legacy registration uses default tenant."""
        result = registry.register_agent_legacy(
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )

        assert result["agent_id"] == "agent-1"
        assert result["tenant_id"] == "default"

    def test_get_agent_legacy(self, registry):
        """Test legacy get_agent searches all tenants."""
        registry.register_agent_legacy(
            agent_id="agent-1",
            agent_info={"name": "Test Agent"},
        )

        agent = registry.get_agent_legacy("agent-1")
        assert agent is not None
        assert agent["name"] == "Test Agent"

    def test_list_agents_legacy(self, registry):
        """Test legacy list_agents returns all agents."""
        registry.register_agent_legacy("agent-1", {"name": "A1"})
        registry.register_agent_legacy("agent-2", {"name": "A2"})

        agents = registry.list_agents_legacy()
        assert len(agents) == 2
        assert "agent-1" in agents
        assert "agent-2" in agents


class TestGlobalInstance:
    """Tests for global registry instance."""

    def test_get_multi_tenant_registry_singleton(self):
        """Test that global instance is a singleton."""
        reg1 = get_multi_tenant_registry()
        reg2 = get_multi_tenant_registry()
        assert reg1 is reg2

    def test_init_multi_tenant_registry(self):
        """Test initializing global instance with custom manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tenant = {"tenant_id": "custom"}
            with open(Path(tmpdir) / "custom.json", 'w') as f:
                json.dump(tenant, f)

            manager = TenantManager(config_dir=tmpdir)
            registry = init_multi_tenant_registry(tenant_manager=manager)

            # Should be able to register in custom tenant
            result = registry.register_agent(
                tenant_id="custom",
                agent_id="agent-1",
                agent_info={"name": "Test"},
            )
            assert result["tenant_id"] == "custom"

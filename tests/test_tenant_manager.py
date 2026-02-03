"""Unit tests for TenantManager."""

import os
import json
import pytest
import tempfile
from pathlib import Path

from ai_agent_connector.app.config.tenant_manager import (
    TenantInfo,
    TenantQuotas,
    TenantFeatures,
    TenantDatabaseConfig,
    TenantManager,
    get_tenant_manager,
    init_tenant_manager,
)


class TestTenantInfo:
    """Tests for TenantInfo dataclass."""

    def test_create_default_tenant_info(self):
        """Test creating TenantInfo with defaults."""
        tenant = TenantInfo(tenant_id="test-tenant")
        assert tenant.tenant_id == "test-tenant"
        assert tenant.name == ""
        assert tenant.plan == "basic"
        assert tenant.is_active is True

    def test_create_full_tenant_info(self):
        """Test creating TenantInfo with all fields."""
        quotas = TenantQuotas(max_queries_per_hour=2000)
        features = TenantFeatures(premium_support=True)
        database = TenantDatabaseConfig(host="db.example.com")

        tenant = TenantInfo(
            tenant_id="enterprise-tenant",
            name="Enterprise Corp",
            plan="enterprise",
            quotas=quotas,
            features=features,
            database=database,
            is_active=True,
        )

        assert tenant.tenant_id == "enterprise-tenant"
        assert tenant.name == "Enterprise Corp"
        assert tenant.plan == "enterprise"
        assert tenant.quotas.max_queries_per_hour == 2000
        assert tenant.features.premium_support is True
        assert tenant.database.host == "db.example.com"

    def test_to_dict(self):
        """Test converting TenantInfo to dictionary."""
        tenant = TenantInfo(tenant_id="test", name="Test Tenant")
        data = tenant.to_dict()

        assert data["tenant_id"] == "test"
        assert data["name"] == "Test Tenant"
        assert "quotas" in data
        assert "features" in data
        assert "database" in data


class TestTenantQuotas:
    """Tests for TenantQuotas dataclass."""

    def test_default_quotas(self):
        """Test default quota values."""
        quotas = TenantQuotas()
        assert quotas.max_queries_per_hour == 1000
        assert quotas.max_queries_per_day == 10000
        assert quotas.max_concurrent_connections == 5
        assert quotas.max_agents == 100
        assert quotas.max_storage_mb == 1024

    def test_custom_quotas(self):
        """Test custom quota values."""
        quotas = TenantQuotas(
            max_queries_per_hour=5000,
            max_queries_per_day=50000,
        )
        assert quotas.max_queries_per_hour == 5000
        assert quotas.max_queries_per_day == 50000


class TestTenantFeatures:
    """Tests for TenantFeatures dataclass."""

    def test_default_features(self):
        """Test default feature flags."""
        features = TenantFeatures()
        assert features.premium_support is False
        assert features.advanced_analytics is False
        assert features.audit_trail is True
        assert features.schema_drift_detection is True

    def test_enterprise_features(self):
        """Test enterprise feature flags."""
        features = TenantFeatures(
            premium_support=True,
            advanced_analytics=True,
            custom_ontologies=True,
        )
        assert features.premium_support is True
        assert features.advanced_analytics is True
        assert features.custom_ontologies is True


class TestTenantManager:
    """Tests for TenantManager class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory with test tenant configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tenant_001.json
            tenant_001 = {
                "tenant_id": "tenant_001",
                "db_host": "db1.example.com",
                "db_port": 5432,
                "db_name": "tenant_001_db",
                "db_user": "user1",
                "db_password": "pass1",
                "quotas": {
                    "max_queries_per_hour": 1000,
                    "max_queries_per_day": 10000,
                },
                "features": {
                    "premium_support": True,
                    "advanced_analytics": False,
                },
            }
            with open(Path(tmpdir) / "tenant_001.json", 'w') as f:
                json.dump(tenant_001, f)

            # Create tenant_002.json (enterprise)
            tenant_002 = {
                "tenant_id": "tenant_002",
                "db_host": "db2.example.com",
                "db_port": 5432,
                "db_name": "tenant_002_db",
                "quotas": {
                    "max_queries_per_hour": 5000,
                },
                "features": {
                    "premium_support": True,
                    "advanced_analytics": True,
                },
            }
            with open(Path(tmpdir) / "tenant_002.json", 'w') as f:
                json.dump(tenant_002, f)

            yield tmpdir

    def test_load_tenant_configs(self, temp_config_dir):
        """Test loading tenant configurations from JSON files."""
        manager = TenantManager(config_dir=temp_config_dir)

        assert "tenant_001" in manager.tenants
        assert "tenant_002" in manager.tenants
        assert "default" in manager.tenants  # Default always exists

    def test_get_tenant(self, temp_config_dir):
        """Test getting tenant by ID."""
        manager = TenantManager(config_dir=temp_config_dir)

        tenant = manager.get_tenant("tenant_001")
        assert tenant is not None
        assert tenant.tenant_id == "tenant_001"
        assert tenant.database.host == "db1.example.com"

    def test_get_nonexistent_tenant(self, temp_config_dir):
        """Test getting non-existent tenant returns None."""
        manager = TenantManager(config_dir=temp_config_dir)
        assert manager.get_tenant("nonexistent") is None

    def test_get_tenant_or_default(self, temp_config_dir):
        """Test fallback to default tenant."""
        manager = TenantManager(config_dir=temp_config_dir)

        # Existing tenant
        tenant = manager.get_tenant_or_default("tenant_001")
        assert tenant.tenant_id == "tenant_001"

        # Non-existent falls back to default
        tenant = manager.get_tenant_or_default("nonexistent")
        assert tenant.tenant_id == "default"

        # None falls back to default
        tenant = manager.get_tenant_or_default(None)
        assert tenant.tenant_id == "default"

    def test_validate_tenant(self, temp_config_dir):
        """Test tenant validation."""
        manager = TenantManager(config_dir=temp_config_dir)

        assert manager.validate_tenant("tenant_001") is True
        assert manager.validate_tenant("nonexistent") is False

    def test_list_tenants(self, temp_config_dir):
        """Test listing all tenants."""
        manager = TenantManager(config_dir=temp_config_dir)
        tenants = manager.list_tenants()

        assert len(tenants) >= 2  # At least tenant_001 and tenant_002
        tenant_ids = [t.tenant_id for t in tenants]
        assert "tenant_001" in tenant_ids
        assert "tenant_002" in tenant_ids

    def test_get_tenant_ids(self, temp_config_dir):
        """Test getting list of tenant IDs."""
        manager = TenantManager(config_dir=temp_config_dir)
        ids = manager.get_tenant_ids()

        assert "tenant_001" in ids
        assert "tenant_002" in ids

    def test_check_quota_within_limit(self, temp_config_dir):
        """Test quota check when within limit."""
        manager = TenantManager(config_dir=temp_config_dir)

        # tenant_001 has 1000 queries/hour
        assert manager.check_quota("tenant_001", "queries_per_hour", 500) is True
        assert manager.check_quota("tenant_001", "queries_per_hour", 999) is True

    def test_check_quota_exceeded(self, temp_config_dir):
        """Test quota check when exceeded."""
        manager = TenantManager(config_dir=temp_config_dir)

        # tenant_001 has 1000 queries/hour
        assert manager.check_quota("tenant_001", "queries_per_hour", 1000) is False
        assert manager.check_quota("tenant_001", "queries_per_hour", 2000) is False

    def test_has_feature(self, temp_config_dir):
        """Test feature flag checking."""
        manager = TenantManager(config_dir=temp_config_dir)

        # tenant_001 has premium_support but not advanced_analytics
        assert manager.has_feature("tenant_001", "premium_support") is True
        assert manager.has_feature("tenant_001", "advanced_analytics") is False

        # tenant_002 has both
        assert manager.has_feature("tenant_002", "premium_support") is True
        assert manager.has_feature("tenant_002", "advanced_analytics") is True

    def test_plan_detection(self, temp_config_dir):
        """Test automatic plan detection based on features."""
        manager = TenantManager(config_dir=temp_config_dir)

        # tenant_001: premium_support only = professional
        assert manager.get_tenant("tenant_001").plan == "professional"

        # tenant_002: premium_support + advanced_analytics = enterprise
        assert manager.get_tenant("tenant_002").plan == "enterprise"

    def test_add_tenant(self, temp_config_dir):
        """Test adding tenant in memory."""
        manager = TenantManager(config_dir=temp_config_dir)

        new_tenant = TenantInfo(tenant_id="new_tenant", name="New Tenant")
        manager.add_tenant(new_tenant)

        assert manager.get_tenant("new_tenant") is not None
        assert manager.get_tenant("new_tenant").name == "New Tenant"

    def test_remove_tenant(self, temp_config_dir):
        """Test removing tenant."""
        manager = TenantManager(config_dir=temp_config_dir)

        assert manager.remove_tenant("tenant_001") is True
        assert manager.get_tenant("tenant_001") is None

    def test_cannot_remove_default_tenant(self, temp_config_dir):
        """Test that default tenant cannot be removed."""
        manager = TenantManager(config_dir=temp_config_dir)

        assert manager.remove_tenant("default") is False
        assert manager.get_tenant("default") is not None

    def test_reload_configs(self, temp_config_dir):
        """Test reloading configurations."""
        manager = TenantManager(config_dir=temp_config_dir)

        # Add in-memory tenant
        manager.add_tenant(TenantInfo(tenant_id="memory_only"))
        assert manager.get_tenant("memory_only") is not None

        # Reload - memory tenant should be gone
        manager.reload_configs()
        assert manager.get_tenant("memory_only") is None
        assert manager.get_tenant("tenant_001") is not None

    def test_get_database_config(self, temp_config_dir):
        """Test getting database configuration."""
        manager = TenantManager(config_dir=temp_config_dir)

        db_config = manager.get_database_config("tenant_001")
        assert db_config.host == "db1.example.com"
        assert db_config.port == 5432
        assert db_config.name == "tenant_001_db"


class TestEnvVarResolution:
    """Tests for environment variable resolution in configs."""

    @pytest.fixture
    def config_with_env_vars(self):
        """Create config with environment variable placeholders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tenant = {
                "tenant_id": "env_tenant",
                "db_host": "${DB_HOST:localhost}",
                "db_password": "${DB_PASSWORD:default_pass}",
                "quotas": {
                    "max_queries_per_hour": 1000,
                },
            }
            with open(Path(tmpdir) / "env_tenant.json", 'w') as f:
                json.dump(tenant, f)
            yield tmpdir

    def test_env_var_with_default(self, config_with_env_vars):
        """Test environment variable with default value."""
        # Don't set env var - should use default
        manager = TenantManager(config_dir=config_with_env_vars)
        tenant = manager.get_tenant("env_tenant")

        assert tenant.database.host == "localhost"
        assert tenant.database.password == "default_pass"

    def test_env_var_override(self, config_with_env_vars):
        """Test environment variable override."""
        os.environ["DB_HOST"] = "prod-db.example.com"
        os.environ["DB_PASSWORD"] = "secret123"

        try:
            manager = TenantManager(config_dir=config_with_env_vars)
            tenant = manager.get_tenant("env_tenant")

            assert tenant.database.host == "prod-db.example.com"
            assert tenant.database.password == "secret123"
        finally:
            del os.environ["DB_HOST"]
            del os.environ["DB_PASSWORD"]


class TestGlobalInstance:
    """Tests for global TenantManager instance."""

    def test_get_tenant_manager_singleton(self):
        """Test that get_tenant_manager returns singleton."""
        manager1 = get_tenant_manager()
        manager2 = get_tenant_manager()
        assert manager1 is manager2

    def test_init_tenant_manager(self):
        """Test initializing global instance with custom config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tenant = {"tenant_id": "custom_tenant"}
            with open(Path(tmpdir) / "custom.json", 'w') as f:
                json.dump(tenant, f)

            manager = init_tenant_manager(config_dir=tmpdir)
            assert manager.get_tenant("custom_tenant") is not None

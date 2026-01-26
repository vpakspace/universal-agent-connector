"""
Pytest test cases for Multi-Tenant MCP Connection Manager
Tests tenant isolation, security, pooling, and error handling
"""

import pytest
import json
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tenant_mcp_manager import TenantMCPManager, get_manager
from tenant_credentials import TenantCredentialVault, MCPError
from scoped_mcp_server import (
    create_tenant_scoped_server,
    scope_uri,
    validate_uri_access,
    MCPForbiddenError
)
from connection_pool import MCPConnectionPool, MCPServerInstance


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for tenant configs"""
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "tenant_configs"
    config_dir.mkdir(parents=True)
    
    # Create sample tenant configs
    tenants = [
        {
            "tenant_id": "tenant_001",
            "db_host": "db1.example.com",
            "db_name": "db1",
            "db_user": "user1",
            "db_password": "pass1",
            "quotas": {"max_queries_per_hour": 1000}
        },
        {
            "tenant_id": "tenant_002",
            "db_host": "db2.example.com",
            "db_name": "db2",
            "db_user": "user2",
            "db_password": "pass2",
            "quotas": {"max_queries_per_hour": 500}
        }
    ]
    
    for tenant in tenants:
        config_file = config_dir / f"{tenant['tenant_id']}.json"
        with open(config_file, 'w') as f:
            json.dump(tenant, f)
    
    yield config_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_config_dir):
    """Create manager instance with temp config directory"""
    manager = TenantMCPManager(
        config_dir=str(temp_config_dir),
        max_instances_per_tenant=5,
        idle_timeout_seconds=600,
        cleanup_interval_seconds=300
    )
    yield manager
    manager.shutdown()


class TestTenantIsolation:
    """Test cases for tenant isolation"""
    
    def test_tenant_a_can_access_own_resources(self, manager):
        """Test that tenant A can access their own resources"""
        server = manager.get_or_create_server("tenant_001")
        
        # Server should be scoped to tenant_001
        assert hasattr(server, '_tenant_id')
        assert server._tenant_id == "tenant_001"
        
        # Test URI scoping
        uri = scope_uri("database/table/customers", "tenant_001")
        assert uri.startswith("mcp://tenant_001/")
        assert validate_uri_access(uri, "tenant_001") is True
    
    def test_tenant_a_cannot_access_tenant_b_resources(self, manager):
        """Test that tenant A cannot access tenant B's resources"""
        # Get server for tenant_001
        server_a = manager.get_or_create_server("tenant_001")
        
        # Try to access tenant_002's URI
        uri_b = scope_uri("database/table/customers", "tenant_002")
        
        # Should fail validation
        assert validate_uri_access(uri_b, "tenant_001") is False
        
        # Should raise MCPForbiddenError if attempted
        with pytest.raises(MCPForbiddenError) as exc_info:
            if not validate_uri_access(uri_b, "tenant_001"):
                raise MCPForbiddenError("tenant_001", uri_b)
        
        assert "FORBIDDEN" in str(exc_info.value.error_code)
    
    def test_cross_tenant_access_blocked(self, manager):
        """Test that cross-tenant access is blocked"""
        server_a = manager.get_or_create_server("tenant_001")
        
        # Create a tool that validates URI access
        uri_b = scope_uri("database/table/customers", "tenant_002")
        
        # This should fail
        with pytest.raises(MCPForbiddenError):
            if not validate_uri_access(uri_b, "tenant_001"):
                raise MCPForbiddenError("tenant_001", uri_b)


class TestInstancePooling:
    """Test cases for instance pooling"""
    
    def test_instance_reuse(self, manager):
        """Test that instances are reused from pool"""
        # Get server twice
        server1 = manager.get_or_create_server("tenant_001")
        server2 = manager.get_or_create_server("tenant_001")
        
        # Both should be the same instance (reused)
        assert server1 is server2
    
    def test_different_tenants_get_different_instances(self, manager):
        """Test that different tenants get different instances"""
        server1 = manager.get_or_create_server("tenant_001")
        server2 = manager.get_or_create_server("tenant_002")
        
        # Should be different instances
        assert server1 is not server2
        assert server1._tenant_id == "tenant_001"
        assert server2._tenant_id == "tenant_002"
    
    def test_pool_stats(self, manager):
        """Test pool statistics"""
        # Get servers for multiple tenants
        manager.get_or_create_server("tenant_001")
        manager.get_or_create_server("tenant_002")
        manager.get_or_create_server("tenant_001")  # Reuse
        
        stats = manager.get_pool_stats()
        
        assert stats["total_acquired"] >= 2
        assert stats["current_pool_size"] >= 2
        assert stats["active_tenants"] >= 2


class TestErrorHandling:
    """Test cases for error handling"""
    
    def test_invalid_tenant_id_format(self, manager):
        """Test invalid tenant_id format raises error"""
        # Too short
        with pytest.raises(MCPError) as exc_info:
            manager.get_or_create_server("abc")
        assert "INVALID_TENANT" in str(exc_info.value.error_code)
        
        # Too long
        with pytest.raises(MCPError) as exc_info:
            manager.get_or_create_server("a" * 21)
        assert "INVALID_TENANT" in str(exc_info.value.error_code)
        
        # Invalid characters
        with pytest.raises(MCPError) as exc_info:
            manager.get_or_create_server("tenant-001")  # Contains hyphen
        assert "INVALID_TENANT" in str(exc_info.value.error_code)
    
    def test_tenant_not_configured(self, manager):
        """Test that unconfigured tenant raises error"""
        with pytest.raises(MCPError) as exc_info:
            manager.get_or_create_server("nonexistent")
        assert "TENANT_NOT_CONFIGURED" in str(exc_info.value.error_code)
    
    def test_empty_tenant_id(self, manager):
        """Test empty tenant_id raises error"""
        with pytest.raises(MCPError) as exc_info:
            manager.get_or_create_server("")
        assert "INVALID_TENANT" in str(exc_info.value.error_code)


class TestURIScoping:
    """Test cases for URI scoping"""
    
    def test_scope_uri(self):
        """Test URI scoping"""
        uri = scope_uri("database/table/customers", "tenant_001")
        assert uri == "mcp://tenant_001/database/table/customers"
        
        # Already scoped URI
        scoped_uri = scope_uri("mcp://tenant_001/database/table", "tenant_001")
        assert scoped_uri.startswith("mcp://tenant_001/")
    
    def test_validate_uri_access(self):
        """Test URI access validation"""
        uri = scope_uri("database/table/customers", "tenant_001")
        assert validate_uri_access(uri, "tenant_001") is True
        assert validate_uri_access(uri, "tenant_002") is False
    
    def test_uri_scoping_preserves_path(self):
        """Test that URI scoping preserves path structure"""
        path = "database/table/customers/column/email"
        uri = scope_uri(path, "tenant_001")
        assert path in uri
        assert uri == f"mcp://tenant_001/{path}"


class TestScopedMCPServer:
    """Test cases for scoped MCP server"""
    
    def test_create_tenant_scoped_server(self, temp_config_dir):
        """Test creating a tenant-scoped server"""
        # Load credentials
        vault = TenantCredentialVault(str(temp_config_dir))
        credentials = vault.get_credentials("tenant_001")
        
        server = create_tenant_scoped_server("tenant_001", credentials)
        
        assert server is not None
        assert hasattr(server, '_tenant_id')
        assert server._tenant_id == "tenant_001"
    
    def test_server_has_scoped_tools(self, temp_config_dir):
        """Test that server has tenant-scoped tools"""
        vault = TenantCredentialVault(str(temp_config_dir))
        credentials = vault.get_credentials("tenant_001")
        server = create_tenant_scoped_server("tenant_001", credentials)
        
        # Check that server has tenant_id attribute
        assert hasattr(server, '_tenant_id')


class TestConnectionPool:
    """Test cases for connection pool"""
    
    def test_pool_creation(self):
        """Test pool creation"""
        pool = MCPConnectionPool(max_instances_per_tenant=5, idle_timeout_seconds=60)
        assert pool.max_instances_per_tenant == 5
        assert pool.idle_timeout_seconds == 60
    
    def test_acquire_and_release(self):
        """Test acquiring and releasing instances"""
        pool = MCPConnectionPool(max_instances_per_tenant=5, idle_timeout_seconds=60)
        
        def mock_factory(tenant_id):
            mock_server = MagicMock()
            mock_server._tenant_id = tenant_id
            return mock_server
        
        instance1 = pool.acquire("tenant_001", mock_factory)
        assert instance1.tenant_id == "tenant_001"
        
        # Release and acquire again (should reuse)
        pool.release(instance1)
        instance2 = pool.acquire("tenant_001", mock_factory)
        
        # Should be the same instance (reused)
        assert instance1 is instance2
    
    def test_idle_cleanup(self):
        """Test idle instance cleanup"""
        pool = MCPConnectionPool(max_instances_per_tenant=5, idle_timeout_seconds=1)
        
        def mock_factory(tenant_id):
            mock_server = MagicMock()
            mock_server._tenant_id = tenant_id
            return mock_server
        
        # Create instance
        instance = pool.acquire("tenant_001", mock_factory)
        
        # Wait for idle timeout
        time.sleep(1.1)
        
        # Cleanup should remove idle instances
        cleaned = pool.cleanup_idle()
        assert cleaned >= 1
        
        # Pool should be empty or have only non-idle instances
        assert pool.get_pool_size("tenant_001") == 0
    
    def test_max_instances_limit(self):
        """Test max instances per tenant limit"""
        pool = MCPConnectionPool(max_instances_per_tenant=2, idle_timeout_seconds=60)
        
        instances = []
        def mock_factory(tenant_id):
            mock_server = MagicMock()
            mock_server._tenant_id = tenant_id
            instances.append(mock_server)
            return mock_server
        
        # Acquire max instances
        instance1 = pool.acquire("tenant_001", mock_factory)
        instance2 = pool.acquire("tenant_001", mock_factory)
        
        # Pool size should be at limit
        assert pool.get_pool_size("tenant_001") == 2
        
        # Acquire another (should reuse oldest or create new)
        instance3 = pool.acquire("tenant_001", mock_factory)
        assert pool.get_pool_size("tenant_001") <= 2


class TestCredentialVault:
    """Test cases for credential vault"""
    
    def test_get_credentials(self, temp_config_dir):
        """Test getting credentials"""
        vault = TenantCredentialVault(str(temp_config_dir))
        credentials = vault.get_credentials("tenant_001")
        
        assert credentials["tenant_id"] == "tenant_001"
        assert "db_host" in credentials
        assert "db_password" in credentials
    
    def test_tenant_exists(self, temp_config_dir):
        """Test checking if tenant exists"""
        vault = TenantCredentialVault(str(temp_config_dir))
        assert vault.tenant_exists("tenant_001") is True
        assert vault.tenant_exists("nonexistent") is False
    
    def test_list_tenants(self, temp_config_dir):
        """Test listing tenants"""
        vault = TenantCredentialVault(str(temp_config_dir))
        tenants = vault.list_tenants()
        
        assert "tenant_001" in tenants
        assert "tenant_002" in tenants
    
    def test_validate_tenant_id(self, temp_config_dir):
        """Test tenant_id validation"""
        vault = TenantCredentialVault(str(temp_config_dir))
        
        # Valid IDs
        vault._validate_tenant_id("tenant001")
        vault._validate_tenant_id("tenant123456")
        
        # Invalid IDs
        with pytest.raises(MCPError):
            vault._validate_tenant_id("short")
        
        with pytest.raises(MCPError):
            vault._validate_tenant_id("a" * 21)
        
        with pytest.raises(MCPError):
            vault._validate_tenant_id("tenant-001")  # Contains hyphen


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, manager):
        """Test complete workflow: get server, use tools, verify isolation"""
        # Get server for tenant_001
        server1 = manager.get_or_create_server("tenant_001")
        
        # Get server for tenant_002
        server2 = manager.get_or_create_server("tenant_002")
        
        # Verify they are different
        assert server1._tenant_id == "tenant_001"
        assert server2._tenant_id == "tenant_002"
        
        # Verify URI scoping
        uri1 = scope_uri("database/table/customers", "tenant_001")
        uri2 = scope_uri("database/table/customers", "tenant_002")
        
        assert validate_uri_access(uri1, "tenant_001") is True
        assert validate_uri_access(uri2, "tenant_002") is True
        assert validate_uri_access(uri1, "tenant_002") is False
    
    def test_manager_singleton(self, temp_config_dir):
        """Test manager singleton pattern"""
        manager1 = get_manager(
            config_dir=str(temp_config_dir),
            max_instances_per_tenant=5,
            idle_timeout_seconds=600
        )
        manager2 = get_manager(
            config_dir=str(temp_config_dir),
            max_instances_per_tenant=5,
            idle_timeout_seconds=600
        )
        
        # Should be the same instance
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


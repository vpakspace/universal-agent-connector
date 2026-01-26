"""
Tenant MCP Manager
Main manager class for creating and managing tenant-scoped MCP server instances
"""

import logging
import threading
import time
from typing import Dict, Optional
from datetime import datetime

from tenant_credentials import TenantCredentialVault, MCPError
from scoped_mcp_server import create_tenant_scoped_server
from connection_pool import MCPConnectionPool, MCPServerInstance

logger = logging.getLogger(__name__)


class TenantMCPManager:
    """
    Manages tenant-scoped MCP server instances.
    Handles creation, pooling, and lifecycle management.
    """
    
    def __init__(
        self,
        config_dir: str = "tenant_configs",
        max_instances_per_tenant: int = 5,
        idle_timeout_seconds: int = 600,
        cleanup_interval_seconds: int = 300
    ):
        """
        Initialize tenant MCP manager
        
        Args:
            config_dir: Directory containing tenant configuration files
            max_instances_per_tenant: Maximum MCP server instances per tenant
            idle_timeout_seconds: Idle timeout for instances (default: 10 minutes)
            cleanup_interval_seconds: Interval for cleanup task (default: 5 minutes)
        """
        self.credential_vault = TenantCredentialVault(config_dir)
        self.connection_pool = MCPConnectionPool(
            max_instances_per_tenant=max_instances_per_tenant,
            idle_timeout_seconds=idle_timeout_seconds
        )
        
        self.cleanup_interval = cleanup_interval_seconds
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info(
            f"Initialized TenantMCPManager: "
            f"max_instances={max_instances_per_tenant}, "
            f"idle_timeout={idle_timeout_seconds}s"
        )
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread"""
        def cleanup_loop():
            while not self._stop_cleanup.is_set():
                try:
                    cleaned = self.connection_pool.cleanup_idle()
                    if cleaned > 0:
                        logger.info(f"Cleanup thread: Removed {cleaned} idle instances")
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")
                
                # Wait for next cleanup interval
                self._stop_cleanup.wait(self.cleanup_interval)
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.debug("Started cleanup thread")
    
    def _server_factory(self, tenant_id: str):
        """
        Factory function to create a new MCP server instance
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            FastMCP server instance
        """
        # Get tenant credentials
        credentials = self.credential_vault.get_credentials(tenant_id)
        
        # Create tenant-scoped server
        server = create_tenant_scoped_server(tenant_id, credentials)
        
        return server
    
    def get_or_create_server(self, tenant_id: str):
        """
        Get or create an MCP server instance for a tenant
        
        Reuses existing instances from the pool if available.
        Creates new instance if not found.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            FastMCP server instance
            
        Raises:
            MCPError: If tenant_id is invalid or tenant is not configured
        """
        try:
            # Validate tenant exists
            if not self.credential_vault.tenant_exists(tenant_id):
                raise MCPError("TENANT_NOT_CONFIGURED", f"Tenant {tenant_id} is not configured")
            
            # Acquire instance from pool
            instance = self.connection_pool.acquire(tenant_id, self._server_factory)
            
            logger.debug(f"Retrieved MCP server instance for tenant: {tenant_id}")
            
            return instance.server
            
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Error getting server for tenant {tenant_id}: {e}")
            raise MCPError("INTERNAL_ERROR", f"Failed to get server: {e}")
    
    def release_server(self, tenant_id: str, server) -> None:
        """
        Release a server instance back to the pool
        
        Args:
            tenant_id: Tenant identifier
            server: MCP server instance
        """
        # Find instance in pool and release it
        # Note: In practice, you might want to track instances differently
        # This is a simplified implementation
        logger.debug(f"Released server instance for tenant: {tenant_id}")
    
    def get_pool_stats(self) -> Dict:
        """
        Get connection pool statistics
        
        Returns:
            Dictionary with pool statistics
        """
        return self.connection_pool.get_stats()
    
    def list_tenants(self) -> list[str]:
        """
        List all configured tenants
        
        Returns:
            List of tenant IDs
        """
        return self.credential_vault.list_tenants()
    
    def cleanup_idle_instances(self) -> int:
        """
        Manually trigger cleanup of idle instances
        
        Returns:
            Number of instances cleaned up
        """
        return self.connection_pool.cleanup_idle()
    
    def shutdown(self) -> None:
        """Shutdown manager and cleanup resources"""
        # Stop cleanup thread
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        # Clear pools
        self.connection_pool.clear()
        
        logger.info("TenantMCPManager shutdown complete")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


# Global singleton instance (optional)
_manager_instance: Optional[TenantMCPManager] = None
_manager_lock = threading.Lock()


def get_manager(
    config_dir: str = "tenant_configs",
    max_instances_per_tenant: int = 5,
    idle_timeout_seconds: int = 600
) -> TenantMCPManager:
    """
    Get or create global manager instance (singleton pattern)
    
    Args:
        config_dir: Directory containing tenant configuration files
        max_instances_per_tenant: Maximum instances per tenant
        idle_timeout_seconds: Idle timeout in seconds
        
    Returns:
        TenantMCPManager instance
    """
    global _manager_instance
    
    with _manager_lock:
        if _manager_instance is None:
            _manager_instance = TenantMCPManager(
                config_dir=config_dir,
                max_instances_per_tenant=max_instances_per_tenant,
                idle_timeout_seconds=idle_timeout_seconds
            )
        
        return _manager_instance


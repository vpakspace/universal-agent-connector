"""
MCP Connection Pool
Manages a pool of MCP server instances with idle timeout and cleanup
"""

import time
import logging
from typing import Dict, Optional, Any
from threading import Lock
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MCPServerInstance:
    """Represents an MCP server instance"""
    server: Any  # FastMCP instance
    tenant_id: str
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    
    def touch(self) -> None:
        """Update last_used timestamp"""
        self.last_used = time.time()
        self.use_count += 1
    
    def is_idle(self, timeout_seconds: int) -> bool:
        """
        Check if instance is idle
        
        Args:
            timeout_seconds: Idle timeout in seconds
            
        Returns:
            True if instance has been idle longer than timeout
        """
        return (time.time() - self.last_used) > timeout_seconds


class MCPConnectionPool:
    """
    Connection pool for MCP server instances.
    Limits instances per tenant and cleans up idle instances.
    """
    
    def __init__(self, max_instances_per_tenant: int = 5, idle_timeout_seconds: int = 600):
        """
        Initialize connection pool
        
        Args:
            max_instances_per_tenant: Maximum number of instances per tenant
            idle_timeout_seconds: Idle timeout in seconds (default: 10 minutes)
        """
        self.max_instances_per_tenant = max_instances_per_tenant
        self.idle_timeout_seconds = idle_timeout_seconds
        
        # Pool storage: {tenant_id: [MCPServerInstance, ...]}
        self._pool: Dict[str, list[MCPServerInstance]] = {}
        
        # Lock for thread safety
        self._lock = Lock()
        
        # Statistics
        self._stats = {
            "total_acquired": 0,
            "total_released": 0,
            "total_created": 0,
            "total_cleaned": 0
        }
    
    def acquire(self, tenant_id: str, server_factory: callable) -> MCPServerInstance:
        """
        Acquire or create an MCP server instance for a tenant
        
        Args:
            tenant_id: Tenant identifier
            server_factory: Function to create a new server instance (tenant_id) -> server
            
        Returns:
            MCPServerInstance
        """
        with self._lock:
            # Get or create pool for tenant
            if tenant_id not in self._pool:
                self._pool[tenant_id] = []
            
            tenant_pool = self._pool[tenant_id]
            
            # Try to reuse an existing instance
            for instance in tenant_pool:
                if not instance.is_idle(self.idle_timeout_seconds):
                    instance.touch()
                    self._stats["total_acquired"] += 1
                    logger.debug(f"Reused instance for tenant: {tenant_id}")
                    return instance
            
            # Check if we can create a new instance
            if len(tenant_pool) >= self.max_instances_per_tenant:
                # Remove idle instances first
                active_instances = [
                    inst for inst in tenant_pool
                    if not inst.is_idle(self.idle_timeout_seconds)
                ]
                
                if len(active_instances) >= self.max_instances_per_tenant:
                    # All instances are active, reuse the oldest one
                    oldest = min(tenant_pool, key=lambda x: x.last_used)
                    oldest.touch()
                    self._stats["total_acquired"] += 1
                    logger.warning(f"Pool full for tenant {tenant_id}, reusing oldest instance")
                    return oldest
                
                # Remove idle instances
                tenant_pool[:] = active_instances
            
            # Create new instance
            server = server_factory(tenant_id)
            instance = MCPServerInstance(
                server=server,
                tenant_id=tenant_id
            )
            instance.touch()
            
            tenant_pool.append(instance)
            self._stats["total_created"] += 1
            self._stats["total_acquired"] += 1
            
            logger.info(f"Created new MCP server instance for tenant: {tenant_id} (pool size: {len(tenant_pool)})")
            
            return instance
    
    def release(self, instance: MCPServerInstance) -> None:
        """
        Release an instance back to the pool (touch it)
        
        Args:
            instance: MCP server instance
        """
        instance.touch()
        self._stats["total_released"] += 1
        logger.debug(f"Released instance for tenant: {instance.tenant_id}")
    
    def cleanup_idle(self) -> int:
        """
        Clean up idle instances across all tenants
        
        Returns:
            Number of instances cleaned up
        """
        with self._lock:
            cleaned_count = 0
            
            for tenant_id in list(self._pool.keys()):
                tenant_pool = self._pool[tenant_id]
                initial_count = len(tenant_pool)
                
                # Keep only non-idle instances
                tenant_pool[:] = [
                    inst for inst in tenant_pool
                    if not inst.is_idle(self.idle_timeout_seconds)
                ]
                
                removed_count = initial_count - len(tenant_pool)
                cleaned_count += removed_count
                
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} idle instances for tenant: {tenant_id}")
                
                # Remove empty tenant pools
                if not tenant_pool:
                    del self._pool[tenant_id]
            
            self._stats["total_cleaned"] += cleaned_count
            
            return cleaned_count
    
    def get_pool_size(self, tenant_id: Optional[str] = None) -> int:
        """
        Get current pool size
        
        Args:
            tenant_id: If provided, get size for this tenant. Otherwise get total size.
            
        Returns:
            Pool size
        """
        with self._lock:
            if tenant_id:
                return len(self._pool.get(tenant_id, []))
            else:
                return sum(len(pool) for pool in self._pool.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                **self._stats,
                "current_pool_size": self.get_pool_size(),
                "active_tenants": len(self._pool),
                "instances_per_tenant": {
                    tenant_id: len(pool)
                    for tenant_id, pool in self._pool.items()
                }
            }
    
    def clear(self, tenant_id: Optional[str] = None) -> None:
        """
        Clear pool for a tenant or all tenants
        
        Args:
            tenant_id: If provided, clear only this tenant's pool. Otherwise clear all.
        """
        with self._lock:
            if tenant_id:
                if tenant_id in self._pool:
                    del self._pool[tenant_id]
                    logger.info(f"Cleared pool for tenant: {tenant_id}")
            else:
                self._pool.clear()
                logger.info("Cleared all pools")


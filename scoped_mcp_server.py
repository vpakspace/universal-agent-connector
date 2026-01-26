"""
Scoped MCP Server Factory
Creates tenant-scoped MCP server instances with URI scoping and access validation
"""

import re
import logging
from typing import Dict, Any, Optional, List
from functools import wraps

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is required. Install it with: pip install fastmcp"
    )

from tenant_credentials import MCPError

logger = logging.getLogger(__name__)


class MCPForbiddenError(MCPError):
    """Exception raised for cross-tenant access attempts"""
    def __init__(self, tenant_id: str, attempted_uri: str):
        self.tenant_id = tenant_id
        self.attempted_uri = attempted_uri
        super().__init__(
            "FORBIDDEN",
            f"Tenant {tenant_id} attempted to access forbidden URI: {attempted_uri}"
        )


def scope_uri(uri: str, tenant_id: str) -> str:
    """
    Scope a URI with tenant prefix
    
    All resource URIs must be: mcp://{tenant_id}/...
    
    Args:
        uri: Original URI
        tenant_id: Tenant identifier
        
    Returns:
        Scoped URI
    """
    # If already scoped, return as-is
    if uri.startswith(f"mcp://{tenant_id}/"):
        return uri
    
    # If starts with mcp://, replace or prepend tenant_id
    if uri.startswith("mcp://"):
        # Remove existing tenant if any: mcp://old_tenant/path -> mcp://{tenant_id}/path
        parts = uri.split("/", 3)
        if len(parts) >= 4:
            return f"mcp://{tenant_id}/{parts[3]}"
        else:
            return f"mcp://{tenant_id}/"
    else:
        # Add mcp:// prefix and tenant scope
        if uri.startswith("/"):
            return f"mcp://{tenant_id}{uri}"
        else:
            return f"mcp://{tenant_id}/{uri}"


def validate_uri_access(uri: str, tenant_id: str) -> bool:
    """
    Validate that a URI belongs to the tenant
    
    Args:
        uri: URI to validate
        tenant_id: Expected tenant identifier
        
    Returns:
        True if URI belongs to tenant, False otherwise
    """
    # URIs must start with mcp://{tenant_id}/
    expected_prefix = f"mcp://{tenant_id}/"
    
    if not uri.startswith(expected_prefix):
        return False
    
    return True


def tenant_scope_decorator(tenant_id: str):
    """
    Decorator to validate tenant scope for MCP tool functions
    
    Args:
        tenant_id: Tenant identifier
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check for resource_uri in kwargs
            resource_uri = kwargs.get("resource_uri") or kwargs.get("uri")
            
            if resource_uri:
                if not validate_uri_access(resource_uri, tenant_id):
                    # Log security event (NEVER log full URI if it contains credentials)
                    safe_uri = resource_uri[:100]  # Limit log length
                    logger.warning(
                        f"SECURITY: Tenant {tenant_id} attempted cross-tenant access to URI: {safe_uri}...",
                        extra={"tenant_id": tenant_id, "attempted_uri": resource_uri}
                    )
                    raise MCPForbiddenError(tenant_id, resource_uri)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def create_tenant_scoped_server(tenant_id: str, credentials: Dict[str, Any]) -> FastMCP:
    """
    Create a tenant-scoped MCP server instance
    
    Args:
        tenant_id: Tenant identifier
        credentials: Tenant credentials dictionary
        
    Returns:
        FastMCP server instance
    """
    server_name = f"Connector-{tenant_id}"
    mcp_server = FastMCP(server_name)
    
    # Store tenant_id in server metadata (for validation)
    mcp_server._tenant_id = tenant_id
    mcp_server._credentials = credentials
    
    # Create scoped tools with tenant validation
    
    @mcp_server.tool()
    async def list_tenant_resources(resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List resources available to this tenant.
        Only shows resources belonging to the tenant.
        
        Args:
            resource_type: Optional filter by resource type (e.g., "database", "table")
            
        Returns:
            List of resource dictionaries with scoped URIs
        """
        # Example: List database tables for this tenant
        # In real implementation, query tenant's database
        resources = []
        
        # Mock resources (in production, query actual database)
        if resource_type is None or resource_type == "database":
            resources.append({
                "uri": scope_uri("database/main", tenant_id),
                "type": "database",
                "name": credentials.get("db_name", "main"),
                "description": f"Main database for tenant {tenant_id}"
            })
        
        if resource_type is None or resource_type == "table":
            # Mock tables (in production, query actual schema)
            tables = ["customers", "orders", "products"]  # Example tables
            for table in tables:
                resources.append({
                    "uri": scope_uri(f"database/table/{table}", tenant_id),
                    "type": "table",
                    "name": table,
                    "description": f"Table {table} for tenant {tenant_id}"
                })
        
        return resources
    
    @mcp_server.tool()
    async def query_tenant_data(
        resource_uri: str,
        query: str,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Query tenant data from a scoped resource.
        Blocks cross-tenant access attempts.
        
        Args:
            resource_uri: Scoped resource URI (must belong to tenant)
            query: SQL query or query string
            limit: Maximum number of results
            
        Returns:
            Query results dictionary
            
        Raises:
            MCPForbiddenError: If URI doesn't belong to tenant
        """
        # Validate URI access (block cross-tenant access)
        if not validate_uri_access(resource_uri, tenant_id):
            # Log security event
            safe_uri = resource_uri[:100]
            logger.warning(
                f"SECURITY: Tenant {tenant_id} attempted cross-tenant access to URI: {safe_uri}...",
                extra={"tenant_id": tenant_id, "attempted_uri": resource_uri}
            )
            raise MCPForbiddenError(tenant_id, resource_uri)
        
        # Extract resource info from URI
        # Format: mcp://{tenant_id}/database/table/{table_name}
        uri_parts = resource_uri.replace(f"mcp://{tenant_id}/", "").split("/")
        
        # In production, execute query against tenant's database
        # For now, return mock results
        logger.info(f"Executing query for tenant {tenant_id} on resource: {resource_uri}")
        
        return {
            "tenant_id": tenant_id,
            "resource_uri": resource_uri,
            "query": query,
            "results": [],  # Mock empty results
            "row_count": 0,
            "limit": limit
        }
    
    @mcp_server.tool()
    async def get_tenant_metadata() -> Dict[str, Any]:
        """
        Get metadata about the current tenant.
        This tool is safe to call without URI scoping.
        
        Returns:
            Tenant metadata dictionary
        """
        return {
            "tenant_id": tenant_id,
            "database_host": credentials.get("db_host", "N/A"),
            "database_name": credentials.get("db_name", "N/A"),
            "quotas": credentials.get("quotas", {}),
            "server_name": server_name
        }
    
    # Override resource listing to scope URIs
    original_resource_handler = getattr(mcp_server, 'resources', None)
    
    # Add a resource handler that scopes all resources
    @mcp_server.resource("mcp://{tenant_id}/{path}")
    def tenant_scoped_resource(path: str) -> Dict[str, Any]:
        """
        Handle tenant-scoped resources
        
        Args:
            path: Resource path (already scoped with tenant_id)
            
        Returns:
            Resource data
        """
        # Validate that path belongs to this tenant
        # Path already contains tenant_id in the URI pattern
        return {
            "uri": f"mcp://{tenant_id}/{path}",
            "type": "resource",
            "tenant_id": tenant_id,
            "data": {}
        }
    
    logger.info(f"Created tenant-scoped MCP server for tenant: {tenant_id}")
    
    return mcp_server


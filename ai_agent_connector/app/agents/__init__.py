"""
AI agent registration and authentication.

Provides both single-tenant (AgentRegistry) and multi-tenant
(MultiTenantAgentRegistry) agent management.
"""

from .registry import AgentRegistry
from .multi_tenant_registry import (
    MultiTenantAgentRegistry,
    get_multi_tenant_registry,
    init_multi_tenant_registry,
)

__all__ = [
    'AgentRegistry',
    'MultiTenantAgentRegistry',
    'get_multi_tenant_registry',
    'init_multi_tenant_registry',
]










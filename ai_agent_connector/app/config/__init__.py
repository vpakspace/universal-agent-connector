"""
Configuration module for AI Agent Connector.

Provides domain configurations, table mappings, role definitions,
and multi-tenancy support.
"""

from .tenant_manager import (
    TenantInfo,
    TenantQuotas,
    TenantFeatures,
    TenantDatabaseConfig,
    TenantManager,
    get_tenant_manager,
    init_tenant_manager,
)

from .domains import (
    DomainConfig,
    DOMAIN_CONFIGS,
    DOMAIN_ALIASES,
    DEFAULT_DOMAIN,
    HOSPITAL_CONFIG,
    FINANCE_CONFIG,
    HOSPITAL_TABLE_ENTITY_MAP,
    FINANCE_TABLE_ENTITY_MAP,
    get_domain_config,
    get_table_entity_map,
    get_entity_from_table,
    get_domain_roles,
    is_valid_role,
    get_ontology_path,
    detect_domain_from_ontology,
)

__all__ = [
    # Tenant Management (Multi-tenancy)
    'TenantInfo',
    'TenantQuotas',
    'TenantFeatures',
    'TenantDatabaseConfig',
    'TenantManager',
    'get_tenant_manager',
    'init_tenant_manager',
    # Domain Configuration
    'DomainConfig',
    'DOMAIN_CONFIGS',
    'DOMAIN_ALIASES',
    'DEFAULT_DOMAIN',
    'HOSPITAL_CONFIG',
    'FINANCE_CONFIG',
    'HOSPITAL_TABLE_ENTITY_MAP',
    'FINANCE_TABLE_ENTITY_MAP',
    'get_domain_config',
    'get_table_entity_map',
    'get_entity_from_table',
    'get_domain_roles',
    'is_valid_role',
    'get_ontology_path',
    'detect_domain_from_ontology',
]

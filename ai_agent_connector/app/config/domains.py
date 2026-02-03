"""
Domain configurations for Universal Agent Connector.

Shared configuration for Hospital and Finance domains including:
- Ontology paths
- Database settings
- Role definitions
- Table-to-Entity mappings
- Permissions matrices
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Base path for ontologies
ONTOLOGIES_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'ontologies'
)


@dataclass
class DomainConfig:
    """Configuration for a domain (Hospital, Finance, etc.)."""
    name: str
    ontology_path: str
    database: Dict[str, Any]
    roles: List[str]
    tables: List[str]
    entity_types: List[str]
    table_entity_map: Dict[str, str]
    permissions_matrix: Dict[str, List[str]] = field(default_factory=dict)
    nl_examples: List[str] = field(default_factory=list)
    sql_examples: List[str] = field(default_factory=list)


# =============================================================================
# Hospital Domain
# =============================================================================

HOSPITAL_TABLE_ENTITY_MAP = {
    'patients': 'PatientRecord',
    'medical_records': 'MedicalRecord',
    'lab_results': 'LabResult',
    'prescriptions': 'Prescription',
    'medications': 'Medication',
    'billing': 'Billing',
    'appointments': 'Appointment',
    'staff': 'Staff',
    'departments': 'Department',
    'rooms': 'Room',
    'insurance': 'Insurance',
    'surgeries': 'Surgery',
    'emergency_cases': 'EmergencyCase',
    'equipment': 'Equipment',
    'audit_log': 'AuditLog',
}

HOSPITAL_CONFIG = DomainConfig(
    name='hospital',
    ontology_path=os.path.join(ONTOLOGIES_BASE_PATH, 'hospital.owl'),
    database={
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5433,
        'database': 'hospital_db',
        'user': 'uac_user',
        'password': 'uac_password'
    },
    roles=['Admin', 'Doctor', 'Nurse', 'LabTech', 'Receptionist', 'Patient', 'InsuranceAgent'],
    tables=['patients', 'medical_records', 'lab_results', 'appointments', 'billing', 'staff'],
    entity_types=['PatientRecord', 'MedicalRecord', 'LabResult', 'Prescription', 'Billing', 'Appointment', 'Staff'],
    table_entity_map=HOSPITAL_TABLE_ENTITY_MAP,
    permissions_matrix={
        'Admin': ['PatientRecord:CRUD', 'MedicalRecord:CRUD', 'LabResult:CRUD', 'Appointment:CRUD', 'Billing:CRUD', 'Staff:CRUD'],
        'Doctor': ['PatientRecord:R', 'MedicalRecord:RU', 'LabResult:R', 'Appointment:R'],
        'Nurse': ['PatientRecord:R', 'Appointment:R'],
        'LabTech': ['LabResult:RU'],
        'Receptionist': ['PatientRecord:CR', 'Appointment:CR'],
        'Patient': ['PatientRecord:R', 'Appointment:R', 'Billing:R'],
        'InsuranceAgent': ['Billing:R'],
    },
    nl_examples=[
        'Покажи всех пациентов',
        'Сколько записей в medical_records?',
        'Покажи результаты анализов для пациента John Doe',
    ],
    sql_examples=[
        'SELECT * FROM patients',
        'SELECT * FROM staff WHERE role = \'Doctor\'',
    ]
)


# =============================================================================
# Finance Domain
# =============================================================================

FINANCE_TABLE_ENTITY_MAP = {
    'accounts': 'Account',
    'transactions': 'Transaction',
    'loans': 'Loan',
    'cards': 'Card',
    'customer_profiles': 'CustomerProfile',
    'reports': 'Report',
    'audit_log': 'AuditLog',
}

FINANCE_CONFIG = DomainConfig(
    name='finance',
    ontology_path=os.path.join(ONTOLOGIES_BASE_PATH, 'finance.owl'),
    database={
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5433,
        'database': 'finance_db',
        'user': 'uac_user',
        'password': 'uac_password'
    },
    roles=['Admin', 'Manager', 'Teller', 'Analyst', 'Auditor', 'ComplianceOfficer', 'IndividualCustomer', 'CorporateCustomer'],
    tables=['accounts', 'transactions', 'loans', 'cards', 'customer_profiles', 'reports', 'audit_log'],
    entity_types=['Account', 'Transaction', 'Loan', 'Card', 'CustomerProfile', 'Report', 'AuditLog'],
    table_entity_map=FINANCE_TABLE_ENTITY_MAP,
    permissions_matrix={
        'Admin': ['Account:CRUD', 'Transaction:CRUD', 'Loan:CRUD', 'Card:CRUD', 'CustomerProfile:CRUD', 'Report:CRUD', 'AuditLog:CRUD'],
        'Manager': ['Account:CRUD', 'Transaction:RU', 'Loan:CRUD', 'Card:CRU', 'CustomerProfile:RU', 'Report:CR'],
        'Teller': ['Account:RU', 'Transaction:CR', 'Loan:R', 'Card:RU', 'CustomerProfile:R'],
        'Analyst': ['Account:R', 'Transaction:R', 'Loan:R', 'CustomerProfile:R', 'Report:CR'],
        'Auditor': ['Account:R', 'Transaction:R', 'Loan:R', 'Card:R', 'CustomerProfile:R', 'Report:R', 'AuditLog:R'],
        'ComplianceOfficer': ['Account:R', 'Transaction:R', 'CustomerProfile:R', 'Report:R', 'AuditLog:R'],
    },
    nl_examples=[
        'Покажи все счета',
        'Сколько транзакций за последний месяц?',
        'Покажи все активные кредиты',
    ],
    sql_examples=[
        'SELECT * FROM accounts',
        'SELECT * FROM transactions WHERE amount > 1000',
    ]
)


# =============================================================================
# Domain Registry
# =============================================================================

DOMAIN_CONFIGS: Dict[str, DomainConfig] = {
    'hospital': HOSPITAL_CONFIG,
    'finance': FINANCE_CONFIG,
}

# Aliases for UI display names
DOMAIN_ALIASES = {
    'Hospital (Госпиталь)': 'hospital',
    'Finance (Финансы)': 'finance',
    'hospital': 'hospital',
    'finance': 'finance',
}

DEFAULT_DOMAIN = 'hospital'


def get_domain_config(domain: str) -> Optional[DomainConfig]:
    """
    Get domain configuration by name or alias.

    Args:
        domain: Domain name or alias (e.g., 'hospital', 'Hospital (Госпиталь)')

    Returns:
        DomainConfig or None if not found
    """
    # Resolve alias
    domain_key = DOMAIN_ALIASES.get(domain, domain.lower())
    return DOMAIN_CONFIGS.get(domain_key)


def get_table_entity_map(domain: str = None) -> Dict[str, str]:
    """
    Get table-to-entity mapping for a domain.

    Args:
        domain: Domain name. If None, returns merged map from all domains.

    Returns:
        Dictionary mapping table names to OWL entity types
    """
    if domain:
        config = get_domain_config(domain)
        if config:
            return config.table_entity_map

    # Merge all domain mappings as fallback
    merged = {}
    for config in DOMAIN_CONFIGS.values():
        merged.update(config.table_entity_map)
    return merged


def get_entity_from_table(table: str, domain: str = None) -> Optional[str]:
    """
    Get OWL entity type for a SQL table name.

    Args:
        table: SQL table name (e.g., 'patients')
        domain: Domain name for context

    Returns:
        OWL entity type (e.g., 'PatientRecord') or None
    """
    mapping = get_table_entity_map(domain)
    return mapping.get(table.lower())


def get_domain_roles(domain: str) -> List[str]:
    """
    Get list of valid roles for a domain.

    Args:
        domain: Domain name

    Returns:
        List of role names
    """
    config = get_domain_config(domain)
    return config.roles if config else []


def is_valid_role(role: str, domain: str) -> bool:
    """
    Check if a role is valid for a domain.

    Args:
        role: Role name
        domain: Domain name

    Returns:
        True if role is valid
    """
    roles = get_domain_roles(domain)
    return role in roles if roles else True  # Allow all if no domain config


def get_ontology_path(domain: str) -> Optional[str]:
    """
    Get ontology file path for a domain.

    Args:
        domain: Domain name

    Returns:
        Path to OWL ontology file
    """
    config = get_domain_config(domain)
    return config.ontology_path if config else None


def detect_domain_from_ontology(ontology_path: str) -> Optional[str]:
    """
    Detect domain from ontology file path.

    Args:
        ontology_path: Path to ontology file

    Returns:
        Domain name or None
    """
    if not ontology_path:
        return None

    path_lower = ontology_path.lower()
    for domain_name in DOMAIN_CONFIGS.keys():
        if domain_name in path_lower:
            return domain_name

    return None

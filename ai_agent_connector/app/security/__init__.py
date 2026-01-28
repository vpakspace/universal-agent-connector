"""
Security module for Universal Agent Connector.

This module provides security features including:
- OntoGuard integration for semantic validation of AI agent actions
- Custom security exceptions
- Policy validation utilities
"""

from .ontoguard_adapter import (
    OntoGuardAdapter,
    ValidationResult,
    get_ontoguard_adapter,
    initialize_ontoguard,
    reset_ontoguard_adapter
)

from .exceptions import (
    OntoGuardError,
    ValidationDeniedError,
    OntologyLoadError,
    OntologyParseError,
    ConfigurationError,
    PermissionDeniedError,
    ApprovalRequiredError
)

__all__ = [
    # Core classes
    'OntoGuardAdapter',
    'ValidationResult',

    # Singleton functions
    'get_ontoguard_adapter',
    'initialize_ontoguard',
    'reset_ontoguard_adapter',

    # Exceptions
    'OntoGuardError',
    'ValidationDeniedError',
    'OntologyLoadError',
    'OntologyParseError',
    'ConfigurationError',
    'PermissionDeniedError',
    'ApprovalRequiredError',
]

"""
Universal Ontology Adapter for JAG Intelligence Suite
Enables enterprise customers to bring their own domain ontologies
"""

from .ontology_adapter import (
    OntologyAdapter,
    TurtleParser,
    YAMLParser,
    JSONLDParser,
    get_ontology_adapter
)
from .tool_registry import (
    ToolRegistry,
    MCPToolDefinition,
    scan_ontology
)
from .validation_engine import (
    ValidationEngine,
    AxiomValidator,
    validate_operation
)
from .ontology_validator import (
    OntologyValidator,
    OntologyHealthReport,
    validate_ontology_health
)

__all__ = [
    'OntologyAdapter',
    'TurtleParser',
    'YAMLParser',
    'JSONLDParser',
    'get_ontology_adapter',
    'ToolRegistry',
    'MCPToolDefinition',
    'scan_ontology',
    'ValidationEngine',
    'AxiomValidator',
    'validate_operation',
    'OntologyValidator',
    'OntologyHealthReport',
    'validate_ontology_health'
]


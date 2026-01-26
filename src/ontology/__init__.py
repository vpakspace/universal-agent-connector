"""
Ontology Compliance Guardrails (JAG-003)
Prevents impossible relationships like "Antibiotic treats Virus" or "Software Bug caused by Medication"
"""

from .compliance_guardrails import (
    OntologyValidator,
    ComplianceViolation,
    ViolationSeverity,
    ComplianceResult
)

__all__ = [
    'OntologyValidator',
    'ComplianceViolation',
    'ViolationSeverity',
    'ComplianceResult'
]


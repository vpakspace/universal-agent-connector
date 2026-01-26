# Ontology Compliance Guardrails (JAG-003)

Prevents impossible relationships like "Antibiotic treats Virus" or "Software Bug caused by Medication" in knowledge graphs.

## Overview

The Ontology Compliance Guardrails system enforces semantic integrity by:
1. **Real-time Validation**: Checks relationships during edge creation
2. **Severity Levels**: Flags violations as CRITICAL, HIGH, MEDIUM, or LOW
3. **Admin Overrides**: Allows exceptions with full audit trail
4. **Weekly Reports**: Generates semantic integrity reports

## Architecture

```
Edge Creation Request
    ↓
[OntologyValidator.validate_relationship()]
    ↓
Check forbidden_relationships.json
    ↓
┌─────────────────────────────────────┐
│  Allowed? → Create Edge             │
│  Forbidden? → Block + Log Violation  │
│  Override? → Allow + Audit Trail     │
└─────────────────────────────────────┘
    ↓
[IntegrityReportGenerator]
    ↓
Weekly Semantic Integrity Report
```

## Usage

### Basic Validation

```python
from src.ontology import OntologyValidator

validator = OntologyValidator()

# Validate relationship
result = validator.validate_relationship(
    source_type="Medication",
    target_type="SoftwareBug",
    relationship_type="CAUSES"
)

if result.is_compliant:
    # Create edge
    create_edge(source, target, relationship_type)
else:
    # Handle violation
    for violation in result.violations:
        print(f"Violation: {violation.severity} - {violation.reason}")
```

### Admin Override

```python
# Override violation with admin approval
validator.override_violation(
    violation=violation,
    override_reason="Research exception approved by Dr. Smith",
    override_by="admin_user"
)
```

### Batch Validation

```python
relationships = [
    {"source_type": "Medication", "target_type": "Disease"},
    {"source_type": "Medication", "target_type": "SoftwareBug"},
    {"source_type": "Antibiotic", "target_type": "Virus"}
]

result = validator.validate_batch(relationships)
print(f"Compliance Score: {result.compliance_score}")
print(f"Violations: {result.violation_count}")
```

### Weekly Reports

```python
from src.reports import IntegrityReportGenerator

generator = IntegrityReportGenerator(validator=validator)

# Generate weekly report
report = generator.generate_weekly_report()

# Print summary
summary = generator.generate_summary(report)
print(summary)

# Save to file
filepath = generator.save_report(report)
```

## Configuration

### forbidden_relationships.json

Define rules for each entity type:

```json
{
  "Medication": {
    "allowed_targets": ["Disease", "Symptom", "Patient"],
    "forbidden_targets": ["SoftwareBug", "Vehicle", "Building"]
  },
  "Antibiotic": {
    "allowed_targets": ["BacterialInfection", "Disease"],
    "forbidden_targets": ["Virus", "ViralInfection", "SoftwareBug"]
  }
}
```

## Severity Levels

| Severity | Description | Examples |
|----------|-------------|----------|
| **CRITICAL** | Physically impossible | Medication → SoftwareBug, Antibiotic → Virus |
| **HIGH** | Highly unlikely | Vehicle → Disease, Building → Symptom |
| **MEDIUM** | Unusual but possible | Person → Building, Organization → Vehicle |
| **LOW** | Edge case | Not in allowed list but not explicitly forbidden |

## Compliance Score

Formula: `1 - (violations / total_relationships)`

- **1.0**: Fully compliant (no violations)
- **0.8**: 20% of relationships are violations
- **0.0**: All relationships are violations

## Integration with Graph Storage

Hook into edge creation (US-015):

```python
def create_edge(source_entity, target_entity, relationship_type):
    # Step 1: Validate relationship
    result = validator.validate_relationship(
        source_type=source_entity.type,
        target_type=target_entity.type,
        relationship_type=relationship_type
    )
    
    # Step 2: Check compliance
    if not result.is_compliant:
        # Check if violation is overridden
        violations = [v for v in result.violations if not v.overridden]
        if violations:
            raise ComplianceError(f"Violation: {violations[0].reason}")
    
    # Step 3: Create edge
    graph.add_edge(source_entity.uri, target_entity.uri, type=relationship_type)
```

## Weekly Reports

Reports include:
- Total relationships analyzed
- Violation count by severity
- Compliance score
- List of critical violations
- Override count and reasons

**Report Format**: JSON with human-readable summary

## Files

- `compliance_guardrails.py`: Main validator class
- `forbidden_relationships.json`: Rules configuration
- `README.md`: This file

## Testing

Run tests:
```bash
pytest tests/test_ontology_compliance.py -v
```

Or standalone:
```bash
python tests/test_ontology_compliance_standalone.py
```


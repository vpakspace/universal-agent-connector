# OntoGuard Integration for Universal Agent Connector

## Overview

This document describes the integration of **OntoGuard** (Semantic Firewall for AI Agents) with the **Universal Agent Connector** (MCP Infrastructure).

OntoGuard provides OWL ontology-based validation for AI agent actions, enabling semantic business rules enforcement in the UAC infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Universal Agent Connector                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Flask     │    │   GraphQL   │    │    MCP Server       │  │
│  │   Routes    │───▶│   Schema    │───▶│  (database tools)   │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                  │                       │             │
│         ▼                  ▼                       ▼             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Policy Engine                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐  │   │
│  │  │RateLimit │ │   RLS    │ │Complexity│ │ PII Filter   │  │   │
│  │  └──────────┘ └──────────┘ └─────────┘ └──────────────┘  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   OntoGuard Adapter                       │   │
│  │  ┌────────────────┐    ┌─────────────────────────────┐   │   │
│  │  │ OntologyLoader │───▶│ OntologyValidator           │   │   │
│  │  │ (config.yaml)  │    │ - validate_action()         │   │   │
│  │  └────────────────┘    │ - check_permissions()       │   │   │
│  │                        │ - get_allowed_actions()     │   │   │
│  │                        └─────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Semantic Validation
- OWL ontology-based action validation
- Role-based access control via ontology rules
- Entity type constraints from business domain

### 2. API Endpoints
- `GET /api/ontoguard/status` - Check OntoGuard status
- `POST /api/ontoguard/validate` - Validate an action
- `POST /api/ontoguard/permissions` - Check role permissions
- `GET /api/ontoguard/allowed-actions` - Get allowed actions for role
- `POST /api/ontoguard/explain` - Explain validation rules

### 3. MCP Tools
- `ontoguard_validate_action` - Validate actions in AI agent workflows
- `ontoguard_check_permissions` - Quick permission checks
- `ontoguard_get_allowed_actions` - Discover allowed actions
- `ontoguard_explain_rule` - Get rule explanations
- `ontoguard_status` - Check OntoGuard status

### 4. Policy Engine Integration
- `OntoGuardValidator` - Policy validator using ontology rules
- `ExtendedPolicyEngine` - Policy engine with OntoGuard support
- Automatic action validation in policy checks

### 5. Graceful Degradation
- Pass-through mode when OntoGuard not installed
- Fail-open by default (configurable)
- Error handling for all failure scenarios

## Installation

### Prerequisites
- Universal Agent Connector installed
- Python 3.10+
- OntoGuard library (optional, for semantic validation)

### Install OntoGuard
```bash
# From OntoGuard repository
cd ~/ontoguard-ai
pip install -e .
```

### Configure OntoGuard
1. Copy ontology files:
```bash
cp ~/ontoguard-ai/examples/ontologies/ecommerce.owl ~/universal-agent-connector/ontologies/
```

2. Configure via environment variables:
```bash
export ONTOGUARD_ONTOLOGY_PATH=/path/to/ontology.owl
export ONTOGUARD_CONFIG_PATH=/path/to/ontoguard.yaml
```

3. Or use the configuration file:
```yaml
# config/ontoguard.yaml
ontoguard:
  enabled: true
  ontologies:
    - path: "ontologies/ecommerce.owl"
      name: "E-Commerce Domain"
```

## Usage

### Python API

```python
from ai_agent_connector.app.security import (
    get_ontoguard_adapter,
    initialize_ontoguard
)

# Initialize with ontology
config = {
    'ontology_paths': ['ontologies/ecommerce.owl']
}
initialize_ontoguard(config)

# Get adapter
adapter = get_ontoguard_adapter()

# Validate an action
result = adapter.validate_action(
    action='delete',
    entity_type='User',
    context={'role': 'Customer', 'user_id': '123'}
)

if result.allowed:
    print("Action permitted")
else:
    print(f"Action denied: {result.reason}")
    print(f"Suggestions: {result.suggestions}")
```

### REST API

```bash
# Check status
curl http://localhost:5000/api/ontoguard/status

# Validate action
curl -X POST http://localhost:5000/api/ontoguard/validate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "delete",
    "entity_type": "User",
    "context": {"role": "Customer"}
  }'

# Check permissions
curl -X POST http://localhost:5000/api/ontoguard/permissions \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Admin",
    "action": "delete",
    "entity_type": "User"
  }'

# Get allowed actions
curl "http://localhost:5000/api/ontoguard/allowed-actions?role=Customer&entity_type=Order"
```

### Using Decorator

```python
from ai_agent_connector.app.api.routes import validate_with_ontoguard

@app.route('/api/users/<user_id>', methods=['DELETE'])
@validate_with_ontoguard(action='delete', entity_type='User')
def delete_user(user_id):
    # This code only executes if OntoGuard permits the action
    # Role is extracted from X-User-Role header
    ...
```

### MCP Tools (for AI Agents)

```python
from ai_agent_connector.app.mcp.tools import (
    validate_action_tool,
    check_permissions_tool,
    get_allowed_actions_tool
)

# Validate before performing action
result = validate_action_tool(
    action='create',
    entity_type='Order',
    context={'role': 'Customer'}
)

if result['allowed']:
    # Proceed with order creation
    ...
```

## Configuration Reference

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `ONTOGUARD_ONTOLOGY_PATH` | Path to ontology file | `ontologies/ecommerce.owl` |
| `ONTOGUARD_CONFIG_PATH` | Path to config file | `config/ontoguard.yaml` |

### Configuration File (ontoguard.yaml)
```yaml
ontoguard:
  enabled: true                    # Enable/disable OntoGuard

  ontologies:                      # Ontology files to load
    - path: "ontologies/ecommerce.owl"
      name: "E-Commerce Domain"

  defaults:
    strict_mode: false             # Fail-closed if true
    log_violations: true           # Log denied actions
    cache_results: true            # Cache validation results
    cache_ttl: 300                 # Cache TTL in seconds

  roles:                           # Role mappings
    admin: [Admin, SystemAdmin]
    manager: [Manager, TeamLead]
    user: [Customer, Guest]

  action_mappings:                 # Action name mappings
    SELECT: read
    INSERT: create
    UPDATE: update
    DELETE: delete
```

## Error Handling

### Exception Types
| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `ValidationDeniedError` | 403 | Action denied by validation |
| `PermissionDeniedError` | 403 | Role lacks permission |
| `ApprovalRequiredError` | 403 | Approval needed |
| `OntologyLoadError` | 500 | Failed to load ontology |
| `ConfigurationError` | 500 | Invalid configuration |

### Error Response Format
```json
{
  "error": "Validation Denied",
  "error_type": "ValidationDeniedError",
  "action": "delete",
  "entity_type": "User",
  "reason": "Action 'delete' requires role 'Admin', but user has role 'Customer'",
  "suggestions": ["read", "update"]
}
```

## Testing

Run tests:
```bash
cd ~/universal-agent-connector
pytest tests/test_ontoguard_integration.py -v
```

## Files Structure

```
universal-agent-connector/
├── ai_agent_connector/
│   └── app/
│       ├── security/
│       │   ├── __init__.py          # Security module exports
│       │   ├── ontoguard_adapter.py # OntoGuard adapter
│       │   └── exceptions.py        # Custom exceptions
│       ├── api/
│       │   └── routes.py            # API endpoints (with OntoGuard)
│       └── mcp/
│           └── tools/
│               ├── __init__.py      # MCP tools exports
│               └── ontoguard_tools.py  # OntoGuard MCP tools
├── config/
│   └── ontoguard.yaml               # OntoGuard configuration
├── ontologies/
│   └── ecommerce.owl                # E-commerce ontology
├── policy_engine.py                 # Extended with OntoGuard
├── main_simple.py                   # Entry point with OntoGuard init
└── tests/
    └── test_ontoguard_integration.py # Integration tests
```

## Troubleshooting

### OntoGuard not validating
1. Check if OntoGuard is installed: `pip show ontoguard`
2. Verify ontology path exists
3. Check logs for initialization errors
4. Ensure `enabled: true` in config

### Pass-through mode active
Pass-through mode means OntoGuard allows all actions. This happens when:
- OntoGuard library not installed
- Ontology file not found
- Initialization error occurred

Check status endpoint: `GET /api/ontoguard/status`

### Validation always denied
1. Verify role is correct in context
2. Check ontology has matching action rules
3. Use explain endpoint for details
4. Check for case sensitivity in role/action names

## Links

- **OntoGuard Repository**: `~/ontoguard-ai/`
- **Universal Agent Connector**: `~/universal-agent-connector/`
- **E-Commerce Ontology**: `ontologies/ecommerce.owl`
- **Configuration**: `config/ontoguard.yaml`

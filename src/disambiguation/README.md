# Entity Disambiguation & Semantic Merging (JAG-001)

## Overview

This module implements the "Jaguar Problem" fix - preventing conflating entities like "Jaguar (cat)" and "Jaguar (car company)" during graph ingestion.

## Problem Statement

When ingesting entities into a knowledge graph, entities with the same name but different types can be incorrectly merged. For example:
- "Jaguar" (the animal) vs "Jaguar" (the car company)
- "Apple" (the fruit) vs "Apple" (the tech company)
- "Paris" (the person) vs "Paris" (the city)

This module prevents such conflations by:
1. **Type Compatibility Checking**: Blocks merging if ontology types are incompatible
2. **Context-Based Disambiguation**: Uses neighboring nodes to determine entity type
3. **Unique URI Assignment**: Assigns unique URIs to similar-sounding entities with different types
4. **Audit Logging**: Logs all disambiguation decisions for compliance

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Node Creation (US-015)                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. DisambiguationService.disambiguate()          │  │
│  │     - Check existing entities                    │  │
│  │     - Analyze context (neighboring nodes)        │  │
│  │     - Generate unique URI                        │  │
│  └──────────────────────────────────────────────────┘  │
│                        ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  2. type_compatibility_check()                    │  │
│  │     - Load forbidden merges from ontology         │  │
│  │     - Check type hierarchies                     │  │
│  │     - Raise TypeCompatibilityError if blocked    │  │
│  └──────────────────────────────────────────────────┘  │
│                        ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  3. Create Node in Graph Storage                  │  │
│  │     - Use resolved URI                           │  │
│  │     - Store entity type                          │  │
│  │     - Log to audit trail                          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. TypeChecker (`type_checker.py`)

Checks if two entity types are compatible for merging.

**Key Functions:**
- `type_compatibility_check()`: Main function to call during node creation
- `check_compatibility()`: Returns compatibility status and reason

**Features:**
- Loads forbidden merges from `business_ontology.json`
- Supports type aliases (e.g., "Individual" → "Person")
- Supports type hierarchies (e.g., "Company" is subtype of "Organization")

**Example:**
```python
from src.disambiguation import type_compatibility_check

# This will raise TypeCompatibilityError
type_compatibility_check("Jaguar", "Animal", "Company")
```

### 2. DisambiguationService (`jaguar_resolver.py`)

Main service for entity disambiguation.

**Key Methods:**
- `disambiguate()`: Disambiguate an entity during ingestion
- `get_entity_uri()`: Retrieve URI for an entity
- `list_conflicts()`: List all entity name conflicts

**Features:**
- Type compatibility checking
- Context-based disambiguation using neighboring nodes
- Unique URI generation
- Audit logging to JSONL file

**Example:**
```python
from src.disambiguation import DisambiguationService

service = DisambiguationService()

# Disambiguate Jaguar (Animal)
result1 = service.disambiguate("Jaguar", "Animal")
# Returns: entity://animal/jaguar

# Disambiguate Jaguar (Company) - gets unique URI
result2 = service.disambiguate("Jaguar", "Company")
# Returns: entity://company/jaguar_1 (unique URI)
```

### 3. Graph Storage Interface (`graph_storage_interface.py`)

Abstract interface for graph storage operations.

**Classes:**
- `GraphStorageInterface`: Abstract base class
- `MockGraphStorage`: Mock implementation for testing

**Methods:**
- `get_neighbors()`: Get neighboring nodes for context
- `create_node()`: Create a node in the graph

## Integration with US-015 (Graph Storage)

To integrate with existing graph storage:

```python
from src.disambiguation import (
    DisambiguationService,
    type_compatibility_check,
    GraphStorageInterface
)

# Initialize services
disambiguation_service = DisambiguationService()
graph_storage = YourGraphStorage()  # Implements GraphStorageInterface

# During node creation:
def create_node(name: str, entity_type: str):
    # Step 1: Disambiguate
    result = disambiguation_service.disambiguate(
        entity_name=name,
        entity_type=entity_type,
        graph_storage=graph_storage
    )
    
    # Step 2: Type compatibility check (if node exists)
    existing_node = graph_storage.get_node(result.resolved_uri)
    if existing_node:
        type_compatibility_check(
            entity_name=name,
            existing_type=existing_node.get("type"),
            new_type=entity_type
        )
    
    # Step 3: Create node
    node = graph_storage.create_node(
        entity_name=name,
        entity_type=entity_type,
        uri=result.resolved_uri
    )
    
    return node
```

## Configuration

### business_ontology.json

The ontology file defines:
- **forbidden_merges**: List of type pairs that cannot merge
- **type_aliases**: Maps aliases to canonical types
- **type_hierarchies**: Defines parent-child type relationships

Example:
```json
{
  "forbidden_merges": [
    ["Person", "Organization"],
    ["Animal", "Company"]
  ],
  "type_aliases": {
    "Person": ["Individual", "Human", "User"],
    "Organization": ["Company", "Corporation", "Business"]
  },
  "type_hierarchies": {
    "Entity": ["Person", "Organization", "Location"],
    "Business": ["Company", "Brand", "Product"]
  }
}
```

## Audit Logging

All disambiguation decisions are logged to `disambiguation_audit.jsonl`:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "action": "disambiguate",
  "entity_name": "Jaguar",
  "resolved_uri": "entity://company/jaguar_1",
  "entity_type": "Company",
  "confidence": 0.9,
  "method": "unique_uri",
  "context_nodes": ["entity://animal/jaguar"],
  "conflicting_entities": [
    {
      "uri": "entity://animal/jaguar",
      "type": "Animal",
      "reason": "Types 'Animal' and 'Company' are explicitly forbidden from merging"
    }
  ],
  "decision_reason": "Type conflict detected. Assigned unique URI to prevent merge."
}
```

## Testing

Run the test suite:

```bash
pytest tests/test_jaguar_problem.py -v
```

**Test Coverage:**
- ✅ Type compatibility checking
- ✅ Jaguar problem (cat vs company)
- ✅ Same type merging
- ✅ Context-based disambiguation
- ✅ Unique URI generation
- ✅ Audit logging
- ✅ Integration with graph storage

## Acceptance Criteria

All acceptance criteria are met:

- ✅ **Block merging if ontology types incompatible**: `type_compatibility_check()` raises `TypeCompatibilityError`
- ✅ **Use neighboring nodes as context**: `DisambiguationService` queries graph storage for neighbors
- ✅ **Assign unique URIs to similar-sounding entities**: `_generate_unique_uri()` creates unique URIs
- ✅ **Log all disambiguation decisions**: `_log_disambiguation()` writes to audit log

## Files

- `type_checker.py`: Type compatibility checking
- `jaguar_resolver.py`: Disambiguation service
- `graph_storage_interface.py`: Graph storage interface
- `__init__.py`: Module exports
- `README.md`: This file

## Usage Example

```python
from src.disambiguation import DisambiguationService, type_compatibility_check
from src.disambiguation.graph_storage_interface import MockGraphStorage

# Initialize
service = DisambiguationService()
graph = MockGraphStorage()

# Disambiguate entities
jaguar_animal = service.disambiguate("Jaguar", "Animal", graph_storage=graph)
jaguar_company = service.disambiguate("Jaguar", "Company", graph_storage=graph)

# Verify they have different URIs
assert jaguar_animal.resolved_uri != jaguar_company.resolved_uri

# List conflicts
conflicts = service.list_conflicts()
print(f"Found {len(conflicts)} entity name conflicts")
```

## Future Enhancements

- [ ] Machine learning-based disambiguation
- [ ] Integration with external knowledge bases (Wikidata, DBpedia)
- [ ] Confidence scoring based on entity frequency
- [ ] Automatic type inference from context
- [ ] Support for multilingual entity names


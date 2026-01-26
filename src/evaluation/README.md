# MINE Score Evaluator (JAG-002)

Academic-grade knowledge graph quality metric based on arXiv:2502.09956 (KGGen paper).

## Overview

The MINE (Metric for INformation Evaluation) score evaluates knowledge graph quality using three components:

1. **Information Retention (40%)**: How well the graph preserves information from source documents
2. **Clustering Quality (30%)**: Penalty for unresolved duplicates (Jaguar Problem)
3. **Graph Connectivity (30%)**: Largest Connected Component ratio

**Formula:**
```
MINE Score = (0.4 × Information Retention) + (0.3 × Clustering Quality) + (0.3 × Connectivity)
```

## Grading Scale

| Score Range | Grade | Status |
|------------|-------|--------|
| > 0.75 | A | Production Ready |
| 0.60 - 0.74 | B | Good |
| 0.40 - 0.59 | C | Fragile |
| < 0.40 | F | Very Fragile |

## Usage

### Basic Usage

```python
from src.evaluation import MINEEvaluator
import networkx as nx

# Initialize evaluator
evaluator = MINEEvaluator()

# Prepare data
source_texts = [
    "Jaguar is a big cat that lives in zoos",
    "Jaguar is a car company",
    "Apple is a tech company"
]
reconstructed_texts = [
    "Jaguar is a big cat that lives in zoos",
    "Jaguar is a car company",
    "Apple is a tech company"
]

entity_registry = {
    "Jaguar": [
        {"uri": "entity://animal/jaguar", "type": "Animal"},
        {"uri": "entity://company/jaguar_1", "type": "Company"}
    ],
    "Apple": [
        {"uri": "entity://company/apple", "type": "Company"}
    ]
}

# Build graph
graph = nx.Graph()
graph.add_edge("entity://animal/jaguar", "entity://location/zoo")
graph.add_edge("entity://company/apple", "entity://company/jaguar_1")

# Calculate MINE score
score = evaluator.calculate_mine_score(
    source_texts=source_texts,
    reconstructed_texts=reconstructed_texts,
    entity_registry=entity_registry,
    graph=graph
)

print(f"MINE Score: {score.total_score:.3f} (Grade {score.grade.value})")
print(f"Information Retention: {score.information_retention.value:.3f}")
print(f"Clustering Quality: {score.clustering_quality.value:.3f}")
print(f"Graph Connectivity: {score.graph_connectivity.value:.3f}")
print(f"Jaguar Problems: {len(score.jaguar_problems)}")
```

### Using Entities and Relationships

```python
from src.evaluation import MINEEvaluator

evaluator = MINEEvaluator()

entities = [
    {"uri": "entity://animal/jaguar", "name": "Jaguar", "type": "Animal"},
    {"uri": "entity://company/jaguar_1", "name": "Jaguar", "type": "Company"},
    {"uri": "entity://location/zoo", "name": "Zoo", "type": "Location"}
]

relationships = [
    {"source_uri": "entity://animal/jaguar", "target_uri": "entity://location/zoo", "type": "LIVES_IN"}
]

source_texts = ["Jaguar is a big cat"]
reconstructed_texts = ["Jaguar is a big cat"]

# Calculate score (graph is built automatically)
score = evaluator.calculate_mine_score_from_entities(
    source_texts=source_texts,
    reconstructed_texts=reconstructed_texts,
    entities=entities,
    relationships=relationships
)
```

### Exporting Reports

```python
# Generate human-readable summary
summary = evaluator.generate_report_summary(score)
print(summary)

# Export to JSON
evaluator.export_report(score, "mine_report.json")

# Or export manually
json_str = score.to_json(indent=2)
```

## Components

### 1. Information Retention (40%)

Measures how well the graph preserves information from source documents by comparing embeddings:

- **Input**: Source texts and graph-reconstructed texts
- **Calculation**: Cosine similarity between embeddings
- **Score**: Average similarity (0-1)

### 2. Clustering Quality (30%)

Penalizes unresolved duplicates (Jaguar Problem cases):

- **Input**: Entity registry with conflicts
- **Calculation**: `1.0 - (num_conflicts / total_entities)`
- **Score**: Higher = fewer conflicts (better)

### 3. Graph Connectivity (30%)

Measures graph connectivity using Largest Connected Component:

- **Input**: NetworkX graph
- **Calculation**: `LCC_size / total_nodes`
- **Score**: Higher = more connected (better)

## Integration with JAG-001

The MINE evaluator integrates with JAG-001 (Entity Disambiguation) to identify Jaguar Problems:

```python
from src.disambiguation import DisambiguationService
from src.evaluation import MINEEvaluator

# Use disambiguation service to build entity registry
disambiguation_service = DisambiguationService()
# ... use service to disambiguate entities ...

# Get entity registry from disambiguation service
entity_registry = disambiguation_service.entity_registry

# Evaluate with MINE
evaluator = MINEEvaluator()
score = evaluator.calculate_mine_score(
    source_texts=...,
    reconstructed_texts=...,
    entity_registry=entity_registry,
    graph=graph
)

# Check Jaguar problems
for problem in score.jaguar_problems:
    print(f"Conflict: {problem['entity_name']} has types {problem['conflicting_types']}")
```

## Embeddings

The evaluator uses an embeddings registry for text embeddings. By default, it uses a mock embeddings model. In production, register your own embeddings model:

```python
from src.evaluation import EmbeddingsModelRegistry, MINEEvaluator
from your_embeddings_module import YourEmbeddingsModel

# Register custom embeddings model
registry = EmbeddingsModelRegistry()
registry.register_model("sentence-bert", YourEmbeddingsModel())
registry.set_default("sentence-bert")

# Use in evaluator
evaluator = MINEEvaluator(embeddings_model=registry.get_model("sentence-bert"))
```

## Testing

Run the test suite:

```bash
pytest tests/test_mine_metrics.py -v
```

## Files

- `mine_evaluator.py`: Main evaluator class
- `mine_components.py`: Three component implementations
- `embeddings_registry.py`: Embeddings model registry interface
- `README.md`: This file

## References

- Paper: arXiv:2502.09956 (KGGen paper)
- Formula: `MINE = (0.4 × Retention) + (0.3 × Clustering) + (0.3 × Connectivity)`


# Spectral Graph Robustness Analysis (JAG-004)

Calculate algebraic connectivity (Fiedler Value λ₂) to measure graph fragility and robustness.

## Overview

The Spectral Analyzer uses spectral graph theory to assess graph robustness by calculating:
- **λ₁**: Largest eigenvalue of adjacency matrix (indicates connectivity)
- **λ₂**: Fiedler value - second smallest eigenvalue of Laplacian (measures robustness)
- **Spectral Gap**: λ₁ - λ₂ (larger gap = more robust)

## Key Metrics

### Fiedler Value (λ₂) Interpretation

- **λ₂ > 5**: Highly robust - Graph can withstand removal of multiple nodes
- **λ₂ = 2-5**: Moderately robust - Graph can handle some node removals
- **λ₂ < 2**: **FRAGILE** - Removing key nodes will disconnect the graph

### Alert Threshold

System alerts if **λ₂ < 2.0** (indicates fragile structure).

## Usage

### Basic Analysis

```python
from src.evaluation import SpectralAnalyzer
import networkx as nx

# Create analyzer
analyzer = SpectralAnalyzer()

# Analyze graph
graph = nx.complete_graph(10)
result = analyzer.analyze_graph(graph)

# Check results
print(f"λ₁ (Largest Eigenvalue): {result.lambda_1:.2f}")
print(f"λ₂ (Fiedler Value): {result.lambda_2:.2f}")
print(f"Spectral Gap: {result.spectral_gap:.2f}")
print(f"Robustness: {result.robustness_level.value}")
```

### Analyze from Entities

```python
entities = [
    {"uri": "uri1", "name": "Node1"},
    {"uri": "uri2", "name": "Node2"},
    {"uri": "uri3", "name": "Node3"}
]

relationships = [
    {"source_uri": "uri1", "target_uri": "uri2"},
    {"source_uri": "uri2", "target_uri": "uri3"}
]

result = analyzer.analyze_from_entities(entities, relationships)
```

### Generate Report

```python
# Generate human-readable report
report = analyzer.generate_report(result)
print(report)

# Save to file
analyzer.save_report(result, "robustness_report.txt")

# Save JSON report
analyzer.save_json_report(result, "robustness_report.json")
```

## Example Report Output

```
========================================
SPECTRAL ANALYSIS REPORT
========================================
λ₁ (Largest Eigenvalue): 127.4
λ₂ (Fiedler Value): 6.8
Spectral Gap: 120.6

INTERPRETATION:
✅ Excellent connectivity
✅ Highly robust structure
✅ Safe for production use

Excellent connectivity. Highly robust structure. Graph can 
withstand removal of multiple nodes without disconnecting. 
Safe for production use.

RECOMMENDATIONS:
  - No action needed - graph structure is robust
  - Monitor for any structural changes that might reduce connectivity

GRAPH STATISTICS:
  Nodes: 100
  Edges: 4950
  Density: 1.0000
========================================
```

## Integration with Neo4j

To integrate with Neo4j, build adjacency matrix from query results:

```python
# Query Neo4j for nodes and relationships
# (pseudo-code)
nodes = neo4j_query("MATCH (n) RETURN id(n) as uri, labels(n) as type")
edges = neo4j_query("MATCH (a)-[r]->(b) RETURN id(a) as source_uri, id(b) as target_uri")

# Convert to format
entities = [{"uri": str(n["uri"]), "type": n["type"]} for n in nodes]
relationships = [
    {"source_uri": str(e["source_uri"]), "target_uri": str(e["target_uri"])}
    for e in edges
]

# Analyze
result = analyzer.analyze_from_entities(entities, relationships)
```

## Mathematical Background

### Algebraic Connectivity (Fiedler Value)

The Fiedler value (λ₂) is the second smallest eigenvalue of the graph's Laplacian matrix.

- **Larger λ₂**: More edges needed to disconnect the graph
- **Smaller λ₂**: Fewer edges needed to disconnect (more fragile)

### Laplacian Matrix

L = D - A, where:
- **D**: Degree matrix (diagonal with node degrees)
- **A**: Adjacency matrix

### Spectral Gap

Gap = λ₁ - λ₂

- **Large gap**: Graph has clear community structure
- **Small gap**: Graph is more uniform/regular

## Requirements

- `networkx`: Graph data structures
- `numpy`: Numerical computations
- `scipy`: Sparse matrix operations and eigenvalue calculations

Install with:
```bash
pip install networkx numpy scipy
```

## Files

- `spectral_analyzer.py`: Main analyzer class
- `graph_matrix_builder.py`: Matrix building utilities
- `README_SPECTRAL.md`: This file


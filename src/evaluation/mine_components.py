"""
MINE Score Components (JAG-002)

Three components of the MINE score:
1. Information Retention (40%): Compare source text vs graph-reconstructed text
2. Clustering Quality (30%): Penalize unresolved duplicates (Jaguar Problem)
3. Graph Connectivity (30%): Largest Connected Component ratio
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Optional imports with helpful error messages
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None  # type: ignore

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

from .embeddings_registry import get_embeddings_registry, EmbeddingsModel


@dataclass
class ComponentScore:
    """Score for a single MINE component"""
    value: float  # Score between 0 and 1
    weight: float  # Component weight
    weighted_score: float  # value * weight
    details: Dict[str, Any]  # Additional details about the score


class InformationRetentionComponent:
    """
    Information Retention Component (40% weight)
    
    Compares source text embeddings vs graph-reconstructed text embeddings.
    Measures how well the graph preserves information from source documents.
    """
    
    def __init__(self, embeddings_model: Optional[EmbeddingsModel] = None):
        """
        Initialize information retention component.
        
        Args:
            embeddings_model: Embeddings model to use (default: from registry)
        """
        registry = get_embeddings_registry()
        self.embeddings_model = embeddings_model or registry.get_model()
    
    def calculate(
        self,
        source_texts: List[str],
        reconstructed_texts: List[str]
    ) -> ComponentScore:
        """
        Calculate information retention score.
        
        Args:
            source_texts: List of original source texts
            reconstructed_texts: List of texts reconstructed from graph
            
        Returns:
            ComponentScore with retention score (0-1)
        """
        if not HAS_NUMPY:
            raise ImportError(
                "numpy is required for InformationRetentionComponent. "
                "Install with: pip install numpy"
            )
        
        if len(source_texts) != len(reconstructed_texts):
            raise ValueError(
                f"Source texts ({len(source_texts)}) and reconstructed texts "
                f"({len(reconstructed_texts)}) must have same length"
            )
        
        if len(source_texts) == 0:
            return ComponentScore(
                value=0.0,
                weight=0.4,
                weighted_score=0.0,
                details={"error": "No texts provided"}
            )
        
        # Calculate embeddings
        source_embeddings = [
            self.embeddings_model.embed(text) for text in source_texts
        ]
        reconstructed_embeddings = [
            self.embeddings_model.embed(text) for text in reconstructed_texts
        ]
        
        # Calculate similarities
        similarities = []
        for src_emb, rec_emb in zip(source_embeddings, reconstructed_embeddings):
            sim = self.embeddings_model.similarity(src_emb, rec_emb)
            similarities.append(sim)
        
        # Average similarity is the retention score
        retention_score = np.mean(similarities)  # type: ignore
        
        return ComponentScore(
            value=retention_score,
            weight=0.4,
            weighted_score=retention_score * 0.4,
            details={
                "num_texts": len(source_texts),
                "avg_similarity": retention_score,
                "min_similarity": np.min(similarities),
                "max_similarity": np.max(similarities),
                "similarities": similarities
            }
        )


class ClusteringQualityComponent:
    """
    Clustering Quality Component (30% weight)
    
    Penalizes unresolved duplicates (Jaguar Problem cases).
    Detects entities with same name but conflicting properties/types.
    """
    
    def __init__(self):
        """Initialize clustering quality component"""
        pass
    
    def calculate(
        self,
        entity_conflicts: List[Dict[str, Any]],
        total_entities: int
    ) -> ComponentScore:
        """
        Calculate clustering quality score.
        
        Args:
            entity_conflicts: List of conflict dictionaries with:
                - entity_name: Name of conflicting entity
                - conflicting_types: List of conflicting types
                - conflicting_uris: List of URIs for conflicts
            total_entities: Total number of entities in graph
            
        Returns:
            ComponentScore with clustering quality score (0-1)
            Higher score = fewer conflicts (better clustering)
        """
        if total_entities == 0:
            return ComponentScore(
                value=1.0,  # Perfect if no entities (no conflicts possible)
                weight=0.3,
                weighted_score=0.3,
                details={"num_conflicts": 0, "total_entities": 0}
            )
        
        # Count unique conflicting entities
        num_conflicts = len(entity_conflicts)
        
        # Penalty: more conflicts = lower score
        # Score = 1.0 - (conflicts / total_entities)
        # But cap at reasonable penalty (don't go below 0)
        conflict_ratio = min(num_conflicts / total_entities, 1.0)
        clustering_score = max(0.0, 1.0 - conflict_ratio)
        
        return ComponentScore(
            value=clustering_score,
            weight=0.3,
            weighted_score=clustering_score * 0.3,
            details={
                "num_conflicts": num_conflicts,
                "total_entities": total_entities,
                "conflict_ratio": conflict_ratio,
                "conflicts": entity_conflicts
            }
        )
    
    def identify_jaguar_problems(
        self,
        entity_registry: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Identify Jaguar Problem cases (entities with conflicting properties).
        
        Args:
            entity_registry: Dictionary mapping entity_name -> List of entity info
                Each entity info should have: uri, type, and optional properties
            
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        for entity_name, entities in entity_registry.items():
            if len(entities) <= 1:
                continue  # No conflict if only one entity
            
            # Check for type conflicts
            types = [e.get("type") for e in entities if e.get("type")]
            unique_types = set(types)
            
            if len(unique_types) > 1:
                # Type conflict detected (Jaguar Problem)
                conflicts.append({
                    "entity_name": entity_name,
                    "conflicting_types": list(unique_types),
                    "conflicting_uris": [e.get("uri") for e in entities],
                    "num_entities": len(entities),
                    "conflict_type": "type_conflict"
                })
        
        return conflicts


class GraphConnectivityComponent:
    """
    Graph Connectivity Component (30% weight)
    
    Calculates Largest Connected Component (LCC) ratio.
    Measures how well-connected the graph is.
    """
    
    def __init__(self):
        """Initialize graph connectivity component"""
        pass
    
    def calculate(self, graph: Any) -> ComponentScore:
        """
        Calculate graph connectivity score.
        
        Args:
            graph: NetworkX graph object
            
        Returns:
            ComponentScore with connectivity score (0-1)
            Score = (size of largest connected component) / (total nodes)
        """
        if graph.number_of_nodes() == 0:
            return ComponentScore(
                value=0.0,
                weight=0.3,
                weighted_score=0.0,
                details={"error": "Empty graph"}
            )
        
        # Find largest connected component
        if graph.is_directed():
            # For directed graphs, use weakly connected components
            connected_components = list(nx.weakly_connected_components(graph))
        else:
            # For undirected graphs, use connected components
            connected_components = list(nx.connected_components(graph))
        
        if not connected_components:
            return ComponentScore(
                value=0.0,
                weight=0.3,
                weighted_score=0.0,
                details={"error": "No connected components"}
            )
        
        # Size of largest connected component
        largest_component_size = max(len(cc) for cc in connected_components)
        total_nodes = graph.number_of_nodes()
        
        # Connectivity score = LCC size / total nodes
        connectivity_score = largest_component_size / total_nodes
        
        return ComponentScore(
            value=connectivity_score,
            weight=0.3,
            weighted_score=connectivity_score * 0.3,
            details={
                "largest_component_size": largest_component_size,
                "total_nodes": total_nodes,
                "num_components": len(connected_components),
                "connectivity_ratio": connectivity_score
            }
        )
    
    def build_graph_from_entities(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Any:
        """
        Build NetworkX graph from entities and relationships.
        
        Args:
            entities: List of entity dictionaries with:
                - uri: Entity URI (used as node ID)
                - name: Entity name
                - type: Entity type
                - properties: Optional properties dict
            relationships: List of relationship dictionaries with:
                - source_uri: Source entity URI
                - target_uri: Target entity URI
                - type: Relationship type
                - properties: Optional properties dict
        
        Returns:
            NetworkX Graph object
        """
        if not HAS_NETWORKX:
            raise ImportError(
                "networkx is required for GraphConnectivityComponent. "
                "Install with: pip install networkx"
            )
        
        graph = nx.Graph()  # Use undirected graph by default
        
        # Add nodes
        for entity in entities:
            uri = entity.get("uri")
            if uri:
                graph.add_node(uri, **{k: v for k, v in entity.items() if k != "uri"})
        
        # Add edges
        for rel in relationships:
            source = rel.get("source_uri")
            target = rel.get("target_uri")
            if source and target and source in graph and target in graph:
                graph.add_edge(
                    source,
                    target,
                    **{k: v for k, v in rel.items() if k not in ("source_uri", "target_uri")}
                )
        
        return graph


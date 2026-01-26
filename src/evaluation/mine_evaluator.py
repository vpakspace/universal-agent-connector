"""
MINE Score Evaluator (JAG-002)

Academic-grade knowledge graph quality metric based on arXiv:2502.09956 (KGGen paper).

MINE Score = (0.4 × Information Retention) + (0.3 × Clustering Quality) + (0.3 × Connectivity)

Grading Scale:
- >0.75: Production Ready (Grade A)
- 0.60-0.74: Good (Grade B)
- <0.60: Fragile (Grade C/F)
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Optional import for networkx
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None  # type: ignore

from .mine_components import (
    InformationRetentionComponent,
    ClusteringQualityComponent,
    GraphConnectivityComponent,
    ComponentScore
)


class MINEGrade(str, Enum):
    """MINE Score Grades"""
    A = "A"  # Production Ready (>0.75)
    B = "B"  # Good (0.60-0.74)
    C = "C"  # Fragile (<0.60)
    F = "F"  # Very Fragile (<0.40)


@dataclass
class MINEScore:
    """MINE Score result"""
    total_score: float  # Overall MINE score (0-1)
    grade: MINEGrade  # Grade (A, B, C, F)
    information_retention: ComponentScore
    clustering_quality: ComponentScore
    graph_connectivity: ComponentScore
    jaguar_problems: List[Dict[str, Any]]  # Identified conflicts
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export"""
        result = asdict(self)
        result["grade"] = self.grade.value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class MINEEvaluator:
    """
    MINE Score Evaluator for knowledge graph quality assessment.
    
    Evaluates knowledge graphs using three components:
    1. Information Retention (40%): How well graph preserves source information
    2. Clustering Quality (30%): Penalty for unresolved duplicates (Jaguar Problem)
    3. Graph Connectivity (30%): Largest Connected Component ratio
    """
    
    def __init__(
        self,
        embeddings_model: Optional[Any] = None
    ):
        """
        Initialize MINE evaluator.
        
        Args:
            embeddings_model: Optional embeddings model (default: from registry)
        """
        self.retention_component = InformationRetentionComponent(embeddings_model)
        self.clustering_component = ClusteringQualityComponent()
        self.connectivity_component = GraphConnectivityComponent()
    
    def calculate_mine_score(
        self,
        source_texts: List[str],
        reconstructed_texts: List[str],
        entity_registry: Dict[str, List[Dict[str, Any]]],
        graph: Any,
        timestamp: Optional[str] = None
    ) -> MINEScore:
        """
        Calculate MINE score for knowledge graph.
        
        Args:
            source_texts: List of original source texts
            reconstructed_texts: List of texts reconstructed from graph
            entity_registry: Dictionary mapping entity_name -> List of entity info
                Used to identify Jaguar Problem cases
            graph: NetworkX graph object representing the knowledge graph
            timestamp: Optional timestamp (default: current time)
            
        Returns:
            MINEScore object with total score, grade, and component breakdown
        """
        from datetime import datetime
        
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        # 1. Calculate Information Retention (40%)
        retention_score = self.retention_component.calculate(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts
        )
        
        # 2. Calculate Clustering Quality (30%)
        # Identify Jaguar Problem cases
        jaguar_problems = self.clustering_component.identify_jaguar_problems(
            entity_registry=entity_registry
        )
        
        # Count total entities
        total_entities = sum(len(entities) for entities in entity_registry.values())
        
        clustering_score = self.clustering_component.calculate(
            entity_conflicts=jaguar_problems,
            total_entities=total_entities
        )
        
        # 3. Calculate Graph Connectivity (30%)
        connectivity_score = self.connectivity_component.calculate(graph=graph)
        
        # Calculate total MINE score
        total_score = (
            retention_score.weighted_score +
            clustering_score.weighted_score +
            connectivity_score.weighted_score
        )
        
        # Determine grade
        grade = self._determine_grade(total_score)
        
        return MINEScore(
            total_score=total_score,
            grade=grade,
            information_retention=retention_score,
            clustering_quality=clustering_score,
            graph_connectivity=connectivity_score,
            jaguar_problems=jaguar_problems,
            timestamp=timestamp
        )
    
    def calculate_mine_score_from_entities(
        self,
        source_texts: List[str],
        reconstructed_texts: List[str],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        entity_registry: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        timestamp: Optional[str] = None
    ) -> MINEScore:
        """
        Calculate MINE score from entities and relationships (builds graph automatically).
        
        Args:
            source_texts: List of original source texts
            reconstructed_texts: List of texts reconstructed from graph
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
            entity_registry: Optional entity registry (auto-built if not provided)
            timestamp: Optional timestamp
            
        Returns:
            MINEScore object
        """
        # Build graph from entities and relationships
        graph = self.connectivity_component.build_graph_from_entities(
            entities=entities,
            relationships=relationships
        )
        
        # Build entity registry if not provided
        if entity_registry is None:
            entity_registry = self._build_entity_registry(entities)
        
        return self.calculate_mine_score(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entity_registry=entity_registry,
            graph=graph,
            timestamp=timestamp
        )
    
    def _build_entity_registry(
        self,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build entity registry from entities list.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Dictionary mapping entity_name -> List of entity info
        """
        registry = {}
        
        for entity in entities:
            name = entity.get("name")
            if name:
                if name not in registry:
                    registry[name] = []
                registry[name].append(entity)
        
        return registry
    
    def _determine_grade(self, score: float) -> MINEGrade:
        """
        Determine grade from MINE score.
        
        Args:
            score: MINE score (0-1)
            
        Returns:
            MINEGrade (A, B, C, or F)
        """
        if score > 0.75:
            return MINEGrade.A  # Production Ready
        elif score >= 0.60:
            return MINEGrade.B  # Good
        elif score >= 0.40:
            return MINEGrade.C  # Fragile
        else:
            return MINEGrade.F  # Very Fragile
    
    def export_report(
        self,
        score: MINEScore,
        output_path: str
    ) -> None:
        """
        Export MINE score report to JSON file.
        
        Args:
            score: MINEScore object
            output_path: Path to output JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(score.to_json(indent=2))
    
    def generate_report_summary(self, score: MINEScore) -> str:
        """
        Generate human-readable report summary.
        
        Args:
            score: MINEScore object
            
        Returns:
            Formatted string summary
        """
        lines = [
            "=" * 60,
            "MINE Score Evaluation Report",
            "=" * 60,
            f"Overall Score: {score.total_score:.3f} (Grade {score.grade.value})",
            f"Timestamp: {score.timestamp}",
            "",
            "Component Scores:",
            f"  Information Retention: {score.information_retention.value:.3f} "
            f"(weight: {score.information_retention.weight}, "
            f"weighted: {score.information_retention.weighted_score:.3f})",
            f"  Clustering Quality: {score.clustering_quality.value:.3f} "
            f"(weight: {score.clustering_quality.weight}, "
            f"weighted: {score.clustering_quality.weighted_score:.3f})",
            f"  Graph Connectivity: {score.graph_connectivity.value:.3f} "
            f"(weight: {score.graph_connectivity.weight}, "
            f"weighted: {score.graph_connectivity.weighted_score:.3f})",
            "",
            f"Jaguar Problems Detected: {len(score.jaguar_problems)}",
        ]
        
        if score.jaguar_problems:
            lines.append("")
            lines.append("Conflicts:")
            for problem in score.jaguar_problems:
                lines.append(
                    f"  - {problem['entity_name']}: "
                    f"{problem['conflicting_types']} "
                    f"({problem['num_entities']} entities)"
                )
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


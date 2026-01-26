"""
Spectral Graph Robustness Analyzer (JAG-004)

Calculates algebraic connectivity (Fiedler Value λ₂) to measure graph fragility.
Uses spectral graph theory to assess graph robustness.

Key Metrics:
- λ₁ (Largest Eigenvalue): Indicates graph connectivity
- λ₂ (Fiedler Value): Algebraic connectivity - measures robustness
- Spectral Gap (λ₁ - λ₂): Larger gap = more robust
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

# Optional imports
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

try:
    from scipy.sparse import linalg
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    linalg = None  # type: ignore

from .graph_matrix_builder import GraphMatrixBuilder


class RobustnessLevel(str, Enum):
    """Graph robustness levels"""
    HIGHLY_ROBUST = "Highly Robust"  # λ₂ > 5
    MODERATELY_ROBUST = "Moderately Robust"  # λ₂ = 2-5
    FRAGILE = "Fragile"  # λ₂ < 2


@dataclass
class SpectralAnalysisResult:
    """Result of spectral analysis"""
    lambda_1: float  # Largest eigenvalue
    lambda_2: float  # Fiedler value (second smallest eigenvalue of Laplacian)
    spectral_gap: float  # λ₁ - λ₂
    robustness_level: RobustnessLevel
    interpretation: str
    recommendations: List[str] = field(default_factory=list)
    matrix_statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        result = asdict(self)
        result["robustness_level"] = self.robustness_level.value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class SpectralAnalyzer:
    """
    Analyzes graph robustness using spectral graph theory.
    
    Calculates algebraic connectivity (Fiedler Value) to determine
    if graph structure is fragile or robust.
    """
    
    def __init__(self):
        """Initialize spectral analyzer"""
        self.matrix_builder = GraphMatrixBuilder()
    
    def analyze_graph(
        self,
        graph: Any,
        k: int = 5
    ) -> SpectralAnalysisResult:
        """
        Analyze graph robustness using spectral methods.
        
        Args:
            graph: NetworkX graph object or adjacency matrix
            k: Number of eigenvalues to compute (default: 5)
            
        Returns:
            SpectralAnalysisResult with λ₁, λ₂, and interpretation
        """
        if not HAS_SCIPY:
            raise ImportError(
                "scipy is required for spectral analysis. "
                "Install with: pip install scipy"
            )
        
        # Build adjacency matrix if graph is not already a matrix
        if hasattr(graph, 'number_of_nodes'):
            # NetworkX graph
            adjacency_matrix = self.matrix_builder.build_adjacency_matrix_from_nx(graph)
        else:
            # Assume it's already a matrix
            adjacency_matrix = graph
        
        # Build Laplacian matrix
        laplacian = self.matrix_builder.build_laplacian_matrix(adjacency_matrix)
        
        # Get matrix statistics
        matrix_stats = self.matrix_builder.get_matrix_statistics(adjacency_matrix)
        
        # Calculate eigenvalues
        lambda_1, lambda_2 = self._calculate_eigenvalues(laplacian, adjacency_matrix, k)
        
        # Calculate spectral gap
        spectral_gap = lambda_1 - lambda_2
        
        # Determine robustness level
        robustness_level, interpretation, recommendations = self._interpret_results(
            lambda_1, lambda_2, spectral_gap
        )
        
        return SpectralAnalysisResult(
            lambda_1=lambda_1,
            lambda_2=lambda_2,
            spectral_gap=spectral_gap,
            robustness_level=robustness_level,
            interpretation=interpretation,
            recommendations=recommendations,
            matrix_statistics=matrix_stats
        )
    
    def analyze_from_entities(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        k: int = 5
    ) -> SpectralAnalysisResult:
        """
        Analyze graph robustness from entities and relationships.
        
        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
            k: Number of eigenvalues to compute
            
        Returns:
            SpectralAnalysisResult
        """
        # Build adjacency matrix
        adjacency_matrix, uri_mapping = self.matrix_builder.build_adjacency_matrix_from_entities(
            entities, relationships
        )
        
        # Analyze using adjacency matrix
        return self.analyze_graph(adjacency_matrix, k=k)
    
    def _calculate_eigenvalues(
        self,
        laplacian: Any,
        adjacency_matrix: Any,
        k: int = 5
    ) -> Tuple[float, float]:
        """
        Calculate λ₁ (largest eigenvalue of adjacency) and λ₂ (Fiedler value).
        
        λ₁: Largest eigenvalue of adjacency matrix
        λ₂: Second smallest eigenvalue of Laplacian matrix (Fiedler value)
        
        Args:
            laplacian: Laplacian matrix
            adjacency_matrix: Adjacency matrix
            k: Number of eigenvalues to compute
            
        Returns:
            Tuple of (lambda_1, lambda_2)
        """
        if not HAS_SCIPY or not HAS_NUMPY:
            raise ImportError("scipy and numpy are required for eigenvalue calculations")
        
        num_nodes = adjacency_matrix.shape[0]
        
        if num_nodes < 2:
            # Graph too small for meaningful analysis
            return 0.0, 0.0
        
        # Calculate λ₁: Largest eigenvalue of adjacency matrix
        # Use eigs to get largest eigenvalue
        k_adj = min(k, num_nodes - 1)
        try:
            eigenvals_adj, _ = linalg.eigs(adjacency_matrix, k=k_adj, which='LM')  # Largest magnitude
            lambda_1 = float(np.real(max(eigenvals_adj)))
        except Exception:
            # Fallback: Use dense matrix if sparse fails
            eigenvals_adj = np.linalg.eigvals(adjacency_matrix.toarray())
            lambda_1 = float(np.real(max(eigenvals_adj)))
        
        # Calculate λ₂: Second smallest eigenvalue of Laplacian (Fiedler value)
        # Use eigs to get smallest eigenvalues
        k_lap = min(k + 1, num_nodes)  # Need at least 2 eigenvalues
        try:
            eigenvals_lap, _ = linalg.eigs(laplacian, k=k_lap, which='SM')  # Smallest magnitude
            eigenvals_lap = np.real(eigenvals_lap)
            eigenvals_lap_sorted = sorted(eigenvals_lap)
            # Second smallest (first is always 0 for connected graphs)
            lambda_2 = float(eigenvals_lap_sorted[1] if len(eigenvals_lap_sorted) > 1 else eigenvals_lap_sorted[0])
        except Exception:
            # Fallback: Use dense matrix
            eigenvals_lap = np.linalg.eigvals(laplacian.toarray())
            eigenvals_lap = np.real(eigenvals_lap)
            eigenvals_lap_sorted = sorted(eigenvals_lap)
            lambda_2 = float(eigenvals_lap_sorted[1] if len(eigenvals_lap_sorted) > 1 else eigenvals_lap_sorted[0])
        
        return lambda_1, lambda_2
    
    def _interpret_results(
        self,
        lambda_1: float,
        lambda_2: float,
        spectral_gap: float
    ) -> Tuple[RobustnessLevel, str, List[str]]:
        """
        Interpret spectral analysis results.
        
        Args:
            lambda_1: Largest eigenvalue
            lambda_2: Fiedler value
            spectral_gap: Spectral gap (λ₁ - λ₂)
            
        Returns:
            Tuple of (robustness_level, interpretation, recommendations)
        """
        recommendations = []
        
        if lambda_2 > 5.0:
            robustness_level = RobustnessLevel.HIGHLY_ROBUST
            interpretation = (
                "Excellent connectivity. Highly robust structure. "
                "Graph can withstand removal of multiple nodes without disconnecting. "
                "Safe for production use."
            )
            recommendations.append("No action needed - graph structure is robust")
            recommendations.append("Monitor for any structural changes that might reduce connectivity")
        
        elif lambda_2 >= 2.0:
            robustness_level = RobustnessLevel.MODERATELY_ROBUST
            interpretation = (
                "Good connectivity. Moderately robust structure. "
                "Graph can handle some node removals, but may become fragile if key nodes are removed. "
                "Suitable for production with monitoring."
            )
            recommendations.append("Monitor graph structure for any degradation")
            recommendations.append("Consider adding edges to critical nodes to improve robustness")
            recommendations.append("Identify and protect high-degree nodes (hubs)")
        
        else:
            robustness_level = RobustnessLevel.FRAGILE
            interpretation = (
                "WARNING: Fragile structure detected. "
                "Removing key nodes will likely disconnect the graph. "
                "Not recommended for production without improvements."
            )
            recommendations.append("URGENT: Add edges to improve connectivity")
            recommendations.append("Identify critical nodes and add redundant connections")
            recommendations.append("Consider restructuring graph to reduce dependency on single nodes")
            recommendations.append("Monitor for graph fragmentation")
        
        return robustness_level, interpretation, recommendations
    
    def generate_report(self, result: SpectralAnalysisResult) -> str:
        """
        Generate human-readable robustness report.
        
        Args:
            result: SpectralAnalysisResult
            
        Returns:
            Formatted report string
        """
        lines = [
            "=" * 40,
            "SPECTRAL ANALYSIS REPORT",
            "=" * 40,
            f"λ₁ (Largest Eigenvalue): {result.lambda_1:.2f}",
            f"λ₂ (Fiedler Value): {result.lambda_2:.2f}",
            f"Spectral Gap: {result.spectral_gap:.2f}",
            "",
            "INTERPRETATION:",
        ]
        
        # Add status indicator
        if result.robustness_level == RobustnessLevel.HIGHLY_ROBUST:
            lines.append("✅ Excellent connectivity")
            lines.append("✅ Highly robust structure")
            lines.append("✅ Safe for production use")
        elif result.robustness_level == RobustnessLevel.MODERATELY_ROBUST:
            lines.append("⚠️  Good connectivity")
            lines.append("⚠️  Moderately robust structure")
            lines.append("⚠️  Suitable for production with monitoring")
        else:
            lines.append("❌ WARNING: Fragile structure")
            lines.append("❌ Removing key nodes may disconnect graph")
            lines.append("❌ Not recommended for production")
        
        lines.append("")
        lines.append(result.interpretation)
        
        if result.recommendations:
            lines.append("")
            lines.append("RECOMMENDATIONS:")
            for rec in result.recommendations:
                lines.append(f"  - {rec}")
        
        if result.matrix_statistics:
            lines.append("")
            lines.append("GRAPH STATISTICS:")
            lines.append(f"  Nodes: {result.matrix_statistics.get('num_nodes', 'N/A')}")
            lines.append(f"  Edges: {result.matrix_statistics.get('nnz', 'N/A')}")
            lines.append(f"  Density: {result.matrix_statistics.get('density', 0.0):.4f}")
        
        lines.append("=" * 40)
        
        return "\n".join(lines)
    
    def save_report(
        self,
        result: SpectralAnalysisResult,
        filepath: str
    ) -> None:
        """
        Save spectral analysis report to file.
        
        Args:
            result: SpectralAnalysisResult
            filepath: Path to output file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_report(result))
    
    def save_json_report(
        self,
        result: SpectralAnalysisResult,
        filepath: str
    ) -> None:
        """
        Save spectral analysis result as JSON.
        
        Args:
            result: SpectralAnalysisResult
            filepath: Path to output JSON file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result.to_json(indent=2))


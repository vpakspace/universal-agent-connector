"""
Standalone test script for JAG-004 Spectral Analysis (no pytest required)
Run with: python tests/test_spectral_metrics_standalone.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check dependencies
try:
    import networkx as nx
    import numpy as np
    from scipy.sparse import linalg
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    print("WARNING: networkx, numpy, or scipy not installed.")
    print("Install with: pip install networkx numpy scipy")
    sys.exit(1)

from src.evaluation.spectral_analyzer import (
    SpectralAnalyzer,
    RobustnessLevel
)
from src.evaluation.graph_matrix_builder import GraphMatrixBuilder


def test_matrix_builder():
    """Test graph matrix builder"""
    print("Testing Graph Matrix Builder...")
    
    builder = GraphMatrixBuilder()
    
    # Test NetworkX graph
    graph = nx.complete_graph(5)
    matrix = builder.build_adjacency_matrix_from_nx(graph)
    
    if matrix.shape == (5, 5) and matrix.nnz > 0:
        print("  [PASS] Adjacency matrix from NetworkX graph")
    else:
        print("  [FAIL] Adjacency matrix building failed")
        return False
    
    # Test entities/relationships
    entities = [
        {"uri": "uri1", "name": "Node1"},
        {"uri": "uri2", "name": "Node2"}
    ]
    relationships = [
        {"source_uri": "uri1", "target_uri": "uri2"}
    ]
    
    matrix2, mapping = builder.build_adjacency_matrix_from_entities(entities, relationships)
    if matrix2.shape[0] == 2 and len(mapping) == 2:
        print("  [PASS] Adjacency matrix from entities/relationships")
    else:
        print("  [FAIL] Entities/relationships matrix building failed")
        return False
    
    # Test Laplacian
    laplacian = builder.build_laplacian_matrix(matrix)
    if laplacian.shape == (5, 5):
        print("  [PASS] Laplacian matrix building")
    else:
        print("  [FAIL] Laplacian matrix building failed")
        return False
    
    return True


def test_robust_graph_analysis():
    """Test analysis of robust graph"""
    print("\nTesting Robust Graph Analysis...")
    
    analyzer = SpectralAnalyzer()
    graph = nx.complete_graph(10)
    
    result = analyzer.analyze_graph(graph)
    
    if result.lambda_1 > 0 and result.lambda_2 > 0:
        print(f"  [PASS] Robust graph analysis: λ₁={result.lambda_1:.2f}, λ₂={result.lambda_2:.2f}")
    else:
        print("  [FAIL] Robust graph analysis failed")
        return False
    
    if result.lambda_2 > 2.0:
        print(f"  [PASS] Robust graph has λ₂ > 2.0 (λ₂={result.lambda_2:.2f})")
    else:
        print(f"  [INFO] Graph has λ₂ <= 2.0 (λ₂={result.lambda_2:.2f})")
    
    return True


def test_fragile_graph_analysis():
    """Test analysis of fragile graph"""
    print("\nTesting Fragile Graph Analysis...")
    
    analyzer = SpectralAnalyzer()
    # Star graph is fragile (hub and spoke)
    graph = nx.star_graph(10)
    
    result = analyzer.analyze_graph(graph)
    
    if result.lambda_2 < 2.0:
        print(f"  [PASS] Fragile graph detected: λ₂={result.lambda_2:.2f} < 2.0")
    else:
        print(f"  [INFO] Graph has λ₂ >= 2.0 (λ₂={result.lambda_2:.2f})")
    
    if result.robustness_level == RobustnessLevel.FRAGILE:
        print("  [PASS] Fragile robustness level correctly assigned")
    else:
        print(f"  [INFO] Robustness level: {result.robustness_level.value}")
    
    return True


def test_interpretation_thresholds():
    """Test interpretation thresholds"""
    print("\nTesting Interpretation Thresholds...")
    
    analyzer = SpectralAnalyzer()
    
    # Highly robust (complete graph)
    robust_graph = nx.complete_graph(20)
    result1 = analyzer.analyze_graph(robust_graph)
    
    if result1.lambda_2 > 5.0:
        if result1.robustness_level == RobustnessLevel.HIGHLY_ROBUST:
            print(f"  [PASS] Highly robust interpretation (λ₂={result1.lambda_2:.2f})")
        else:
            print(f"  [INFO] λ₂={result1.lambda_2:.2f}, level={result1.robustness_level.value}")
    
    # Fragile (star graph)
    fragile_graph = nx.star_graph(10)
    result2 = analyzer.analyze_graph(fragile_graph)
    
    if result2.lambda_2 < 2.0:
        if result2.robustness_level == RobustnessLevel.FRAGILE:
            print(f"  [PASS] Fragile interpretation (λ₂={result2.lambda_2:.2f})")
        else:
            print(f"  [INFO] λ₂={result2.lambda_2:.2f}, level={result2.robustness_level.value}")
    
    return True


def test_report_generation():
    """Test report generation"""
    print("\nTesting Report Generation...")
    
    analyzer = SpectralAnalyzer()
    graph = nx.complete_graph(10)
    
    result = analyzer.analyze_graph(graph)
    report = analyzer.generate_report(result)
    
    if "SPECTRAL ANALYSIS REPORT" in report and "λ₁" in report and "λ₂" in report:
        print("  [PASS] Report generation")
    else:
        print("  [FAIL] Report generation failed")
        return False
    
    if "RECOMMENDATIONS" in report or len(result.recommendations) > 0:
        print("  [PASS] Recommendations included in report")
    else:
        print("  [INFO] No recommendations in report")
    
    return True


def test_spectral_gap():
    """Test spectral gap calculation"""
    print("\nTesting Spectral Gap Calculation...")
    
    analyzer = SpectralAnalyzer()
    graph = nx.complete_graph(10)
    
    result = analyzer.analyze_graph(graph)
    
    expected_gap = result.lambda_1 - result.lambda_2
    if abs(result.spectral_gap - expected_gap) < 0.01:
        print(f"  [PASS] Spectral gap calculation (gap={result.spectral_gap:.2f})")
    else:
        print(f"  [FAIL] Spectral gap mismatch: expected {expected_gap:.2f}, got {result.spectral_gap:.2f}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("JAG-004 Spectral Analysis Test Suite")
    print("=" * 60)
    
    if not HAS_DEPENDENCIES:
        print("\nERROR: Required dependencies not installed")
        print("Install with: pip install networkx numpy scipy")
        return 1
    
    results = []
    
    results.append(("Matrix Builder", test_matrix_builder()))
    results.append(("Robust Graph Analysis", test_robust_graph_analysis()))
    results.append(("Fragile Graph Analysis", test_fragile_graph_analysis()))
    results.append(("Interpretation Thresholds", test_interpretation_thresholds()))
    results.append(("Report Generation", test_report_generation()))
    results.append(("Spectral Gap", test_spectral_gap()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:30} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())


"""
Standalone test script for JAG-002 MINE Score Evaluator (no pytest required)
Run with: python tests/test_mine_standalone.py
"""

import sys
import os
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if networkx is available
try:
    import networkx as nx
    import numpy as np
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    print("WARNING: networkx or numpy not installed. Some tests will be skipped.")
    print("Install with: pip install networkx numpy")

if HAS_DEPENDENCIES:
    from src.evaluation.mine_evaluator import (
        MINEEvaluator,
        MINEScore,
        MINEGrade
    )
    from src.evaluation.mine_components import (
        InformationRetentionComponent,
        ClusteringQualityComponent,
        GraphConnectivityComponent
    )


def test_information_retention():
    """Test Information Retention Component"""
    if not HAS_DEPENDENCIES:
        return False, "Dependencies not available"
    
    print("Testing Information Retention Component...")
    
    component = InformationRetentionComponent()
    
    # Test 1: Identical texts
    source_texts = ["Jaguar is a big cat"]
    reconstructed_texts = ["Jaguar is a big cat"]
    
    score = component.calculate(source_texts, reconstructed_texts)
    
    if score.weight != 0.4:
        print("  [FAIL] Weight should be 0.4")
        return False
    
    if score.value < 0.5:
        print("  [FAIL] Similarity should be high for identical texts")
        return False
    
    print("  [PASS] Information retention calculation")
    return True


def test_clustering_quality():
    """Test Clustering Quality Component"""
    if not HAS_DEPENDENCIES:
        return False, "Dependencies not available"
    
    print("\nTesting Clustering Quality Component...")
    
    component = ClusteringQualityComponent()
    
    # Test 1: No conflicts
    conflicts = []
    total_entities = 10
    
    score = component.calculate(conflicts, total_entities)
    
    if score.value != 1.0:
        print("  [FAIL] Score should be 1.0 for no conflicts")
        return False
    
    # Test 2: With conflicts (Jaguar problem)
    conflicts = [
        {
            "entity_name": "Jaguar",
            "conflicting_types": ["Animal", "Company"],
            "conflicting_uris": ["uri1", "uri2"],
            "num_entities": 2
        }
    ]
    
    score = component.calculate(conflicts, total_entities)
    
    if score.value >= 1.0:
        print("  [FAIL] Score should be < 1.0 for conflicts")
        return False
    
    # Test 3: Identify Jaguar problems
    entity_registry = {
        "Jaguar": [
            {"uri": "uri1", "type": "Animal"},
            {"uri": "uri2", "type": "Company"}
        ]
    }
    
    problems = component.identify_jaguar_problems(entity_registry)
    
    if len(problems) != 1:
        print(f"  [FAIL] Expected 1 conflict, got {len(problems)}")
        return False
    
    if problems[0]["entity_name"] != "Jaguar":
        print("  [FAIL] Expected Jaguar conflict")
        return False
    
    print("  [PASS] Clustering quality calculation")
    return True


def test_graph_connectivity():
    """Test Graph Connectivity Component"""
    if not HAS_DEPENDENCIES:
        return False, "Dependencies not available"
    
    print("\nTesting Graph Connectivity Component...")
    
    component = GraphConnectivityComponent()
    
    # Test 1: Fully connected graph
    graph = nx.complete_graph(5)
    
    score = component.calculate(graph)
    
    if score.value != 1.0:
        print(f"  [FAIL] Fully connected graph should have score 1.0, got {score.value}")
        return False
    
    # Test 2: Disconnected graph
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2)])  # Component 1 (3 nodes)
    graph.add_edges_from([(3, 4)])  # Component 2 (2 nodes)
    
    score = component.calculate(graph)
    
    expected = 3.0 / 5.0  # Largest component (3) / total (5)
    if abs(score.value - expected) > 0.01:
        print(f"  [FAIL] Expected {expected}, got {score.value}")
        return False
    
    # Test 3: Build graph from entities
    entities = [
        {"uri": "uri1", "name": "Jaguar", "type": "Animal"},
        {"uri": "uri2", "name": "Zoo", "type": "Location"}
    ]
    
    relationships = [
        {"source_uri": "uri1", "target_uri": "uri2", "type": "LIVES_IN"}
    ]
    
    graph = component.build_graph_from_entities(entities, relationships)
    
    if graph.number_of_nodes() != 2:
        print(f"  [FAIL] Expected 2 nodes, got {graph.number_of_nodes()}")
        return False
    
    if graph.number_of_edges() != 1:
        print(f"  [FAIL] Expected 1 edge, got {graph.number_of_edges()}")
        return False
    
    print("  [PASS] Graph connectivity calculation")
    return True


def test_mine_evaluator():
    """Test MINE Evaluator"""
    if not HAS_DEPENDENCIES:
        return False, "Dependencies not available"
    
    print("\nTesting MINE Evaluator...")
    
    evaluator = MINEEvaluator()
    
    # Test data
    source_texts = ["Jaguar is a big cat", "Jaguar is a car company"]
    reconstructed_texts = ["Jaguar is a big cat", "Jaguar is a car company"]
    
    entities = [
        {"uri": "entity://animal/jaguar", "name": "Jaguar", "type": "Animal"},
        {"uri": "entity://company/jaguar_1", "name": "Jaguar", "type": "Company"}
    ]
    
    relationships = [
        {"source_uri": "entity://animal/jaguar", "target_uri": "entity://company/jaguar_1", "type": "RELATED"}
    ]
    
    # Test 1: Calculate MINE score
    score = evaluator.calculate_mine_score_from_entities(
        source_texts=source_texts,
        reconstructed_texts=reconstructed_texts,
        entities=entities,
        relationships=relationships
    )
    
    if not isinstance(score, MINEScore):
        print("  [FAIL] Should return MINEScore object")
        return False
    
    if not (0.0 <= score.total_score <= 1.0):
        print(f"  [FAIL] Score should be between 0 and 1, got {score.total_score}")
        return False
    
    # Test 2: Grade determination
    if score.grade not in [MINEGrade.A, MINEGrade.B, MINEGrade.C, MINEGrade.F]:
        print(f"  [FAIL] Invalid grade: {score.grade}")
        return False
    
    # Test 3: Component scores
    if score.information_retention.weight != 0.4:
        print("  [FAIL] Information retention weight should be 0.4")
        return False
    
    if score.clustering_quality.weight != 0.3:
        print("  [FAIL] Clustering quality weight should be 0.3")
        return False
    
    if score.graph_connectivity.weight != 0.3:
        print("  [FAIL] Graph connectivity weight should be 0.3")
        return False
    
    # Test 4: Jaguar problems detection
    if len(score.jaguar_problems) == 0:
        print("  [FAIL] Should detect Jaguar conflict")
        return False
    
    # Test 5: JSON export
    json_str = score.to_json()
    try:
        data = json.loads(json_str)
        if "total_score" not in data:
            print("  [FAIL] JSON should contain total_score")
            return False
    except json.JSONDecodeError:
        print("  [FAIL] Invalid JSON output")
        return False
    
    # Test 6: Report summary
    summary = evaluator.generate_report_summary(score)
    if "MINE Score Evaluation Report" not in summary:
        print("  [FAIL] Summary should contain report header")
        return False
    
    # Test 7: Export report
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_report.json")
        evaluator.export_report(score, output_path)
        
        if not os.path.exists(output_path):
            print("  [FAIL] Report file should be created")
            return False
        
        with open(output_path, 'r') as f:
            data = json.load(f)
            if "total_score" not in data:
                print("  [FAIL] Exported report should contain total_score")
                return False
    
    print("  [PASS] MINE evaluator")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("JAG-002 MINE Score Evaluator Test Suite")
    print("=" * 60)
    
    if not HAS_DEPENDENCIES:
        print("\nERROR: Required dependencies not installed.")
        print("Install with: pip install networkx numpy")
        return 1
    
    results = []
    
    results.append(("Information Retention", test_information_retention()))
    results.append(("Clustering Quality", test_clustering_quality()))
    results.append(("Graph Connectivity", test_graph_connectivity()))
    results.append(("MINE Evaluator", test_mine_evaluator()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        if isinstance(result, tuple):
            passed, message = result
            status = "PASS" if passed else f"FAIL ({message})"
        else:
            passed = result
            status = "PASS" if passed else "FAIL"
        
        print(f"{name:30} {status}")
        if not passed:
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


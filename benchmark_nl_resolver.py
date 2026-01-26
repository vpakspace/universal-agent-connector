"""
Accuracy Benchmark for Natural Language Resource Resolver
Tests resolution accuracy on example queries
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
import statistics

from nl_resource_resolver import resolve_query, ResolutionResult


# Test queries with expected concepts (ground truth)
TEST_QUERIES: List[Tuple[str, List[str]]] = [
    # Customer queries
    ("Show me customer data", ["Customer"]),
    ("List all customers", ["Customer"]),
    ("Get customer details for ID 123", ["Customer"]),
    ("What is the customer lifetime value?", ["Customer"]),
    ("Show customer purchase history", ["Customer", "Transaction"]),
    
    # Revenue queries
    ("What was our revenue last quarter?", ["Revenue"]),
    ("Show me total sales last month", ["Revenue"]),
    ("Calculate monthly revenue", ["Revenue"]),
    ("What are the payment trends?", ["Revenue"]),
    ("Generate revenue report", ["Revenue"]),
    
    # Inventory queries
    ("Check stock levels", ["Inventory"]),
    ("What products are low in stock?", ["Inventory"]),
    ("Show warehouse inventory", ["Inventory"]),
    ("Reorder product X", ["Inventory"]),
    ("Calculate inventory value", ["Inventory"]),
    
    # Employee queries
    ("List all employees", ["Employee"]),
    ("Show employees in sales department", ["Employee"]),
    ("What is employee ID 456's salary?", ["Employee"]),
    ("Track attendance for John Doe", ["Employee"]),
    ("Generate payroll report", ["Employee"]),
    
    # Transaction queries
    ("Get all transactions", ["Transaction"]),
    ("Show transactions from last week", ["Transaction"]),
    ("Process payment for order 789", ["Transaction"]),
    ("Issue refund for transaction 101", ["Transaction"]),
    ("Generate daily transaction report", ["Transaction"]),
    
    # Multi-concept queries
    ("Show me customer purchase history for last quarter", ["Customer", "Transaction"]),
    ("Revenue by customer segment", ["Revenue", "Customer"]),
    ("Employee sales performance", ["Employee", "Revenue"]),
    ("Product inventory and sales", ["Inventory", "Revenue"]),
    
    # Edge cases
    ("What is the weather today?", []),  # No concept match
    ("Show me data", []),  # Ambiguous
]


def calculate_accuracy(
    predicted_concepts: List[str],
    expected_concepts: List[str]
) -> float:
    """
    Calculate accuracy (F1-like score) for concept prediction
    
    Args:
        predicted_concepts: Predicted concept list
        expected_concepts: Expected concept list
        
    Returns:
        Accuracy score (0.0 to 1.0)
    """
    if not expected_concepts and not predicted_concepts:
        return 1.0  # Both empty = correct
    
    if not expected_concepts:
        return 0.0  # Expected empty but predicted something = wrong
    
    if not predicted_concepts:
        return 0.0  # Expected something but predicted nothing = wrong
    
    # Convert to sets for comparison
    predicted_set = set(predicted_concepts)
    expected_set = set(expected_concepts)
    
    # Calculate precision and recall
    if len(predicted_set) == 0:
        precision = 0.0
    else:
        precision = len(predicted_set & expected_set) / len(predicted_set)
    
    if len(expected_set) == 0:
        recall = 0.0
    else:
        recall = len(predicted_set & expected_set) / len(expected_set)
    
    # F1 score
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def run_benchmark():
    """Run accuracy benchmark"""
    print("=" * 70)
    print("NATURAL LANGUAGE RESOURCE RESOLVER ACCURACY BENCHMARK")
    print("=" * 70)
    print()
    
    tenant_id = "tenant_001"
    
    results: List[Dict] = []
    accuracies: List[float] = []
    confidences: List[float] = []
    
    print("Running queries...")
    print("-" * 70)
    
    for query, expected_concepts in TEST_QUERIES:
        # Resolve query
        result: ResolutionResult = resolve_query(query, tenant_id)
        
        # Calculate accuracy
        accuracy = calculate_accuracy(result.matched_concepts, expected_concepts)
        accuracies.append(accuracy)
        confidences.append(result.confidence_score)
        
        # Store result
        results.append({
            "query": query,
            "expected": expected_concepts,
            "predicted": result.matched_concepts,
            "accuracy": accuracy,
            "confidence": result.confidence_score,
            "correct": accuracy >= 0.5  # Consider >= 0.5 F1 as correct
        })
    
    # Calculate statistics
    overall_accuracy = statistics.mean(accuracies)
    avg_confidence = statistics.mean(confidences)
    correct_count = sum(1 for r in results if r["correct"])
    total_count = len(results)
    correct_percentage = (correct_count / total_count) * 100
    
    # Print results
    print(f"\nTotal queries: {total_count}")
    print(f"Correctly resolved: {correct_count} ({correct_percentage:.1f}%)")
    print(f"Average accuracy (F1): {overall_accuracy:.3f}")
    print(f"Average confidence: {avg_confidence:.3f}")
    print()
    
    # Print detailed results
    print("Detailed Results:")
    print("-" * 70)
    for i, result in enumerate(results[:10], 1):  # Show first 10
        status = "✓" if result["correct"] else "✗"
        print(f"{status} Query {i}: {result['query'][:50]}")
        print(f"  Expected: {result['expected']}")
        print(f"  Predicted: {result['predicted']}")
        print(f"  Accuracy: {result['accuracy']:.3f}, Confidence: {result['confidence']:.3f}")
        print()
    
    if len(results) > 10:
        print(f"... and {len(results) - 10} more queries")
        print()
    
    # Breakdown by concept type
    print("Accuracy by Concept Type:")
    print("-" * 70)
    concept_accuracies: Dict[str, List[float]] = {}
    
    for result in results:
        for expected_concept in result["expected"]:
            if expected_concept not in concept_accuracies:
                concept_accuracies[expected_concept] = []
            
            # Check if this concept was predicted
            if expected_concept in result["predicted"]:
                concept_accuracies[expected_concept].append(1.0)
            else:
                concept_accuracies[expected_concept].append(0.0)
    
    for concept, accs in sorted(concept_accuracies.items()):
        avg_acc = statistics.mean(accs) if accs else 0.0
        print(f"  {concept}: {avg_acc:.3f} ({len(accs)} queries)")
    
    print()
    
    # Summary
    print("=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"✓ Total queries tested: {total_count}")
    print(f"✓ Correctly resolved: {correct_count} ({correct_percentage:.1f}%)")
    print(f"✓ Average accuracy (F1): {overall_accuracy:.3f}")
    print(f"✓ Average confidence: {avg_confidence:.3f}")
    print(f"✓ Accuracy range: {min(accuracies):.3f} - {max(accuracies):.3f}")
    print("=" * 70)
    
    return {
        "total_queries": total_count,
        "correct": correct_count,
        "accuracy_percentage": correct_percentage,
        "average_accuracy": overall_accuracy,
        "average_confidence": avg_confidence,
        "results": results
    }


if __name__ == "__main__":
    run_benchmark()


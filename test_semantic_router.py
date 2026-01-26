"""
Test function to verify concept resolution and semantic router functionality
"""

import json
from pathlib import Path
from mcp_semantic_router import (
    resolve_concept,
    get_tools_for_concept,
    get_top_tools,
    load_ontology
)


def test_resolve_concept():
    """Test the resolve_concept function with various queries"""
    print("=" * 60)
    print("Testing resolve_concept() function")
    print("=" * 60)
    
    test_cases = [
        ("How much revenue last quarter?", "Revenue"),
        ("What was our total sales last month?", "Revenue"),
        ("List all customers", "Customer"),
        ("Find customers in segment A", "Customer"),
        ("Check stock levels", "Inventory"),
        ("What products are low in stock?", "Inventory"),
        ("List all employees", "Employee"),
        ("Show employees in sales department", "Employee"),
        ("Get all transactions", "Transaction"),
        ("Show transactions from last week", "Transaction"),
        ("Random query that doesn't match", None),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = resolve_concept(query)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Query: '{query}'")
        print(f"  Expected: {expected}, Got: {result}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    print()
    return failed == 0


def test_get_tools_for_concept():
    """Test getting tools for a specific concept"""
    print("=" * 60)
    print("Testing get_tools_for_concept() function")
    print("=" * 60)
    
    ontology = load_ontology()
    
    for concept in ontology.keys():
        tools = get_tools_for_concept(concept, limit=10)
        print(f"Concept: {concept}")
        print(f"  Tools returned: {len(tools)}")
        print(f"  First 3 tools: {[t['name'] for t in tools[:3]]}")
        print()
        
        # Verify limit
        assert len(tools) <= 10, f"Too many tools returned for {concept}"
    
    print("✓ All concepts returned tools within limit")
    print()


def test_ontology_structure():
    """Test that ontology JSON has correct structure"""
    print("=" * 60)
    print("Testing ontology JSON structure")
    print("=" * 60)
    
    ontology = load_ontology()
    
    required_fields = ["tables", "tools", "description", "sample_queries"]
    concepts_to_check = ["Revenue", "Customer", "Inventory", "Employee", "Transaction"]
    
    for concept in concepts_to_check:
        assert concept in ontology, f"Missing concept: {concept}"
        
        concept_data = ontology[concept]
        for field in required_fields:
            assert field in concept_data, f"Missing field '{field}' in concept '{concept}'"
        
        # Verify tools count
        tools = concept_data.get("tools", [])
        assert len(tools) > 0, f"No tools defined for concept '{concept}'"
        assert len(tools) <= 10, f"Too many tools for concept '{concept}' (max 10)"
        
        print(f"✓ {concept}: {len(tools)} tools, {len(concept_data.get('tables', []))} tables")
    
    print(f"\n✓ All {len(concepts_to_check)} concepts validated")
    print()


def test_unknown_concept():
    """Test handling of unknown concepts"""
    print("=" * 60)
    print("Testing unknown concept handling")
    print("=" * 60)
    
    tools = get_tools_for_concept("UnknownConcept")
    assert len(tools) == 0, "Should return empty list for unknown concept"
    print("✓ Unknown concept returns empty tool list")
    print()


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SEMANTIC ROUTER TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Test ontology structure first
        test_ontology_structure()
        
        # Test concept resolution
        concept_resolution_passed = test_resolve_concept()
        
        # Test tool retrieval
        test_get_tools_for_concept()
        
        # Test error handling
        test_unknown_concept()
        
        print("=" * 60)
        if concept_resolution_passed:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("=" * 60)
        
        return concept_resolution_passed
        
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)


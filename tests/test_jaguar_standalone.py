"""
Standalone test script for JAG-001 (no pytest required)
Run with: python tests/test_jaguar_standalone.py
"""

import sys
import os
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.disambiguation.type_checker import (
    type_compatibility_check,
    TypeCompatibilityError,
    TypeChecker
)
from src.disambiguation.jaguar_resolver import (
    DisambiguationService,
    DisambiguationResult
)
from src.disambiguation.graph_storage_interface import MockGraphStorage


def test_type_compatibility():
    """Test type compatibility checking"""
    print("Testing Type Compatibility...")
    
    # Test 1: Compatible types merge
    try:
        type_compatibility_check("TestEntity", "Person", "Person")
        type_compatibility_check("TestEntity", "Company", "Organization")
        print("  [PASS] Compatible types merge")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 2: Incompatible types blocked
    try:
        type_compatibility_check("TestEntity", "Person", "Organization")
        print("  [FAIL] Should have raised TypeCompatibilityError")
        return False
    except TypeCompatibilityError:
        print("  [PASS] Incompatible types blocked")
    
    # Test 3: Jaguar problem (Animal vs Company)
    try:
        type_compatibility_check("Jaguar", "Animal", "Company")
        print("  [FAIL] Should have raised TypeCompatibilityError")
        return False
    except TypeCompatibilityError:
        print("  [PASS] Jaguar problem (Animal vs Company) blocked")
    
    # Test 4: Type aliases
    checker = TypeChecker()
    is_compatible, _ = checker.check_compatibility("Test", "Individual", "Person")
    if is_compatible:
        print("  [PASS] Type aliases work")
    else:
        print("  [FAIL] Type aliases")
        return False
    
    return True


def test_jaguar_resolver():
    """Test disambiguation service"""
    print("\nTesting Jaguar Resolver...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_log = os.path.join(tmpdir, "audit.jsonl")
        service = DisambiguationService(audit_log_path=audit_log)
        
        # Test 1: Jaguar cat vs company
        result1 = service.disambiguate("Jaguar", "Animal")
        result2 = service.disambiguate("Jaguar", "Company")
        
        if result1.resolved_uri != result2.resolved_uri:
            print("  [PASS] Jaguar cat vs company get different URIs")
        else:
            print("  [FAIL] Jaguar entities should have different URIs")
            return False
        
        # Test 2: Same type merges
        result3 = service.disambiguate("Apple", "Company")
        result4 = service.disambiguate("Apple", "Company")
        
        if result3.resolved_uri == result4.resolved_uri:
            print("  [PASS] Same type merges")
        else:
            print("  [FAIL] Same type should merge")
            return False
        
        # Test 3: Unique URI generation
        results = []
        for entity_type in ["Animal", "Company", "Brand"]:
            result = service.disambiguate("Jaguar", entity_type)
            results.append(result)
        
        uris = [r.resolved_uri for r in results]
        if len(uris) == len(set(uris)):
            print("  [PASS] Unique URI generation")
        else:
            print("  [FAIL] URIs should be unique")
            return False
        
        # Test 4: Audit logging
        if os.path.exists(audit_log):
            with open(audit_log, 'r') as f:
                lines = f.readlines()
            if len(lines) > 0:
                print("  [PASS] Audit logging")
            else:
                print("  [FAIL] Audit log is empty")
                return False
        else:
            print("  [FAIL] Audit log file not created")
            return False
        
        # Test 5: Get entity URI
        uri = service.get_entity_uri("Jaguar", "Animal")
        if uri == result1.resolved_uri:
            print("  [PASS] Get entity URI")
        else:
            print("  [FAIL] Get entity URI")
            return False
        
        # Test 6: List conflicts
        conflicts = service.list_conflicts()
        if len(conflicts) >= 1:
            print("  [PASS] List conflicts")
        else:
            print("  [FAIL] List conflicts")
            return False
    
    return True


def test_integration():
    """Test integration with graph storage"""
    print("\nTesting Integration with Graph Storage...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_log = os.path.join(tmpdir, "audit.jsonl")
        service = DisambiguationService(audit_log_path=audit_log)
        graph = MockGraphStorage()
        
        # Create Jaguar as Animal
        result1 = service.disambiguate("Jaguar", "Animal", graph_storage=graph)
        node1 = graph.create_node("Jaguar", "Animal", result1.resolved_uri)
        
        if node1["type"] == "Animal":
            print("  [PASS] Node creation with disambiguation")
        else:
            print("  [FAIL] Node creation")
            return False
        
        # Try to create Jaguar as Company - type check should fail
        result2 = service.disambiguate("Jaguar", "Company", graph_storage=graph)
        existing_node = graph.get_node(result2.resolved_uri)
        
        if existing_node is None:  # New URI created
            print("  [PASS] Type conflict creates unique URI")
        else:
            print("  [FAIL] Should create unique URI")
            return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("JAG-001 Standalone Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Type Compatibility", test_type_compatibility()))
    results.append(("Jaguar Resolver", test_jaguar_resolver()))
    results.append(("Integration", test_integration()))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
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


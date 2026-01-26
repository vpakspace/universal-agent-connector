"""
Test script for Self-Healing Query System
Demonstrates the healing flow: failure -> alternatives -> LLM suggestion -> success -> learning
"""

import asyncio
import json
from pathlib import Path

from self_healing_mcp_tools import query_with_healing, sql_executor
from ontology_matcher import load_learned_mappings


async def test_healing_flow():
    """Test the complete healing flow"""
    print("=" * 70)
    print("SELF-HEALING QUERY SYSTEM TEST")
    print("=" * 70)
    print()
    
    # Reset executor
    sql_executor.reset()
    
    # Configure failure: "tax_id" column doesn't exist in "customers" table
    # The mock executor will automatically fail if column is not in schema
    # "vat_number" exists in schema and is semantically similar to "tax_id"
    print("Step 1: Configuring test scenario")
    print("-" * 70)
    print("Table: customers")
    print("Available columns:", sorted(sql_executor.get_table_schema("customers")))
    print("Query will attempt to use: tax_id (does not exist in schema)")
    print("Expected alternative: vat_number (exists and is semantically similar)")
    print("Note: Mock executor will fail automatically for columns not in schema")
    print()
    
    # Clear learned mappings for clean test
    learned_mappings_path = Path("learned_mappings.json")
    if learned_mappings_path.exists():
        learned_mappings_path.unlink()
        print("Cleared learned mappings for clean test")
    print()
    
    # Execute query with failing column
    print("Step 2: Executing query with non-existent column 'tax_id'")
    print("-" * 70)
    print("Query: SELECT tax_id FROM customers")
    print()
    
    result = await query_with_healing(
        table="customers",
        column="tax_id",
        filter=None
    )
    
    # Display results
    print("Step 3: Healing Results")
    print("-" * 70)
    print(f"Success: {result['success']}")
    print(f"Attempts: {result['attempt']}")
    print(f"Healing Applied: {result['healing_applied']}")
    print()
    
    if result['success']:
        print("✓ Query succeeded after healing!")
        print()
        print("Healing History:")
        for i, healing in enumerate(result.get('healing_history', []), 1):
            print(f"  Attempt {i}:")
            print(f"    Failed column: {healing['failed_column']}")
            print(f"    Alternatives found: {healing['alternatives']}")
            print(f"    LLM suggested: {healing['suggested_column']}")
            print()
        
        print("Final Query:", result['query'])
        print()
        print("Results:")
        for row in result['result'][:5]:  # Show first 5 rows
            print(f"  {row}")
        print()
        
        # Check learned mappings
        print("Step 4: Checking Learned Mappings")
        print("-" * 70)
        learned = load_learned_mappings()
        if "customers" in learned and "tax_id" in learned["customers"]:
            print(f"✓ Learned mapping saved: tax_id → {learned['customers']['tax_id']}")
        else:
            print("✗ Learned mapping not found (may not be saved yet)")
        print()
        
    else:
        print("✗ Query failed after all retries")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Message: {result.get('message', 'No message')}")
        print()
    
    print("=" * 70)
    return result['success']


async def test_direct_sql_execution():
    """Test direct SQL execution to show the failure"""
    print("\n" + "=" * 70)
    print("DIRECT SQL EXECUTION TEST (Without Healing)")
    print("=" * 70)
    print()
    
    sql_executor.reset()
    
    try:
        result = sql_executor.execute("SELECT tax_id FROM customers")
        print("✓ Query succeeded (unexpected!)")
        print(f"Results: {result}")
    except Exception as e:
        print(f"✗ Query failed as expected: {type(e).__name__}")
        print(f"Error: {e}")
        print()
        print("This demonstrates why healing is needed!")


async def test_ontology_matching():
    """Test ontology matching functionality"""
    print("\n" + "=" * 70)
    print("ONTOLOGY MATCHING TEST")
    print("=" * 70)
    print()
    
    from ontology_matcher import find_semantic_alternatives
    
    test_cases = [
        ("tax_id", "customers"),
        ("customer_name", "customers"),
        ("email_address", "customers"),
    ]
    
    for failed_column, table in test_cases:
        alternatives = find_semantic_alternatives(failed_column, table)
        print(f"Failed column: '{failed_column}' in table '{table}'")
        print(f"Alternatives: {alternatives}")
        print()


async def main():
    """Run all tests"""
    # Test 1: Ontology matching
    await test_ontology_matching()
    
    # Test 2: Direct SQL (show failure)
    await test_direct_sql_execution()
    
    # Test 3: Healing flow
    success = await test_healing_flow()
    
    print("\n" + "=" * 70)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())


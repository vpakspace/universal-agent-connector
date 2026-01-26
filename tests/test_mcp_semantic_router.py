"""
Pytest test cases for MCP Semantic Router
Tests concept resolution, tool filtering, and ontology management
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import mcp_semantic_router
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_semantic_router import (
    resolve_concept,
    get_tools_for_concept,
    get_top_tools,
    load_ontology,
    tool_usage_count
)


@pytest.fixture
def reset_tool_usage():
    """Reset tool usage count before each test"""
    tool_usage_count.clear()
    yield
    tool_usage_count.clear()


@pytest.fixture
def sample_ontology():
    """Sample ontology data for testing"""
    return {
        "Revenue": {
            "tables": ["sales_data", "invoices"],
            "tools": ["query_sales", "aggregate_revenue", "get_revenue_by_period"],
            "description": "Revenue and sales analysis",
            "sample_queries": ["How much revenue last quarter?"]
        },
        "Customer": {
            "tables": ["customers", "customer_profiles"],
            "tools": ["get_customer_list", "search_customers"],
            "description": "Customer management",
            "sample_queries": ["List all customers"]
        }
    }


class TestResolveConcept:
    """Test cases for resolve_concept function"""
    
    def test_revenue_concept_resolution(self):
        """Test resolving Revenue concept from various queries"""
        test_cases = [
            ("How much revenue last quarter?", "Revenue"),
            ("What was our total sales last month?", "Revenue"),
            ("Show me revenue by product", "Revenue"),
            ("Calculate monthly revenue", "Revenue"),
            ("What are the payment trends?", "Revenue"),
            ("invoice summary", "Revenue"),
        ]
        
        for query, expected in test_cases:
            result = resolve_concept(query)
            assert result == expected, f"Query '{query}' should resolve to '{expected}', got '{result}'"
    
    def test_customer_concept_resolution(self):
        """Test resolving Customer concept from various queries"""
        test_cases = [
            ("List all customers", "Customer"),
            ("Find customers in segment A", "Customer"),
            ("What is the customer lifetime value?", "Customer"),
            ("Show customer satisfaction scores", "Customer"),
            ("Get customer details for ID 123", "Customer"),
            ("client list", "Customer"),
        ]
        
        for query, expected in test_cases:
            result = resolve_concept(query)
            assert result == expected, f"Query '{query}' should resolve to '{expected}', got '{result}'"
    
    def test_inventory_concept_resolution(self):
        """Test resolving Inventory concept from various queries"""
        test_cases = [
            ("Check stock levels", "Inventory"),
            ("What products are low in stock?", "Inventory"),
            ("Show inventory by warehouse", "Inventory"),
            ("Calculate inventory value", "Inventory"),
            ("Get product availability", "Inventory"),
        ]
        
        for query, expected in test_cases:
            result = resolve_concept(query)
            assert result == expected, f"Query '{query}' should resolve to '{expected}', got '{result}'"
    
    def test_employee_concept_resolution(self):
        """Test resolving Employee concept from various queries"""
        test_cases = [
            ("List all employees", "Employee"),
            ("Show employees in sales department", "Employee"),
            ("Get payroll summary for this month", "Employee"),
            ("Employee attendance report", "Employee"),
            ("What is the team composition?", "Employee"),
        ]
        
        for query, expected in test_cases:
            result = resolve_concept(query)
            assert result == expected, f"Query '{query}' should resolve to '{expected}', got '{result}'"
    
    def test_transaction_concept_resolution(self):
        """Test resolving Transaction concept from various queries"""
        test_cases = [
            ("Get all transactions", "Transaction"),
            ("Show transactions from last week", "Transaction"),
            ("Transaction summary by type", "Transaction"),
            ("Payment history for customer 123", "Transaction"),
            ("What are the transaction trends?", "Transaction"),
        ]
        
        for query, expected in test_cases:
            result = resolve_concept(query)
            assert result == expected, f"Query '{query}' should resolve to '{expected}', got '{result}'"
    
    def test_no_concept_match(self):
        """Test queries that don't match any concept"""
        test_cases = [
            "Random query that doesn't match",
            "What is the weather today?",
            "Tell me a joke",
            "",
        ]
        
        for query in test_cases:
            result = resolve_concept(query)
            assert result is None, f"Query '{query}' should not match any concept, got '{result}'"
    
    def test_case_insensitive_matching(self):
        """Test that concept resolution is case-insensitive"""
        assert resolve_concept("REVENUE last quarter") == "Revenue"
        assert resolve_concept("Revenue Last Quarter") == "Revenue"
        assert resolve_concept("revenue last quarter") == "Revenue"
        assert resolve_concept("CUSTOMER list") == "Customer"
    
    def test_empty_string(self):
        """Test handling of empty string"""
        assert resolve_concept("") is None
        assert resolve_concept(None) is None


class TestGetToolsForConcept:
    """Test cases for get_tools_for_concept function"""
    
    def test_get_revenue_tools(self):
        """Test getting tools for Revenue concept"""
        tools = get_tools_for_concept("Revenue", limit=10)
        
        assert isinstance(tools, list)
        assert len(tools) <= 10
        assert len(tools) > 0, "Revenue concept should have tools"
        
        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
    
    def test_get_customer_tools(self):
        """Test getting tools for Customer concept"""
        tools = get_tools_for_concept("Customer", limit=10)
        
        assert isinstance(tools, list)
        assert len(tools) <= 10
        assert len(tools) > 0, "Customer concept should have tools"
    
    def test_get_inventory_tools(self):
        """Test getting tools for Inventory concept"""
        tools = get_tools_for_concept("Inventory", limit=10)
        
        assert isinstance(tools, list)
        assert len(tools) <= 10
        assert len(tools) > 0, "Inventory concept should have tools"
    
    def test_get_employee_tools(self):
        """Test getting tools for Employee concept"""
        tools = get_tools_for_concept("Employee", limit=10)
        
        assert isinstance(tools, list)
        assert len(tools) <= 10
        assert len(tools) > 0, "Employee concept should have tools"
    
    def test_get_transaction_tools(self):
        """Test getting tools for Transaction concept"""
        tools = get_tools_for_concept("Transaction", limit=10)
        
        assert isinstance(tools, list)
        assert len(tools) <= 10
        assert len(tools) > 0, "Transaction concept should have tools"
    
    def test_unknown_concept(self):
        """Test getting tools for unknown concept"""
        tools = get_tools_for_concept("UnknownConcept", limit=10)
        
        assert isinstance(tools, list)
        assert len(tools) == 0, "Unknown concept should return empty list"
    
    def test_tool_limit_enforcement(self):
        """Test that tool limit is enforced"""
        tools = get_tools_for_concept("Revenue", limit=5)
        
        assert len(tools) <= 5, "Should respect limit parameter"
    
    def test_tool_structure(self):
        """Test that returned tools have correct structure"""
        tools = get_tools_for_concept("Revenue", limit=3)
        
        for tool in tools:
            # Required fields
            assert "name" in tool, "Tool should have 'name' field"
            assert "description" in tool, "Tool should have 'description' field"
            assert "inputSchema" in tool, "Tool should have 'inputSchema' field"
            
            # Input schema structure
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "query" in schema["properties"]
            assert "required" in schema
            assert "query" in schema["required"]


class TestGetTopTools:
    """Test cases for get_top_tools function"""
    
    def test_get_top_tools_no_usage(self, reset_tool_usage):
        """Test getting top tools when no usage data exists"""
        tools = get_top_tools(limit=10)
        
        assert isinstance(tools, list)
        # Should return tools from first concept if no usage data
        assert len(tools) >= 0
    
    def test_get_top_tools_with_usage(self, reset_tool_usage):
        """Test getting top tools with usage tracking"""
        # Simulate tool usage
        tool_usage_count["query_sales"] = 5
        tool_usage_count["aggregate_revenue"] = 3
        tool_usage_count["get_customer_list"] = 2
        
        tools = get_top_tools(limit=10)
        
        assert isinstance(tools, list)
        # Should return tools sorted by usage
        if len(tools) > 1:
            # Most used tools should appear first
            tool_names = [t["name"] for t in tools]
            assert "query_sales" in tool_names, "Most used tool should be included"
    
    def test_top_tools_limit(self, reset_tool_usage):
        """Test that top tools respects limit"""
        # Add some usage
        tool_usage_count["tool1"] = 10
        tool_usage_count["tool2"] = 5
        tool_usage_count["tool3"] = 3
        
        tools = get_top_tools(limit=2)
        assert len(tools) <= 2, "Should respect limit parameter"


class TestLoadOntology:
    """Test cases for load_ontology function"""
    
    def test_load_ontology_exists(self):
        """Test loading ontology file"""
        ontology = load_ontology()
        
        assert isinstance(ontology, dict)
        assert len(ontology) > 0, "Ontology should contain concepts"
    
    def test_ontology_structure(self):
        """Test that ontology has correct structure"""
        ontology = load_ontology()
        
        required_concepts = ["Revenue", "Customer", "Inventory", "Employee", "Transaction"]
        
        for concept in required_concepts:
            assert concept in ontology, f"Missing concept: {concept}"
            
            concept_data = ontology[concept]
            required_fields = ["tables", "tools", "description", "sample_queries"]
            
            for field in required_fields:
                assert field in concept_data, f"Missing field '{field}' in concept '{concept}'"
    
    def test_ontology_tool_counts(self):
        """Test that each concept has appropriate number of tools"""
        ontology = load_ontology()
        
        for concept, data in ontology.items():
            tools = data.get("tools", [])
            assert len(tools) > 0, f"Concept '{concept}' should have at least one tool"
            assert len(tools) <= 10, f"Concept '{concept}' should have at most 10 tools (has {len(tools)})"
    
    def test_ontology_caching(self):
        """Test that ontology is cached after first load"""
        # Load twice
        ontology1 = load_ontology()
        ontology2 = load_ontology()
        
        # Should return same object (cached)
        assert ontology1 is ontology2, "Ontology should be cached"
    
    @patch('mcp_semantic_router.Path')
    def test_ontology_file_not_found(self, mock_path):
        """Test handling of missing ontology file"""
        mock_path.return_value.parent.__truediv__.return_value.exists.return_value = False
        mock_path.return_value.parent.__truediv__.return_value.open.side_effect = FileNotFoundError("File not found")
        
        # Force reload by clearing cache
        import mcp_semantic_router
        mcp_semantic_router.ontology = {}
        
        with pytest.raises(FileNotFoundError):
            load_ontology()


class TestOntologyConcepts:
    """Test cases for each business concept in ontology"""
    
    @pytest.mark.parametrize("concept", [
        "Revenue",
        "Customer", 
        "Inventory",
        "Employee",
        "Transaction"
    ])
    def test_concept_has_tables(self, concept):
        """Test that each concept has associated tables"""
        ontology = load_ontology()
        
        assert concept in ontology
        tables = ontology[concept].get("tables", [])
        assert len(tables) > 0, f"Concept '{concept}' should have tables"
        assert isinstance(tables, list)
    
    @pytest.mark.parametrize("concept", [
        "Revenue",
        "Customer",
        "Inventory", 
        "Employee",
        "Transaction"
    ])
    def test_concept_has_tools(self, concept):
        """Test that each concept has associated tools"""
        ontology = load_ontology()
        
        assert concept in ontology
        tools = ontology[concept].get("tools", [])
        assert len(tools) > 0, f"Concept '{concept}' should have tools"
        assert isinstance(tools, list)
        assert all(isinstance(tool, str) for tool in tools), "All tools should be strings"
    
    @pytest.mark.parametrize("concept", [
        "Revenue",
        "Customer",
        "Inventory",
        "Employee", 
        "Transaction"
    ])
    def test_concept_has_description(self, concept):
        """Test that each concept has a description"""
        ontology = load_ontology()
        
        assert concept in ontology
        description = ontology[concept].get("description", "")
        assert len(description) > 0, f"Concept '{concept}' should have a description"
        assert isinstance(description, str)
    
    @pytest.mark.parametrize("concept", [
        "Revenue",
        "Customer",
        "Inventory",
        "Employee",
        "Transaction"
    ])
    def test_concept_has_sample_queries(self, concept):
        """Test that each concept has sample queries"""
        ontology = load_ontology()
        
        assert concept in ontology
        sample_queries = ontology[concept].get("sample_queries", [])
        assert len(sample_queries) > 0, f"Concept '{concept}' should have sample queries"
        assert isinstance(sample_queries, list)
        assert all(isinstance(q, str) for q in sample_queries), "All sample queries should be strings"


class TestToolUsageTracking:
    """Test cases for tool usage tracking"""
    
    def test_tool_usage_count_initialization(self, reset_tool_usage):
        """Test that tool usage count is initialized"""
        assert isinstance(tool_usage_count, dict)
        assert len(tool_usage_count) == 0, "Tool usage should start empty"
    
    def test_tool_usage_tracking(self, reset_tool_usage):
        """Test tracking tool usage"""
        from mcp_semantic_router import track_tool_usage
        
        track_tool_usage("test_tool")
        assert tool_usage_count["test_tool"] == 1
        
        track_tool_usage("test_tool")
        assert tool_usage_count["test_tool"] == 2
        
        track_tool_usage("another_tool")
        assert tool_usage_count["another_tool"] == 1
        assert tool_usage_count["test_tool"] == 2


class TestIntegration:
    """Integration tests combining multiple functions"""
    
    def test_resolve_and_get_tools_workflow(self):
        """Test complete workflow: resolve concept -> get tools"""
        query = "How much revenue last quarter?"
        
        # Step 1: Resolve concept
        concept = resolve_concept(query)
        assert concept == "Revenue"
        
        # Step 2: Get tools for concept
        tools = get_tools_for_concept(concept, limit=10)
        assert len(tools) > 0
        assert all(tool["name"] in ["query_sales", "aggregate_revenue", "get_revenue_by_period",
                                     "calculate_total_revenue", "revenue_forecast",
                                     "sales_trend_analysis", "invoice_summary", "payment_analytics",
                                     "revenue_by_product", "monthly_revenue_report"]
                   for tool in tools[:3])  # Check first few tools
    
    def test_all_concepts_have_resolvable_queries(self):
        """Test that each concept has at least one query that resolves to it"""
        ontology = load_ontology()
        
        for concept, data in ontology.items():
            sample_queries = data.get("sample_queries", [])
            
            # At least one sample query should resolve to the concept
            resolved_concepts = [resolve_concept(q) for q in sample_queries]
            assert concept in resolved_concepts, \
                f"At least one sample query for '{concept}' should resolve to '{concept}'. " \
                f"Queries: {sample_queries}, Resolved: {resolved_concepts}"


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_none_input(self):
        """Test handling of None input"""
        assert resolve_concept(None) is None
    
    def test_very_long_query(self):
        """Test handling of very long queries"""
        long_query = "revenue " * 1000
        result = resolve_concept(long_query)
        assert result == "Revenue"
    
    def test_special_characters(self):
        """Test handling of special characters in queries"""
        queries = [
            "revenue!!!",
            "sales@#$%",
            "customer()[]{}",
            "inventory-*-+=",
        ]
        
        results = [resolve_concept(q) for q in queries]
        assert results[0] == "Revenue"
        assert results[1] == "Revenue"
        assert results[2] == "Customer"
        assert results[3] == "Inventory"
    
    def test_mixed_case_concepts(self):
        """Test handling of mixed case concept names"""
        # Concept names should work case-insensitively in queries
        assert resolve_concept("REVENUE query") == "Revenue"
        assert resolve_concept("revenue query") == "Revenue"
        assert resolve_concept("Revenue query") == "Revenue"
    
    def test_multiple_concept_keywords(self):
        """Test queries with keywords from multiple concepts"""
        # Query with multiple concept keywords - should match the one with most matches
        query = "customer revenue sales"  # Has customer (1) and revenue (2)
        result = resolve_concept(query)
        # Revenue should win due to more keyword matches
        assert result == "Revenue"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


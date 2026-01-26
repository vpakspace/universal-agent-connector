"""
Pytest test cases for Natural Language to MCP Resource URI Resolver
Tests concept extraction, query resolution, and tool ranking
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from nl_resource_resolver import (
    resolve_query,
    resolve_template,
    rank_tools,
    calculate_overall_confidence,
    generate_explanation,
    ResolutionResult,
    load_resource_mapper
)
from concept_extractor import (
    extract_concepts,
    extract_primary_concept,
    normalize_text,
    calculate_concept_score
)


class TestConceptExtractor:
    """Test cases for concept extraction"""
    
    def test_extract_customer_concept(self):
        """Test extracting Customer concept"""
        concepts = extract_concepts("Show me customer data")
        assert len(concepts) > 0
        assert any(c[0] == "Customer" for c in concepts)
    
    def test_extract_revenue_concept(self):
        """Test extracting Revenue concept"""
        concepts = extract_concepts("What was our revenue last quarter?")
        assert len(concepts) > 0
        assert any(c[0] == "Revenue" for c in concepts)
    
    def test_extract_multiple_concepts(self):
        """Test extracting multiple concepts"""
        concepts = extract_concepts("Show me customer purchase history")
        concept_names = [c[0] for c in concepts]
        assert "Customer" in concept_names or "Transaction" in concept_names
    
    def test_no_concepts_found(self):
        """Test when no concepts match"""
        concepts = extract_concepts("What is the weather today?")
        # Should return empty list or very low confidence matches
        assert isinstance(concepts, list)
    
    def test_extract_primary_concept(self):
        """Test extracting primary concept"""
        concept, score = extract_primary_concept("Show me customer data")
        assert concept == "Customer"
        assert 0.0 <= score <= 1.0
    
    def test_normalize_text(self):
        """Test text normalization"""
        normalized = normalize_text("  Show  Me   Customer  Data  ")
        assert normalized == "show me customer data"
        assert "  " not in normalized


class TestTemplateResolution:
    """Test cases for URI template resolution"""
    
    def test_resolve_template(self):
        """Test resolving URI template"""
        template = "mcp://{{tenant}}/postgres/customers"
        resolved = resolve_template(template, "tenant_001")
        assert resolved == "mcp://tenant_001/postgres/customers"
        assert "{{tenant}}" not in resolved
    
    def test_resolve_template_multiple_placeholders(self):
        """Test template with multiple placeholders (if supported)"""
        template = "mcp://{{tenant}}/postgres/customers"
        resolved = resolve_template(template, "tenant_abc")
        assert resolved == "mcp://tenant_abc/postgres/customers"


class TestToolRanking:
    """Test cases for tool ranking"""
    
    def test_rank_tools_single_concept(self):
        """Test ranking tools for single concept"""
        concepts = ["Customer"]
        available_tools = [
            "get_customer_list",
            "search_customers",
            "customer_segmentation",
            "query_sales",
            "aggregate_revenue"
        ]
        concept_to_tools = {
            "Customer": ["get_customer_list", "search_customers", "customer_segmentation"]
        }
        
        ranked = rank_tools(concepts, available_tools, concept_to_tools)
        assert len(ranked) <= 5
        assert "get_customer_list" in ranked or "search_customers" in ranked
    
    def test_rank_tools_multiple_concepts(self):
        """Test ranking tools for multiple concepts"""
        concepts = ["Customer", "Transaction"]
        available_tools = [
            "get_customer_list",
            "query_customer_orders",
            "get_transaction_history",
            "aggregate_purchases"
        ]
        concept_to_tools = {
            "Customer": ["get_customer_list", "query_customer_orders"],
            "Transaction": ["get_transaction_history", "query_customer_orders", "aggregate_purchases"]
        }
        
        ranked = rank_tools(concepts, available_tools, concept_to_tools)
        # Tools that appear in both concepts should be ranked higher
        assert "query_customer_orders" in ranked  # Common to both
    
    def test_rank_tools_no_concepts(self):
        """Test ranking when no concepts matched"""
        concepts = []
        available_tools = ["search_resources", "query_data"]
        concept_to_tools = {}
        
        ranked = rank_tools(concepts, available_tools, concept_to_tools)
        assert len(ranked) > 0
        assert any(tool in ranked for tool in ["search_resources", "query_data"])


class TestQueryResolution:
    """Test cases for query resolution"""
    
    def test_resolve_customer_query(self):
        """Test resolving customer-related query"""
        result = resolve_query("Show me customer data", "tenant_001")
        
        assert isinstance(result, ResolutionResult)
        assert len(result.matched_concepts) > 0
        assert "Customer" in result.matched_concepts
        assert len(result.resource_uris) > 0
        assert len(result.suggested_tools) > 0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.explanation
    
    def test_resolve_revenue_query(self):
        """Test resolving revenue-related query"""
        result = resolve_query("What was our revenue last quarter?", "tenant_001")
        
        assert isinstance(result, ResolutionResult)
        assert "Revenue" in result.matched_concepts
        assert any("revenue" in uri.lower() or "sales" in uri.lower() for uri in result.resource_uris)
    
    def test_resolve_multiple_concepts(self):
        """Test resolving query with multiple concepts"""
        result = resolve_query(
            "Show me customer purchase history for last quarter",
            "tenant_001"
        )
        
        assert len(result.matched_concepts) >= 1
        assert "Customer" in result.matched_concepts or "Transaction" in result.matched_concepts
        assert len(result.resource_uris) > 0
        assert len(result.suggested_tools) > 0
    
    def test_resolve_empty_query(self):
        """Test resolving empty query"""
        result = resolve_query("", "tenant_001")
        
        assert result.confidence_score == 0.0
        assert len(result.matched_concepts) == 0
    
    def test_resolve_no_match_query(self):
        """Test resolving query with no concept matches"""
        result = resolve_query("What is the weather today?", "tenant_001")
        
        # Should return generic tools
        assert len(result.suggested_tools) > 0
        assert result.confidence_score < 0.5  # Low confidence
    
    def test_resolve_with_available_tools_filter(self):
        """Test resolution with available tools filter"""
        available_tools = ["get_customer_list", "search_customers"]
        result = resolve_query("Show me customer data", "tenant_001", available_tools)
        
        # Suggested tools should only include available ones
        assert all(tool in available_tools for tool in result.suggested_tools)


class TestExampleQueries:
    """Test cases with example queries from requirements"""
    
    def test_example_customer_purchase_history(self):
        """Test example query: customer purchase history"""
        query = "Show me customer purchase history for last quarter"
        result = resolve_query(query, "tenant_001")
        
        assert isinstance(result, ResolutionResult)
        assert len(result.matched_concepts) >= 1
        assert len(result.resource_uris) > 0
        assert len(result.suggested_tools) > 0
        assert result.confidence_score > 0.0
        
        # Verify structure matches expected format
        result_dict = result.to_dict()
        assert "matched_concepts" in result_dict
        assert "resource_uris" in result_dict
        assert "suggested_tools" in result_dict
        assert "confidence_score" in result_dict
        assert "explanation" in result_dict
    
    def test_example_revenue_query(self):
        """Test example: revenue query"""
        query = "What was our total sales last month?"
        result = resolve_query(query, "tenant_002")
        
        assert "Revenue" in result.matched_concepts or len(result.matched_concepts) > 0
        assert result.confidence_score > 0.3
    
    def test_example_inventory_query(self):
        """Test example: inventory query"""
        query = "Check stock levels for product X"
        result = resolve_query(query, "tenant_001")
        
        assert "Inventory" in result.matched_concepts or len(result.matched_concepts) > 0


class TestConfidenceScoring:
    """Test cases for confidence score calculation"""
    
    def test_calculate_overall_confidence(self):
        """Test calculating overall confidence from concept scores"""
        concept_scores = [
            ("Customer", 0.9),
            ("Transaction", 0.7),
            ("Revenue", 0.5)
        ]
        confidence = calculate_overall_confidence(concept_scores)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably high with good matches
    
    def test_calculate_confidence_empty(self):
        """Test confidence calculation with empty scores"""
        confidence = calculate_overall_confidence([])
        assert confidence == 0.0
    
    def test_calculate_confidence_single_concept(self):
        """Test confidence with single concept"""
        concept_scores = [("Customer", 0.95)]
        confidence = calculate_overall_confidence(concept_scores)
        assert confidence == 0.95


class TestExplanation:
    """Test cases for explanation generation"""
    
    def test_generate_explanation_single_concept(self):
        """Test explanation with single concept"""
        explanation = generate_explanation(
            "Show me customer data",
            ["Customer"],
            0.9
        )
        assert "Customer" in explanation
        assert "90" in explanation or "0.9" in explanation
    
    def test_generate_explanation_multiple_concepts(self):
        """Test explanation with multiple concepts"""
        explanation = generate_explanation(
            "Customer purchase history",
            ["Customer", "Transaction"],
            0.85
        )
        assert "Customer" in explanation
        assert "Transaction" in explanation
    
    def test_generate_explanation_no_concepts(self):
        """Test explanation with no concepts"""
        explanation = generate_explanation("", [], 0.0)
        assert "No specific" in explanation or "generic" in explanation.lower()


class TestResourceMapper:
    """Test cases for resource mapper"""
    
    def test_load_resource_mapper(self):
        """Test loading resource mapper"""
        mapper = load_resource_mapper()
        assert isinstance(mapper, dict)
        assert "Customer" in mapper
        assert "Revenue" in mapper
        assert "Inventory" in mapper
    
    def test_resource_mapper_structure(self):
        """Test resource mapper structure"""
        mapper = load_resource_mapper()
        customer_config = mapper.get("Customer", {})
        
        assert "resources" in customer_config
        assert "tools" in customer_config
        assert "requires" in customer_config
        assert isinstance(customer_config["resources"], list)
        assert isinstance(customer_config["tools"], list)


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_ambiguous_query(self):
        """Test ambiguous query handling"""
        result = resolve_query("Show me data", "tenant_001")
        # Should return generic tools with low confidence
        assert result.confidence_score < 0.5
        assert len(result.suggested_tools) > 0
    
    def test_very_long_query(self):
        """Test very long query"""
        long_query = " ".join(["customer"] * 100)
        result = resolve_query(long_query, "tenant_001")
        assert isinstance(result, ResolutionResult)
    
    def test_special_characters(self):
        """Test query with special characters"""
        query = "Show me customer data! @#$%"
        result = resolve_query(query, "tenant_001")
        assert isinstance(result, ResolutionResult)
        assert len(result.matched_concepts) > 0
    
    def test_multiple_equally_matched_concepts(self):
        """Test query matching multiple concepts equally"""
        query = "customer revenue data"
        result = resolve_query(query, "tenant_001")
        assert len(result.matched_concepts) >= 1
        assert len(result.resource_uris) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


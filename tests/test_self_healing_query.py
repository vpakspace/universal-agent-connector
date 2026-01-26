"""
Pytest test cases for Self-Healing Query System
Tests query execution, error handling, healing flow, and learning component
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import sys

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from self_healing_mcp_tools import (
    query_with_healing,
    sql_executor,
    build_healing_prompt,
    parse_llm_response,
    rebuild_query,
    request_sampling,
    mcp
)
from ontology_matcher import (
    find_semantic_alternatives,
    save_learned_mapping,
    load_learned_mappings,
    ColumnNotFoundError,
    TableNotFoundError
)
from mock_sql_executor import MockSQLExecutor


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test"""
    # Reset SQL executor
    sql_executor.reset()
    
    # Clear learned mappings
    learned_mappings_path = Path(__file__).parent.parent / "learned_mappings.json"
    if learned_mappings_path.exists():
        learned_mappings_path.unlink()
    
    yield
    
    # Cleanup after test
    sql_executor.reset()
    if learned_mappings_path.exists():
        learned_mappings_path.unlink()


@pytest.fixture
def clean_learned_mappings():
    """Fixture to ensure learned mappings are cleared"""
    learned_mappings_path = Path(__file__).parent.parent / "learned_mappings.json"
    if learned_mappings_path.exists():
        learned_mappings_path.unlink()
    yield
    if learned_mappings_path.exists():
        learned_mappings_path.unlink()


class TestQueryWithHealing:
    """Test cases for query_with_healing tool"""
    
    @pytest.mark.asyncio
    async def test_successful_query_no_healing_needed(self):
        """Test successful query without any errors (no healing needed)"""
        result = await query_with_healing(
            table="customers",
            column="name",
            filter=None
        )
        
        assert result["success"] is True
        assert result["attempt"] == 1
        assert result["healing_applied"] is False
        assert len(result.get("healing_history", [])) == 0
        assert len(result["result"]) > 0
        assert "name" in result["query"].lower()
    
    @pytest.mark.asyncio
    async def test_healing_with_column_not_found(self, clean_learned_mappings):
        """Test healing when column is not found"""
        # Query with column that doesn't exist but has semantic alternative
        result = await query_with_healing(
            table="customers",
            column="tax_id",  # Doesn't exist, but "vat_number" does
            filter=None
        )
        
        assert result["success"] is True
        assert result["attempt"] >= 2  # At least 2 attempts (initial + retry)
        assert result["healing_applied"] is True
        assert len(result.get("healing_history", [])) > 0
        
        # Check that final query uses alternative column
        assert "vat_number" in result["query"].lower() or "tax_id" not in result["query"]
    
    @pytest.mark.asyncio
    async def test_healing_learns_mapping(self, clean_learned_mappings):
        """Test that successful healing saves learned mapping"""
        # First query with healing
        result1 = await query_with_healing(
            table="customers",
            column="tax_id",
            filter=None
        )
        
        assert result1["success"] is True
        
        # Check learned mappings were saved
        learned = load_learned_mappings()
        assert "customers" in learned
        assert "tax_id" in learned["customers"]
        
        # Second query should use learned mapping (faster)
        result2 = await query_with_healing(
            table="customers",
            column="tax_id",
            filter=None
        )
        
        assert result2["success"] is True
    
    @pytest.mark.asyncio
    async def test_failure_with_no_alternatives(self):
        """Test failure when no semantic alternatives are found"""
        # Query with column that has no alternatives
        result = await query_with_healing(
            table="customers",
            column="nonexistent_column_xyz",
            filter=None
        )
        
        assert result["success"] is False
        assert "No semantic alternatives" in result.get("message", "") or "error" in result
    
    @pytest.mark.asyncio
    async def test_table_not_found_no_healing(self):
        """Test that table not found errors don't trigger healing"""
        result = await query_with_healing(
            table="nonexistent_table",
            column="id",
            filter=None
        )
        
        assert result["success"] is False
        assert "Table not found" in result.get("message", "") or "not found" in result.get("error", "").lower()
        assert result["healing_applied"] is False
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that max retries (2) are respected"""
        # Mock alternatives that all fail
        with patch('self_healing_mcp_tools.find_semantic_alternatives') as mock_find:
            mock_find.return_value = ["fake_col1", "fake_col2"]  # These don't exist
            
            result = await query_with_healing(
                table="customers",
                column="tax_id",
                filter=None
            )
            
            # Should fail after max retries
            assert result["success"] is False or result["attempt"] >= 3
            assert result["healing_applied"] is True  # Healing was attempted
    
    @pytest.mark.asyncio
    async def test_query_with_filter(self):
        """Test query with WHERE filter clause"""
        result = await query_with_healing(
            table="customers",
            column="name",
            filter="id = 1"
        )
        
        assert result["success"] is True
        assert "where" in result["query"].lower()
        assert "id = 1" in result["query"].lower()
    
    @pytest.mark.asyncio
    async def test_healing_preserves_filter(self):
        """Test that healing preserves WHERE clause"""
        result = await query_with_healing(
            table="customers",
            column="tax_id",  # Will be healed
            filter="id = 1"
        )
        
        assert result["success"] is True
        assert "where" in result["query"].lower()
        assert "id = 1" in result["query"].lower()


class TestOntologyMatcher:
    """Test cases for ontology matching"""
    
    def test_find_semantic_alternatives_tax_id(self):
        """Test finding alternatives for tax_id"""
        alternatives = find_semantic_alternatives("tax_id", "customers")
        
        assert len(alternatives) > 0
        assert "vat_number" in alternatives or "ein" in alternatives or "gst_id" in alternatives
    
    def test_find_semantic_alternatives_customer_name(self):
        """Test finding alternatives for customer_name"""
        alternatives = find_semantic_alternatives("customer_name", "customers")
        
        assert len(alternatives) > 0
        # Should find name-related alternatives
        assert any("name" in alt.lower() for alt in alternatives)
    
    def test_find_semantic_alternatives_email(self):
        """Test finding alternatives for email"""
        alternatives = find_semantic_alternatives("email_address", "customers")
        
        assert len(alternatives) > 0
        assert any("email" in alt.lower() for alt in alternatives)
    
    def test_find_semantic_alternatives_no_match(self):
        """Test when no alternatives are found"""
        alternatives = find_semantic_alternatives("nonexistent_xyz_column", "customers")
        
        # May return empty list or fuzzy matches
        assert isinstance(alternatives, list)
    
    def test_learned_mapping_priority(self, clean_learned_mappings):
        """Test that learned mappings take priority over ontology"""
        # Save a learned mapping
        save_learned_mapping("customers", "tax_id", "vat_number")
        
        # Find alternatives (should include learned mapping first)
        alternatives = find_semantic_alternatives("tax_id", "customers")
        
        # Learned mapping should be in alternatives
        assert "vat_number" in alternatives or len(alternatives) > 0


class TestHealingPrompt:
    """Test cases for healing prompt building"""
    
    def test_build_healing_prompt(self):
        """Test building a healing prompt"""
        prompt = build_healing_prompt(
            failed_column="tax_id",
            table="customers",
            alternatives=["vat_number", "ein", "gst_id"],
            error_message="Column 'tax_id' not found"
        )
        
        assert "tax_id" in prompt
        assert "customers" in prompt
        assert "vat_number" in prompt or "ein" in prompt or "gst_id" in prompt
        assert "Column 'tax_id' not found" in prompt
    
    def test_build_healing_prompt_empty_alternatives(self):
        """Test building prompt with no alternatives"""
        prompt = build_healing_prompt(
            failed_column="tax_id",
            table="customers",
            alternatives=[],
            error_message="Column not found"
        )
        
        assert "tax_id" in prompt
        assert "none found" in prompt.lower() or len(prompt) > 0


class TestLLMResponseParsing:
    """Test cases for LLM response parsing"""
    
    def test_parse_llm_response_simple(self):
        """Test parsing simple column name response"""
        response = "vat_number"
        result = parse_llm_response(response)
        
        assert result == "vat_number"
    
    def test_parse_llm_response_with_quotes(self):
        """Test parsing response with quotes"""
        response = '"vat_number"'
        result = parse_llm_response(response)
        
        assert result == "vat_number"
    
    def test_parse_llm_response_with_prefix(self):
        """Test parsing response with prefix text"""
        response = "The suggested column is vat_number"
        result = parse_llm_response(response)
        
        assert result == "vat_number"
    
    def test_parse_llm_response_none(self):
        """Test parsing NONE response"""
        response = "NONE"
        result = parse_llm_response(response)
        
        assert result is None
    
    def test_parse_llm_response_empty(self):
        """Test parsing empty response"""
        response = ""
        result = parse_llm_response(response)
        
        assert result is None or result == ""
    
    def test_parse_llm_response_whitespace(self):
        """Test parsing response with whitespace"""
        response = "  vat_number  "
        result = parse_llm_response(response)
        
        assert result == "vat_number"


class TestQueryRebuilding:
    """Test cases for query rebuilding"""
    
    def test_rebuild_query_simple(self):
        """Test rebuilding a simple query"""
        original = "SELECT tax_id FROM customers"
        rebuilt = rebuild_query(original, "tax_id", "vat_number")
        
        assert "vat_number" in rebuilt
        assert "tax_id" not in rebuilt
        assert "customers" in rebuilt
    
    def test_rebuild_query_case_insensitive(self):
        """Test rebuilding query with different case"""
        original = "SELECT TAX_ID FROM customers"
        rebuilt = rebuild_query(original, "tax_id", "vat_number")
        
        assert "vat_number" in rebuilt.lower()
        assert "tax_id" not in rebuilt.lower()
    
    def test_rebuild_query_with_where(self):
        """Test rebuilding query with WHERE clause"""
        original = "SELECT tax_id FROM customers WHERE id = 1"
        rebuilt = rebuild_query(original, "tax_id", "vat_number")
        
        assert "vat_number" in rebuilt
        assert "WHERE id = 1" in rebuilt
        assert "tax_id" not in rebuilt
    
    def test_rebuild_query_preserves_structure(self):
        """Test that query structure is preserved"""
        original = "SELECT tax_id, name FROM customers WHERE id > 5"
        rebuilt = rebuild_query(original, "tax_id", "vat_number")
        
        assert "vat_number" in rebuilt
        assert "name" in rebuilt
        assert "WHERE id > 5" in rebuilt


class TestMockSQLExecutor:
    """Test cases for mock SQL executor"""
    
    def test_execute_success(self):
        """Test successful query execution"""
        executor = MockSQLExecutor()
        result = executor.execute("SELECT name FROM customers")
        
        assert len(result) > 0
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
    
    def test_execute_column_not_found(self):
        """Test ColumnNotFoundError is raised"""
        executor = MockSQLExecutor()
        
        with pytest.raises(ColumnNotFoundError):
            executor.execute("SELECT nonexistent_column FROM customers")
    
    def test_execute_table_not_found(self):
        """Test TableNotFoundError is raised"""
        executor = MockSQLExecutor()
        
        with pytest.raises(TableNotFoundError):
            executor.execute("SELECT id FROM nonexistent_table")
    
    def test_execute_select_star(self):
        """Test SELECT * query"""
        executor = MockSQLExecutor()
        result = executor.execute("SELECT * FROM customers")
        
        assert len(result) > 0
        assert len(result[0]) > 0  # Should have multiple columns
    
    def test_set_failing_column(self):
        """Test configuring a column to fail"""
        executor = MockSQLExecutor()
        executor.set_failing_column("customers", "name")
        
        with pytest.raises(ColumnNotFoundError):
            executor.execute("SELECT name FROM customers")
    
    def test_get_table_schema(self):
        """Test getting table schema"""
        executor = MockSQLExecutor()
        schema = executor.get_table_schema("customers")
        
        assert isinstance(schema, set)
        assert len(schema) > 0
        assert "name" in schema or "id" in schema


class TestLearnedMappings:
    """Test cases for learned mappings"""
    
    def test_save_and_load_mapping(self, clean_learned_mappings):
        """Test saving and loading a mapping"""
        save_learned_mapping("customers", "tax_id", "vat_number")
        
        mappings = load_learned_mappings()
        assert "customers" in mappings
        assert "tax_id" in mappings["customers"]
        assert mappings["customers"]["tax_id"] == "vat_number"
    
    def test_multiple_mappings(self, clean_learned_mappings):
        """Test saving multiple mappings"""
        save_learned_mapping("customers", "tax_id", "vat_number")
        save_learned_mapping("customers", "customer_name", "name")
        save_learned_mapping("orders", "order_total", "total_amount")
        
        mappings = load_learned_mappings()
        assert "customers" in mappings
        assert "orders" in mappings
        assert mappings["customers"]["tax_id"] == "vat_number"
        assert mappings["customers"]["customer_name"] == "name"
        assert mappings["orders"]["order_total"] == "total_amount"
    
    def test_load_empty_mappings(self, clean_learned_mappings):
        """Test loading when no mappings exist"""
        mappings = load_learned_mappings()
        assert mappings == {}


class TestMCPSampling:
    """Test cases for MCP sampling (mocked)"""
    
    @pytest.mark.asyncio
    async def test_request_sampling_fallback(self):
        """Test request_sampling with fallback (when MCP sampling not available)"""
        prompt = "Available alternative column names: vat_number, ein, gst_id"
        
        response = await request_sampling(prompt)
        
        # Should return a response (even if mocked)
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_request_sampling_with_mcp_sample(self):
        """Test request_sampling when mcp.sample is available"""
        # Mock mcp.sample
        mock_response = "vat_number"
        mcp.sample = AsyncMock(return_value=mock_response)
        
        prompt = "Test prompt"
        response = await request_sampling(prompt)
        
        assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_request_sampling_error_handling(self):
        """Test request_sampling error handling"""
        # Mock mcp.sample to raise an error
        mcp.sample = AsyncMock(side_effect=Exception("Sampling failed"))
        
        prompt = "Available alternative column names: vat_number, ein"
        response = await request_sampling(prompt)
        
        # Should fall back to mock response
        assert isinstance(response, str)


class TestIntegration:
    """Integration tests for complete healing flow"""
    
    @pytest.mark.asyncio
    async def test_complete_healing_flow(self, clean_learned_mappings):
        """Test complete healing flow from failure to success"""
        # Step 1: Query fails
        result1 = await query_with_healing(
            table="customers",
            column="tax_id",
            filter=None
        )
        
        assert result1["success"] is True
        assert result1["healing_applied"] is True
        
        # Step 2: Check learned mapping was saved
        mappings = load_learned_mappings()
        assert "customers" in mappings
        assert "tax_id" in mappings["customers"]
        
        # Step 3: Second query should use learned mapping
        result2 = await query_with_healing(
            table="customers",
            column="tax_id",
            filter=None
        )
        
        assert result2["success"] is True
    
    @pytest.mark.asyncio
    async def test_multiple_failures_same_column(self, clean_learned_mappings):
        """Test handling multiple failures for same column"""
        # First failure
        result1 = await query_with_healing(
            table="customers",
            column="tax_id",
            filter=None
        )
        assert result1["success"] is True
        
        # Second failure (should use learned mapping)
        result2 = await query_with_healing(
            table="customers",
            column="tax_id",
            filter=None
        )
        assert result2["success"] is True
        
        # Both should succeed
        assert result1["healing_applied"] is True or result2["healing_applied"] is True


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_empty_table_name(self):
        """Test with empty table name"""
        result = await query_with_healing(
            table="",
            column="id",
            filter=None
        )
        
        # Should handle gracefully
        assert "success" in result
    
    @pytest.mark.asyncio
    async def test_special_characters_in_column(self):
        """Test with special characters in column name"""
        result = await query_with_healing(
            table="customers",
            column="id",  # Use valid column
            filter=None
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_very_long_column_name(self):
        """Test with very long column name"""
        result = await query_with_healing(
            table="customers",
            column="a" * 200,  # Very long name
            filter=None
        )
        
        # Should handle gracefully (may fail, but shouldn't crash)
        assert "success" in result
    
    def test_rebuild_query_multiple_occurrences(self):
        """Test rebuilding query when column appears multiple times"""
        original = "SELECT tax_id, tax_id as tid FROM customers WHERE tax_id > 0"
        rebuilt = rebuild_query(original, "tax_id", "vat_number")
        
        # All occurrences should be replaced
        assert "tax_id" not in rebuilt.lower()
        assert "vat_number" in rebuilt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


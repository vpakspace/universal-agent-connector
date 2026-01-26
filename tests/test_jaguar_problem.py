"""
Test Suite for Entity Disambiguation & Semantic Merging (JAG-001)

Tests the "Jaguar Problem" - preventing conflating entities like
"Jaguar (cat)" and "Jaguar (car company)".
"""

import pytest
import os
import json
import tempfile
from typing import Dict, Any

# Import disambiguation components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


class TestTypeCompatibility:
    """Test type compatibility checking"""
    
    def test_compatible_types_merge(self):
        """Test that compatible types can merge"""
        # Same type should merge
        type_compatibility_check("TestEntity", "Person", "Person")
        
        # Compatible types should merge
        type_compatibility_check("TestEntity", "Company", "Organization")
    
    def test_incompatible_types_blocked(self):
        """Test that incompatible types are blocked"""
        # Person and Organization should not merge
        with pytest.raises(TypeCompatibilityError) as exc_info:
            type_compatibility_check("TestEntity", "Person", "Organization")
        
        assert "Person" in str(exc_info.value)
        assert "Organization" in str(exc_info.value)
    
    def test_animal_company_blocked(self):
        """Test that Animal and Company types are blocked (Jaguar problem)"""
        # Jaguar (cat) and Jaguar (car company) should not merge
        with pytest.raises(TypeCompatibilityError) as exc_info:
            type_compatibility_check("Jaguar", "Animal", "Company")
        
        assert "Animal" in str(exc_info.value)
        assert "Company" in str(exc_info.value)
    
    def test_person_location_blocked(self):
        """Test that Person and Location types are blocked"""
        with pytest.raises(TypeCompatibilityError) as exc_info:
            type_compatibility_check("Paris", "Person", "Location")
        
        assert "Person" in str(exc_info.value)
        assert "Location" in str(exc_info.value)
    
    def test_type_aliases(self):
        """Test that type aliases work correctly"""
        checker = TypeChecker()
        
        # "Individual" should be normalized to "Person"
        is_compatible, _ = checker.check_compatibility(
            "Test", "Individual", "Person"
        )
        assert is_compatible  # Same type after normalization
    
    def test_type_hierarchies(self):
        """Test that type hierarchies allow merging"""
        checker = TypeChecker()
        
        # Company (subtype) should merge with Organization (parent)
        is_compatible, _ = checker.check_compatibility(
            "Test", "Company", "Organization"
        )
        assert is_compatible


class TestJaguarResolver:
    """Test the Jaguar Resolver disambiguation service"""
    
    @pytest.fixture
    def disambiguation_service(self, tmp_path):
        """Create a disambiguation service for testing"""
        # Create temporary audit log
        audit_log = tmp_path / "audit.jsonl"
        
        service = DisambiguationService(audit_log_path=str(audit_log))
        return service
    
    @pytest.fixture
    def graph_storage(self):
        """Create mock graph storage"""
        return MockGraphStorage()
    
    def test_jaguar_cat_vs_company(self, disambiguation_service):
        """Test the classic Jaguar problem: cat vs car company"""
        # First, create Jaguar as an Animal
        result1 = disambiguation_service.disambiguate(
            entity_name="Jaguar",
            entity_type="Animal"
        )
        
        assert result1.entity_name == "Jaguar"
        assert result1.entity_type == "Animal"
        assert "animal" in result1.resolved_uri.lower()
        assert result1.method == "new_entity"
        
        # Try to create Jaguar as a Company - should get unique URI
        result2 = disambiguation_service.disambiguate(
            entity_name="Jaguar",
            entity_type="Company"
        )
        
        assert result2.entity_name == "Jaguar"
        assert result2.entity_type == "Company"
        assert "company" in result2.resolved_uri.lower()
        assert result2.method == "unique_uri"
        assert result2.resolved_uri != result1.resolved_uri
        assert len(result2.conflicting_entities) > 0
    
    def test_same_type_merges(self, disambiguation_service):
        """Test that entities with same type merge"""
        # Create first entity
        result1 = disambiguation_service.disambiguate(
            entity_name="Apple",
            entity_type="Company"
        )
        
        # Create same entity with same type - should merge
        result2 = disambiguation_service.disambiguate(
            entity_name="Apple",
            entity_type="Company"
        )
        
        assert result2.method == "merge"
        assert result2.resolved_uri == result1.resolved_uri
    
    def test_context_based_disambiguation(self, disambiguation_service, graph_storage):
        """Test context-based disambiguation using neighboring nodes"""
        # Create context: Jaguar (Animal) with related entities
        result1 = disambiguation_service.disambiguate(
            entity_name="Jaguar",
            entity_type="Animal"
        )
        
        # Create node in graph
        graph_storage.create_node(
            entity_name="Jaguar",
            entity_type="Animal",
            uri=result1.resolved_uri
        )
        
        # Create related entities (zoo, wildlife)
        zoo_result = disambiguation_service.disambiguate(
            entity_name="Zoo",
            entity_type="Location"
        )
        graph_storage.create_node(
            entity_name="Zoo",
            entity_type="Location",
            uri=zoo_result.resolved_uri
        )
        
        # Create relationship
        graph_storage.create_relationship(
            source_uri=result1.resolved_uri,
            target_uri=zoo_result.resolved_uri,
            relationship_type="LIVES_IN"
        )
        
        # Now disambiguate with context
        result2 = disambiguation_service.disambiguate(
            entity_name="Jaguar",
            entity_type="Animal",
            graph_storage=graph_storage
        )
        
        # Should use context to boost confidence
        assert result2.method in ["merge", "context"]
        assert len(result2.context_nodes) > 0
    
    def test_unique_uri_generation(self, disambiguation_service):
        """Test that unique URIs are generated for conflicts"""
        # Create multiple entities with same name but different types
        results = []
        
        for entity_type in ["Animal", "Company", "Brand"]:
            result = disambiguation_service.disambiguate(
                entity_name="Jaguar",
                entity_type=entity_type
            )
            results.append(result)
        
        # All should have different URIs
        uris = [r.resolved_uri for r in results]
        assert len(uris) == len(set(uris))  # All unique
    
    def test_audit_logging(self, disambiguation_service, tmp_path):
        """Test that disambiguation decisions are logged"""
        # Perform disambiguation
        result = disambiguation_service.disambiguate(
            entity_name="Jaguar",
            entity_type="Animal"
        )
        
        # Check audit log exists
        assert os.path.exists(disambiguation_service.audit_log_path)
        
        # Read audit log
        with open(disambiguation_service.audit_log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 0
        
        # Parse last entry
        last_entry = json.loads(lines[-1])
        assert last_entry["entity_name"] == "Jaguar"
        assert last_entry["entity_type"] == "Animal"
        assert last_entry["resolved_uri"] == result.resolved_uri
    
    def test_get_entity_uri(self, disambiguation_service):
        """Test retrieving entity URI"""
        # Create entity
        result = disambiguation_service.disambiguate(
            entity_name="Jaguar",
            entity_type="Animal"
        )
        
        # Retrieve URI
        uri = disambiguation_service.get_entity_uri("Jaguar", "Animal")
        assert uri == result.resolved_uri
        
        # Test with type filter
        uri2 = disambiguation_service.get_entity_uri("Jaguar", "Company")
        assert uri2 is None  # Doesn't exist yet
    
    def test_list_conflicts(self, disambiguation_service):
        """Test listing all conflicts"""
        # Create conflicting entities
        disambiguation_service.disambiguate("Jaguar", "Animal")
        disambiguation_service.disambiguate("Jaguar", "Company")
        disambiguation_service.disambiguate("Apple", "Company")
        disambiguation_service.disambiguate("Apple", "Product")
        
        # List conflicts
        conflicts = disambiguation_service.list_conflicts()
        
        assert len(conflicts) >= 2  # At least Jaguar and Apple
        
        # Check Jaguar conflict
        jaguar_conflict = next(
            (c for c in conflicts if c["entity_name"] == "Jaguar"),
            None
        )
        assert jaguar_conflict is not None
        assert len(jaguar_conflict["entities"]) == 2


class TestIntegrationWithGraphStorage:
    """Test integration with graph storage (US-015)"""
    
    def test_node_creation_with_disambiguation(self, tmp_path):
        """Test node creation with disambiguation check"""
        from src.disambiguation.type_checker import type_compatibility_check
        from src.disambiguation.jaguar_resolver import DisambiguationService
        from src.disambiguation.graph_storage_interface import MockGraphStorage
        
        # Initialize services
        disambiguation_service = DisambiguationService(
            audit_log_path=str(tmp_path / "audit.jsonl")
        )
        graph_storage = MockGraphStorage()
        
        # Simulate node creation with disambiguation
        def create_node_with_disambiguation(name: str, entity_type: str):
            # Step 1: Disambiguate
            result = disambiguation_service.disambiguate(
                entity_name=name,
                entity_type=entity_type,
                graph_storage=graph_storage
            )
            
            # Step 2: Check type compatibility (if node exists)
            existing_node = graph_storage.get_node(result.resolved_uri)
            if existing_node:
                type_compatibility_check(
                    entity_name=name,
                    existing_type=existing_node.get("type"),
                    new_type=entity_type
                )
            
            # Step 3: Create node in graph
            node = graph_storage.create_node(
                entity_name=name,
                entity_type=entity_type,
                uri=result.resolved_uri
            )
            
            return node, result
        
        # Create Jaguar as Animal
        node1, result1 = create_node_with_disambiguation("Jaguar", "Animal")
        assert node1["type"] == "Animal"
        
        # Try to create Jaguar as Company - should fail type check
        with pytest.raises(TypeCompatibilityError):
            create_node_with_disambiguation("Jaguar", "Company")
        
        # But disambiguation should still work (creates unique URI)
        result2 = disambiguation_service.disambiguate("Jaguar", "Company")
        assert result2.entity_type == "Company"
        assert result2.resolved_uri != result1.resolved_uri


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


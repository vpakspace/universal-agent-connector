"""
Test Suite for MINE Score Evaluator (JAG-002)

Tests knowledge graph quality metrics:
- Information Retention (40%)
- Clustering Quality (30%)
- Graph Connectivity (30%)
"""

import pytest
import sys
import os
import json
import tempfile
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import networkx as nx
import numpy as np

from src.evaluation.mine_evaluator import (
    MINEEvaluator,
    MINEScore,
    MINEGrade
)
from src.evaluation.mine_components import (
    InformationRetentionComponent,
    ClusteringQualityComponent,
    GraphConnectivityComponent,
    ComponentScore
)
from src.evaluation.embeddings_registry import (
    MockEmbeddingsModel,
    EmbeddingsModelRegistry
)


class TestInformationRetentionComponent:
    """Test Information Retention Component (40% weight)"""
    
    def test_calculate_retention_perfect_match(self):
        """Test retention with identical texts (should be high)"""
        component = InformationRetentionComponent()
        
        source_texts = ["Jaguar is a big cat", "Apple is a tech company"]
        reconstructed_texts = ["Jaguar is a big cat", "Apple is a tech company"]
        
        score = component.calculate(source_texts, reconstructed_texts)
        
        assert score.weight == 0.4
        assert score.value > 0.5  # Should be high for identical texts
        assert score.weighted_score == score.value * 0.4
    
    def test_calculate_retention_different_texts(self):
        """Test retention with different texts (should be lower)"""
        component = InformationRetentionComponent()
        
        source_texts = ["Jaguar is a big cat"]
        reconstructed_texts = ["Completely different text about something else"]
        
        score = component.calculate(source_texts, reconstructed_texts)
        
        assert score.weight == 0.4
        assert score.value < 1.0
        assert "num_texts" in score.details
    
    def test_calculate_retention_empty_input(self):
        """Test retention with empty input"""
        component = InformationRetentionComponent()
        
        score = component.calculate([], [])
        
        assert score.value == 0.0
        assert "error" in score.details
    
    def test_calculate_retention_mismatched_lengths(self):
        """Test retention with mismatched input lengths"""
        component = InformationRetentionComponent()
        
        with pytest.raises(ValueError):
            component.calculate(["text1"], ["text1", "text2"])


class TestClusteringQualityComponent:
    """Test Clustering Quality Component (30% weight)"""
    
    def test_calculate_clustering_no_conflicts(self):
        """Test clustering with no conflicts (perfect score)"""
        component = ClusteringQualityComponent()
        
        conflicts = []
        total_entities = 10
        
        score = component.calculate(conflicts, total_entities)
        
        assert score.weight == 0.3
        assert score.value == 1.0  # Perfect if no conflicts
        assert score.weighted_score == 0.3
    
    def test_calculate_clustering_with_conflicts(self):
        """Test clustering with conflicts (lower score)"""
        component = ClusteringQualityComponent()
        
        conflicts = [
            {
                "entity_name": "Jaguar",
                "conflicting_types": ["Animal", "Company"],
                "conflicting_uris": ["uri1", "uri2"],
                "num_entities": 2
            }
        ]
        total_entities = 10
        
        score = component.calculate(conflicts, total_entities)
        
        assert score.weight == 0.3
        assert score.value < 1.0  # Should be penalized
        assert "num_conflicts" in score.details
        assert score.details["num_conflicts"] == 1
    
    def test_calculate_clustering_empty_graph(self):
        """Test clustering with empty graph"""
        component = ClusteringQualityComponent()
        
        score = component.calculate([], 0)
        
        assert score.value == 1.0  # Perfect if no entities
    
    def test_identify_jaguar_problems(self):
        """Test identification of Jaguar Problem cases"""
        component = ClusteringQualityComponent()
        
        entity_registry = {
            "Jaguar": [
                {"uri": "uri1", "type": "Animal"},
                {"uri": "uri2", "type": "Company"}
            ],
            "Apple": [
                {"uri": "uri3", "type": "Company"}
            ]
        }
        
        conflicts = component.identify_jaguar_problems(entity_registry)
        
        assert len(conflicts) == 1
        assert conflicts[0]["entity_name"] == "Jaguar"
        assert "Animal" in conflicts[0]["conflicting_types"]
        assert "Company" in conflicts[0]["conflicting_types"]
        assert conflicts[0]["conflict_type"] == "type_conflict"


class TestGraphConnectivityComponent:
    """Test Graph Connectivity Component (30% weight)"""
    
    def test_calculate_connectivity_fully_connected(self):
        """Test connectivity with fully connected graph"""
        component = GraphConnectivityComponent()
        
        # Create fully connected graph
        graph = nx.complete_graph(5)
        
        score = component.calculate(graph)
        
        assert score.weight == 0.3
        assert score.value == 1.0  # Fully connected
        assert score.weighted_score == 0.3
    
    def test_calculate_connectivity_disconnected(self):
        """Test connectivity with disconnected graph"""
        component = GraphConnectivityComponent()
        
        # Create graph with multiple components
        graph = nx.Graph()
        graph.add_edges_from([(0, 1), (1, 2)])  # Component 1 (3 nodes)
        graph.add_edges_from([(3, 4)])  # Component 2 (2 nodes)
        graph.add_node(5)  # Isolated node
        
        score = component.calculate(graph)
        
        assert score.weight == 0.3
        assert score.value < 1.0  # Not fully connected
        assert score.value == 3.0 / 6.0  # Largest component (3) / total (6)
    
    def test_calculate_connectivity_empty_graph(self):
        """Test connectivity with empty graph"""
        component = GraphConnectivityComponent()
        
        graph = nx.Graph()
        
        score = component.calculate(graph)
        
        assert score.value == 0.0
        assert "error" in score.details
    
    def test_build_graph_from_entities(self):
        """Test building graph from entities and relationships"""
        component = GraphConnectivityComponent()
        
        entities = [
            {"uri": "uri1", "name": "Jaguar", "type": "Animal"},
            {"uri": "uri2", "name": "Zoo", "type": "Location"},
            {"uri": "uri3", "name": "Wildlife", "type": "Concept"}
        ]
        
        relationships = [
            {"source_uri": "uri1", "target_uri": "uri2", "type": "LIVES_IN"},
            {"source_uri": "uri1", "target_uri": "uri3", "type": "IS_A"}
        ]
        
        graph = component.build_graph_from_entities(entities, relationships)
        
        assert graph.number_of_nodes() == 3
        assert graph.number_of_edges() == 2
        assert graph.has_edge("uri1", "uri2")
        assert graph.has_edge("uri1", "uri3")


class TestMINEEvaluator:
    """Test MINE Score Evaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create MINE evaluator instance"""
        return MINEEvaluator()
    
    @pytest.fixture
    def sample_entities(self):
        """Sample entities for testing"""
        return [
            {"uri": "entity://animal/jaguar", "name": "Jaguar", "type": "Animal"},
            {"uri": "entity://company/jaguar_1", "name": "Jaguar", "type": "Company"},
            {"uri": "entity://location/zoo", "name": "Zoo", "type": "Location"},
            {"uri": "entity://company/apple", "name": "Apple", "type": "Company"}
        ]
    
    @pytest.fixture
    def sample_relationships(self):
        """Sample relationships for testing"""
        return [
            {"source_uri": "entity://animal/jaguar", "target_uri": "entity://location/zoo", "type": "LIVES_IN"},
            {"source_uri": "entity://company/apple", "target_uri": "entity://company/jaguar_1", "type": "COMPETES_WITH"}
        ]
    
    @pytest.fixture
    def sample_entity_registry(self, sample_entities):
        """Sample entity registry with Jaguar conflict"""
        registry = {}
        for entity in sample_entities:
            name = entity["name"]
            if name not in registry:
                registry[name] = []
            registry[name].append(entity)
        return registry
    
    def test_calculate_mine_score(self, evaluator, sample_entities, sample_relationships, sample_entity_registry):
        """Test MINE score calculation"""
        source_texts = [
            "Jaguar is a big cat that lives in zoos",
            "Jaguar is a car company",
            "Apple is a tech company"
        ]
        reconstructed_texts = [
            "Jaguar is a big cat that lives in zoos",
            "Jaguar is a car company",
            "Apple is a tech company"
        ]
        
        # Build graph
        graph = evaluator.connectivity_component.build_graph_from_entities(
            sample_entities, sample_relationships
        )
        
        score = evaluator.calculate_mine_score(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entity_registry=sample_entity_registry,
            graph=graph
        )
        
        assert isinstance(score, MINEScore)
        assert 0.0 <= score.total_score <= 1.0
        assert score.information_retention.weight == 0.4
        assert score.clustering_quality.weight == 0.3
        assert score.graph_connectivity.weight == 0.3
        assert len(score.jaguar_problems) > 0  # Should detect Jaguar conflict
    
    def test_calculate_mine_score_from_entities(self, evaluator, sample_entities, sample_relationships):
        """Test MINE score calculation from entities (auto-builds graph)"""
        source_texts = ["Jaguar is a big cat"]
        reconstructed_texts = ["Jaguar is a big cat"]
        
        score = evaluator.calculate_mine_score_from_entities(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entities=sample_entities,
            relationships=sample_relationships
        )
        
        assert isinstance(score, MINEScore)
        assert 0.0 <= score.total_score <= 1.0
        assert len(score.jaguar_problems) > 0
    
    def test_grade_determination(self, evaluator):
        """Test grade determination from score"""
        assert evaluator._determine_grade(0.80) == MINEGrade.A  # Production Ready
        assert evaluator._determine_grade(0.70) == MINEGrade.B  # Good
        assert evaluator._determine_grade(0.50) == MINEGrade.C  # Fragile
        assert evaluator._determine_grade(0.30) == MINEGrade.F  # Very Fragile
    
    def test_export_report(self, evaluator, sample_entities, sample_relationships, tmp_path):
        """Test exporting report to JSON"""
        source_texts = ["Test text"]
        reconstructed_texts = ["Test text"]
        
        score = evaluator.calculate_mine_score_from_entities(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entities=sample_entities,
            relationships=sample_relationships
        )
        
        output_path = tmp_path / "mine_report.json"
        evaluator.export_report(score, str(output_path))
        
        assert output_path.exists()
        
        # Verify JSON is valid
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "total_score" in data
        assert "grade" in data
        assert data["grade"] in ["A", "B", "C", "F"]
    
    def test_generate_report_summary(self, evaluator, sample_entities, sample_relationships):
        """Test generating human-readable report summary"""
        source_texts = ["Test text"]
        reconstructed_texts = ["Test text"]
        
        score = evaluator.calculate_mine_score_from_entities(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entities=sample_entities,
            relationships=sample_relationships
        )
        
        summary = evaluator.generate_report_summary(score)
        
        assert "MINE Score Evaluation Report" in summary
        assert "Overall Score" in summary
        assert "Information Retention" in summary
        assert "Clustering Quality" in summary
        assert "Graph Connectivity" in summary
        assert "Jaguar Problems Detected" in summary
    
    def test_identify_jaguar_problems_in_score(self, evaluator, sample_entities, sample_relationships):
        """Test that Jaguar problems are identified in score"""
        source_texts = ["Jaguar is a big cat", "Jaguar is a car company"]
        reconstructed_texts = ["Jaguar is a big cat", "Jaguar is a car company"]
        
        score = evaluator.calculate_mine_score_from_entities(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entities=sample_entities,
            relationships=sample_relationships
        )
        
        # Should identify Jaguar conflict
        jaguar_conflicts = [p for p in score.jaguar_problems if p["entity_name"] == "Jaguar"]
        assert len(jaguar_conflicts) > 0
        assert "Animal" in jaguar_conflicts[0]["conflicting_types"]
        assert "Company" in jaguar_conflicts[0]["conflicting_types"]
    
    def test_mine_score_to_json(self, evaluator, sample_entities, sample_relationships):
        """Test MINEScore JSON export"""
        source_texts = ["Test"]
        reconstructed_texts = ["Test"]
        
        score = evaluator.calculate_mine_score_from_entities(
            source_texts=source_texts,
            reconstructed_texts=reconstructed_texts,
            entities=sample_entities,
            relationships=sample_relationships
        )
        
        json_str = score.to_json()
        data = json.loads(json_str)
        
        assert "total_score" in data
        assert "grade" in data
        assert "information_retention" in data
        assert "clustering_quality" in data
        assert "graph_connectivity" in data
        assert "jaguar_problems" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


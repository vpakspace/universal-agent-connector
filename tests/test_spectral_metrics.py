"""
Test Suite for Spectral Graph Robustness Analysis (JAG-004)

Tests algebraic connectivity (Fiedler Value) calculations and robustness assessment.
"""

import pytest
import sys
import os
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check dependencies
try:
    import networkx as nx
    import numpy as np
    from scipy.sparse import linalg
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    print("WARNING: networkx, numpy, or scipy not installed. Some tests will be skipped.")

if HAS_DEPENDENCIES:
    from src.evaluation.spectral_analyzer import (
        SpectralAnalyzer,
        SpectralAnalysisResult,
        RobustnessLevel
    )
    from src.evaluation.graph_matrix_builder import GraphMatrixBuilder


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Requires networkx, numpy, scipy")
class TestGraphMatrixBuilder:
    """Test Graph Matrix Builder"""
    
    def test_build_adjacency_matrix_from_nx(self):
        """Test building adjacency matrix from NetworkX graph"""
        graph = nx.complete_graph(5)
        
        builder = GraphMatrixBuilder()
        matrix = builder.build_adjacency_matrix_from_nx(graph)
        
        assert matrix.shape == (5, 5)
        assert matrix.nnz > 0  # Should have edges
    
    def test_build_adjacency_matrix_from_entities(self):
        """Test building adjacency matrix from entities and relationships"""
        entities = [
            {"uri": "uri1", "name": "Node1"},
            {"uri": "uri2", "name": "Node2"},
            {"uri": "uri3", "name": "Node3"}
        ]
        
        relationships = [
            {"source_uri": "uri1", "target_uri": "uri2", "type": "RELATED"},
            {"source_uri": "uri2", "target_uri": "uri3", "type": "RELATED"}
        ]
        
        builder = GraphMatrixBuilder()
        matrix, mapping = builder.build_adjacency_matrix_from_entities(entities, relationships)
        
        assert matrix.shape[0] == 3
        assert matrix.nnz > 0
        assert len(mapping) == 3
        assert "uri1" in mapping
    
    def test_build_laplacian_matrix(self):
        """Test building Laplacian matrix"""
        graph = nx.complete_graph(5)
        builder = GraphMatrixBuilder()
        
        adjacency = builder.build_adjacency_matrix_from_nx(graph)
        laplacian = builder.build_laplacian_matrix(adjacency)
        
        assert laplacian.shape == (5, 5)
        # Laplacian should have row sums = 0
        row_sums = laplacian.sum(axis=1).A1
        assert all(abs(s) < 1e-10 for s in row_sums)
    
    def test_get_matrix_statistics(self):
        """Test matrix statistics"""
        graph = nx.complete_graph(5)
        builder = GraphMatrixBuilder()
        
        matrix = builder.build_adjacency_matrix_from_nx(graph)
        stats = builder.get_matrix_statistics(matrix)
        
        assert "shape" in stats
        assert "nnz" in stats
        assert "density" in stats
        assert stats["num_nodes"] == 5


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Requires networkx, numpy, scipy")
class TestSpectralAnalyzer:
    """Test Spectral Analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create spectral analyzer instance"""
        return SpectralAnalyzer()
    
    @pytest.fixture
    def robust_graph(self):
        """Create a robust graph (complete graph)"""
        return nx.complete_graph(10)
    
    @pytest.fixture
    def fragile_graph(self):
        """Create a fragile graph (star graph - hub and spoke)"""
        return nx.star_graph(10)  # 1 center node, 10 leaf nodes
    
    def test_analyze_robust_graph(self, analyzer, robust_graph):
        """Test analysis of robust graph"""
        result = analyzer.analyze_graph(robust_graph)
        
        assert isinstance(result, SpectralAnalysisResult)
        assert result.lambda_1 > 0
        assert result.lambda_2 > 0
        assert result.spectral_gap > 0
        assert result.lambda_2 > 2.0  # Robust graph should have λ₂ > 2
        assert result.robustness_level in [RobustnessLevel.HIGHLY_ROBUST, RobustnessLevel.MODERATELY_ROBUST]
    
    def test_analyze_fragile_graph(self, analyzer, fragile_graph):
        """Test analysis of fragile graph (star graph)"""
        result = analyzer.analyze_graph(fragile_graph)
        
        assert isinstance(result, SpectralAnalysisResult)
        assert result.lambda_1 > 0
        assert result.lambda_2 > 0
        # Star graph should have λ₂ < 2 (fragile)
        # Actually, star graphs have λ₂ = 1.0
        assert result.lambda_2 <= 2.0
        assert result.robustness_level == RobustnessLevel.FRAGILE
    
    def test_analyze_from_entities(self, analyzer):
        """Test analysis from entities and relationships"""
        entities = [
            {"uri": "uri1", "name": "Node1"},
            {"uri": "uri2", "name": "Node2"},
            {"uri": "uri3", "name": "Node3"},
            {"uri": "uri4", "name": "Node4"}
        ]
        
        relationships = [
            {"source_uri": "uri1", "target_uri": "uri2"},
            {"source_uri": "uri2", "target_uri": "uri3"},
            {"source_uri": "uri3", "target_uri": "uri4"},
            {"source_uri": "uri4", "target_uri": "uri1"}  # Creates cycle
        ]
        
        result = analyzer.analyze_from_entities(entities, relationships)
        
        assert isinstance(result, SpectralAnalysisResult)
        assert result.lambda_1 > 0
        assert result.lambda_2 >= 0
    
    def test_lambda_2_interpretation(self, analyzer):
        """Test λ₂ interpretation thresholds"""
        # Create graph with known λ₂ > 5 (highly robust)
        graph = nx.complete_graph(20)
        result = analyzer.analyze_graph(graph)
        
        if result.lambda_2 > 5.0:
            assert result.robustness_level == RobustnessLevel.HIGHLY_ROBUST
        elif result.lambda_2 >= 2.0:
            assert result.robustness_level == RobustnessLevel.MODERATELY_ROBUST
        else:
            assert result.robustness_level == RobustnessLevel.FRAGILE
    
    def test_generate_report(self, analyzer, robust_graph):
        """Test report generation"""
        result = analyzer.analyze_graph(robust_graph)
        report = analyzer.generate_report(result)
        
        assert "SPECTRAL ANALYSIS REPORT" in report
        assert "λ₁" in report
        assert "λ₂" in report
        assert "Spectral Gap" in report
        assert "INTERPRETATION" in report
    
    def test_save_report(self, analyzer, robust_graph, tmp_path):
        """Test saving report to file"""
        result = analyzer.analyze_graph(robust_graph)
        
        filepath = tmp_path / "spectral_report.txt"
        analyzer.save_report(result, str(filepath))
        
        assert filepath.exists()
        with open(filepath, 'r') as f:
            content = f.read()
            assert "SPECTRAL ANALYSIS REPORT" in content
    
    def test_save_json_report(self, analyzer, robust_graph, tmp_path):
        """Test saving JSON report"""
        result = analyzer.analyze_graph(robust_graph)
        
        filepath = tmp_path / "spectral_report.json"
        analyzer.save_json_report(result, str(filepath))
        
        assert filepath.exists()
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert "lambda_1" in data
            assert "lambda_2" in data
            assert "robustness_level" in data
    
    def test_spectral_gap_calculation(self, analyzer, robust_graph):
        """Test spectral gap calculation (λ₁ - λ₂)"""
        result = analyzer.analyze_graph(robust_graph)
        
        expected_gap = result.lambda_1 - result.lambda_2
        assert abs(result.spectral_gap - expected_gap) < 0.01
    
    def test_recommendations_generated(self, analyzer):
        """Test that recommendations are generated based on robustness level"""
        # Fragile graph (star)
        fragile_graph = nx.star_graph(10)
        result = analyzer.analyze_graph(fragile_graph)
        
        assert len(result.recommendations) > 0
        assert any("URGENT" in rec or "fragile" in rec.lower() for rec in result.recommendations)
    
    def test_matrix_statistics_in_result(self, analyzer, robust_graph):
        """Test that matrix statistics are included in result"""
        result = analyzer.analyze_graph(robust_graph)
        
        assert "num_nodes" in result.matrix_statistics
        assert result.matrix_statistics["num_nodes"] == robust_graph.number_of_nodes()


@pytest.mark.skipif(not HAS_DEPENDENCIES, reason="Requires networkx, numpy, scipy")
class TestIntegration:
    """Integration tests"""
    
    def test_complete_analysis_workflow(self, tmp_path):
        """Test complete spectral analysis workflow"""
        from src.evaluation.spectral_analyzer import SpectralAnalyzer
        import networkx as nx
        
        # Create graph
        graph = nx.complete_graph(10)
        
        # Analyze
        analyzer = SpectralAnalyzer()
        result = analyzer.analyze_graph(graph)
        
        # Generate report
        report = analyzer.generate_report(result)
        
        # Save reports
        txt_file = tmp_path / "report.txt"
        json_file = tmp_path / "report.json"
        
        analyzer.save_report(result, str(txt_file))
        analyzer.save_json_report(result, str(json_file))
        
        # Verify files
        assert txt_file.exists()
        assert json_file.exists()
        
        # Verify content
        assert result.lambda_1 > 0
        assert result.lambda_2 > 0
        assert result.spectral_gap > 0
    
    def test_fragile_graph_alert(self):
        """Test that fragile graphs (λ₂ < 2) trigger alerts"""
        from src.evaluation.spectral_analyzer import SpectralAnalyzer
        import networkx as nx
        
        # Star graph is fragile (λ₂ = 1.0)
        fragile_graph = nx.star_graph(10)
        
        analyzer = SpectralAnalyzer()
        result = analyzer.analyze_graph(fragile_graph)
        
        # Should be flagged as fragile
        assert result.lambda_2 < 2.0
        assert result.robustness_level == RobustnessLevel.FRAGILE
        assert "WARNING" in result.interpretation or "Fragile" in result.interpretation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


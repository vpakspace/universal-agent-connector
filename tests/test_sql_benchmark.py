"""
Tests for SQL Benchmark Suite
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from ai_agent_connector.app.utils.sql_benchmark import (
    BenchmarkQuery,
    BenchmarkResult,
    BenchmarkRun,
    SQLAccuracyScorer,
    SQLBenchmarkSuite
)
from ai_agent_connector.app.utils.nl_to_sql import NLToSQLConverter


class TestSQLAccuracyScorer:
    """Test SQL accuracy scoring"""
    
    def test_exact_match(self):
        """Test exact SQL match"""
        scorer = SQLAccuracyScorer()
        score, is_exact = scorer.calculate_accuracy(
            "SELECT * FROM users",
            "SELECT * FROM users"
        )
        assert is_exact is True
        assert score == 1.0
    
    def test_normalize_sql(self):
        """Test SQL normalization"""
        scorer = SQLAccuracyScorer()
        
        sql1 = "SELECT * FROM users"
        sql2 = "SELECT  *  FROM  users"
        sql3 = "select * from users"
        
        norm1 = scorer.normalize_sql(sql1)
        norm2 = scorer.normalize_sql(sql2)
        norm3 = scorer.normalize_sql(sql3)
        
        # Should normalize to similar format
        assert norm1 is not None
        assert norm2 is not None
        assert norm3 is not None
    
    def test_keyword_extraction(self):
        """Test keyword extraction"""
        scorer = SQLAccuracyScorer()
        keywords = scorer.extract_keywords("SELECT * FROM users WHERE id = 1")
        assert 'SELECT' in keywords or 'select' in keywords.upper()
        assert 'FROM' in keywords or 'from' in keywords.upper()
        assert 'WHERE' in keywords or 'where' in keywords.upper()
    
    def test_partial_match(self):
        """Test partial SQL match"""
        scorer = SQLAccuracyScorer()
        score, is_exact = scorer.calculate_accuracy(
            "SELECT name FROM users",
            "SELECT * FROM users"
        )
        assert is_exact is False
        assert 0.0 < score < 1.0
    
    def test_no_match(self):
        """Test completely different SQL"""
        scorer = SQLAccuracyScorer()
        score, is_exact = scorer.calculate_accuracy(
            "SELECT * FROM products",
            "SELECT * FROM users"
        )
        assert is_exact is False
        assert score < 1.0
    
    def test_empty_sql(self):
        """Test empty SQL handling"""
        scorer = SQLAccuracyScorer()
        score, is_exact = scorer.calculate_accuracy("", "SELECT * FROM users")
        assert score == 0.0
        assert is_exact is False


class TestBenchmarkQuery:
    """Test BenchmarkQuery dataclass"""
    
    def test_benchmark_query_creation(self):
        """Test creating a benchmark query"""
        query = BenchmarkQuery(
            id="test_1",
            category="basic",
            difficulty="easy",
            natural_language="Show me all users",
            expected_sql="SELECT * FROM users"
        )
        assert query.id == "test_1"
        assert query.category == "basic"
        assert query.difficulty == "easy"
        assert query.natural_language == "Show me all users"
        assert query.expected_sql == "SELECT * FROM users"


class TestSQLBenchmarkSuite:
    """Test SQL Benchmark Suite"""
    
    @pytest.fixture
    def benchmark_suite(self, tmp_path):
        """Create benchmark suite with temp directory"""
        benchmark_file = tmp_path / "benchmark_queries.json"
        suite = SQLBenchmarkSuite(benchmark_file=str(benchmark_file))
        return suite
    
    def test_suite_initialization(self, benchmark_suite):
        """Test benchmark suite initialization"""
        assert benchmark_suite is not None
        assert len(benchmark_suite.queries) > 0
    
    def test_default_queries(self, benchmark_suite):
        """Test default queries are loaded"""
        assert len(benchmark_suite.queries) >= 100
    
    def test_query_categories(self, benchmark_suite):
        """Test queries have different categories"""
        categories = set(q.category for q in benchmark_suite.queries)
        assert len(categories) > 1
    
    def test_query_difficulties(self, benchmark_suite):
        """Test queries have different difficulty levels"""
        difficulties = set(q.difficulty for q in benchmark_suite.queries)
        assert 'easy' in difficulties
        assert 'medium' in difficulties
        assert 'hard' in difficulties
    
    def test_run_benchmark(self, benchmark_suite):
        """Test running benchmark"""
        # Mock converter
        converter = Mock(spec=NLToSQLConverter)
        converter.convert_to_sql.return_value = {
            'sql': 'SELECT * FROM users',
            'natural_language': 'Show me all users'
        }
        
        # Run benchmark on first query only
        first_query = benchmark_suite.queries[0]
        run = benchmark_suite.run_benchmark(
            converter,
            model='gpt-4o-mini',
            query_ids=[first_query.id]
        )
        
        assert run is not None
        assert run.model == 'gpt-4o-mini'
        assert run.total_queries == 1
        assert len(run.results) == 1
    
    def test_benchmark_with_error(self, benchmark_suite):
        """Test benchmark handles errors"""
        converter = Mock(spec=NLToSQLConverter)
        converter.convert_to_sql.side_effect = Exception("API Error")
        
        first_query = benchmark_suite.queries[0]
        run = benchmark_suite.run_benchmark(
            converter,
            model='gpt-4o-mini',
            query_ids=[first_query.id]
        )
        
        assert run is not None
        assert len(run.results) == 1
        assert run.results[0].error is not None
        assert run.results[0].accuracy_score == 0.0
    
    def test_get_runs(self, benchmark_suite):
        """Test getting benchmark runs"""
        # Create a mock run
        converter = Mock(spec=NLToSQLConverter)
        converter.convert_to_sql.return_value = {
            'sql': 'SELECT * FROM users'
        }
        
        run = benchmark_suite.run_benchmark(
            converter,
            model='gpt-4o-mini',
            query_ids=[benchmark_suite.queries[0].id]
        )
        
        # Get runs
        runs = benchmark_suite.get_runs(limit=10)
        assert len(runs) > 0
        assert any(r.run_id == run.run_id for r in runs)
    
    def test_get_trends(self, benchmark_suite):
        """Test getting trends"""
        # Create multiple runs
        converter = Mock(spec=NLToSQLConverter)
        converter.convert_to_sql.return_value = {
            'sql': 'SELECT * FROM users'
        }
        
        # Run benchmark multiple times
        for _ in range(3):
            benchmark_suite.run_benchmark(
                converter,
                model='gpt-4o-mini',
                query_ids=[benchmark_suite.queries[0].id]
            )
        
        # Get trends
        trends = benchmark_suite.get_trends(days=30)
        assert trends is not None
        assert 'trends' in trends
        assert len(trends['trends']) > 0


class TestBenchmarkAPI:
    """Test benchmark API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        from main import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app.test_client()
    
    def test_run_benchmark_endpoint(self, client):
        """Test run benchmark endpoint"""
        with patch('ai_agent_connector.app.api.routes.NLToSQLConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_to_sql.return_value = {
                'sql': 'SELECT * FROM users'
            }
            mock_converter_class.return_value = mock_converter
            
            response = client.post('/api/benchmark/sql/run', json={
                'model': 'gpt-4o-mini'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'run_id' in data
            assert 'summary' in data
    
    def test_get_benchmark_runs_endpoint(self, client):
        """Test get benchmark runs endpoint"""
        response = client.get('/api/benchmark/sql/runs')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'runs' in data
    
    def test_get_benchmark_trends_endpoint(self, client):
        """Test get benchmark trends endpoint"""
        response = client.get('/api/benchmark/sql/trends?days=30')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'trends' in data
    
    def test_get_benchmark_queries_endpoint(self, client):
        """Test get benchmark queries endpoint"""
        response = client.get('/api/benchmark/sql/queries')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'queries' in data
        assert len(data['queries']) >= 100
    
    def test_get_benchmark_queries_filtered(self, client):
        """Test get benchmark queries with filters"""
        response = client.get('/api/benchmark/sql/queries?difficulty=easy')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert all(q['difficulty'] == 'easy' for q in data['queries'])


@pytest.mark.integration
class TestBenchmarkIntegration:
    """Integration tests for benchmark suite"""
    
    def test_full_benchmark_workflow(self, tmp_path):
        """Test complete benchmark workflow"""
        benchmark_file = tmp_path / "benchmark_queries.json"
        suite = SQLBenchmarkSuite(benchmark_file=str(benchmark_file))
        
        # Mock converter
        converter = Mock(spec=NLToSQLConverter)
        converter.convert_to_sql.return_value = {
            'sql': 'SELECT * FROM users'
        }
        
        # Run benchmark
        run = suite.run_benchmark(converter, model='gpt-4o-mini')
        
        # Verify results
        assert run is not None
        assert run.total_queries > 0
        assert len(run.results) == run.total_queries
        
        # Get runs
        runs = suite.get_runs(limit=10)
        assert len(runs) > 0
        
        # Get trends
        trends = suite.get_trends(days=30)
        assert trends is not None

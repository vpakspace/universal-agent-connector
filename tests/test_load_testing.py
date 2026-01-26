"""
Tests for Load Testing Infrastructure
"""

import pytest
import json
import os
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from ai_agent_connector.app.utils.performance_baseline import (
    PerformanceBaselineGenerator,
    BaselineMetric,
    PerformanceBaseline
)

# Import performance_test module
import sys
from pathlib import Path
load_tests_path = Path(__file__).parent.parent / "load_tests"
if load_tests_path.exists():
    sys.path.insert(0, str(load_tests_path.parent))
    try:
        from load_tests.performance_test import (
            PerformanceTester,
            PerformanceMetric,
            PerformanceReport
        )
    except ImportError:
        # Fallback: try direct import
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "performance_test",
                load_tests_path / "performance_test.py"
            )
            if spec and spec.loader:
                performance_test = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(performance_test)
                PerformanceTester = performance_test.PerformanceTester
                PerformanceMetric = performance_test.PerformanceMetric
                PerformanceReport = performance_test.PerformanceReport
            else:
                PerformanceTester = None
                PerformanceMetric = None
                PerformanceReport = None
        except Exception:
            PerformanceTester = None
            PerformanceMetric = None
            PerformanceReport = None
else:
    PerformanceTester = None
    PerformanceMetric = None
    PerformanceReport = None


@pytest.mark.skipif(PerformanceMetric is None, reason="PerformanceMetric not available")
class TestPerformanceMetric:
    """Test PerformanceMetric dataclass"""
    
    def test_performance_metric_creation(self):
        """Test creating a performance metric"""
        metric = PerformanceMetric(
            endpoint="/api/health",
            method="GET",
            status_code=200,
            response_time_ms=50.0,
            timestamp="2024-01-01T12:00:00"
        )
        
        assert metric.endpoint == "/api/health"
        assert metric.method == "GET"
        assert metric.status_code == 200
        assert metric.response_time_ms == 50.0
        assert metric.error is None
    
    def test_performance_metric_with_error(self):
        """Test performance metric with error"""
        metric = PerformanceMetric(
            endpoint="/api/test",
            method="GET",
            status_code=500,
            response_time_ms=100.0,
            timestamp="2024-01-01T12:00:00",
            error="Connection timeout"
        )
        
        assert metric.error == "Connection timeout"
        assert metric.status_code == 500


@pytest.mark.skipif(PerformanceTester is None, reason="PerformanceTester not available")
class TestPerformanceTester:
    """Test PerformanceTester class"""
    
    @pytest.fixture
    def tester(self):
        """Create PerformanceTester instance"""
        return PerformanceTester(base_url="http://localhost:5000")
    
    def test_tester_initialization(self, tester):
        """Test tester initialization"""
        assert tester.base_url == "http://localhost:5000"
        assert tester.session is not None
    
    def test_single_request(self, tester):
        """Test single request execution"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        tester.session = mock_session
        
        metric = tester.single_request("GET", "/api/health")
        
        assert metric.endpoint == "/api/health"
        assert metric.method == "GET"
        assert metric.status_code == 200
        assert metric.response_time_ms >= 0
    
    def test_single_request_with_error(self, tester):
        """Test single request with error"""
        mock_session = Mock()
        mock_session.request.side_effect = Exception("Connection error")
        tester.session = mock_session
        
        metric = tester.single_request("GET", "/api/health")
        
        assert metric.error is not None
        assert metric.status_code == 0
    
    def test_concurrent_requests(self, tester):
        """Test concurrent requests"""
        mock_metric = PerformanceMetric(
            endpoint="/api/health",
            method="GET",
            status_code=200,
            response_time_ms=50.0,
            timestamp=datetime.utcnow().isoformat()
        )
        
        with patch.object(tester, 'single_request', return_value=mock_metric):
            metrics = tester.concurrent_requests(
                "GET",
                "/api/health",
                num_requests=10,
                concurrent=5
            )
            
            assert len(metrics) == 10
            assert all(m.status_code == 200 for m in metrics)
    
    def test_load_test(self, tester):
        """Test load test execution"""
        mock_metric = PerformanceMetric(
            endpoint="/api/health",
            method="GET",
            status_code=200,
            response_time_ms=50.0,
            timestamp=datetime.utcnow().isoformat()
        )
        
        with patch.object(tester, 'single_request', return_value=mock_metric):
            endpoints = [
                {'method': 'GET', 'endpoint': '/api/health'},
                {'method': 'GET', 'endpoint': '/api/agents'}
            ]
            
            report = tester.load_test(
                endpoints=endpoints,
                total_requests=20,
                concurrent_users=10
            )
            
            assert report is not None
            assert report.total_requests == 20
            assert report.concurrent_users == 10
            assert len(report.metrics) == 20
            assert 'summary' in report.summary
    
    def test_calculate_summary(self, tester):
        """Test summary calculation"""
        metrics = [
            PerformanceMetric(
                endpoint="/api/health",
                method="GET",
                status_code=200,
                response_time_ms=50.0,
                timestamp=datetime.utcnow().isoformat()
            ),
            PerformanceMetric(
                endpoint="/api/health",
                method="GET",
                status_code=200,
                response_time_ms=100.0,
                timestamp=datetime.utcnow().isoformat()
            ),
            PerformanceMetric(
                endpoint="/api/health",
                method="GET",
                status_code=500,
                response_time_ms=0.0,
                timestamp=datetime.utcnow().isoformat(),
                error="Error"
            )
        ]
        
        summary = tester._calculate_summary(metrics)
        
        assert summary['total_requests'] == 3
        assert summary['successful_requests'] == 2
        assert summary['failed_requests'] == 1
        assert 'response_time' in summary
        assert summary['response_time']['mean'] == 75.0
    
    def test_save_report(self, tester, tmp_path):
        """Test saving report"""
        report = PerformanceReport(
            test_id="test_123",
            timestamp=datetime.utcnow().isoformat(),
            total_requests=10,
            concurrent_users=5,
            duration_seconds=10.0,
            metrics=[
                PerformanceMetric(
                    endpoint="/api/health",
                    method="GET",
                    status_code=200,
                    response_time_ms=50.0,
                    timestamp=datetime.utcnow().isoformat()
                )
            ],
            summary={'total_requests': 10}
        )
        
        # Change results dir to tmp_path
        original_dir = tester.results_dir if hasattr(tester, 'results_dir') else None
        tester.results_dir = tmp_path
        
        filename = tmp_path / "test_report.json"
        tester.save_report(report, str(filename))
        
        assert filename.exists()
        with open(filename, 'r') as f:
            data = json.load(f)
            assert data['test_id'] == "test_123"


class TestPerformanceBaselineGenerator:
    """Test PerformanceBaselineGenerator"""
    
    @pytest.fixture
    def generator(self, tmp_path):
        """Create baseline generator with temp directory"""
        gen = PerformanceBaselineGenerator(results_dir=str(tmp_path / "results"))
        gen.baselines_dir = tmp_path / "baselines"
        gen.baselines_dir.mkdir(exist_ok=True)
        return gen
    
    @pytest.fixture
    def sample_test_results(self, tmp_path):
        """Create sample test results file"""
        results_file = tmp_path / "results" / "test_results.json"
        results_file.parent.mkdir(exist_ok=True)
        
        data = {
            'test_id': 'test_123',
            'timestamp': datetime.utcnow().isoformat(),
            'total_requests': 100,
            'concurrent_users': 10,
            'duration_seconds': 60.0,
            'metrics': [
                {
                    'endpoint': '/api/health',
                    'method': 'GET',
                    'status_code': 200,
                    'response_time_ms': 50.0,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': None
                },
                {
                    'endpoint': '/api/health',
                    'method': 'GET',
                    'status_code': 200,
                    'response_time_ms': 100.0,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': None
                },
                {
                    'endpoint': '/api/agents',
                    'method': 'GET',
                    'status_code': 200,
                    'response_time_ms': 75.0,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': None
                }
            ],
            'summary': {
                'response_time': {
                    'mean': 75.0,
                    'p95': 100.0,
                    'p99': 100.0
                },
                'error_rate': 0.0
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(data, f)
        
        return str(results_file.name)
    
    def test_generator_initialization(self, generator):
        """Test generator initialization"""
        assert generator is not None
        assert generator.results_dir.exists()
        assert generator.baselines_dir.exists()
    
    def test_load_test_results(self, generator, sample_test_results):
        """Test loading test results"""
        results = generator.load_test_results(sample_test_results)
        
        assert results is not None
        assert results['test_id'] == 'test_123'
        assert len(results['metrics']) == 3
    
    def test_load_test_results_not_found(self, generator):
        """Test loading non-existent test results"""
        with pytest.raises(FileNotFoundError):
            generator.load_test_results("nonexistent.json")
    
    def test_calculate_percentile(self, generator):
        """Test percentile calculation"""
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        p50 = generator.calculate_percentile(data, 0.5)
        p95 = generator.calculate_percentile(data, 0.95)
        p99 = generator.calculate_percentile(data, 0.99)
        
        assert p50 == 50.0
        assert p95 == 95.0
        assert p99 == 99.0
    
    def test_generate_baseline(self, generator, sample_test_results):
        """Test baseline generation"""
        results = generator.load_test_results(sample_test_results)
        baseline = generator.generate_baseline(results, "test_baseline")
        
        assert baseline is not None
        assert baseline.baseline_id == "test_baseline"
        assert len(baseline.metrics) > 0
        assert baseline.summary is not None
        assert len(baseline.recommendations) > 0
    
    def test_generate_recommendations(self, generator):
        """Test recommendation generation"""
        metrics = [
            BaselineMetric(
                endpoint="/api/slow",
                method="GET",
                p50_response_time_ms=500.0,
                p95_response_time_ms=1500.0,
                p99_response_time_ms=2000.0,
                max_response_time_ms=2000.0,
                min_response_time_ms=100.0,
                avg_response_time_ms=800.0,
                requests_per_second=10.0,
                error_rate=0.0,
                sample_size=100
            ),
            BaselineMetric(
                endpoint="/api/error",
                method="GET",
                p50_response_time_ms=50.0,
                p95_response_time_ms=100.0,
                p99_response_time_ms=150.0,
                max_response_time_ms=150.0,
                min_response_time_ms=10.0,
                avg_response_time_ms=60.0,
                requests_per_second=50.0,
                error_rate=0.1,  # 10% error rate
                sample_size=100
            )
        ]
        
        summary = {
            'response_time': {'p95': 1500.0},
            'error_rate': 0.05
        }
        
        recommendations = generator._generate_recommendations(metrics, summary)
        
        assert len(recommendations) > 0
        assert any("slow" in rec.lower() or "response time" in rec.lower() for rec in recommendations)
        assert any("error" in rec.lower() for rec in recommendations)
    
    def test_generate_report(self, generator, sample_test_results):
        """Test report generation"""
        results = generator.load_test_results(sample_test_results)
        baseline = generator.generate_baseline(results, "test_baseline")
        
        report = generator.generate_report(baseline)
        
        assert "Performance Baseline Report" in report
        assert baseline.baseline_id in report
        assert "Overall Summary" in report
        assert "Endpoint Performance" in report
        assert "Recommendations" in report
    
    def test_save_report(self, generator, sample_test_results, tmp_path):
        """Test saving report"""
        results = generator.load_test_results(sample_test_results)
        baseline = generator.generate_baseline(results, "test_baseline")
        
        filename = tmp_path / "test_report.txt"
        generator.save_report(baseline, str(filename))
        
        assert filename.exists()
        content = filename.read_text()
        assert "Performance Baseline Report" in content
    
    def test_get_baseline(self, generator, sample_test_results):
        """Test getting baseline by ID"""
        results = generator.load_test_results(sample_test_results)
        baseline = generator.generate_baseline(results, "test_baseline")
        
        loaded = generator.get_baseline("test_baseline")
        
        assert loaded is not None
        assert loaded.baseline_id == "test_baseline"
        assert len(loaded.metrics) == len(baseline.metrics)
    
    def test_list_baselines(self, generator, sample_test_results):
        """Test listing baselines"""
        results = generator.load_test_results(sample_test_results)
        generator.generate_baseline(results, "baseline_1")
        generator.generate_baseline(results, "baseline_2")
        
        baselines = generator.list_baselines()
        
        assert len(baselines) >= 2
        assert "baseline_1" in baselines
        assert "baseline_2" in baselines


class TestLoadTestingAPI:
    """Test load testing API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        from main import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app.test_client()
    
    def test_get_load_test_info(self, client):
        """Test get load test info endpoint"""
        response = client.get('/api/load-test/info')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'load_testing' in data
        assert 'tools' in data['load_testing']
        assert 'endpoints' in data['load_testing']
    
    def test_list_baselines_endpoint(self, client):
        """Test list baselines endpoint"""
        response = client.get('/api/load-test/baselines')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'baselines' in data
    
    def test_get_baseline_endpoint_not_found(self, client):
        """Test get baseline endpoint with non-existent baseline"""
        response = client.get('/api/load-test/baselines/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_generate_baseline_endpoint_missing_file(self, client):
        """Test generate baseline endpoint with missing file"""
        response = client.post('/api/load-test/baseline', json={
            'test_results_file': 'nonexistent.json'
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_generate_baseline_endpoint_missing_field(self, client):
        """Test generate baseline endpoint with missing required field"""
        response = client.post('/api/load-test/baseline', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestLoadTestingIntegration:
    """Integration tests for load testing"""
    
    @pytest.fixture
    def tmp_results_dir(self, tmp_path):
        """Create temporary results directory"""
        results_dir = tmp_path / "results"
        results_dir.mkdir(exist_ok=True)
        return results_dir
    
    @pytest.fixture
    def sample_results_file(self, tmp_results_dir):
        """Create sample results file"""
        results_file = tmp_results_dir / "test_results.json"
        
        data = {
            'test_id': 'integration_test',
            'timestamp': datetime.utcnow().isoformat(),
            'total_requests': 50,
            'concurrent_users': 10,
            'duration_seconds': 30.0,
            'metrics': [
                {
                    'endpoint': '/api/health',
                    'method': 'GET',
                    'status_code': 200,
                    'response_time_ms': float(i * 10),
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': None
                }
                for i in range(1, 51)
            ],
            'summary': {
                'response_time': {
                    'mean': 250.0,
                    'p95': 475.0,
                    'p99': 490.0
                },
                'error_rate': 0.0
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(data, f)
        
        return str(results_file.name)
    
    def test_full_baseline_workflow(self, tmp_path, sample_results_file):
        """Test complete baseline generation workflow"""
        generator = PerformanceBaselineGenerator(results_dir=str(tmp_path / "results"))
        generator.baselines_dir = tmp_path / "baselines"
        generator.baselines_dir.mkdir(exist_ok=True)
        
        # Load results
        results = generator.load_test_results(sample_results_file)
        assert results is not None
        
        # Generate baseline
        baseline = generator.generate_baseline(results, "integration_baseline")
        assert baseline is not None
        assert len(baseline.metrics) > 0
        
        # Generate report
        report = generator.generate_report(baseline)
        assert len(report) > 0
        
        # Save report
        report_file = tmp_path / "baselines" / "integration_report.txt"
        generator.save_report(baseline, str(report_file))
        assert report_file.exists()
        
        # Load baseline
        loaded = generator.get_baseline("integration_baseline")
        assert loaded is not None
        assert loaded.baseline_id == "integration_baseline"
    
    def test_performance_tester_workflow(self, tmp_path):
        """Test performance tester workflow"""
        tester = PerformanceTester(base_url="http://localhost:5000")
        tester.results_dir = tmp_path
        
        # Mock requests
        import performance_test
        with patch.object(performance_test, 'requests') as mock_requests:
            mock_session_class = mock_requests.Session
            mock_response = Mock()
            mock_response.status_code = 200
            mock_session = Mock()
            mock_session.request.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            # Run load test
            endpoints = [
                {'method': 'GET', 'endpoint': '/api/health'}
            ]
            
            report = tester.load_test(
                endpoints=endpoints,
                total_requests=10,
                concurrent_users=5
            )
            
            assert report is not None
            assert report.total_requests == 10
            
            # Save report
            report_file = tmp_path / "test_report.json"
            tester.save_report(report, str(report_file))
            assert report_file.exists()


@pytest.mark.skipif(PerformanceTester is None or PerformanceMetric is None, reason="PerformanceTester not available")
class TestLoadTestingEdgeCases:
    """Test edge cases for load testing"""
    
    def test_empty_metrics_summary(self):
        """Test summary calculation with empty metrics"""
        tester = PerformanceTester()
        summary = tester._calculate_summary([])
        
        assert summary == {}
    
    def test_all_failed_requests(self):
        """Test summary with all failed requests"""
        tester = PerformanceTester()
        metrics = [
            PerformanceMetric(
                endpoint="/api/test",
                method="GET",
                status_code=0,
                response_time_ms=0.0,
                timestamp=datetime.utcnow().isoformat(),
                error="Error"
            )
            for _ in range(10)
        ]
        
        summary = tester._calculate_summary(metrics)
        
        assert summary['total_requests'] == 10
        assert summary['successful_requests'] == 0
        assert summary['failed_requests'] == 10
        assert summary['error_rate'] == 1.0
    
    def test_percentile_with_single_value(self):
        """Test percentile calculation with single value"""
        generator = PerformanceBaselineGenerator()
        data = [100.0]
        
        p50 = generator.calculate_percentile(data, 0.5)
        assert p50 == 100.0
    
    def test_baseline_with_no_metrics(self, tmp_path):
        """Test baseline generation with no metrics"""
        generator = PerformanceBaselineGenerator(results_dir=str(tmp_path / "results"))
        generator.baselines_dir = tmp_path / "baselines"
        generator.baselines_dir.mkdir(exist_ok=True)
        
        results = {
            'test_id': 'empty_test',
            'timestamp': datetime.utcnow().isoformat(),
            'total_requests': 0,
            'concurrent_users': 0,
            'duration_seconds': 0.0,
            'metrics': [],
            'summary': {}
        }
        
        baseline = generator.generate_baseline(results, "empty_baseline")
        
        assert baseline is not None
        assert len(baseline.metrics) == 0


class TestLoadTestingPerformance:
    """Test performance of load testing utilities"""
    
    def test_percentile_calculation_performance(self):
        """Test percentile calculation performance"""
        generator = PerformanceBaselineGenerator()
        data = list(range(10000))
        
        start = time.time()
        for _ in range(100):
            generator.calculate_percentile(data, 0.95)
        duration = time.time() - start
        
        # Should complete quickly
        assert duration < 1.0
    
    @pytest.mark.skipif(PerformanceTester is None or PerformanceMetric is None, reason="PerformanceTester not available")
    def test_summary_calculation_performance(self):
        """Test summary calculation performance"""
        tester = PerformanceTester()
        metrics = [
            PerformanceMetric(
                endpoint=f"/api/endpoint_{i}",
                method="GET",
                status_code=200,
                response_time_ms=float(i),
                timestamp=datetime.utcnow().isoformat()
            )
            for i in range(1000)
        ]
        
        start = time.time()
        summary = tester._calculate_summary(metrics)
        duration = time.time() - start
        
        # Should complete quickly
        assert duration < 1.0
        assert summary is not None

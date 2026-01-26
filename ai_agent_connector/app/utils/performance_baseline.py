"""
Performance Baseline Report Generator
Generates baseline performance reports from load test results
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class BaselineMetric:
    """Baseline performance metric"""
    endpoint: str
    method: str
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    avg_response_time_ms: float
    requests_per_second: float
    error_rate: float
    sample_size: int


@dataclass
class PerformanceBaseline:
    """Performance baseline report"""
    baseline_id: str
    timestamp: str
    test_duration_seconds: float
    total_requests: int
    concurrent_users: int
    metrics: List[BaselineMetric]
    summary: Dict[str, Any]
    recommendations: List[str]


class PerformanceBaselineGenerator:
    """Generate performance baselines from test results"""
    
    def __init__(self, results_dir: str = "load_test_results"):
        """
        Initialize baseline generator
        
        Args:
            results_dir: Directory containing load test results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.baselines_dir = Path("performance_baselines")
        self.baselines_dir.mkdir(exist_ok=True)
    
    def load_test_results(self, filename: str) -> Dict[str, Any]:
        """Load test results from JSON file"""
        filepath = self.results_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Test results file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_data):
            return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
        return sorted_data[f]
    
    def generate_baseline(
        self,
        test_results: Dict[str, Any],
        baseline_name: str = None
    ) -> PerformanceBaseline:
        """
        Generate baseline from test results
        
        Args:
            test_results: Test results dictionary
            baseline_name: Optional baseline name
            
        Returns:
            PerformanceBaseline
        """
        if baseline_name is None:
            baseline_name = f"baseline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        metrics_data = test_results.get('metrics', [])
        summary = test_results.get('summary', {})
        
        # Group metrics by endpoint
        endpoint_metrics = {}
        for metric in metrics_data:
            endpoint = metric.get('endpoint', 'unknown')
            method = metric.get('method', 'GET')
            key = f"{method} {endpoint}"
            
            if key not in endpoint_metrics:
                endpoint_metrics[key] = {
                    'response_times': [],
                    'errors': 0,
                    'total': 0
                }
            
            endpoint_metrics[key]['total'] += 1
            if metric.get('error'):
                endpoint_metrics[key]['errors'] += 1
            else:
                rt = metric.get('response_time_ms', 0)
                if rt > 0:
                    endpoint_metrics[key]['response_times'].append(rt)
        
        # Calculate baseline metrics
        baseline_metrics = []
        for key, data in endpoint_metrics.items():
            method, endpoint = key.split(' ', 1)
            response_times = data['response_times']
            
            if response_times:
                baseline_metrics.append(BaselineMetric(
                    endpoint=endpoint,
                    method=method,
                    p50_response_time_ms=self.calculate_percentile(response_times, 0.5),
                    p95_response_time_ms=self.calculate_percentile(response_times, 0.95),
                    p99_response_time_ms=self.calculate_percentile(response_times, 0.99),
                    max_response_time_ms=max(response_times),
                    min_response_time_ms=min(response_times),
                    avg_response_time_ms=sum(response_times) / len(response_times),
                    requests_per_second=len(response_times) / (sum(response_times) / 1000) if response_times else 0,
                    error_rate=data['errors'] / data['total'] if data['total'] > 0 else 0,
                    sample_size=data['total']
                ))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(baseline_metrics, summary)
        
        baseline = PerformanceBaseline(
            baseline_id=baseline_name,
            timestamp=datetime.utcnow().isoformat(),
            test_duration_seconds=test_results.get('duration_seconds', 0),
            total_requests=test_results.get('total_requests', 0),
            concurrent_users=test_results.get('concurrent_users', 0),
            metrics=baseline_metrics,
            summary={
                'overall_avg_response_time': summary.get('response_time', {}).get('mean', 0),
                'overall_p95_response_time': summary.get('response_time', {}).get('p95', 0),
                'overall_error_rate': summary.get('error_rate', 0),
                'total_requests_per_second': summary.get('requests_per_second', 0)
            },
            recommendations=recommendations
        )
        
        # Save baseline
        self._save_baseline(baseline)
        
        return baseline
    
    def _generate_recommendations(
        self,
        metrics: List[BaselineMetric],
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Check response times
        for metric in metrics:
            if metric.p95_response_time_ms > 1000:
                recommendations.append(
                    f"{metric.method} {metric.endpoint}: P95 response time ({metric.p95_response_time_ms:.0f}ms) "
                    f"exceeds 1 second. Consider optimization."
                )
            elif metric.p95_response_time_ms > 500:
                recommendations.append(
                    f"{metric.method} {metric.endpoint}: P95 response time ({metric.p95_response_time_ms:.0f}ms) "
                    f"is high. Monitor for degradation."
                )
        
        # Check error rates
        for metric in metrics:
            if metric.error_rate > 0.05:  # 5% error rate
                recommendations.append(
                    f"{metric.method} {metric.endpoint}: Error rate ({metric.error_rate:.1%}) is high. "
                    f"Investigate failures."
                )
        
        # Overall recommendations
        overall_error_rate = summary.get('error_rate', 0)
        if overall_error_rate > 0.01:  # 1% overall error rate
            recommendations.append(
                f"Overall error rate ({overall_error_rate:.1%}) exceeds 1%. Review system health."
            )
        
        overall_p95 = summary.get('response_time', {}).get('p95', 0)
        if overall_p95 > 2000:
            recommendations.append(
                f"Overall P95 response time ({overall_p95:.0f}ms) exceeds 2 seconds. "
                f"Consider scaling or optimization."
            )
        
        if not recommendations:
            recommendations.append("Performance metrics are within acceptable ranges.")
        
        return recommendations
    
    def _save_baseline(self, baseline: PerformanceBaseline):
        """Save baseline to file"""
        filename = f"{baseline.baseline_id}.json"
        filepath = self.baselines_dir / filename
        
        data = {
            'baseline_id': baseline.baseline_id,
            'timestamp': baseline.timestamp,
            'test_duration_seconds': baseline.test_duration_seconds,
            'total_requests': baseline.total_requests,
            'concurrent_users': baseline.concurrent_users,
            'summary': baseline.summary,
            'recommendations': baseline.recommendations,
            'metrics': [
                {
                    'endpoint': m.endpoint,
                    'method': m.method,
                    'p50_response_time_ms': m.p50_response_time_ms,
                    'p95_response_time_ms': m.p95_response_time_ms,
                    'p99_response_time_ms': m.p99_response_time_ms,
                    'max_response_time_ms': m.max_response_time_ms,
                    'min_response_time_ms': m.min_response_time_ms,
                    'avg_response_time_ms': m.avg_response_time_ms,
                    'requests_per_second': m.requests_per_second,
                    'error_rate': m.error_rate,
                    'sample_size': m.sample_size
                }
                for m in baseline.metrics
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Baseline saved to {filepath}")
    
    def generate_report(self, baseline: PerformanceBaseline) -> str:
        """Generate human-readable report"""
        report = []
        report.append("=" * 80)
        report.append("Performance Baseline Report")
        report.append("=" * 80)
        report.append(f"Baseline ID: {baseline.baseline_id}")
        report.append(f"Generated: {baseline.timestamp}")
        report.append(f"Test Duration: {baseline.test_duration_seconds:.2f} seconds")
        report.append(f"Total Requests: {baseline.total_requests:,}")
        report.append(f"Concurrent Users: {baseline.concurrent_users}")
        report.append("")
        
        report.append("Overall Summary")
        report.append("-" * 80)
        summary = baseline.summary
        report.append(f"Average Response Time: {summary.get('overall_avg_response_time', 0):.2f} ms")
        report.append(f"P95 Response Time: {summary.get('overall_p95_response_time', 0):.2f} ms")
        report.append(f"Error Rate: {summary.get('overall_error_rate', 0):.2%}")
        report.append(f"Requests per Second: {summary.get('total_requests_per_second', 0):.2f}")
        report.append("")
        
        report.append("Endpoint Performance")
        report.append("-" * 80)
        report.append(f"{'Method':<8} {'Endpoint':<40} {'P50':<10} {'P95':<10} {'P99':<10} {'RPS':<10} {'Errors':<10}")
        report.append("-" * 80)
        
        for metric in sorted(baseline.metrics, key=lambda x: x.p95_response_time_ms, reverse=True):
            report.append(
                f"{metric.method:<8} {metric.endpoint[:38]:<40} "
                f"{metric.p50_response_time_ms:>8.0f} {metric.p95_response_time_ms:>8.0f} "
                f"{metric.p99_response_time_ms:>8.0f} {metric.requests_per_second:>8.1f} "
                f"{metric.error_rate:>8.1%}"
            )
        
        report.append("")
        report.append("Recommendations")
        report.append("-" * 80)
        for i, rec in enumerate(baseline.recommendations, 1):
            report.append(f"{i}. {rec}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, baseline: PerformanceBaseline, filename: str = None):
        """Save human-readable report to file"""
        if filename is None:
            filename = f"{baseline.baseline_id}_report.txt"
        
        filepath = self.baselines_dir / filename
        report_text = self.generate_report(baseline)
        
        with open(filepath, 'w') as f:
            f.write(report_text)
        
        print(f"Report saved to {filepath}")
        return filepath
    
    def get_baseline(self, baseline_id: str) -> Optional[PerformanceBaseline]:
        """Load baseline by ID"""
        filepath = self.baselines_dir / f"{baseline_id}.json"
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return PerformanceBaseline(
            baseline_id=data['baseline_id'],
            timestamp=data['timestamp'],
            test_duration_seconds=data['test_duration_seconds'],
            total_requests=data['total_requests'],
            concurrent_users=data['concurrent_users'],
            metrics=[
                BaselineMetric(**m) for m in data['metrics']
            ],
            summary=data['summary'],
            recommendations=data['recommendations']
        )
    
    def list_baselines(self) -> List[str]:
        """List all baseline IDs"""
        return [
            f.stem for f in self.baselines_dir.glob("*.json")
            if not f.name.endswith("_report.txt")
        ]

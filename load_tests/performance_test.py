"""
Performance testing script using pytest-benchmark
Tests individual endpoint performance
"""

import pytest
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PerformanceMetric:
    """Performance metric for a single request"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: str
    error: str = None


@dataclass
class PerformanceReport:
    """Performance test report"""
    test_id: str
    timestamp: str
    total_requests: int
    concurrent_users: int
    duration_seconds: float
    metrics: List[PerformanceMetric]
    summary: Dict[str, Any]


class PerformanceTester:
    """Performance testing utility"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize performance tester
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def single_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> PerformanceMetric:
        """
        Make a single request and measure performance
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            PerformanceMetric
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        error = None
        status_code = 0
        
        try:
            response = self.session.request(method, url, **kwargs)
            status_code = response.status_code
        except Exception as e:
            error = str(e)
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return PerformanceMetric(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time,
            timestamp=datetime.utcnow().isoformat(),
            error=error
        )
    
    def concurrent_requests(
        self,
        method: str,
        endpoint: str,
        num_requests: int,
        concurrent: int = 10,
        **kwargs
    ) -> List[PerformanceMetric]:
        """
        Make concurrent requests
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            num_requests: Total number of requests
            concurrent: Number of concurrent requests
            **kwargs: Additional request arguments
            
        Returns:
            List of PerformanceMetric
        """
        metrics = []
        
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [
                executor.submit(self.single_request, method, endpoint, **kwargs)
                for _ in range(num_requests)
            ]
            
            for future in as_completed(futures):
                try:
                    metric = future.result()
                    metrics.append(metric)
                except Exception as e:
                    metrics.append(PerformanceMetric(
                        endpoint=endpoint,
                        method=method,
                        status_code=0,
                        response_time_ms=0.0,
                        timestamp=datetime.utcnow().isoformat(),
                        error=str(e)
                    ))
        
        return metrics
    
    def load_test(
        self,
        endpoints: List[Dict[str, Any]],
        total_requests: int = 1000,
        concurrent_users: int = 100
    ) -> PerformanceReport:
        """
        Run load test on multiple endpoints
        
        Args:
            endpoints: List of endpoint configurations
            total_requests: Total number of requests
            concurrent_users: Number of concurrent users
            
        Returns:
            PerformanceReport
        """
        test_id = f"load_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        all_metrics = []
        
        # Distribute requests across endpoints
        requests_per_endpoint = total_requests // len(endpoints)
        remaining = total_requests % len(endpoints)
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for i, endpoint_config in enumerate(endpoints):
                num_requests = requests_per_endpoint + (1 if i < remaining else 0)
                method = endpoint_config.get('method', 'GET')
                endpoint = endpoint_config.get('endpoint')
                kwargs = endpoint_config.get('kwargs', {})
                
                # Submit concurrent requests for this endpoint
                for _ in range(num_requests):
                    future = executor.submit(
                        self.single_request,
                        method,
                        endpoint,
                        **kwargs
                    )
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    metric = future.result()
                    all_metrics.append(metric)
                except Exception as e:
                    all_metrics.append(PerformanceMetric(
                        endpoint="unknown",
                        method="GET",
                        status_code=0,
                        response_time_ms=0.0,
                        timestamp=datetime.utcnow().isoformat(),
                        error=str(e)
                    ))
        
        duration = time.time() - start_time
        
        # Calculate summary
        summary = self._calculate_summary(all_metrics)
        
        return PerformanceReport(
            test_id=test_id,
            timestamp=datetime.utcnow().isoformat(),
            total_requests=len(all_metrics),
            concurrent_users=concurrent_users,
            duration_seconds=duration,
            metrics=all_metrics,
            summary=summary
        )
    
    def _calculate_summary(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate performance summary statistics"""
        if not metrics:
            return {}
        
        response_times = [m.response_time_ms for m in metrics if m.error is None]
        status_codes = [m.status_code for m in metrics]
        errors = [m for m in metrics if m.error is not None]
        
        if not response_times:
            return {
                'total_requests': len(metrics),
                'errors': len(errors),
                'error_rate': 1.0
            }
        
        response_times.sort()
        
        # Calculate percentiles
        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + c * (data[f + 1] - data[f])
            return data[f]
        
        summary = {
            'total_requests': len(metrics),
            'successful_requests': len(response_times),
            'failed_requests': len(errors),
            'error_rate': len(errors) / len(metrics) if metrics else 0,
            'response_time': {
                'min': min(response_times),
                'max': max(response_times),
                'mean': sum(response_times) / len(response_times),
                'median': percentile(response_times, 0.5),
                'p95': percentile(response_times, 0.95),
                'p99': percentile(response_times, 0.99)
            },
            'status_codes': {
                code: status_codes.count(code)
                for code in set(status_codes)
            },
            'requests_per_second': len(metrics) / (sum(response_times) / 1000) if response_times else 0
        }
        
        # Group by endpoint
        endpoint_stats = {}
        for metric in metrics:
            if metric.endpoint not in endpoint_stats:
                endpoint_stats[metric.endpoint] = {
                    'count': 0,
                    'response_times': [],
                    'errors': 0
                }
            
            endpoint_stats[metric.endpoint]['count'] += 1
            if metric.error:
                endpoint_stats[metric.endpoint]['errors'] += 1
            else:
                endpoint_stats[metric.endpoint]['response_times'].append(metric.response_time_ms)
        
        # Calculate endpoint averages
        for endpoint, stats in endpoint_stats.items():
            if stats['response_times']:
                stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
                stats['min_response_time'] = min(stats['response_times'])
                stats['max_response_time'] = max(stats['response_times'])
            else:
                stats['avg_response_time'] = 0
                stats['min_response_time'] = 0
                stats['max_response_time'] = 0
        
        summary['endpoints'] = endpoint_stats
        
        return summary
    
    def save_report(self, report: PerformanceReport, filename: str = None):
        """Save performance report to JSON file"""
        if filename is None:
            filename = f"performance_report_{report.test_id}.json"
        
        data = {
            'test_id': report.test_id,
            'timestamp': report.timestamp,
            'total_requests': report.total_requests,
            'concurrent_users': report.concurrent_users,
            'duration_seconds': report.duration_seconds,
            'summary': report.summary,
            'metrics': [
                {
                    'endpoint': m.endpoint,
                    'method': m.method,
                    'status_code': m.status_code,
                    'response_time_ms': m.response_time_ms,
                    'timestamp': m.timestamp,
                    'error': m.error
                }
                for m in report.metrics[:1000]  # Limit to first 1000 for file size
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Performance report saved to {filename}")


def run_load_test(
    base_url: str = "http://localhost:5000",
    total_requests: int = 1000,
    concurrent_users: int = 100
):
    """
    Run load test
    
    Args:
        base_url: Base URL of the API
        total_requests: Total number of requests
        concurrent_users: Number of concurrent users
    """
    tester = PerformanceTester(base_url)
    
    # Define endpoints to test
    endpoints = [
        {'method': 'GET', 'endpoint': '/api/health'},
        {'method': 'GET', 'endpoint': '/api/agents'},
        {'method': 'POST', 'endpoint': '/api/agents/register', 'kwargs': {
            'json': {
                'agent_id': f'test_agent_{i}',
                'agent_credentials': {'api_key': 'key', 'api_secret': 'secret'},
                'database': {'host': 'localhost', 'database': 'test'}
            }
        } for i in range(10)},
    ]
    
    # Flatten endpoints
    flat_endpoints = []
    for ep in endpoints:
        if 'kwargs' in ep and isinstance(ep['kwargs'], list):
            for kw in ep['kwargs']:
                flat_endpoints.append({
                    'method': ep['method'],
                    'endpoint': ep['endpoint'],
                    'kwargs': kw
                })
        else:
            flat_endpoints.append(ep)
    
    print(f"Running load test: {total_requests} requests with {concurrent_users} concurrent users")
    print(f"Target: {base_url}")
    
    report = tester.load_test(
        endpoints=flat_endpoints[:10],  # Limit to 10 unique endpoints
        total_requests=total_requests,
        concurrent_users=concurrent_users
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("Performance Test Summary")
    print("=" * 60)
    print(f"Test ID: {report.test_id}")
    print(f"Duration: {report.duration_seconds:.2f} seconds")
    print(f"Total Requests: {report.total_requests}")
    print(f"Successful: {report.summary.get('successful_requests', 0)}")
    print(f"Failed: {report.summary.get('failed_requests', 0)}")
    print(f"Error Rate: {report.summary.get('error_rate', 0):.2%}")
    
    if 'response_time' in report.summary:
        rt = report.summary['response_time']
        print(f"\nResponse Times (ms):")
        print(f"  Min: {rt.get('min', 0):.2f}")
        print(f"  Max: {rt.get('max', 0):.2f}")
        print(f"  Mean: {rt.get('mean', 0):.2f}")
        print(f"  Median: {rt.get('median', 0):.2f}")
        print(f"  P95: {rt.get('p95', 0):.2f}")
        print(f"  P99: {rt.get('p99', 0):.2f}")
    
    print(f"\nRequests per Second: {report.summary.get('requests_per_second', 0):.2f}")
    
    # Save report
    tester.save_report(report)
    
    return report


if __name__ == '__main__':
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    total_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    concurrent_users = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    run_load_test(base_url, total_requests, concurrent_users)

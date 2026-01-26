"""
Performance Benchmark for Multi-Tenant MCP Connection Manager
Tests performance with 100 tenants and 1000 requests
"""

import time
import json
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from tenant_mcp_manager import TenantMCPManager
from tenant_credentials import TenantCredentialVault


def create_test_configs(config_dir: Path, num_tenants: int = 100):
    """Create test tenant configuration files"""
    config_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(1, num_tenants + 1):
        tenant_id = f"tenant_{i:03d}"
        config = {
            "tenant_id": tenant_id,
            "db_host": f"db-{i}.example.com",
            "db_name": f"db_{i}",
            "db_user": f"user_{i}",
            "db_password": f"pass_{i}",
            "quotas": {
                "max_queries_per_hour": 1000
            }
        }
        
        config_file = config_dir / f"{tenant_id}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)


def benchmark_get_server(manager: TenantMCPManager, tenant_id: str, iterations: int = 10):
    """Benchmark getting server for a tenant"""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        server = manager.get_or_create_server(tenant_id)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    return {
        "tenant_id": tenant_id,
        "times": times,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0
    }


def run_benchmark():
    """Run comprehensive benchmark"""
    print("=" * 70)
    print("MULTI-TENANT MCP CONNECTION MANAGER BENCHMARK")
    print("=" * 70)
    print()
    
    # Create temporary config directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "tenant_configs"
    
    try:
        # Create 100 tenant configs
        print("Creating 100 tenant configurations...")
        create_test_configs(config_dir, num_tenants=100)
        print(f"✓ Created 100 tenant configs in {config_dir}")
        print()
        
        # Create manager
        print("Initializing TenantMCPManager...")
        manager = TenantMCPManager(
            config_dir=str(config_dir),
            max_instances_per_tenant=5,
            idle_timeout_seconds=600,
            cleanup_interval_seconds=300
        )
        print("✓ Manager initialized")
        print()
        
        # Benchmark 1: Sequential access (warmup and measure)
        print("Benchmark 1: Sequential Server Access (10 tenants, 10 iterations each)")
        print("-" * 70)
        sequential_results = []
        for i in range(1, 11):
            tenant_id = f"tenant_{i:03d}"
            result = benchmark_get_server(manager, tenant_id, iterations=10)
            sequential_results.append(result)
            print(f"  {tenant_id}: mean={result['mean']:.2f}ms, "
                  f"median={result['median']:.2f}ms, "
                  f"min={result['min']:.2f}ms, max={result['max']:.2f}ms")
        
        all_times = [t for r in sequential_results for t in r['times']]
        print(f"\n  Overall: mean={statistics.mean(all_times):.2f}ms, "
              f"median={statistics.median(all_times):.2f}ms")
        print()
        
        # Benchmark 2: Concurrent access (100 tenants, 1000 requests)
        print("Benchmark 2: Concurrent Access (100 tenants, 1000 requests)")
        print("-" * 70)
        
        def concurrent_request(tenant_id: str):
            start = time.perf_counter()
            server = manager.get_or_create_server(tenant_id)
            end = time.perf_counter()
            return (end - start) * 1000  # milliseconds
        
        # Generate 1000 requests across 100 tenants
        tenant_ids = [f"tenant_{i:03d}" for i in range(1, 101)]
        requests = []
        for _ in range(1000):
            import random
            tenant_id = random.choice(tenant_ids)
            requests.append(tenant_id)
        
        # Execute concurrently (10 threads)
        concurrent_times = []
        start_total = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(concurrent_request, tenant_id): tenant_id 
                      for tenant_id in requests}
            
            for future in as_completed(futures):
                try:
                    elapsed = future.result()
                    concurrent_times.append(elapsed)
                except Exception as e:
                    print(f"  Error: {e}")
        
        end_total = time.perf_counter()
        total_time = (end_total - start_total) * 1000
        
        print(f"  Total requests: {len(requests)}")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Requests per second: {len(requests) / (total_time / 1000):.2f}")
        print(f"  Mean: {statistics.mean(concurrent_times):.2f}ms")
        print(f"  Median: {statistics.median(concurrent_times):.2f}ms")
        print(f"  Min: {min(concurrent_times):.2f}ms")
        print(f"  Max: {max(concurrent_times):.2f}ms")
        print(f"  P95: {sorted(concurrent_times)[int(len(concurrent_times) * 0.95)]:.2f}ms")
        print(f"  P99: {sorted(concurrent_times)[int(len(concurrent_times) * 0.99)]:.2f}ms")
        print()
        
        # Benchmark 3: Pool statistics
        print("Benchmark 3: Pool Statistics")
        print("-" * 70)
        stats = manager.get_pool_stats()
        print(f"  Total acquired: {stats['total_acquired']}")
        print(f"  Total created: {stats['total_created']}")
        print(f"  Current pool size: {stats['current_pool_size']}")
        print(f"  Active tenants: {stats['active_tenants']}")
        print(f"  Instances per tenant (sample):")
        for tenant_id, count in list(stats['instances_per_tenant'].items())[:5]:
            print(f"    {tenant_id}: {count}")
        print()
        
        # Benchmark 4: Instance reuse
        print("Benchmark 4: Instance Reuse Test")
        print("-" * 70)
        reuse_times_first = []
        reuse_times_second = []
        
        for i in range(1, 11):
            tenant_id = f"tenant_{i:03d}"
            
            # First access
            start = time.perf_counter()
            server1 = manager.get_or_create_server(tenant_id)
            end = time.perf_counter()
            reuse_times_first.append((end - start) * 1000)
            
            # Second access (should reuse)
            start = time.perf_counter()
            server2 = manager.get_or_create_server(tenant_id)
            end = time.perf_counter()
            reuse_times_second.append((end - start) * 1000)
            
            # Verify reuse
            assert server1 is server2, "Server instances should be reused"
        
        print(f"  First access mean: {statistics.mean(reuse_times_first):.2f}ms")
        print(f"  Second access mean (reused): {statistics.mean(reuse_times_second):.2f}ms")
        print(f"  Reuse speedup: {statistics.mean(reuse_times_first) / statistics.mean(reuse_times_second):.2f}x")
        print()
        
        # Summary
        print("=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        print(f"✓ 100 tenants configured")
        print(f"✓ {len(requests)} concurrent requests processed")
        print(f"✓ {stats['total_created']} server instances created")
        print(f"✓ {stats['current_pool_size']} instances in pool")
        print(f"✓ Average response time: {statistics.mean(concurrent_times):.2f}ms")
        print(f"✓ Throughput: {len(requests) / (total_time / 1000):.2f} req/s")
        print("=" * 70)
        
        # Cleanup
        manager.shutdown()
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    run_benchmark()


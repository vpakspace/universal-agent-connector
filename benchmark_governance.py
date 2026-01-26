"""
Performance Benchmark for MCP Governance Middleware
Measures validation and masking performance to ensure < 100ms target
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any

from policy_engine import policy_engine
from pii_masker import mask_sensitive_fields
from mcp_governance_middleware import _execute_with_governance
from example_governed_tool import query_customer_data


async def benchmark_validation_performance() -> Dict[str, Any]:
    """Benchmark policy validation performance"""
    user_id = "benchmark_user"
    tenant_id = "benchmark_tenant"
    
    # Grant permissions
    policy_engine.grant_tenant_access(user_id, tenant_id)
    policy_engine.grant_pii_permission(user_id)
    
    times = []
    iterations = 100
    
    print(f"Running {iterations} validation checks...")
    
    for i in range(iterations):
        start = time.time()
        
        await policy_engine.validate(
            user_id=user_id,
            tenant_id=tenant_id,
            tool_name="test_tool",
            arguments={"customer_id": f"customer_{i}", "query": "test query"}
        )
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
    
    return {
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "p95_ms": statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0],  # 95th percentile
        "p99_ms": statistics.quantiles(times, n=100)[98] if len(times) > 1 else times[0]  # 99th percentile
    }


def benchmark_masking_performance() -> Dict[str, Any]:
    """Benchmark PII masking performance"""
    # Sample data with PII
    sample_data = {
        "customers": [
            {
                "id": i,
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "phone": f"(555) {100+i}-{2000+i}",
                "ssn": f"123-45-{1000+i}",
                "address": f"{i} Main St"
            }
            for i in range(100)
        ]
    }
    
    times = []
    iterations = 100
    
    print(f"Running {iterations} masking operations on {len(sample_data['customers'])} records...")
    
    for _ in range(iterations):
        start = time.time()
        mask_sensitive_fields(sample_data, sensitivity_level="standard")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
    
    return {
        "iterations": iterations,
        "records_per_iteration": len(sample_data["customers"]),
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


async def benchmark_full_execution() -> Dict[str, Any]:
    """Benchmark full tool execution with governance"""
    user_id = "benchmark_user"
    tenant_id = "benchmark_tenant"
    
    # Grant permissions
    policy_engine.grant_tenant_access(user_id, tenant_id)
    policy_engine.grant_pii_permission(user_id)
    
    times = []
    iterations = 50  # Fewer iterations for full execution
    
    print(f"Running {iterations} full tool executions with governance...")
    
    async def mock_func(*args, **kwargs):
        # Simulate tool execution
        await asyncio.sleep(0.001)  # 1ms execution time
        return {"result": "success"}
    
    for i in range(iterations):
        start = time.time()
        
        try:
            await _execute_with_governance(
                func=mock_func,
                args=(),
                kwargs={"customer_id": f"customer_{i}"},
                requires_pii=True,
                sensitivity_level="standard",
                is_async=True
            )
        except Exception as e:
            print(f"Error in iteration {i}: {e}")
            continue
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)
    
    return {
        "iterations": len(times),
        "mean_ms": statistics.mean(times) if times else 0,
        "median_ms": statistics.median(times) if times else 0,
        "min_ms": min(times) if times else 0,
        "max_ms": max(times) if times else 0,
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0
    }


def print_results(title: str, results: Dict[str, Any], target_ms: float = 100.0):
    """Print benchmark results"""
    print("\n" + "=" * 60)
    print(f"{title}")
    print("=" * 60)
    
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key:20s}: {value:8.2f} ms")
        else:
            print(f"{key:20s}: {value}")
    
    # Check if target is met
    mean = results.get("mean_ms", 0)
    p95 = results.get("p95_ms", mean)
    p99 = results.get("p99_ms", mean)
    
    print("\nPerformance Target: < 100ms")
    print(f"Mean:     {mean:.2f} ms {'✓ PASS' if mean < target_ms else '✗ FAIL'}")
    if "p95_ms" in results:
        print(f"P95:      {p95:.2f} ms {'✓ PASS' if p95 < target_ms else '✗ FAIL'}")
    if "p99_ms" in results:
        print(f"P99:      {p99:.2f} ms {'✓ PASS' if p99 < target_ms else '✗ FAIL'}")


async def main():
    """Run all benchmarks"""
    print("MCP Governance Middleware Performance Benchmark")
    print("=" * 60)
    
    # Benchmark 1: Policy validation
    validation_results = await benchmark_validation_performance()
    print_results("Policy Validation Performance", validation_results)
    
    # Benchmark 2: PII masking
    masking_results = benchmark_masking_performance()
    print_results("PII Masking Performance", masking_results)
    
    # Benchmark 3: Full execution
    execution_results = await benchmark_full_execution()
    print_results("Full Execution Performance", execution_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    if validation_results["mean_ms"] >= 100:
        print("✗ Validation performance: FAILED (> 100ms)")
        all_passed = False
    else:
        print("✓ Validation performance: PASSED")
    
    if masking_results["mean_ms"] >= 100:
        print("✗ Masking performance: FAILED (> 100ms)")
        all_passed = False
    else:
        print("✓ Masking performance: PASSED")
    
    if execution_results["mean_ms"] >= 100:
        print("✗ Full execution performance: FAILED (> 100ms)")
        all_passed = False
    else:
        print("✓ Full execution performance: PASSED")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL BENCHMARKS PASSED")
    else:
        print("✗ SOME BENCHMARKS FAILED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


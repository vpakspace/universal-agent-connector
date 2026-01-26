"""
Simple test runner for JAG-001 tests (bypasses pytest.ini coverage requirements)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import pytest and run tests
if __name__ == "__main__":
    import pytest
    
    # Run tests with minimal options (no coverage)
    exit_code = pytest.main([
        "tests/test_jaguar_problem.py",
        "-v",
        "--tb=short",
        "-W", "ignore::DeprecationWarning"
    ])
    
    sys.exit(exit_code)


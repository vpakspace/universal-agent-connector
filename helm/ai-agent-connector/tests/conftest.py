"""
Pytest configuration for Helm chart tests
"""
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def chart_root():
    """Get chart root directory"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def templates_dir(chart_root):
    """Get templates directory"""
    return chart_root / "templates"


@pytest.fixture(scope="session")
def values_file(chart_root):
    """Get default values file"""
    return chart_root / "values.yaml"

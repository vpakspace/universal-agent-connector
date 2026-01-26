"""
Test Helm chart structure and basic validation
"""
import os
import yaml
import pytest
from pathlib import Path


class TestChartStructure:
    """Test Helm chart structure and metadata"""
    
    @pytest.fixture
    def chart_dir(self):
        """Get chart directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def chart_yaml(self, chart_dir):
        """Load Chart.yaml"""
        chart_file = chart_dir / "Chart.yaml"
        assert chart_file.exists(), "Chart.yaml not found"
        with open(chart_file, 'r') as f:
            return yaml.safe_load(f)
    
    def test_chart_yaml_exists(self, chart_dir):
        """Test Chart.yaml exists"""
        chart_file = chart_dir / "Chart.yaml"
        assert chart_file.exists(), "Chart.yaml must exist"
    
    def test_chart_yaml_structure(self, chart_yaml):
        """Test Chart.yaml has required fields"""
        required_fields = ['apiVersion', 'name', 'description', 'type', 'version']
        for field in required_fields:
            assert field in chart_yaml, f"Chart.yaml missing required field: {field}"
    
    def test_chart_version(self, chart_yaml):
        """Test chart version is valid"""
        version = chart_yaml.get('version')
        assert version is not None, "Chart version must be set"
        assert isinstance(version, str), "Chart version must be a string"
        # Version should be semver format
        parts = version.split('.')
        assert len(parts) >= 2, "Chart version should be in semver format"
    
    def test_values_yaml_exists(self, chart_dir):
        """Test values.yaml exists"""
        values_file = chart_dir / "values.yaml"
        assert values_file.exists(), "values.yaml must exist"
    
    def test_values_yaml_valid(self, chart_dir):
        """Test values.yaml is valid YAML"""
        values_file = chart_dir / "values.yaml"
        with open(values_file, 'r') as f:
            values = yaml.safe_load(f)
        assert values is not None, "values.yaml must be valid YAML"
        assert isinstance(values, dict), "values.yaml must be a dictionary"
    
    def test_templates_directory_exists(self, chart_dir):
        """Test templates directory exists"""
        templates_dir = chart_dir / "templates"
        assert templates_dir.exists(), "templates directory must exist"
        assert templates_dir.is_dir(), "templates must be a directory"
    
    def test_required_templates_exist(self, chart_dir):
        """Test required template files exist"""
        templates_dir = chart_dir / "templates"
        required_templates = [
            'deployment.yaml',
            'service.yaml',
            '_helpers.tpl'
        ]
        for template in required_templates:
            template_file = templates_dir / template
            assert template_file.exists(), f"Required template {template} not found"
    
    def test_helpers_template_exists(self, chart_dir):
        """Test _helpers.tpl exists"""
        helpers_file = chart_dir / "templates" / "_helpers.tpl"
        assert helpers_file.exists(), "_helpers.tpl must exist"
    
    def test_helmignore_exists(self, chart_dir):
        """Test .helmignore exists"""
        helmignore_file = chart_dir / ".helmignore"
        assert helmignore_file.exists(), ".helmignore should exist"
    
    def test_readme_exists(self, chart_dir):
        """Test README.md exists"""
        readme_file = chart_dir / "README.md"
        assert readme_file.exists(), "README.md should exist for documentation"

"""
Test auto-scaling configuration in Helm chart
"""
import yaml
import pytest
from pathlib import Path


class TestAutoscaling:
    """Test HorizontalPodAutoscaler configuration"""
    
    @pytest.fixture
    def chart_dir(self):
        """Get chart directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def default_values(self, chart_dir):
        """Load default values"""
        values_file = chart_dir / "values.yaml"
        with open(values_file, 'r') as f:
            return yaml.safe_load(f)
    
    @pytest.fixture
    def production_values(self, chart_dir):
        """Load production values"""
        values_file = chart_dir / "values-production.yaml"
        if values_file.exists():
            with open(values_file, 'r') as f:
                return yaml.safe_load(f)
        return None
    
    def test_autoscaling_configuration_exists(self, default_values):
        """Test autoscaling configuration exists"""
        assert 'autoscaling' in default_values, "autoscaling configuration must exist"
        autoscaling = default_values['autoscaling']
        assert 'enabled' in autoscaling, "autoscaling.enabled must exist"
        assert isinstance(autoscaling['enabled'], bool), "autoscaling.enabled must be boolean"
    
    def test_autoscaling_min_max_replicas(self, default_values):
        """Test min and max replicas are configured correctly"""
        autoscaling = default_values.get('autoscaling', {})
        if autoscaling.get('enabled'):
            assert 'minReplicas' in autoscaling, "minReplicas must be set when autoscaling enabled"
            assert 'maxReplicas' in autoscaling, "maxReplicas must be set when autoscaling enabled"
            
            min_replicas = autoscaling['minReplicas']
            max_replicas = autoscaling['maxReplicas']
            
            assert isinstance(min_replicas, int), "minReplicas must be integer"
            assert isinstance(max_replicas, int), "maxReplicas must be integer"
            assert min_replicas > 0, "minReplicas must be positive"
            assert max_replicas > 0, "maxReplicas must be positive"
            assert min_replicas <= max_replicas, "minReplicas must be <= maxReplicas"
    
    def test_autoscaling_targets_configured(self, default_values):
        """Test autoscaling targets are configured"""
        autoscaling = default_values.get('autoscaling', {})
        if autoscaling.get('enabled'):
            # At least one target should be configured
            has_cpu_target = 'targetCPUUtilizationPercentage' in autoscaling
            has_memory_target = 'targetMemoryUtilizationPercentage' in autoscaling
            
            assert has_cpu_target or has_memory_target, \
                "At least one autoscaling target (CPU or memory) must be configured"
            
            if has_cpu_target:
                cpu_target = autoscaling['targetCPUUtilizationPercentage']
                assert isinstance(cpu_target, int), "CPU target must be integer"
                assert 1 <= cpu_target <= 100, "CPU target must be between 1 and 100"
            
            if has_memory_target:
                memory_target = autoscaling['targetMemoryUtilizationPercentage']
                assert isinstance(memory_target, int), "Memory target must be integer"
                assert 1 <= memory_target <= 100, "Memory target must be between 1 and 100"
    
    def test_production_autoscaling_enabled(self, production_values):
        """Test production values have autoscaling enabled"""
        if production_values:
            autoscaling = production_values.get('autoscaling', {})
            if autoscaling.get('enabled'):
                assert autoscaling.get('minReplicas', 0) >= 2, \
                    "Production should have at least 2 minimum replicas"
                assert autoscaling.get('maxReplicas', 0) >= autoscaling.get('minReplicas', 0), \
                    "Production maxReplicas should be >= minReplicas"
    
    def test_autoscaling_behavior_optional(self, default_values):
        """Test autoscaling behavior is optional but valid if present"""
        autoscaling = default_values.get('autoscaling', {})
        if 'behavior' in autoscaling:
            behavior = autoscaling['behavior']
            assert isinstance(behavior, dict), "behavior must be a dictionary"
            
            # If scaleDown is present, validate it
            if 'scaleDown' in behavior:
                scale_down = behavior['scaleDown']
                if 'stabilizationWindowSeconds' in scale_down:
                    assert scale_down['stabilizationWindowSeconds'] >= 0, \
                        "stabilizationWindowSeconds must be non-negative"
            
            # If scaleUp is present, validate it
            if 'scaleUp' in behavior:
                scale_up = behavior['scaleUp']
                if 'stabilizationWindowSeconds' in scale_up:
                    assert scale_up['stabilizationWindowSeconds'] >= 0, \
                        "stabilizationWindowSeconds must be non-negative"

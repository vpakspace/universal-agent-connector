"""
Test health check configuration in Helm chart
"""
import yaml
import pytest
from pathlib import Path


class TestHealthChecks:
    """Test health check probe configuration"""
    
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
    
    def test_liveness_probe_configured(self, default_values):
        """Test liveness probe is configured"""
        health_check = default_values.get('healthCheck', {})
        liveness = health_check.get('livenessProbe', {})
        
        assert liveness.get('enabled', False), "Liveness probe should be enabled by default"
        assert liveness.get('path') == '/api/health', "Liveness probe should use /api/health"
        assert liveness.get('initialDelaySeconds', 0) >= 0, "Initial delay should be non-negative"
        assert liveness.get('periodSeconds', 0) > 0, "Period should be positive"
        assert liveness.get('timeoutSeconds', 0) > 0, "Timeout should be positive"
        assert liveness.get('failureThreshold', 0) > 0, "Failure threshold should be positive"
    
    def test_readiness_probe_configured(self, default_values):
        """Test readiness probe is configured"""
        health_check = default_values.get('healthCheck', {})
        readiness = health_check.get('readinessProbe', {})
        
        assert readiness.get('enabled', False), "Readiness probe should be enabled by default"
        assert readiness.get('path') == '/api/health', "Readiness probe should use /api/health"
        assert readiness.get('initialDelaySeconds', 0) >= 0, "Initial delay should be non-negative"
        assert readiness.get('periodSeconds', 0) > 0, "Period should be positive"
        assert readiness.get('timeoutSeconds', 0) > 0, "Timeout should be positive"
        assert readiness.get('failureThreshold', 0) > 0, "Failure threshold should be positive"
    
    def test_startup_probe_configured(self, default_values):
        """Test startup probe is configured"""
        health_check = default_values.get('healthCheck', {})
        startup = health_check.get('startupProbe', {})
        
        assert startup.get('enabled', False), "Startup probe should be enabled by default"
        assert startup.get('path') == '/api/health', "Startup probe should use /api/health"
        assert startup.get('initialDelaySeconds', 0) >= 0, "Initial delay should be non-negative"
        assert startup.get('periodSeconds', 0) > 0, "Period should be positive"
        assert startup.get('timeoutSeconds', 0) > 0, "Timeout should be positive"
        assert startup.get('failureThreshold', 0) > 0, "Failure threshold should be positive"
    
    def test_probe_timing_reasonable(self, default_values):
        """Test probe timing is reasonable"""
        health_check = default_values.get('healthCheck', {})
        
        # Liveness probe should have longer initial delay
        liveness = health_check.get('livenessProbe', {})
        if liveness.get('enabled'):
            assert liveness.get('initialDelaySeconds', 0) >= 30, \
                "Liveness probe should have at least 30s initial delay"
        
        # Readiness probe should have shorter initial delay
        readiness = health_check.get('readinessProbe', {})
        if readiness.get('enabled'):
            assert readiness.get('initialDelaySeconds', 0) <= 30, \
                "Readiness probe should have shorter initial delay than liveness"
        
        # Startup probe should allow enough time for startup
        startup = health_check.get('startupProbe', {})
        if startup.get('enabled'):
            failure_threshold = startup.get('failureThreshold', 0)
            period = startup.get('periodSeconds', 0)
            total_timeout = failure_threshold * period
            assert total_timeout >= 300, \
                "Startup probe should allow at least 5 minutes for startup"
    
    def test_probe_paths_match(self, default_values):
        """Test all probes use the same health check path"""
        health_check = default_values.get('healthCheck', {})
        
        paths = []
        for probe_name in ['livenessProbe', 'readinessProbe', 'startupProbe']:
            probe = health_check.get(probe_name, {})
            if probe.get('enabled'):
                paths.append(probe.get('path'))
        
        # All enabled probes should use the same path
        if paths:
            assert len(set(paths)) == 1, "All probes should use the same health check path"
            assert paths[0] == '/api/health', "Health check path should be /api/health"

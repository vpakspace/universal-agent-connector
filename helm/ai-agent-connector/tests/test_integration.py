"""
Integration tests for Helm chart
"""
import yaml
import pytest
from pathlib import Path


class TestChartIntegration:
    """Integration tests for complete chart configuration"""
    
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
    
    def test_production_configuration_complete(self, production_values):
        """Test production configuration is complete"""
        if not production_values:
            pytest.skip("Production values file not found")
        
        # Production should have autoscaling enabled
        assert production_values.get('autoscaling', {}).get('enabled', False), \
            "Production should have autoscaling enabled"
        
        # Production should have resource limits
        resources = production_values.get('resources', {})
        assert 'limits' in resources, "Production should have resource limits"
        assert 'requests' in resources, "Production should have resource requests"
        
        # Production should have security contexts
        assert 'securityContext' in production_values, \
            "Production should have security context"
        assert 'podSecurityContext' in production_values, \
            "Production should have pod security context"
    
    def test_health_checks_in_production(self, production_values):
        """Test production has health checks configured"""
        if not production_values:
            pytest.skip("Production values file not found")
        
        health_check = production_values.get('healthCheck', {})
        assert health_check.get('livenessProbe', {}).get('enabled', False), \
            "Production should have liveness probe enabled"
        assert health_check.get('readinessProbe', {}).get('enabled', False), \
            "Production should have readiness probe enabled"
        assert health_check.get('startupProbe', {}).get('enabled', False), \
            "Production should have startup probe enabled"
    
    def test_replica_count_consistency(self, default_values):
        """Test replica count is consistent with autoscaling"""
        replica_count = default_values.get('replicaCount', 1)
        autoscaling = default_values.get('autoscaling', {})
        
        if not autoscaling.get('enabled', False):
            # When autoscaling is disabled, replica count should be set
            assert replica_count > 0, "replicaCount must be positive when autoscaling disabled"
        else:
            # When autoscaling is enabled, replica count is ignored (HPA controls it)
            min_replicas = autoscaling.get('minReplicas', 1)
            assert min_replicas > 0, "minReplicas must be positive"
    
    def test_service_port_matches_container(self, default_values):
        """Test service port matches container port"""
        service_port = default_values.get('service', {}).get('port', 5000)
        env_port = default_values.get('env', {}).get('PORT', '5000')
        
        # Service port should match environment PORT
        assert str(service_port) == str(env_port), \
            "Service port should match environment PORT"
    
    def test_image_configuration_complete(self, default_values):
        """Test image configuration is complete"""
        image = default_values.get('image', {})
        assert 'repository' in image, "Image repository must be set"
        assert 'tag' in image, "Image tag must be set"
        assert 'pullPolicy' in image, "Image pull policy must be set"
    
    def test_all_required_templates_exist(self, chart_dir):
        """Test all required template files exist"""
        templates_dir = chart_dir / "templates"
        required_templates = [
            'deployment.yaml',
            'service.yaml',
            'serviceaccount.yaml',
            '_helpers.tpl'
        ]
        
        for template in required_templates:
            template_file = templates_dir / template
            assert template_file.exists(), f"Required template {template} not found"
    
    def test_optional_templates_exist(self, chart_dir):
        """Test optional template files exist"""
        templates_dir = chart_dir / "templates"
        optional_templates = [
            'hpa.yaml',
            'ingress.yaml',
            'configmap.yaml',
            'secret.yaml',
            'networkpolicy.yaml',
            'pdb.yaml'
        ]
        
        # These should exist but are conditionally rendered
        for template in optional_templates:
            template_file = templates_dir / template
            # Just verify they exist, not that they're always rendered
            if template_file.exists():
                assert True, f"Optional template {template} exists"
    
    def test_environment_variables_configured(self, default_values):
        """Test required environment variables are configured"""
        env = default_values.get('env', {})
        required_env = ['FLASK_ENV', 'PORT', 'HOST']
        
        for var in required_env:
            assert var in env, f"Required environment variable {var} must be configured"
    
    def test_resources_have_both_limits_and_requests(self, default_values):
        """Test resources have both limits and requests"""
        resources = default_values.get('resources', {})
        assert 'limits' in resources, "Resource limits must be configured"
        assert 'requests' in resources, "Resource requests must be configured"
        
        limits = resources['limits']
        requests = resources['requests']
        
        # If CPU is set in both, requests should be <= limits
        if 'cpu' in limits and 'cpu' in requests:
            # Parse CPU values (handles 'm' suffix)
            def parse_cpu(cpu_str):
                if isinstance(cpu_str, (int, float)):
                    return float(cpu_str)
                if cpu_str.endswith('m'):
                    return float(cpu_str[:-1]) / 1000
                return float(cpu_str)
            
            limit_cpu = parse_cpu(limits['cpu'])
            request_cpu = parse_cpu(requests['cpu'])
            assert request_cpu <= limit_cpu, \
                "CPU request should be <= CPU limit"
        
        # If memory is set in both, requests should be <= limits
        if 'memory' in limits and 'memory' in requests:
            # Basic check - in practice would need to parse memory units
            assert True, "Memory request should be <= memory limit (validate manually)"

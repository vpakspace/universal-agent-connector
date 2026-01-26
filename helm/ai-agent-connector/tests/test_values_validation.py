"""
Test Helm chart values validation
"""
import yaml
import pytest
from pathlib import Path


class TestValuesValidation:
    """Test values.yaml configuration"""
    
    @pytest.fixture
    def chart_dir(self):
        """Get chart directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def default_values(self, chart_dir):
        """Load default values.yaml"""
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
    
    def test_image_configuration(self, default_values):
        """Test image configuration exists"""
        assert 'image' in default_values, "image configuration must exist"
        assert 'repository' in default_values['image'], "image.repository must exist"
        assert 'tag' in default_values['image'], "image.tag must exist"
        assert 'pullPolicy' in default_values['image'], "image.pullPolicy must exist"
    
    def test_replica_count(self, default_values):
        """Test replica count is set"""
        assert 'replicaCount' in default_values, "replicaCount must exist"
        assert isinstance(default_values['replicaCount'], int), "replicaCount must be integer"
        assert default_values['replicaCount'] > 0, "replicaCount must be positive"
    
    def test_service_configuration(self, default_values):
        """Test service configuration"""
        assert 'service' in default_values, "service configuration must exist"
        assert 'type' in default_values['service'], "service.type must exist"
        assert 'port' in default_values['service'], "service.port must exist"
        assert isinstance(default_values['service']['port'], int), "service.port must be integer"
    
    def test_autoscaling_configuration(self, default_values):
        """Test autoscaling configuration"""
        assert 'autoscaling' in default_values, "autoscaling configuration must exist"
        assert 'enabled' in default_values['autoscaling'], "autoscaling.enabled must exist"
        assert isinstance(default_values['autoscaling']['enabled'], bool), "autoscaling.enabled must be boolean"
        
        if default_values['autoscaling']['enabled']:
            assert 'minReplicas' in default_values['autoscaling'], "autoscaling.minReplicas must exist"
            assert 'maxReplicas' in default_values['autoscaling'], "autoscaling.maxReplicas must exist"
            assert default_values['autoscaling']['minReplicas'] <= default_values['autoscaling']['maxReplicas'], \
                "minReplicas must be <= maxReplicas"
    
    def test_health_check_configuration(self, default_values):
        """Test health check configuration"""
        assert 'healthCheck' in default_values, "healthCheck configuration must exist"
        
        probes = ['livenessProbe', 'readinessProbe', 'startupProbe']
        for probe in probes:
            assert probe in default_values['healthCheck'], f"healthCheck.{probe} must exist"
            probe_config = default_values['healthCheck'][probe]
            assert 'enabled' in probe_config, f"healthCheck.{probe}.enabled must exist"
            
            if probe_config.get('enabled'):
                assert 'path' in probe_config, f"healthCheck.{probe}.path must exist"
                assert 'initialDelaySeconds' in probe_config, f"healthCheck.{probe}.initialDelaySeconds must exist"
                assert 'periodSeconds' in probe_config, f"healthCheck.{probe}.periodSeconds must exist"
    
    def test_resources_configuration(self, default_values):
        """Test resources configuration"""
        assert 'resources' in default_values, "resources configuration must exist"
        assert 'limits' in default_values['resources'], "resources.limits must exist"
        assert 'requests' in default_values['resources'], "resources.requests must exist"
    
    def test_ingress_configuration(self, default_values):
        """Test ingress configuration"""
        assert 'ingress' in default_values, "ingress configuration must exist"
        assert 'enabled' in default_values['ingress'], "ingress.enabled must exist"
    
    def test_env_configuration(self, default_values):
        """Test environment variables configuration"""
        assert 'env' in default_values, "env configuration must exist"
        assert 'FLASK_ENV' in default_values['env'], "env.FLASK_ENV must exist"
        assert 'PORT' in default_values['env'], "env.PORT must exist"
        assert 'HOST' in default_values['env'], "env.HOST must exist"
    
    def test_secrets_configuration(self, default_values):
        """Test secrets configuration"""
        assert 'secrets' in default_values, "secrets configuration must exist"
        assert 'enabled' in default_values['secrets'], "secrets.enabled must exist"
    
    def test_configmap_configuration(self, default_values):
        """Test ConfigMap configuration"""
        assert 'configMap' in default_values, "configMap configuration must exist"
        assert 'enabled' in default_values['configMap'], "configMap.enabled must exist"
    
    def test_production_values_valid(self, production_values):
        """Test production values file is valid"""
        if production_values:
            assert isinstance(production_values, dict), "Production values must be a dictionary"
            # Production should have autoscaling enabled
            if 'autoscaling' in production_values:
                if production_values['autoscaling'].get('enabled'):
                    assert production_values['autoscaling'].get('minReplicas', 0) >= 2, \
                        "Production should have at least 2 replicas"
    
    def test_security_context_configuration(self, default_values):
        """Test security context configuration"""
        assert 'securityContext' in default_values, "securityContext must exist"
        assert 'podSecurityContext' in default_values, "podSecurityContext must exist"

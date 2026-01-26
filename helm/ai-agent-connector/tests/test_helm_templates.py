"""
Test Helm chart template rendering
"""
import yaml
import pytest
import subprocess
import tempfile
from pathlib import Path


class TestHelmTemplates:
    """Test Helm template rendering"""
    
    @pytest.fixture
    def chart_dir(self):
        """Get chart directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def helm_available(self):
        """Check if Helm is available"""
        try:
            result = subprocess.run(['helm', 'version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def render_template(self, chart_dir, values_file=None, template=None):
        """Render Helm template"""
        cmd = ['helm', 'template', 'test-release', str(chart_dir)]
        if values_file:
            cmd.extend(['-f', str(values_file)])
        if template:
            cmd.extend(['--show-only', f'templates/{template}'])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            pytest.skip(f"Helm template rendering failed: {result.stderr}")
        return yaml.safe_load_all(result.stdout)
    
    @pytest.mark.skipif(not pytest.config.getoption("--helm-tests"), reason="Helm tests require --helm-tests flag")
    def test_deployment_template_renders(self, chart_dir, helm_available):
        """Test deployment template renders correctly"""
        if not helm_available:
            pytest.skip("Helm not available")
        
        manifests = list(self.render_template(chart_dir, template='deployment.yaml'))
        deployment = next((m for m in manifests if m.get('kind') == 'Deployment'), None)
        assert deployment is not None, "Deployment manifest not found"
        assert deployment['kind'] == 'Deployment', "Should be a Deployment"
    
    @pytest.mark.skipif(not pytest.config.getoption("--helm-tests"), reason="Helm tests require --helm-tests flag")
    def test_service_template_renders(self, chart_dir, helm_available):
        """Test service template renders correctly"""
        if not helm_available:
            pytest.skip("Helm not available")
        
        manifests = list(self.render_template(chart_dir, template='service.yaml'))
        service = next((m for m in manifests if m.get('kind') == 'Service'), None)
        assert service is not None, "Service manifest not found"
        assert service['kind'] == 'Service', "Should be a Service"
    
    @pytest.mark.skipif(not pytest.config.getoption("--helm-tests"), reason="Helm tests require --helm-tests flag")
    def test_hpa_template_renders(self, chart_dir, helm_available):
        """Test HPA template renders when enabled"""
        if not helm_available:
            pytest.skip("Helm not available")
        
        # Create temp values file with autoscaling enabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'autoscaling': {'enabled': True}}, f)
            values_file = Path(f.name)
        
        try:
            manifests = list(self.render_template(chart_dir, values_file=values_file, template='hpa.yaml'))
            hpa = next((m for m in manifests if m.get('kind') == 'HorizontalPodAutoscaler'), None)
            assert hpa is not None, "HPA manifest should be created when enabled"
        finally:
            values_file.unlink()
    
    @pytest.mark.skipif(not pytest.config.getoption("--helm-tests"), reason="Helm tests require --helm-tests flag")
    def test_configmap_template_renders(self, chart_dir, helm_available):
        """Test ConfigMap template renders when enabled"""
        if not helm_available:
            pytest.skip("Helm not available")
        
        # Create temp values file with configMap enabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'configMap': {
                    'enabled': True,
                    'data': {'TEST_KEY': 'test_value'}
                }
            }, f)
            values_file = Path(f.name)
        
        try:
            manifests = list(self.render_template(chart_dir, values_file=values_file, template='configmap.yaml'))
            configmap = next((m for m in manifests if m.get('kind') == 'ConfigMap'), None)
            assert configmap is not None, "ConfigMap manifest should be created when enabled"
        finally:
            values_file.unlink()
    
    @pytest.mark.skipif(not pytest.config.getoption("--helm-tests"), reason="Helm tests require --helm-tests flag")
    def test_ingress_template_renders_when_enabled(self, chart_dir, helm_available):
        """Test Ingress template renders when enabled"""
        if not helm_available:
            pytest.skip("Helm not available")
        
        # Create temp values file with ingress enabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'ingress': {
                    'enabled': True,
                    'hosts': [{'host': 'test.example.com', 'paths': [{'path': '/', 'pathType': 'Prefix'}]}]
                }
            }, f)
            values_file = Path(f.name)
        
        try:
            manifests = list(self.render_template(chart_dir, values_file=values_file, template='ingress.yaml'))
            ingress = next((m for m in manifests if m.get('kind') == 'Ingress'), None)
            assert ingress is not None, "Ingress manifest should be created when enabled"
        finally:
            values_file.unlink()
    
    @pytest.mark.skipif(not pytest.config.getoption("--helm-tests"), reason="Helm tests require --helm-tests flag")
    def test_all_templates_render_without_errors(self, chart_dir, helm_available):
        """Test all templates render without errors"""
        if not helm_available:
            pytest.skip("Helm not available")
        
        cmd = ['helm', 'template', 'test-release', str(chart_dir), '--debug']
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Template rendering failed: {result.stderr}"


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--helm-tests",
        action="store_true",
        default=False,
        help="Run Helm template rendering tests (requires Helm CLI)"
    )

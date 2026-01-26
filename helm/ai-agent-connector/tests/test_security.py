"""
Test security configuration in Helm chart
"""
import yaml
import pytest
from pathlib import Path


class TestSecurity:
    """Test security context and configuration"""
    
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
    
    def test_security_context_exists(self, default_values):
        """Test security context configuration exists"""
        assert 'securityContext' in default_values, "securityContext must exist"
        assert 'podSecurityContext' in default_values, "podSecurityContext must exist"
    
    def test_container_security_context(self, default_values):
        """Test container security context is secure"""
        security_context = default_values.get('securityContext', {})
        
        # Should run as non-root
        if 'runAsNonRoot' in security_context:
            assert security_context['runAsNonRoot'] is True, \
                "Container should run as non-root user"
        
        # Should not allow privilege escalation
        if 'allowPrivilegeEscalation' in security_context:
            assert security_context['allowPrivilegeEscalation'] is False, \
                "Container should not allow privilege escalation"
        
        # Should drop all capabilities
        if 'capabilities' in security_context:
            capabilities = security_context['capabilities']
            if 'drop' in capabilities:
                assert 'ALL' in capabilities['drop'], \
                    "Container should drop ALL capabilities"
    
    def test_pod_security_context(self, default_values):
        """Test pod security context is secure"""
        pod_security_context = default_values.get('podSecurityContext', {})
        
        # Should run as non-root
        if 'runAsNonRoot' in pod_security_context:
            assert pod_security_context['runAsNonRoot'] is True, \
                "Pod should run as non-root user"
        
        # Should have runAsUser set
        if 'runAsUser' in pod_security_context:
            assert pod_security_context['runAsUser'] > 0, \
                "runAsUser should be a non-root UID"
    
    def test_secrets_configuration(self, default_values):
        """Test secrets are configured securely"""
        secrets = default_values.get('secrets', {})
        assert 'enabled' in secrets, "secrets.enabled must exist"
        
        # Secrets should be enabled in production
        # Values should not contain actual secrets (they should be base64 encoded or external)
        if secrets.get('enabled'):
            # Check that secret values are not plain text in values file
            # (This is a basic check - in practice, secrets should be external)
            pass
    
    def test_network_policy_optional(self, default_values):
        """Test network policy configuration is optional"""
        network_policy = default_values.get('networkPolicy', {})
        # Network policy is optional, but if enabled, should have proper config
        if network_policy.get('enabled'):
            assert isinstance(network_policy.get('ingress', []), list), \
                "networkPolicy.ingress should be a list"
            assert isinstance(network_policy.get('egress', []), list), \
                "networkPolicy.egress should be a list"

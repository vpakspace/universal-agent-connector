"""
Test cases for deployment guides
"""
import pytest
from pathlib import Path


class TestDeploymentGuidesStructure:
    """Test deployment guides structure"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    def test_aws_guide_exists(self, deployment_dir):
        """Test that AWS deployment guide exists"""
        assert (deployment_dir / "AWS_DEPLOYMENT_GUIDE.md").exists(), "AWS_DEPLOYMENT_GUIDE.md should exist"
    
    def test_gcp_guide_exists(self, deployment_dir):
        """Test that GCP deployment guide exists"""
        assert (deployment_dir / "GCP_DEPLOYMENT_GUIDE.md").exists(), "GCP_DEPLOYMENT_GUIDE.md should exist"
    
    def test_azure_guide_exists(self, deployment_dir):
        """Test that Azure deployment guide exists"""
        assert (deployment_dir / "AZURE_DEPLOYMENT_GUIDE.md").exists(), "AZURE_DEPLOYMENT_GUIDE.md should exist"
    
    def test_readme_exists(self, deployment_dir):
        """Test that deployment README exists"""
        assert (deployment_dir / "README.md").exists(), "README.md should exist"
    
    def test_quick_start_guide_exists(self, deployment_dir):
        """Test that Quick Start guide exists"""
        assert (deployment_dir / "QUICK_START.md").exists(), "QUICK_START.md should exist"


class TestDeploymentGuidesContent:
    """Test deployment guides content"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    def test_aws_guide_has_prerequisites(self, deployment_dir):
        """Test that AWS guide has prerequisites section"""
        content = (deployment_dir / "AWS_DEPLOYMENT_GUIDE.md").read_text()
        assert "Prerequisites" in content, "AWS guide should have Prerequisites section"
    
    def test_aws_guide_has_terraform_steps(self, deployment_dir):
        """Test that AWS guide has Terraform steps"""
        content = (deployment_dir / "AWS_DEPLOYMENT_GUIDE.md").read_text()
        assert "terraform" in content.lower(), "AWS guide should have Terraform steps"
    
    def test_aws_guide_has_cloudformation_steps(self, deployment_dir):
        """Test that AWS guide has CloudFormation steps"""
        content = (deployment_dir / "AWS_DEPLOYMENT_GUIDE.md").read_text()
        assert "cloudformation" in content.lower(), "AWS guide should have CloudFormation steps"
    
    def test_aws_guide_has_troubleshooting(self, deployment_dir):
        """Test that AWS guide has troubleshooting section"""
        content = (deployment_dir / "AWS_DEPLOYMENT_GUIDE.md").read_text()
        assert "Troubleshooting" in content, "AWS guide should have Troubleshooting section"
    
    def test_gcp_guide_has_prerequisites(self, deployment_dir):
        """Test that GCP guide has prerequisites section"""
        content = (deployment_dir / "GCP_DEPLOYMENT_GUIDE.md").read_text()
        assert "Prerequisites" in content, "GCP guide should have Prerequisites section"
    
    def test_gcp_guide_has_terraform_steps(self, deployment_dir):
        """Test that GCP guide has Terraform steps"""
        content = (deployment_dir / "GCP_DEPLOYMENT_GUIDE.md").read_text()
        assert "terraform" in content.lower(), "GCP guide should have Terraform steps"
    
    def test_gcp_guide_has_troubleshooting(self, deployment_dir):
        """Test that GCP guide has troubleshooting section"""
        content = (deployment_dir / "GCP_DEPLOYMENT_GUIDE.md").read_text()
        assert "Troubleshooting" in content, "GCP guide should have Troubleshooting section"
    
    def test_azure_guide_has_prerequisites(self, deployment_dir):
        """Test that Azure guide has prerequisites section"""
        content = (deployment_dir / "AZURE_DEPLOYMENT_GUIDE.md").read_text()
        assert "Prerequisites" in content, "Azure guide should have Prerequisites section"
    
    def test_azure_guide_has_terraform_steps(self, deployment_dir):
        """Test that Azure guide has Terraform steps"""
        content = (deployment_dir / "AZURE_DEPLOYMENT_GUIDE.md").read_text()
        assert "terraform" in content.lower(), "Azure guide should have Terraform steps"
    
    def test_azure_guide_has_troubleshooting(self, deployment_dir):
        """Test that Azure guide has troubleshooting section"""
        content = (deployment_dir / "AZURE_DEPLOYMENT_GUIDE.md").read_text()
        assert "Troubleshooting" in content, "Azure guide should have Troubleshooting section"
    
    def test_readme_has_quick_start(self, deployment_dir):
        """Test that README has quick start section"""
        content = (deployment_dir / "README.md").read_text()
        assert "Quick Start" in content or "quick start" in content.lower(), "README should have Quick Start section"
    
    def test_readme_has_aws_section(self, deployment_dir):
        """Test that README has AWS section"""
        content = (deployment_dir / "README.md").read_text()
        assert "AWS" in content, "README should have AWS section"
    
    def test_readme_has_gcp_section(self, deployment_dir):
        """Test that README has GCP section"""
        content = (deployment_dir / "README.md").read_text()
        assert "GCP" in content, "README should have GCP section"
    
    def test_readme_has_azure_section(self, deployment_dir):
        """Test that README has Azure section"""
        content = (deployment_dir / "README.md").read_text()
        assert "Azure" in content, "README should have Azure section"
    
    def test_aws_guide_has_security_best_practices(self, deployment_dir):
        """Test that AWS guide has security best practices"""
        content = (deployment_dir / "AWS_DEPLOYMENT_GUIDE.md").read_text()
        assert "Security" in content or "security" in content.lower(), "AWS guide should have security best practices"
    
    def test_gcp_guide_has_security_best_practices(self, deployment_dir):
        """Test that GCP guide has security best practices"""
        content = (deployment_dir / "GCP_DEPLOYMENT_GUIDE.md").read_text()
        assert "Security" in content or "security" in content.lower(), "GCP guide should have security best practices"
    
    def test_azure_guide_has_security_best_practices(self, deployment_dir):
        """Test that Azure guide has security best practices"""
        content = (deployment_dir / "AZURE_DEPLOYMENT_GUIDE.md").read_text()
        assert "Security" in content or "security" in content.lower(), "Azure guide should have security best practices"
    
    def test_quick_start_has_prerequisites(self, deployment_dir):
        """Test that Quick Start guide has prerequisites section"""
        content = (deployment_dir / "QUICK_START.md").read_text()
        assert "Prerequisites" in content, "Quick Start guide should have Prerequisites section"
    
    def test_quick_start_has_deployment_options(self, deployment_dir):
        """Test that Quick Start guide has deployment options"""
        content = (deployment_dir / "QUICK_START.md").read_text()
        assert "deploy.sh" in content or "deploy.ps1" in content, "Quick Start guide should mention deployment scripts"
        assert "terraform" in content.lower(), "Quick Start guide should mention Terraform"
    
    def test_quick_start_has_post_deployment(self, deployment_dir):
        """Test that Quick Start guide has post-deployment section"""
        content = (deployment_dir / "QUICK_START.md").read_text()
        assert "Post-Deployment" in content or "post-deployment" in content.lower(), "Quick Start guide should have post-deployment section"

"""
Integration tests for cloud deployment templates
"""
import pytest
from pathlib import Path


class TestTerraformTemplatesIntegration:
    """Integration tests for Terraform templates"""
    
    @pytest.fixture
    def terraform_dirs(self):
        base = Path(__file__).parent.parent
        return {
            "aws": base / "terraform" / "aws",
            "gcp": base / "terraform" / "gcp",
            "azure": base / "terraform" / "azure"
        }
    
    def test_all_providers_have_main_tf(self, terraform_dirs):
        """Test that all providers have main.tf"""
        for provider, dir_path in terraform_dirs.items():
            assert (dir_path / "main.tf").exists(), f"{provider} should have main.tf"
    
    def test_all_providers_have_variables_tf(self, terraform_dirs):
        """Test that all providers have variables.tf"""
        for provider, dir_path in terraform_dirs.items():
            assert (dir_path / "variables.tf").exists(), f"{provider} should have variables.tf"
    
    def test_all_providers_have_tfvars_example(self, terraform_dirs):
        """Test that all providers have terraform.tfvars.example"""
        for provider, dir_path in terraform_dirs.items():
            assert (dir_path / "terraform.tfvars.example").exists(), f"{provider} should have terraform.tfvars.example"
    
    def test_all_providers_have_helm_values_template(self, terraform_dirs):
        """Test that all providers have helm-values.yaml.tpl"""
        for provider, dir_path in terraform_dirs.items():
            assert (dir_path / "helm-values.yaml.tpl").exists(), f"{provider} should have helm-values.yaml.tpl"
    
    def test_all_providers_contain_kubernetes_cluster(self, terraform_dirs):
        """Test that all providers contain Kubernetes cluster resource"""
        cluster_resources = {
            "aws": "aws_eks_cluster",
            "gcp": "google_container_cluster",
            "azure": "azurerm_kubernetes_cluster"
        }
        
        for provider, dir_path in terraform_dirs.items():
            content = (dir_path / "main.tf").read_text()
            assert cluster_resources[provider] in content, f"{provider} should contain {cluster_resources[provider]}"
    
    def test_all_providers_contain_container_registry(self, terraform_dirs):
        """Test that all providers contain container registry"""
        registry_resources = {
            "aws": "aws_ecr_repository",
            "gcp": "google_artifact_registry_repository",
            "azure": "azurerm_container_registry"
        }
        
        for provider, dir_path in terraform_dirs.items():
            content = (dir_path / "main.tf").read_text()
            assert registry_resources[provider] in content, f"{provider} should contain {registry_resources[provider]}"
    
    def test_all_providers_contain_helm_release(self, terraform_dirs):
        """Test that all providers contain Helm release"""
        for provider, dir_path in terraform_dirs.items():
            content = (dir_path / "main.tf").read_text()
            assert "helm_release" in content, f"{provider} should contain helm_release"


class TestDeploymentGuidesIntegration:
    """Integration tests for deployment guides"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    def test_all_guides_exist(self, deployment_dir):
        """Test that all deployment guides exist"""
        guides = [
            "AWS_DEPLOYMENT_GUIDE.md",
            "GCP_DEPLOYMENT_GUIDE.md",
            "AZURE_DEPLOYMENT_GUIDE.md"
        ]
        
        for guide in guides:
            assert (deployment_dir / guide).exists(), f"{guide} should exist"
    
    def test_all_guides_have_common_sections(self, deployment_dir):
        """Test that all guides have common sections"""
        common_sections = [
            "Prerequisites",
            "Troubleshooting",
            "Cleanup"
        ]
        
        guides = {
            "AWS": deployment_dir / "AWS_DEPLOYMENT_GUIDE.md",
            "GCP": deployment_dir / "GCP_DEPLOYMENT_GUIDE.md",
            "Azure": deployment_dir / "AZURE_DEPLOYMENT_GUIDE.md"
        }
        
        for provider, guide_path in guides.items():
            content = guide_path.read_text()
            for section in common_sections:
                assert section in content, f"{provider} guide should have {section} section"


class TestDeploymentScriptsIntegration:
    """Integration tests for deployment scripts"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    def test_both_scripts_exist(self, deployment_dir):
        """Test that both deployment scripts exist"""
        assert (deployment_dir / "deploy.sh").exists(), "deploy.sh should exist"
        assert (deployment_dir / "deploy.ps1").exists(), "deploy.ps1 should exist"
    
    def test_both_scripts_support_all_providers(self, deployment_dir):
        """Test that both scripts support all providers"""
        providers = ["aws", "gcp", "azure"]
        
        bash_content = (deployment_dir / "deploy.sh").read_text()
        ps_content = (deployment_dir / "deploy.ps1").read_text()
        
        for provider in providers:
            assert provider in bash_content.lower(), f"deploy.sh should support {provider}"
            assert provider in ps_content.lower(), f"deploy.ps1 should support {provider}"


class TestConfigurationFilesIntegration:
    """Integration tests for configuration files"""
    
    @pytest.fixture
    def terraform_dirs(self):
        base = Path(__file__).parent.parent
        return {
            "aws": base / "terraform" / "aws",
            "gcp": base / "terraform" / "gcp",
            "azure": base / "terraform" / "azure"
        }
    
    def test_all_tfvars_examples_have_project_name(self, terraform_dirs):
        """Test that all tfvars examples have project_name"""
        for provider, dir_path in terraform_dirs.items():
            content = (dir_path / "terraform.tfvars.example").read_text()
            assert "project_name" in content, f"{provider} tfvars example should have project_name"
    
    def test_all_helm_values_templates_have_image_config(self, terraform_dirs):
        """Test that all helm values templates have image configuration"""
        for provider, dir_path in terraform_dirs.items():
            content = (dir_path / "helm-values.yaml.tpl").read_text()
            assert "image:" in content, f"{provider} helm values template should have image configuration"
            assert "replicaCount:" in content, f"{provider} helm values template should have replicaCount"
    
    def test_all_providers_have_required_outputs(self, terraform_dirs):
        """Test that all providers have required outputs for deployment scripts"""
        required_outputs = {
            "aws": ["cluster_name", "ecr_repository_url", "configure_kubectl", "aws_region"],
            "gcp": ["cluster_name", "artifact_registry_url", "configure_kubectl", "gcp_region"],
            "azure": ["cluster_name", "acr_login_server", "configure_kubectl"]
        }
        
        for provider, dir_path in terraform_dirs.items():
            # AWS has outputs.tf, GCP/Azure have outputs in main.tf
            if provider == "aws":
                content = (dir_path / "outputs.tf").read_text()
            else:
                content = (dir_path / "main.tf").read_text()
            
            for output in required_outputs[provider]:
                assert f'output "{output}"' in content, f"{provider} should have {output} output"
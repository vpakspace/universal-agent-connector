"""
Test cases for Azure Terraform templates
"""
import os
import pytest
from pathlib import Path


class TestTerraformAzureStructure:
    """Test Azure Terraform template structure"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "azure"
    
    def test_main_tf_exists(self, terraform_dir):
        """Test that main.tf exists"""
        assert (terraform_dir / "main.tf").exists(), "main.tf should exist"
    
    def test_variables_tf_exists(self, terraform_dir):
        """Test that variables.tf exists"""
        assert (terraform_dir / "variables.tf").exists(), "variables.tf should exist"
    
    def test_helm_values_template_exists(self, terraform_dir):
        """Test that helm-values.yaml.tpl exists"""
        assert (terraform_dir / "helm-values.yaml.tpl").exists(), "helm-values.yaml.tpl should exist"
    
    def test_tfvars_example_exists(self, terraform_dir):
        """Test that terraform.tfvars.example exists"""
        assert (terraform_dir / "terraform.tfvars.example").exists(), "terraform.tfvars.example should exist"


class TestTerraformAzureContent:
    """Test Azure Terraform template content"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "azure"
    
    def test_main_tf_contains_resource_group(self, terraform_dir):
        """Test that main.tf contains resource group"""
        content = (terraform_dir / "main.tf").read_text()
        assert "azurerm_resource_group" in content, "main.tf should contain resource group"
    
    def test_main_tf_contains_vnet(self, terraform_dir):
        """Test that main.tf contains virtual network"""
        content = (terraform_dir / "main.tf").read_text()
        assert "azurerm_virtual_network" in content, "main.tf should contain virtual network"
    
    def test_main_tf_contains_aks_cluster(self, terraform_dir):
        """Test that main.tf contains AKS cluster"""
        content = (terraform_dir / "main.tf").read_text()
        assert "azurerm_kubernetes_cluster" in content, "main.tf should contain AKS cluster"
    
    def test_main_tf_contains_acr(self, terraform_dir):
        """Test that main.tf contains ACR"""
        content = (terraform_dir / "main.tf").read_text()
        assert "azurerm_container_registry" in content, "main.tf should contain ACR"
    
    def test_main_tf_contains_helm_release(self, terraform_dir):
        """Test that main.tf contains Helm release"""
        content = (terraform_dir / "main.tf").read_text()
        assert "helm_release" in content, "main.tf should contain Helm release"
    
    def test_variables_contains_required_vars(self, terraform_dir):
        """Test that variables.tf contains required variables"""
        content = (terraform_dir / "variables.tf").read_text()
        required_vars = [
            "azure_region",
            "project_name"
        ]
        for var in required_vars:
            assert f'variable "{var}"' in content, f"variables.tf should contain {var}"
    
    def test_tfvars_example_contains_azure_region(self, terraform_dir):
        """Test that terraform.tfvars.example contains azure_region"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "azure_region" in content, "terraform.tfvars.example should contain azure_region"
    
    def test_tfvars_example_contains_project_name(self, terraform_dir):
        """Test that terraform.tfvars.example contains project_name"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "project_name" in content, "terraform.tfvars.example should contain project_name"
    
    def test_outputs_contains_required_outputs(self, terraform_dir):
        """Test that main.tf contains all required outputs for deployment scripts"""
        content = (terraform_dir / "main.tf").read_text()
        required_outputs = [
            "cluster_name",
            "acr_login_server",
            "configure_kubectl"
        ]
        for output in required_outputs:
            assert f'output "{output}"' in content, f"main.tf should contain {output} output"


class TestTerraformAzureSyntax:
    """Test Azure Terraform syntax (requires terraform binary)"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "azure"
    
    @pytest.mark.helm_tests
    def test_terraform_validate(self, terraform_dir):
        """Test that Terraform configuration is valid"""
        import subprocess
        import tempfile
        
        # Create a temporary tfvars file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write("""
azure_region = "eastus"
project_name = "test-project"
vnet_address_space = "10.0.0.0/16"
subnet_address_prefix = "10.0.1.0/24"
kubernetes_version = "1.28"
node_count = 1
node_min_count = 1
node_max_count = 3
node_vm_size = "Standard_D2s_v3"
node_os_disk_size_gb = 50
helm_release_name = "test-release"
helm_chart_path = "../../helm/ai-agent-connector"
helm_chart_version = "1.0.0"
kubernetes_namespace = "default"
image_tag = "latest"
replica_count = 1
""")
            temp_tfvars = f.name
        
        try:
            # Initialize Terraform
            result = subprocess.run(
                ["terraform", "init"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Validate Terraform
            result = subprocess.run(
                ["terraform", "validate"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            assert result.returncode == 0, f"Terraform validation failed: {result.stderr}"
        finally:
            os.unlink(temp_tfvars)

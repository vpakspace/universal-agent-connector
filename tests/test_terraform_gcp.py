"""
Test cases for GCP Terraform templates
"""
import os
import pytest
from pathlib import Path


class TestTerraformGCPStructure:
    """Test GCP Terraform template structure"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "gcp"
    
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


class TestTerraformGCPContent:
    """Test GCP Terraform template content"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "gcp"
    
    def test_main_tf_contains_vpc(self, terraform_dir):
        """Test that main.tf contains VPC network"""
        content = (terraform_dir / "main.tf").read_text()
        assert "google_compute_network" in content, "main.tf should contain VPC network"
    
    def test_main_tf_contains_gke_cluster(self, terraform_dir):
        """Test that main.tf contains GKE cluster"""
        content = (terraform_dir / "main.tf").read_text()
        assert "google_container_cluster" in content, "main.tf should contain GKE cluster"
    
    def test_main_tf_contains_artifact_registry(self, terraform_dir):
        """Test that main.tf contains Artifact Registry"""
        content = (terraform_dir / "main.tf").read_text()
        assert "google_artifact_registry_repository" in content, "main.tf should contain Artifact Registry"
    
    def test_main_tf_contains_helm_release(self, terraform_dir):
        """Test that main.tf contains Helm release"""
        content = (terraform_dir / "main.tf").read_text()
        assert "helm_release" in content, "main.tf should contain Helm release"
    
    def test_variables_contains_required_vars(self, terraform_dir):
        """Test that variables.tf contains required variables"""
        content = (terraform_dir / "variables.tf").read_text()
        required_vars = [
            "gcp_project_id",
            "gcp_region",
            "project_name"
        ]
        for var in required_vars:
            assert f'variable "{var}"' in content, f"variables.tf should contain {var}"
    
    def test_tfvars_example_contains_gcp_project_id(self, terraform_dir):
        """Test that terraform.tfvars.example contains gcp_project_id"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "gcp_project_id" in content, "terraform.tfvars.example should contain gcp_project_id"
    
    def test_tfvars_example_contains_gcp_region(self, terraform_dir):
        """Test that terraform.tfvars.example contains gcp_region"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "gcp_region" in content, "terraform.tfvars.example should contain gcp_region"
    
    def test_outputs_contains_gcp_region(self, terraform_dir):
        """Test that main.tf contains gcp_region output"""
        content = (terraform_dir / "main.tf").read_text()
        assert 'output "gcp_region"' in content, "main.tf should contain gcp_region output for deployment scripts"
    
    def test_outputs_contains_required_outputs(self, terraform_dir):
        """Test that main.tf contains all required outputs for deployment scripts"""
        content = (terraform_dir / "main.tf").read_text()
        required_outputs = [
            "cluster_name",
            "artifact_registry_url",
            "configure_kubectl",
            "gcp_region"
        ]
        for output in required_outputs:
            assert f'output "{output}"' in content, f"main.tf should contain {output} output"


class TestTerraformGCPSyntax:
    """Test GCP Terraform syntax (requires terraform binary)"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "gcp"
    
    @pytest.mark.helm_tests
    def test_terraform_validate(self, terraform_dir):
        """Test that Terraform configuration is valid"""
        import subprocess
        import tempfile
        
        # Create a temporary tfvars file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write("""
gcp_project_id = "test-project"
gcp_region = "us-central1"
project_name = "test-project"
subnet_cidr = "10.0.0.0/16"
master_ipv4_cidr_block = "172.16.0.0/28"
node_count = 1
node_min_count = 1
node_max_count = 3
node_machine_type = "e2-medium"
node_disk_size = 50
preemptible_nodes = false
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

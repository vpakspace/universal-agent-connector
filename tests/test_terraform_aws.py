"""
Test cases for AWS Terraform templates
"""
import os
import pytest
import yaml
import json
from pathlib import Path


class TestTerraformAWSStructure:
    """Test AWS Terraform template structure"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "aws"
    
    def test_main_tf_exists(self, terraform_dir):
        """Test that main.tf exists"""
        assert (terraform_dir / "main.tf").exists(), "main.tf should exist"
    
    def test_variables_tf_exists(self, terraform_dir):
        """Test that variables.tf exists"""
        assert (terraform_dir / "variables.tf").exists(), "variables.tf should exist"
    
    def test_outputs_tf_exists(self, terraform_dir):
        """Test that outputs.tf exists"""
        assert (terraform_dir / "outputs.tf").exists(), "outputs.tf should exist"
    
    def test_helm_values_template_exists(self, terraform_dir):
        """Test that helm-values.yaml.tpl exists"""
        assert (terraform_dir / "helm-values.yaml.tpl").exists(), "helm-values.yaml.tpl should exist"
    
    def test_tfvars_example_exists(self, terraform_dir):
        """Test that terraform.tfvars.example exists"""
        assert (terraform_dir / "terraform.tfvars.example").exists(), "terraform.tfvars.example should exist"


class TestTerraformAWSContent:
    """Test AWS Terraform template content"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "aws"
    
    def test_main_tf_contains_vpc(self, terraform_dir):
        """Test that main.tf contains VPC resource"""
        content = (terraform_dir / "main.tf").read_text()
        assert "aws_vpc" in content, "main.tf should contain VPC resource"
    
    def test_main_tf_contains_eks_cluster(self, terraform_dir):
        """Test that main.tf contains EKS cluster"""
        content = (terraform_dir / "main.tf").read_text()
        assert "aws_eks_cluster" in content, "main.tf should contain EKS cluster"
    
    def test_main_tf_contains_ecr(self, terraform_dir):
        """Test that main.tf contains ECR repository"""
        content = (terraform_dir / "main.tf").read_text()
        assert "aws_ecr_repository" in content, "main.tf should contain ECR repository"
    
    def test_main_tf_contains_helm_release(self, terraform_dir):
        """Test that main.tf contains Helm release"""
        content = (terraform_dir / "main.tf").read_text()
        assert "helm_release" in content, "main.tf should contain Helm release"
    
    def test_variables_contains_required_vars(self, terraform_dir):
        """Test that variables.tf contains required variables"""
        content = (terraform_dir / "variables.tf").read_text()
        required_vars = [
            "aws_region",
            "project_name",
            "vpc_cidr",
            "availability_zones_count",
            "kubernetes_version"
        ]
        for var in required_vars:
            assert f'variable "{var}"' in content, f"variables.tf should contain {var}"
    
    def test_outputs_contains_cluster_info(self, terraform_dir):
        """Test that outputs.tf contains cluster information"""
        content = (terraform_dir / "outputs.tf").read_text()
        assert "cluster_name" in content or "cluster_endpoint" in content, "outputs.tf should contain cluster information"
    
    def test_outputs_contains_aws_region(self, terraform_dir):
        """Test that outputs.tf contains aws_region output"""
        content = (terraform_dir / "outputs.tf").read_text()
        assert 'output "aws_region"' in content, "outputs.tf should contain aws_region output for deployment scripts"
    
    def test_outputs_contains_required_outputs(self, terraform_dir):
        """Test that outputs.tf contains all required outputs for deployment scripts"""
        content = (terraform_dir / "outputs.tf").read_text()
        required_outputs = [
            "cluster_name",
            "ecr_repository_url",
            "configure_kubectl",
            "aws_region"
        ]
        for output in required_outputs:
            assert f'output "{output}"' in content, f"outputs.tf should contain {output} output"
    
    def test_helm_values_template_valid(self, terraform_dir):
        """Test that helm-values.yaml.tpl is valid YAML when templated"""
        template = (terraform_dir / "helm-values.yaml.tpl").read_text()
        # Basic check that it contains expected keys
        assert "image:" in template, "helm-values.yaml.tpl should contain image configuration"
        assert "replicaCount:" in template, "helm-values.yaml.tpl should contain replicaCount"
    
    def test_tfvars_example_valid_format(self, terraform_dir):
        """Test that terraform.tfvars.example has valid format"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        # Check for key-value pairs
        assert "=" in content, "terraform.tfvars.example should contain key-value pairs"


class TestTerraformAWSConfiguration:
    """Test AWS Terraform configuration"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "aws"
    
    def test_tfvars_example_contains_aws_region(self, terraform_dir):
        """Test that terraform.tfvars.example contains aws_region"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "aws_region" in content, "terraform.tfvars.example should contain aws_region"
    
    def test_tfvars_example_contains_project_name(self, terraform_dir):
        """Test that terraform.tfvars.example contains project_name"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "project_name" in content, "terraform.tfvars.example should contain project_name"
    
    def test_tfvars_example_contains_vpc_cidr(self, terraform_dir):
        """Test that terraform.tfvars.example contains vpc_cidr"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "vpc_cidr" in content, "terraform.tfvars.example should contain vpc_cidr"
    
    def test_tfvars_example_contains_node_config(self, terraform_dir):
        """Test that terraform.tfvars.example contains node configuration"""
        content = (terraform_dir / "terraform.tfvars.example").read_text()
        assert "node_" in content, "terraform.tfvars.example should contain node configuration"


class TestTerraformAWSSyntax:
    """Test AWS Terraform syntax (requires terraform binary)"""
    
    @pytest.fixture
    def terraform_dir(self):
        return Path(__file__).parent.parent / "terraform" / "aws"
    
    @pytest.mark.helm_tests
    def test_terraform_validate(self, terraform_dir):
        """Test that Terraform configuration is valid"""
        import subprocess
        import tempfile
        
        # Create a temporary tfvars file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write("""
aws_region = "us-east-1"
project_name = "test-project"
vpc_cidr = "10.0.0.0/16"
availability_zones_count = 2
kubernetes_version = "1.28"
node_instance_types = ["t3.medium"]
node_desired_size = 1
node_min_size = 1
node_max_size = 3
ecr_repository_name = "test-repo"
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

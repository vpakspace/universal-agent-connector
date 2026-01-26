"""
Test cases for AWS CloudFormation template
"""
import pytest
import yaml
from pathlib import Path


class TestCloudFormationStructure:
    """Test CloudFormation template structure"""
    
    @pytest.fixture
    def cloudformation_file(self):
        return Path(__file__).parent.parent / "cloudformation" / "aws" / "eks-stack.yaml"
    
    def test_cloudformation_file_exists(self, cloudformation_file):
        """Test that CloudFormation template exists"""
        assert cloudformation_file.exists(), "eks-stack.yaml should exist"
    
    def test_cloudformation_valid_yaml(self, cloudformation_file):
        """Test that CloudFormation template is valid YAML"""
        content = cloudformation_file.read_text()
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f"CloudFormation template is not valid YAML: {e}")


class TestCloudFormationContent:
    """Test CloudFormation template content"""
    
    @pytest.fixture
    def cloudformation_file(self):
        return Path(__file__).parent.parent / "cloudformation" / "aws" / "eks-stack.yaml"
    
    @pytest.fixture
    def template_content(self, cloudformation_file):
        return yaml.safe_load(cloudformation_file.read_text())
    
    def test_has_parameters(self, template_content):
        """Test that template has Parameters section"""
        assert "Parameters" in template_content, "Template should have Parameters section"
    
    def test_has_resources(self, template_content):
        """Test that template has Resources section"""
        assert "Resources" in template_content, "Template should have Resources section"
    
    def test_has_outputs(self, template_content):
        """Test that template has Outputs section"""
        assert "Outputs" in template_content, "Template should have Outputs section"
    
    def test_contains_vpc_resource(self, template_content):
        """Test that template contains VPC resource"""
        resources = template_content.get("Resources", {})
        assert "VPC" in resources, "Template should contain VPC resource"
    
    def test_contains_eks_cluster(self, template_content):
        """Test that template contains EKS cluster"""
        resources = template_content.get("Resources", {})
        assert "EKSCluster" in resources, "Template should contain EKS cluster"
    
    def test_contains_eks_node_group(self, template_content):
        """Test that template contains EKS node group"""
        resources = template_content.get("Resources", {})
        assert "EKSNodeGroup" in resources, "Template should contain EKS node group"
    
    def test_contains_ecr_repository(self, template_content):
        """Test that template contains ECR repository"""
        resources = template_content.get("Resources", {})
        assert "ECRRepository" in resources, "Template should contain ECR repository"
    
    def test_contains_public_subnets(self, template_content):
        """Test that template contains public subnets"""
        resources = template_content.get("Resources", {})
        assert "PublicSubnet1" in resources, "Template should contain public subnets"
        assert "PublicSubnet2" in resources, "Template should contain at least 2 public subnets"
    
    def test_contains_private_subnets(self, template_content):
        """Test that template contains private subnets"""
        resources = template_content.get("Resources", {})
        assert "PrivateSubnet1" in resources, "Template should contain private subnets"
        assert "PrivateSubnet2" in resources, "Template should contain at least 2 private subnets"
    
    def test_contains_nat_gateways(self, template_content):
        """Test that template contains NAT gateways"""
        resources = template_content.get("Resources", {})
        assert "NatGateway1" in resources, "Template should contain NAT gateways"
    
    def test_contains_iam_roles(self, template_content):
        """Test that template contains IAM roles"""
        resources = template_content.get("Resources", {})
        assert "EKSClusterRole" in resources, "Template should contain EKS cluster IAM role"
        assert "EKSNodeGroupRole" in resources, "Template should contain EKS node group IAM role"
    
    def test_eks_cluster_role_has_service_policy(self, template_content):
        """Test that EKS cluster role has AmazonEKSServicePolicy"""
        resources = template_content.get("Resources", {})
        cluster_role = resources.get("EKSClusterRole", {})
        managed_policies = cluster_role.get("Properties", {}).get("ManagedPolicyArns", [])
        assert "arn:aws:iam::aws:policy/AmazonEKSServicePolicy" in managed_policies, \
            "EKS cluster role should have AmazonEKSServicePolicy attached"
    
    def test_parameters_include_project_name(self, template_content):
        """Test that Parameters include ProjectName"""
        parameters = template_content.get("Parameters", {})
        assert "ProjectName" in parameters, "Parameters should include ProjectName"
    
    def test_parameters_include_node_config(self, template_content):
        """Test that Parameters include node configuration"""
        parameters = template_content.get("Parameters", {})
        assert "NodeInstanceType" in parameters, "Parameters should include NodeInstanceType"
        assert "NodeDesiredSize" in parameters, "Parameters should include NodeDesiredSize"
        assert "NodeMinSize" in parameters, "Parameters should include NodeMinSize"
        assert "NodeMaxSize" in parameters, "Parameters should include NodeMaxSize"
    
    def test_outputs_include_cluster_info(self, template_content):
        """Test that Outputs include cluster information"""
        outputs = template_content.get("Outputs", {})
        assert "EKSClusterName" in outputs, "Outputs should include EKSClusterName"
        assert "EKSClusterEndpoint" in outputs, "Outputs should include EKSClusterEndpoint"
    
    def test_outputs_include_ecr_uri(self, template_content):
        """Test that Outputs include ECR repository URI"""
        outputs = template_content.get("Outputs", {})
        assert "ECRRepositoryURI" in outputs, "Outputs should include ECRRepositoryURI"
    
    def test_outputs_include_kubectl_config(self, template_content):
        """Test that Outputs include kubectl configuration command"""
        outputs = template_content.get("Outputs", {})
        assert "ConfigureKubectl" in outputs, "Outputs should include ConfigureKubectl"


class TestCloudFormationValidation:
    """Test CloudFormation template validation (requires AWS CLI)"""
    
    @pytest.fixture
    def cloudformation_file(self):
        return Path(__file__).parent.parent / "cloudformation" / "aws" / "eks-stack.yaml"
    
    @pytest.mark.helm_tests
    def test_cloudformation_validate_template(self, cloudformation_file):
        """Test that CloudFormation template is valid"""
        import subprocess
        
        result = subprocess.run(
            [
                "aws", "cloudformation", "validate-template",
                "--template-body", f"file://{cloudformation_file}"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"CloudFormation validation failed: {result.stderr}"

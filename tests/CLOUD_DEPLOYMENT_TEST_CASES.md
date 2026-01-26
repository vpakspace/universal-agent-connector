# Cloud Deployment Test Cases

Complete list of test cases for cloud deployment templates.

## Test Files Overview

1. `test_terraform_aws.py` - AWS Terraform template tests
2. `test_terraform_gcp.py` - GCP Terraform template tests
3. `test_terraform_azure.py` - Azure Terraform template tests
4. `test_cloudformation.py` - AWS CloudFormation template tests
5. `test_deployment_scripts.py` - Deployment script tests
6. `test_deployment_guides.py` - Deployment guide tests
7. `test_cloud_deployment_integration.py` - Integration tests

## Detailed Test Cases

### AWS Terraform Tests (`test_terraform_aws.py`)

#### Structure Tests
- ✅ `test_main_tf_exists` - Verifies main.tf exists
- ✅ `test_variables_tf_exists` - Verifies variables.tf exists
- ✅ `test_outputs_tf_exists` - Verifies outputs.tf exists
- ✅ `test_helm_values_template_exists` - Verifies helm-values.yaml.tpl exists
- ✅ `test_tfvars_example_exists` - Verifies terraform.tfvars.example exists

#### Content Tests
- ✅ `test_main_tf_contains_vpc` - Verifies VPC resource exists
- ✅ `test_main_tf_contains_eks_cluster` - Verifies EKS cluster resource exists
- ✅ `test_main_tf_contains_ecr` - Verifies ECR repository resource exists
- ✅ `test_main_tf_contains_helm_release` - Verifies Helm release resource exists
- ✅ `test_variables_contains_required_vars` - Verifies required variables exist
- ✅ `test_outputs_contains_cluster_info` - Verifies cluster outputs exist
- ✅ **NEW** `test_outputs_contains_aws_region` - Verifies aws_region output exists
- ✅ **NEW** `test_outputs_contains_required_outputs` - Verifies all required outputs exist
- ✅ `test_helm_values_template_valid` - Verifies Helm values template structure
- ✅ `test_tfvars_example_valid_format` - Verifies tfvars example format

#### Configuration Tests
- ✅ `test_tfvars_example_contains_aws_region` - Verifies aws_region in example
- ✅ `test_tfvars_example_contains_project_name` - Verifies project_name in example
- ✅ `test_tfvars_example_contains_vpc_cidr` - Verifies vpc_cidr in example
- ✅ `test_tfvars_example_contains_node_config` - Verifies node configuration in example

#### Syntax Tests (Requires terraform binary)
- ✅ `test_terraform_validate` - Validates Terraform syntax

**Total: 18+ test cases**

### GCP Terraform Tests (`test_terraform_gcp.py`)

#### Structure Tests
- ✅ `test_main_tf_exists` - Verifies main.tf exists
- ✅ `test_variables_tf_exists` - Verifies variables.tf exists
- ✅ `test_helm_values_template_exists` - Verifies helm-values.yaml.tpl exists
- ✅ `test_tfvars_example_exists` - Verifies terraform.tfvars.example exists

#### Content Tests
- ✅ `test_main_tf_contains_vpc` - Verifies VPC network exists
- ✅ `test_main_tf_contains_gke_cluster` - Verifies GKE cluster exists
- ✅ `test_main_tf_contains_artifact_registry` - Verifies Artifact Registry exists
- ✅ `test_main_tf_contains_helm_release` - Verifies Helm release exists
- ✅ `test_variables_contains_required_vars` - Verifies required variables exist
- ✅ `test_tfvars_example_contains_gcp_project_id` - Verifies gcp_project_id in example
- ✅ `test_tfvars_example_contains_gcp_region` - Verifies gcp_region in example
- ✅ **NEW** `test_outputs_contains_gcp_region` - Verifies gcp_region output exists
- ✅ **NEW** `test_outputs_contains_required_outputs` - Verifies all required outputs exist

#### Syntax Tests (Requires terraform binary)
- ✅ `test_terraform_validate` - Validates Terraform syntax

**Total: 13+ test cases**

### Azure Terraform Tests (`test_terraform_azure.py`)

#### Structure Tests
- ✅ `test_main_tf_exists` - Verifies main.tf exists
- ✅ `test_variables_tf_exists` - Verifies variables.tf exists
- ✅ `test_helm_values_template_exists` - Verifies helm-values.yaml.tpl exists
- ✅ `test_tfvars_example_exists` - Verifies terraform.tfvars.example exists

#### Content Tests
- ✅ `test_main_tf_contains_resource_group` - Verifies resource group exists
- ✅ `test_main_tf_contains_vnet` - Verifies virtual network exists
- ✅ `test_main_tf_contains_aks_cluster` - Verifies AKS cluster exists
- ✅ `test_main_tf_contains_acr` - Verifies ACR exists
- ✅ `test_main_tf_contains_helm_release` - Verifies Helm release exists
- ✅ `test_variables_contains_required_vars` - Verifies required variables exist
- ✅ `test_tfvars_example_contains_azure_region` - Verifies azure_region in example
- ✅ `test_tfvars_example_contains_project_name` - Verifies project_name in example
- ✅ **NEW** `test_outputs_contains_required_outputs` - Verifies all required outputs exist

#### Syntax Tests (Requires terraform binary)
- ✅ `test_terraform_validate` - Validates Terraform syntax

**Total: 12+ test cases**

### CloudFormation Tests (`test_cloudformation.py`)

#### Structure Tests
- ✅ `test_cloudformation_file_exists` - Verifies template file exists
- ✅ `test_cloudformation_valid_yaml` - Verifies template is valid YAML

#### Content Tests
- ✅ `test_has_parameters` - Verifies Parameters section exists
- ✅ `test_has_resources` - Verifies Resources section exists
- ✅ `test_has_outputs` - Verifies Outputs section exists
- ✅ `test_contains_vpc_resource` - Verifies VPC resource exists
- ✅ `test_contains_eks_cluster` - Verifies EKS cluster exists
- ✅ `test_contains_eks_node_group` - Verifies EKS node group exists
- ✅ `test_contains_ecr_repository` - Verifies ECR repository exists
- ✅ `test_contains_public_subnets` - Verifies public subnets exist
- ✅ `test_contains_private_subnets` - Verifies private subnets exist
- ✅ `test_contains_nat_gateways` - Verifies NAT gateways exist
- ✅ `test_contains_iam_roles` - Verifies IAM roles exist
- ✅ **NEW** `test_eks_cluster_role_has_service_policy` - Verifies EKS service policy attached
- ✅ `test_parameters_include_project_name` - Verifies ProjectName parameter
- ✅ `test_parameters_include_node_config` - Verifies node configuration parameters
- ✅ `test_outputs_include_cluster_info` - Verifies cluster outputs
- ✅ `test_outputs_include_ecr_uri` - Verifies ECR URI output
- ✅ `test_outputs_include_kubectl_config` - Verifies kubectl config output

#### Validation Tests (Requires AWS CLI)
- ✅ `test_cloudformation_validate_template` - Validates CloudFormation template

**Total: 16+ test cases**

### Deployment Script Tests (`test_deployment_scripts.py`)

#### Structure Tests
- ✅ `test_bash_script_exists` - Verifies deploy.sh exists
- ✅ `test_powershell_script_exists` - Verifies deploy.ps1 exists
- ✅ `test_bash_script_executable` - Verifies deploy.sh is executable

#### Content Tests
- ✅ `test_bash_script_has_shebang` - Verifies shebang exists
- ✅ `test_bash_script_checks_prerequisites` - Verifies prerequisites checking
- ✅ `test_bash_script_has_aws_function` - Verifies AWS deployment function
- ✅ `test_bash_script_has_gcp_function` - Verifies GCP deployment function
- ✅ `test_bash_script_has_azure_function` - Verifies Azure deployment function
- ✅ `test_bash_script_handles_providers` - Verifies all providers supported
- ✅ `test_powershell_script_has_param` - Verifies Provider parameter
- ✅ `test_powershell_script_validates_provider` - Verifies provider validation
- ✅ `test_powershell_script_has_aws_function` - Verifies AWS function
- ✅ `test_powershell_script_has_gcp_function` - Verifies GCP function
- ✅ `test_powershell_script_has_azure_function` - Verifies Azure function
- ✅ `test_bash_script_has_error_handling` - Verifies error handling
- ✅ `test_bash_script_has_colored_output` - Verifies colored output
- ✅ `test_powershell_script_has_error_handling` - Verifies error handling
- ✅ **NEW** `test_bash_script_references_terraform_outputs` - Verifies output references
- ✅ **NEW** `test_powershell_script_references_terraform_outputs` - Verifies output references

#### Syntax Tests (Requires bash/powershell)
- ✅ `test_bash_script_syntax_valid` - Validates bash syntax
- ✅ `test_powershell_script_syntax_valid` - Validates PowerShell syntax

**Total: 18+ test cases**

### Deployment Guide Tests (`test_deployment_guides.py`)

#### Structure Tests
- ✅ `test_aws_guide_exists` - Verifies AWS guide exists
- ✅ `test_gcp_guide_exists` - Verifies GCP guide exists
- ✅ `test_azure_guide_exists` - Verifies Azure guide exists
- ✅ `test_readme_exists` - Verifies README exists
- ✅ **NEW** `test_quick_start_guide_exists` - Verifies Quick Start guide exists

#### Content Tests
- ✅ `test_aws_guide_has_prerequisites` - Verifies prerequisites section
- ✅ `test_aws_guide_has_terraform_steps` - Verifies Terraform steps
- ✅ `test_aws_guide_has_cloudformation_steps` - Verifies CloudFormation steps
- ✅ `test_aws_guide_has_troubleshooting` - Verifies troubleshooting section
- ✅ `test_gcp_guide_has_prerequisites` - Verifies prerequisites section
- ✅ `test_gcp_guide_has_terraform_steps` - Verifies Terraform steps
- ✅ `test_gcp_guide_has_troubleshooting` - Verifies troubleshooting section
- ✅ `test_azure_guide_has_prerequisites` - Verifies prerequisites section
- ✅ `test_azure_guide_has_terraform_steps` - Verifies Terraform steps
- ✅ `test_azure_guide_has_troubleshooting` - Verifies troubleshooting section
- ✅ `test_readme_has_quick_start` - Verifies quick start section
- ✅ `test_readme_has_aws_section` - Verifies AWS section
- ✅ `test_readme_has_gcp_section` - Verifies GCP section
- ✅ `test_readme_has_azure_section` - Verifies Azure section
- ✅ `test_aws_guide_has_security_best_practices` - Verifies security section
- ✅ `test_gcp_guide_has_security_best_practices` - Verifies security section
- ✅ `test_azure_guide_has_security_best_practices` - Verifies security section
- ✅ **NEW** `test_quick_start_has_prerequisites` - Verifies prerequisites
- ✅ **NEW** `test_quick_start_has_deployment_options` - Verifies deployment options
- ✅ **NEW** `test_quick_start_has_post_deployment` - Verifies post-deployment section

**Total: 19+ test cases**

### Integration Tests (`test_cloud_deployment_integration.py`)

#### Terraform Templates Integration
- ✅ `test_all_providers_have_main_tf` - All providers have main.tf
- ✅ `test_all_providers_have_variables_tf` - All providers have variables.tf
- ✅ `test_all_providers_have_tfvars_example` - All providers have tfvars example
- ✅ `test_all_providers_have_helm_values_template` - All providers have Helm template
- ✅ `test_all_providers_contain_kubernetes_cluster` - All providers have K8s cluster
- ✅ `test_all_providers_contain_container_registry` - All providers have registry
- ✅ `test_all_providers_contain_helm_release` - All providers have Helm release
- ✅ **NEW** `test_all_providers_have_required_outputs` - All providers have required outputs

#### Deployment Guides Integration
- ✅ `test_all_guides_exist` - All guides exist
- ✅ `test_all_guides_have_common_sections` - Common sections across guides

#### Deployment Scripts Integration
- ✅ `test_both_scripts_exist` - Both scripts exist
- ✅ `test_both_scripts_support_all_providers` - All providers supported

#### Configuration Files Integration
- ✅ `test_all_tfvars_examples_have_project_name` - Project name in all examples
- ✅ `test_all_helm_values_templates_have_image_config` - Image config in all templates

**Total: 16+ test cases**

## Running Tests

### Run All Cloud Deployment Tests
```bash
pytest tests/test_terraform_*.py tests/test_cloudformation.py tests/test_deployment_*.py -v
```

### Run Specific Test Suite
```bash
# AWS Terraform
pytest tests/test_terraform_aws.py -v

# CloudFormation
pytest tests/test_cloudformation.py -v

# Deployment Scripts
pytest tests/test_deployment_scripts.py -v

# Integration Tests
pytest tests/test_cloud_deployment_integration.py -v
```

### Run Tests with Coverage
```bash
pytest tests/test_terraform_*.py tests/test_cloudformation.py tests/test_deployment_*.py \
  --cov=terraform --cov=cloudformation --cov=deployment --cov-report=html
```

## Test Coverage Summary

- **Total Test Files**: 7
- **Total Test Cases**: 110+
- **Unit Tests**: ~80
- **Integration Tests**: ~25
- **Syntax/Validation Tests**: ~10

## Test Categories

### ✅ Structure Tests
- File existence
- File format validation
- Required files present

### ✅ Content Tests
- Resource definitions
- Variable definitions
- Output definitions
- Configuration validation

### ✅ Integration Tests
- Cross-provider consistency
- Cross-script consistency
- Configuration consistency

### ✅ Syntax/Validation Tests
- Terraform validation
- CloudFormation validation
- Script syntax validation

## Recent Additions

### New Test Cases (Latest Update)
1. Output validation tests for all providers
2. CloudFormation EKS service policy test
3. Deployment script output reference tests
4. Quick Start guide tests
5. Integration output validation tests

## Notes

- Tests marked with `@pytest.mark.helm_tests` require external tools (terraform, AWS CLI)
- These tests are skipped by default in CI environments
- Run with `--helm-tests` flag to include them


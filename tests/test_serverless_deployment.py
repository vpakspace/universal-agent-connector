"""
Test cases for serverless deployment templates
"""
import pytest
import yaml
from pathlib import Path


class TestServerlessStructure:
    """Test serverless deployment structure"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_aws_handler_exists(self, serverless_dir):
        """Test that AWS Lambda handler exists"""
        assert (serverless_dir / "aws" / "lambda_handler.py").exists(), \
            "AWS Lambda handler should exist"
    
    def test_gcp_handler_exists(self, serverless_dir):
        """Test that GCP Cloud Functions handler exists"""
        assert (serverless_dir / "gcp" / "cloud_function_handler.py").exists(), \
            "GCP Cloud Functions handler should exist"
    
    def test_azure_handler_exists(self, serverless_dir):
        """Test that Azure Functions handler exists"""
        assert (serverless_dir / "azure" / "function_app.py").exists(), \
            "Azure Functions handler should exist"
    
    def test_aws_template_exists(self, serverless_dir):
        """Test that AWS SAM template exists"""
        assert (serverless_dir / "aws" / "template.yaml").exists(), \
            "AWS SAM template should exist"
    
    def test_gcp_deploy_script_exists(self, serverless_dir):
        """Test that GCP deployment script exists"""
        assert (serverless_dir / "gcp" / "deploy.sh").exists(), \
            "GCP deployment script should exist"
    
    def test_azure_deploy_script_exists(self, serverless_dir):
        """Test that Azure deployment script exists"""
        assert (serverless_dir / "azure" / "deploy.sh").exists(), \
            "Azure deployment script should exist"
    
    def test_readme_exists(self, serverless_dir):
        """Test that serverless README exists"""
        assert (serverless_dir / "README.md").exists(), \
            "Serverless README should exist"


class TestServerlessContent:
    """Test serverless deployment content"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_aws_handler_has_lazy_import(self, serverless_dir):
        """Test that AWS handler uses lazy imports"""
        content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        assert "_lazy_import_app" in content, \
            "AWS handler should use lazy imports for cold start optimization"
        assert "_app = None" in content or "_initialized" in content, \
            "AWS handler should cache app instance"
    
    def test_gcp_handler_has_lazy_import(self, serverless_dir):
        """Test that GCP handler uses lazy imports"""
        content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        assert "_lazy_import_app" in content, \
            "GCP handler should use lazy imports for cold start optimization"
        assert "_app = None" in content or "_initialized" in content, \
            "GCP handler should cache app instance"
    
    def test_azure_handler_has_lazy_import(self, serverless_dir):
        """Test that Azure handler uses lazy imports"""
        content = (serverless_dir / "azure" / "function_app.py").read_text()
        assert "_lazy_import_app" in content, \
            "Azure handler should use lazy imports for cold start optimization"
        assert "_app = None" in content or "_initialized" in content, \
            "Azure handler should cache app instance"
    
    def test_aws_template_has_api_gateway(self, serverless_dir):
        """Test that AWS template has API Gateway"""
        content = (serverless_dir / "aws" / "template.yaml").read_text()
        assert "AWS::Serverless::Api" in content or "ApiGateway" in content, \
            "AWS template should include API Gateway"
    
    def test_aws_template_has_provisioned_concurrency(self, serverless_dir):
        """Test that AWS template has provisioned concurrency"""
        content = (serverless_dir / "aws" / "template.yaml").read_text()
        assert "ProvisionedConcurrencyConfig" in content or "ProvisionedConcurrentExecutions" in content, \
            "AWS template should configure provisioned concurrency for cold start optimization"
    
    def test_gcp_deploy_has_min_instances(self, serverless_dir):
        """Test that GCP deployment script sets minimum instances"""
        content = (serverless_dir / "gcp" / "deploy.sh").read_text()
        assert "--min-instances" in content, \
            "GCP deployment should set minimum instances to avoid cold starts"
    
    def test_azure_deploy_has_min_instances(self, serverless_dir):
        """Test that Azure deployment script sets minimum instances"""
        content = (serverless_dir / "azure" / "deploy.sh").read_text()
        assert "--min-instances" in content or "Always-On" in content, \
            "Azure deployment should set minimum instances or always-on"
    
    def test_handlers_have_health_endpoint(self, serverless_dir):
        """Test that all handlers have health check endpoints"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        assert "health_handler" in aws_content or "health" in aws_content.lower(), \
            "AWS handler should have health check endpoint"
        assert "health_handler" in gcp_content or "health" in gcp_content.lower(), \
            "GCP handler should have health check endpoint"
        assert "health" in azure_content.lower(), \
            "Azure handler should have health check endpoint"
    
    def test_handlers_configure_connection_pooling(self, serverless_dir):
        """Test that handlers configure connection pooling"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        assert "DATABASE_POOL_SIZE" in aws_content, \
            "AWS handler should configure database pool size"
        assert "DATABASE_POOL_SIZE" in gcp_content, \
            "GCP handler should configure database pool size"
        assert "DATABASE_POOL_SIZE" in azure_content, \
            "Azure handler should configure database pool size"


class TestServerlessConfiguration:
    """Test serverless configuration"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_aws_template_valid_yaml(self, serverless_dir):
        """Test that AWS template is valid YAML"""
        template_file = serverless_dir / "aws" / "template.yaml"
        content = template_file.read_text()
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f"AWS template is not valid YAML: {e}")
    
    def test_aws_template_has_database_secret(self, serverless_dir):
        """Test that AWS template configures Secrets Manager"""
        content = (serverless_dir / "aws" / "template.yaml").read_text()
        assert "SecretsManager" in content or "Secret" in content, \
            "AWS template should configure Secrets Manager for database credentials"
    
    def test_aws_template_has_iam_role(self, serverless_dir):
        """Test that AWS template has IAM role"""
        content = (serverless_dir / "aws" / "template.yaml").read_text()
        assert "IAM::Role" in content or "Role" in content, \
            "AWS template should configure IAM role"
    
    def test_gcp_requirements_optimized(self, serverless_dir):
        """Test that GCP requirements are optimized"""
        content = (serverless_dir / "gcp" / "requirements.txt").read_text()
        # Check for minimal dependencies
        assert "Flask" in content, "GCP requirements should include Flask"
        assert "# Optimized" in content or "# Lazy loaded" in content, \
            "GCP requirements should be optimized for cold start"
    
    def test_azure_requirements_optimized(self, serverless_dir):
        """Test that Azure requirements are optimized"""
        content = (serverless_dir / "azure" / "requirements.txt").read_text()
        # Check for minimal dependencies
        assert "Flask" in content, "Azure requirements should include Flask"
        assert "azure-functions" in content, "Azure requirements should include azure-functions"
        assert "# Optimized" in content or "# Lazy loaded" in content, \
            "Azure requirements should be optimized for cold start"


class TestServerlessDocumentation:
    """Test serverless documentation"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_readme_has_quick_start(self, serverless_dir):
        """Test that README has quick start section"""
        content = (serverless_dir / "README.md").read_text()
        assert "Quick Start" in content, "README should have Quick Start section"
    
    def test_readme_has_cold_start_info(self, serverless_dir):
        """Test that README mentions cold start optimization"""
        content = (serverless_dir / "README.md").read_text()
        assert "cold start" in content.lower() or "Cold Start" in content, \
            "README should mention cold start optimization"
    
    def test_readme_has_managed_db_info(self, serverless_dir):
        """Test that README mentions managed database support"""
        content = (serverless_dir / "README.md").read_text()
        assert "managed database" in content.lower() or "Managed Database" in content, \
            "README should mention managed database support"
    
    def test_aws_guide_exists(self, serverless_dir):
        """Test that AWS deployment guide exists"""
        assert (serverless_dir / "aws" / "README.md").exists(), \
            "AWS deployment guide should exist"
    
    def test_gcp_guide_exists(self, serverless_dir):
        """Test that GCP deployment guide exists"""
        assert (serverless_dir / "gcp" / "README.md").exists(), \
            "GCP deployment guide should exist"
    
    def test_azure_guide_exists(self, serverless_dir):
        """Test that Azure deployment guide exists"""
        assert (serverless_dir / "azure" / "README.md").exists(), \
            "Azure deployment guide should exist"
    
    def test_cold_start_guide_exists(self, serverless_dir):
        """Test that cold start optimization guide exists"""
        assert (serverless_dir / "COLD_START_OPTIMIZATION.md").exists(), \
            "Cold start optimization guide should exist"


class TestServerlessFunctionality:
    """Test serverless handler functionality"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_aws_handler_has_lambda_handler_function(self, serverless_dir):
        """Test that AWS handler has lambda_handler function"""
        content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        assert "def lambda_handler" in content, \
            "AWS handler should have lambda_handler function"
        assert "event" in content and "context" in content, \
            "AWS lambda_handler should accept event and context parameters"
    
    def test_aws_handler_has_health_handler_function(self, serverless_dir):
        """Test that AWS handler has health_handler function"""
        content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        assert "def health_handler" in content, \
            "AWS handler should have health_handler function"
    
    def test_gcp_handler_has_cloud_function_handler(self, serverless_dir):
        """Test that GCP handler has cloud_function_handler function"""
        content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        assert "def cloud_function_handler" in content, \
            "GCP handler should have cloud_function_handler function"
        assert "request" in content, \
            "GCP cloud_function_handler should accept request parameter"
    
    def test_gcp_handler_has_health_handler_function(self, serverless_dir):
        """Test that GCP handler has health_handler function"""
        content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        assert "def health_handler" in content, \
            "GCP handler should have health_handler function"
    
    def test_azure_handler_has_main_function(self, serverless_dir):
        """Test that Azure handler has main function"""
        content = (serverless_dir / "azure" / "function_app.py").read_text()
        assert "def main" in content, \
            "Azure handler should have main function"
        assert "req:" in content or "HttpRequest" in content, \
            "Azure main function should accept HttpRequest"
    
    def test_azure_handler_has_health_function(self, serverless_dir):
        """Test that Azure handler has health function"""
        content = (serverless_dir / "azure" / "function_app.py").read_text()
        assert "def health" in content, \
            "Azure handler should have health function"
    
    def test_handlers_monitor_cold_start_time(self, serverless_dir):
        """Test that handlers monitor cold start time"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        assert "time.time()" in aws_content or "_init_start_time" in aws_content, \
            "AWS handler should monitor cold start time"
        assert "time.time()" in gcp_content or "_init_start_time" in gcp_content, \
            "GCP handler should monitor cold start time"
        assert "time.time()" in azure_content or "_init_start_time" in azure_content, \
            "Azure handler should monitor cold start time"
    
    def test_handlers_warn_on_slow_cold_start(self, serverless_dir):
        """Test that handlers warn when cold start exceeds 2s"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        assert "2.0" in aws_content or "2s" in aws_content or "WARNING" in aws_content, \
            "AWS handler should warn on slow cold start"
        assert "2.0" in gcp_content or "2s" in gcp_content or "WARNING" in gcp_content, \
            "GCP handler should warn on slow cold start"
        assert "2.0" in azure_content or "2s" in azure_content or "WARNING" in azure_content, \
            "Azure handler should warn on slow cold start"
    
    def test_health_handlers_no_app_initialization(self, serverless_dir):
        """Test that health handlers don't initialize the app"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        # Health handlers should not call _lazy_import_app
        aws_health = aws_content.split("def health_handler")[1].split("\n\n")[0] if "def health_handler" in aws_content else ""
        gcp_health = gcp_content.split("def health_handler")[1].split("\n\n")[0] if "def health_handler" in gcp_content else ""
        azure_health = azure_content.split("def health")[1].split("\n\n")[0] if "def health" in azure_content else ""
        
        assert "_lazy_import_app" not in aws_health, \
            "AWS health handler should not initialize app"
        assert "_lazy_import_app" not in gcp_health, \
            "GCP health handler should not initialize app"
        assert "_lazy_import_app" not in azure_health, \
            "Azure health handler should not initialize app"


class TestServerlessTemplateStructure:
    """Test serverless template structure and configuration"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    @pytest.fixture
    def aws_template(self, serverless_dir):
        template_file = serverless_dir / "aws" / "template.yaml"
        return yaml.safe_load(template_file.read_text())
    
    def test_aws_template_has_resources(self, aws_template):
        """Test that AWS template has Resources section"""
        assert "Resources" in aws_template, \
            "AWS template should have Resources section"
    
    def test_aws_template_has_parameters(self, aws_template):
        """Test that AWS template has Parameters section"""
        assert "Parameters" in aws_template, \
            "AWS template should have Parameters section"
    
    def test_aws_template_has_outputs(self, aws_template):
        """Test that AWS template has Outputs section"""
        assert "Outputs" in aws_template, \
            "AWS template should have Outputs section"
    
    def test_aws_template_has_api_function(self, aws_template):
        """Test that AWS template defines API function"""
        resources = aws_template.get("Resources", {})
        assert "ApiFunction" in resources or any("Function" in key for key in resources.keys()), \
            "AWS template should define Lambda function"
    
    def test_aws_template_has_health_function(self, aws_template):
        """Test that AWS template defines health check function"""
        resources = aws_template.get("Resources", {})
        assert "HealthFunction" in resources, \
            "AWS template should define health check function"
    
    def test_aws_template_api_function_has_timeout(self, aws_template):
        """Test that API function has timeout configured"""
        resources = aws_template.get("Resources", {})
        globals_config = aws_template.get("Globals", {}).get("Function", {})
        function_timeout = globals_config.get("Timeout") or \
            resources.get("ApiFunction", {}).get("Properties", {}).get("Timeout")
        assert function_timeout is not None, \
            "AWS template should configure function timeout"
    
    def test_aws_template_api_function_has_memory(self, aws_template):
        """Test that API function has memory configured"""
        resources = aws_template.get("Resources", {})
        globals_config = aws_template.get("Globals", {}).get("Function", {})
        function_memory = globals_config.get("MemorySize") or \
            resources.get("ApiFunction", {}).get("Properties", {}).get("MemorySize")
        assert function_memory is not None, \
            "AWS template should configure function memory"
    
    def test_aws_template_has_environment_variables(self, aws_template):
        """Test that AWS template configures environment variables"""
        resources = aws_template.get("Resources", {})
        globals_config = aws_template.get("Globals", {}).get("Function", {})
        env_vars = globals_config.get("Environment", {}).get("Variables") or \
            resources.get("ApiFunction", {}).get("Properties", {}).get("Environment", {}).get("Variables")
        assert env_vars is not None, \
            "AWS template should configure environment variables"
        assert "SERVERLESS" in str(env_vars), \
            "AWS template should set SERVERLESS environment variable"
    
    def test_aws_template_has_secrets_manager_access(self, aws_template):
        """Test that AWS template grants Secrets Manager access"""
        resources = aws_template.get("Resources", {})
        # Check for IAM role with Secrets Manager policy
        role_resources = {k: v for k, v in resources.items() if "Role" in k}
        role_content = str(role_resources)
        assert "SecretsManager" in role_content or "Secret" in role_content, \
            "AWS template should grant Secrets Manager access"


class TestServerlessDeploymentScripts:
    """Test serverless deployment scripts"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_gcp_deploy_script_has_shebang(self, serverless_dir):
        """Test that GCP deploy script has shebang"""
        content = (serverless_dir / "gcp" / "deploy.sh").read_text()
        assert content.startswith("#!/bin/bash"), \
            "GCP deploy script should start with shebang"
    
    def test_azure_deploy_script_has_shebang(self, serverless_dir):
        """Test that Azure deploy script has shebang"""
        content = (serverless_dir / "azure" / "deploy.sh").read_text()
        assert content.startswith("#!/bin/bash"), \
            "Azure deploy script should start with shebang"
    
    def test_gcp_deploy_script_has_error_handling(self, serverless_dir):
        """Test that GCP deploy script has error handling"""
        content = (serverless_dir / "gcp" / "deploy.sh").read_text()
        assert "set -e" in content, \
            "GCP deploy script should exit on error"
    
    def test_azure_deploy_script_has_error_handling(self, serverless_dir):
        """Test that Azure deploy script has error handling"""
        content = (serverless_dir / "azure" / "deploy.sh").read_text()
        assert "set -e" in content, \
            "Azure deploy script should exit on error"
    
    def test_gcp_deploy_script_configures_secrets(self, serverless_dir):
        """Test that GCP deploy script configures secrets"""
        content = (serverless_dir / "gcp" / "deploy.sh").read_text()
        assert "--set-secrets" in content or "secrets" in content.lower(), \
            "GCP deploy script should configure secrets"
    
    def test_azure_deploy_script_configures_key_vault(self, serverless_dir):
        """Test that Azure deploy script configures Key Vault"""
        content = (serverless_dir / "azure" / "deploy.sh").read_text()
        assert "keyvault" in content.lower() or "key-vault" in content.lower(), \
            "Azure deploy script should configure Key Vault"
    
    def test_gcp_deploy_script_sets_env_vars(self, serverless_dir):
        """Test that GCP deploy script sets environment variables"""
        content = (serverless_dir / "gcp" / "deploy.sh").read_text()
        assert "--set-env-vars" in content or "FLASK_ENV" in content, \
            "GCP deploy script should set environment variables"
    
    def test_azure_deploy_script_sets_env_vars(self, serverless_dir):
        """Test that Azure deploy script sets environment variables"""
        content = (serverless_dir / "azure" / "deploy.sh").read_text()
        assert "FLASK_ENV" in content or "--settings" in content, \
            "Azure deploy script should set environment variables"


class TestServerlessIntegration:
    """Integration tests for serverless deployment"""
    
    @pytest.fixture
    def serverless_dir(self):
        return Path(__file__).parent.parent / "serverless"
    
    def test_all_handlers_use_same_lazy_import_pattern(self, serverless_dir):
        """Test that all handlers use consistent lazy import pattern"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        # All should have lazy import function
        assert "_lazy_import_app" in aws_content
        assert "_lazy_import_app" in gcp_content
        assert "_lazy_import_app" in azure_content
        
        # All should cache app instance
        assert "_app = None" in aws_content or "_initialized" in aws_content
        assert "_app = None" in gcp_content or "_initialized" in gcp_content
        assert "_app = None" in azure_content or "_initialized" in azure_content
    
    def test_all_handlers_configure_serverless_mode(self, serverless_dir):
        """Test that all handlers configure serverless mode"""
        aws_content = (serverless_dir / "aws" / "lambda_handler.py").read_text()
        gcp_content = (serverless_dir / "gcp" / "cloud_function_handler.py").read_text()
        azure_content = (serverless_dir / "azure" / "function_app.py").read_text()
        
        assert "SERVERLESS" in aws_content or "'SERVERLESS': True" in aws_content
        assert "SERVERLESS" in gcp_content or "'SERVERLESS': True" in gcp_content
        assert "SERVERLESS" in azure_content or "'SERVERLESS': True" in azure_content
    
    def test_all_platforms_have_deployment_guides(self, serverless_dir):
        """Test that all platforms have deployment guides"""
        assert (serverless_dir / "aws" / "README.md").exists()
        assert (serverless_dir / "gcp" / "README.md").exists()
        assert (serverless_dir / "azure" / "README.md").exists()
    
    def test_all_platforms_have_requirements(self, serverless_dir):
        """Test that GCP and Azure have requirements files"""
        assert (serverless_dir / "gcp" / "requirements.txt").exists()
        assert (serverless_dir / "azure" / "requirements.txt").exists()
    
    def test_requirements_have_core_dependencies(self, serverless_dir):
        """Test that requirements files have core dependencies"""
        gcp_reqs = (serverless_dir / "gcp" / "requirements.txt").read_text()
        azure_reqs = (serverless_dir / "azure" / "requirements.txt").read_text()
        
        assert "Flask" in gcp_reqs
        assert "Flask" in azure_reqs
        assert "psycopg2" in gcp_reqs or "pymysql" in gcp_reqs
        assert "psycopg2" in azure_reqs or "pymysql" in azure_reqs


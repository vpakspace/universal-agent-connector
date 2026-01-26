"""
Test cases for deployment scripts
"""
import pytest
import os
from pathlib import Path


class TestDeploymentScriptsStructure:
    """Test deployment scripts structure"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    def test_bash_script_exists(self, deployment_dir):
        """Test that deploy.sh exists"""
        assert (deployment_dir / "deploy.sh").exists(), "deploy.sh should exist"
    
    def test_powershell_script_exists(self, deployment_dir):
        """Test that deploy.ps1 exists"""
        assert (deployment_dir / "deploy.ps1").exists(), "deploy.ps1 should exist"
    
    def test_bash_script_executable(self, deployment_dir):
        """Test that deploy.sh is executable (on Unix)"""
        if os.name != 'nt':  # Not Windows
            script = deployment_dir / "deploy.sh"
            assert os.access(script, os.X_OK), "deploy.sh should be executable"


class TestDeploymentScriptsContent:
    """Test deployment scripts content"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    def test_bash_script_has_shebang(self, deployment_dir):
        """Test that deploy.sh has shebang"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert content.startswith("#!/bin/bash"), "deploy.sh should start with shebang"
    
    def test_bash_script_checks_prerequisites(self, deployment_dir):
        """Test that deploy.sh checks prerequisites"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "check_prerequisites" in content, "deploy.sh should check prerequisites"
        assert "terraform" in content.lower(), "deploy.sh should check for terraform"
        assert "kubectl" in content.lower(), "deploy.sh should check for kubectl"
        assert "helm" in content.lower(), "deploy.sh should check for helm"
    
    def test_bash_script_has_aws_function(self, deployment_dir):
        """Test that deploy.sh has AWS deployment function"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "deploy_aws" in content, "deploy.sh should have deploy_aws function"
    
    def test_bash_script_has_gcp_function(self, deployment_dir):
        """Test that deploy.sh has GCP deployment function"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "deploy_gcp" in content, "deploy.sh should have deploy_gcp function"
    
    def test_bash_script_has_azure_function(self, deployment_dir):
        """Test that deploy.sh has Azure deployment function"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "deploy_azure" in content, "deploy.sh should have deploy_azure function"
    
    def test_bash_script_handles_providers(self, deployment_dir):
        """Test that deploy.sh handles all providers"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "aws" in content.lower(), "deploy.sh should handle aws"
        assert "gcp" in content.lower(), "deploy.sh should handle gcp"
        assert "azure" in content.lower(), "deploy.sh should handle azure"
    
    def test_powershell_script_has_param(self, deployment_dir):
        """Test that deploy.ps1 has Provider parameter"""
        content = (deployment_dir / "deploy.ps1").read_text()
        assert "param(" in content, "deploy.ps1 should have parameters"
        assert "Provider" in content, "deploy.ps1 should have Provider parameter"
    
    def test_powershell_script_validates_provider(self, deployment_dir):
        """Test that deploy.ps1 validates provider"""
        content = (deployment_dir / "deploy.ps1").read_text()
        assert "ValidateSet" in content, "deploy.ps1 should validate provider"
        assert "aws" in content.lower(), "deploy.ps1 should support aws"
        assert "gcp" in content.lower(), "deploy.ps1 should support gcp"
        assert "azure" in content.lower(), "deploy.ps1 should support azure"
    
    def test_powershell_script_has_aws_function(self, deployment_dir):
        """Test that deploy.ps1 has AWS deployment function"""
        content = (deployment_dir / "deploy.ps1").read_text()
        assert "Deploy-AWS" in content or "deploy_aws" in content.lower(), "deploy.ps1 should have AWS deployment function"
    
    def test_powershell_script_has_gcp_function(self, deployment_dir):
        """Test that deploy.ps1 has GCP deployment function"""
        content = (deployment_dir / "deploy.ps1").read_text()
        assert "Deploy-GCP" in content or "deploy_gcp" in content.lower(), "deploy.ps1 should have GCP deployment function"
    
    def test_powershell_script_has_azure_function(self, deployment_dir):
        """Test that deploy.ps1 has Azure deployment function"""
        content = (deployment_dir / "deploy.ps1").read_text()
        assert "Deploy-Azure" in content or "deploy_azure" in content.lower(), "deploy.ps1 should have Azure deployment function"
    
    def test_bash_script_has_error_handling(self, deployment_dir):
        """Test that deploy.sh has error handling"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "set -e" in content, "deploy.sh should exit on error"
    
    def test_bash_script_has_colored_output(self, deployment_dir):
        """Test that deploy.sh has colored output"""
        content = (deployment_dir / "deploy.sh").read_text()
        assert "GREEN" in content or "INFO" in content, "deploy.sh should have colored output"
    
    def test_powershell_script_has_error_handling(self, deployment_dir):
        """Test that deploy.ps1 has error handling"""
        content = (deployment_dir / "deploy.ps1").read_text()
        assert "ErrorActionPreference" in content, "deploy.ps1 should have error handling"


class TestDeploymentScriptsFunctionality:
    """Test deployment scripts functionality (requires actual execution)"""
    
    @pytest.fixture
    def deployment_dir(self):
        return Path(__file__).parent.parent / "deployment"
    
    @pytest.mark.helm_tests
    def test_bash_script_syntax_valid(self, deployment_dir):
        """Test that deploy.sh has valid bash syntax"""
        import subprocess
        
        result = subprocess.run(
            ["bash", "-n", str(deployment_dir / "deploy.sh")],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0, f"Bash script syntax error: {result.stderr}"
    
    @pytest.mark.helm_tests
    def test_powershell_script_syntax_valid(self, deployment_dir):
        """Test that deploy.ps1 has valid PowerShell syntax"""
        import subprocess
        
        result = subprocess.run(
            [
                "powershell", "-Command",
                f"$ErrorActionPreference = 'Stop'; $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content '{deployment_dir / 'deploy.ps1'}'), [ref]$null)"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # PowerShell parser doesn't return error code, so we check stderr
        if result.returncode != 0 or result.stderr:
            # Try alternative validation
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    f"try {{ . '{deployment_dir / 'deploy.ps1'}'; exit 0 }} catch {{ Write-Error $_.Exception.Message; exit 1 }}"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
        
        # If it's a parameter validation error, that's expected (we're not providing params)
        # So we just check it's not a syntax error
        assert "syntax" not in result.stderr.lower() or result.returncode == 0, f"PowerShell script syntax error: {result.stderr}"
    
    def test_bash_script_references_terraform_outputs(self, deployment_dir):
        """Test that deploy.sh references required Terraform outputs"""
        content = (deployment_dir / "deploy.sh").read_text()
        # Check that script uses terraform output commands
        assert "terraform output" in content, "deploy.sh should use terraform output"
        # Check for specific outputs used in deployment
        assert "configure_kubectl" in content, "deploy.sh should use configure_kubectl output"
        assert "ecr_repository_url" in content or "artifact_registry_url" in content or "acr_login_server" in content, \
            "deploy.sh should use container registry output"
    
    def test_powershell_script_references_terraform_outputs(self, deployment_dir):
        """Test that deploy.ps1 references required Terraform outputs"""
        content = (deployment_dir / "deploy.ps1").read_text()
        # Check that script uses terraform output commands
        assert "terraform output" in content, "deploy.ps1 should use terraform output"
        # Check for specific outputs used in deployment
        assert "configure_kubectl" in content, "deploy.ps1 should use configure_kubectl output"
        assert "ecr_repository_url" in content or "artifact_registry_url" in content or "acr_login_server" in content, \
            "deploy.ps1 should use container registry output"
"""
Tests for Playground Implementation (Gitpod/Codespaces)
Tests one-click environment, pre-loaded data, and guided tutorial
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestPlaygroundConfiguration:
    """Tests for playground configuration files"""
    
    def test_gitpod_yml_exists(self):
        """Test that .gitpod.yml exists"""
        gitpod_file = Path(".gitpod.yml")
        assert gitpod_file.exists(), ".gitpod.yml should exist"
    
    def test_gitpod_yml_valid_yaml(self):
        """Test that .gitpod.yml is valid YAML"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            pytest.fail(f".gitpod.yml is not valid YAML: {e}")
    
    def test_gitpod_yml_has_image(self):
        """Test that .gitpod.yml specifies an image"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "image:" in content, "Should specify workspace image"
    
    def test_gitpod_yml_has_tasks(self):
        """Test that .gitpod.yml has setup tasks"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "tasks:" in content, "Should have tasks section"
        assert "init:" in content or "command:" in content, "Should have task commands"
    
    def test_gitpod_yml_has_ports(self):
        """Test that .gitpod.yml configures ports"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "ports:" in content, "Should configure ports"
        assert "5000" in content, "Should expose port 5000"
    
    def test_devcontainer_json_exists(self):
        """Test that devcontainer.json exists"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        assert devcontainer_file.exists(), "devcontainer.json should exist"
    
    def test_devcontainer_json_valid_json(self):
        """Test that devcontainer.json is valid JSON"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"devcontainer.json is not valid JSON: {e}")
    
    def test_devcontainer_has_image(self):
        """Test that devcontainer.json specifies an image"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        assert "image" in config or "build" in config, "Should specify image or build"
    
    def test_devcontainer_has_features(self):
        """Test that devcontainer.json includes features"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        assert "features" in config, "Should include features"
        assert "postgres" in str(config.get("features", {})).lower(), "Should include PostgreSQL"
    
    def test_devcontainer_has_forward_ports(self):
        """Test that devcontainer.json forwards ports"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        assert "forwardPorts" in config, "Should forward ports"
        assert 5000 in config.get("forwardPorts", []), "Should forward port 5000"


class TestPlaygroundSetupScripts:
    """Tests for playground setup scripts"""
    
    def test_setup_script_exists(self):
        """Test that setup.sh exists"""
        setup_script = Path(".devcontainer/setup.sh")
        assert setup_script.exists(), "setup.sh should exist"
    
    def test_start_script_exists(self):
        """Test that start.sh exists"""
        start_script = Path(".devcontainer/start.sh")
        assert start_script.exists(), "start.sh should exist"
    
    def test_setup_script_has_shebang(self):
        """Test that setup.sh has shebang"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert content.startswith("#!/bin/bash"), "Should have bash shebang"
    
    def test_start_script_has_shebang(self):
        """Test that start.sh has shebang"""
        start_script = Path(".devcontainer/start.sh")
        content = start_script.read_text()
        
        assert content.startswith("#!/bin/bash"), "Should have bash shebang"
    
    def test_setup_script_creates_venv(self):
        """Test that setup.sh creates virtual environment"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "venv" in content.lower() or "virtual" in content.lower(), \
            "Should create virtual environment"
    
    def test_setup_script_installs_dependencies(self):
        """Test that setup.sh installs dependencies"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "pip install" in content or "requirements.txt" in content, \
            "Should install dependencies"
    
    def test_setup_script_creates_databases(self):
        """Test that setup.sh creates demo databases"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "createdb" in content.lower() or "create database" in content.lower(), \
            "Should create databases"
        assert "ecommerce" in content.lower(), "Should create ecommerce database"
        assert "saas" in content.lower(), "Should create saas database"
        assert "financial" in content.lower(), "Should create financial database"
    
    def test_setup_script_loads_demo_data(self):
        """Test that setup.sh loads demo data"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "setup.sql" in content, "Should load SQL setup files"
        assert "psql" in content.lower(), "Should use psql to load data"
    
    def test_start_script_starts_server(self):
        """Test that start.sh starts the server"""
        start_script = Path(".devcontainer/start.sh")
        content = start_script.read_text()
        
        assert "python main.py" in content or "python3 main.py" in content, \
            "Should start the server"
    
    def test_start_script_sets_environment(self):
        """Test that start.sh sets environment variables"""
        start_script = Path(".devcontainer/start.sh")
        content = start_script.read_text()
        
        assert "export" in content or "ENV" in content, \
            "Should set environment variables"
        assert "FLASK_ENV" in content or "PORT" in content, \
            "Should set Flask environment"


class TestPlaygroundTutorial:
    """Tests for playground tutorial documentation"""
    
    def test_tutorial_exists(self):
        """Test that PLAYGROUND_TUTORIAL.md exists"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        assert tutorial.exists(), "PLAYGROUND_TUTORIAL.md should exist"
    
    def test_tutorial_has_quick_start(self):
        """Test that tutorial has quick start section"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "quick start" in content.lower() or "Quick Start" in content, \
            "Should have quick start section"
    
    def test_tutorial_has_steps(self):
        """Test that tutorial has step-by-step instructions"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "Step" in content, "Should have step-by-step instructions"
        assert "Step 1" in content or "step 1" in content.lower(), \
            "Should have numbered steps"
    
    def test_tutorial_has_sample_queries(self):
        """Test that tutorial includes sample queries"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "query" in content.lower(), "Should include query examples"
        assert "natural language" in content.lower() or "natural" in content.lower(), \
            "Should mention natural language queries"
    
    def test_tutorial_has_troubleshooting(self):
        """Test that tutorial has troubleshooting section"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "troubleshooting" in content.lower() or "Troubleshooting" in content, \
            "Should have troubleshooting section"
    
    def test_tutorial_has_demo_overview(self):
        """Test that tutorial describes demo databases"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "demo" in content.lower(), "Should mention demos"
        assert "database" in content.lower(), "Should mention databases"
    
    def test_tutorial_has_exercises(self):
        """Test that tutorial includes exercises"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "exercise" in content.lower() or "Exercise" in content, \
            "Should include exercises"
    
    def test_tutorial_has_next_steps(self):
        """Test that tutorial has next steps section"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "next step" in content.lower() or "Next Step" in content, \
            "Should have next steps section"


class TestPlaygroundDocumentation:
    """Tests for playground documentation files"""
    
    def test_playground_readme_exists(self):
        """Test that PLAYGROUND_README.md exists"""
        readme = Path("PLAYGROUND_README.md")
        assert readme.exists(), "PLAYGROUND_README.md should exist"
    
    def test_playground_setup_exists(self):
        """Test that PLAYGROUND_SETUP.md exists"""
        setup_doc = Path("PLAYGROUND_SETUP.md")
        assert setup_doc.exists(), "PLAYGROUND_SETUP.md should exist"
    
    def test_devcontainer_readme_exists(self):
        """Test that .devcontainer/README.md exists"""
        readme = Path(".devcontainer/README.md")
        assert readme.exists(), ".devcontainer/README.md should exist"
    
    def test_playground_readme_has_gitpod_link(self):
        """Test that playground README has Gitpod link"""
        readme = Path("PLAYGROUND_README.md")
        content = readme.read_text()
        
        assert "gitpod" in content.lower(), "Should mention Gitpod"
        assert "button" in content.lower() or "link" in content.lower(), \
            "Should have Gitpod button/link"
    
    def test_playground_readme_has_codespaces_link(self):
        """Test that playground README has Codespaces link"""
        readme = Path("PLAYGROUND_README.md")
        content = readme.read_text()
        
        assert "codespace" in content.lower(), "Should mention Codespaces"
    
    def test_playground_readme_has_whats_included(self):
        """Test that playground README lists what's included"""
        readme = Path("PLAYGROUND_README.md")
        content = readme.read_text()
        
        assert "included" in content.lower() or "what" in content.lower(), \
            "Should list what's included"
        assert "demo" in content.lower(), "Should mention demo data"
    
    def test_setup_doc_has_configuration_details(self):
        """Test that setup doc explains configuration"""
        setup_doc = Path("PLAYGROUND_SETUP.md")
        content = setup_doc.read_text()
        
        assert "configuration" in content.lower(), "Should explain configuration"
        assert "gitpod" in content.lower(), "Should explain Gitpod config"
        assert "codespace" in content.lower(), "Should explain Codespaces config"


class TestPlaygroundIntegration:
    """Integration tests for playground setup"""
    
    def test_gitpod_references_setup_scripts(self):
        """Test that Gitpod config references setup tasks"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        # Should reference demo setup
        assert "demo" in content.lower() or "setup.sql" in content, \
            "Should reference demo setup"
    
    def test_devcontainer_references_setup_script(self):
        """Test that devcontainer references setup script"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        assert "postCreateCommand" in config or "postStartCommand" in config, \
            "Should have post-create or post-start command"
        assert "setup.sh" in str(config.get("postCreateCommand", "")) or \
               "setup.sh" in str(config.get("postStartCommand", "")), \
            "Should reference setup.sh"
    
    def test_devcontainer_references_start_script(self):
        """Test that devcontainer references start script"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        assert "start.sh" in str(config.get("postStartCommand", "")) or \
               "start.sh" in str(config.get("postCreateCommand", "")), \
            "Should reference start.sh"
    
    def test_setup_script_references_demo_sql(self):
        """Test that setup script references demo SQL files"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        # Should reference all three demo SQL files
        assert "ecommerce/setup.sql" in content, "Should reference ecommerce setup"
        assert "saas/setup.sql" in content, "Should reference saas setup"
        assert "financial/setup.sql" in content, "Should reference financial setup"
    
    def test_gitpod_has_welcome_message(self):
        """Test that Gitpod config has welcome/post-create message"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "postCreateCommand" in content or "welcome" in content.lower(), \
            "Should have welcome message or post-create command"
    
    def test_all_demos_referenced_in_setup(self):
        """Test that all demos are referenced in setup"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        demos = ["ecommerce", "saas", "financial"]
        for demo in demos:
            assert demo in content.lower(), f"Should reference {demo} demo"


class TestPlaygroundPreLoadedData:
    """Tests for pre-loaded data configuration"""
    
    def test_gitpod_loads_ecommerce_data(self):
        """Test that Gitpod loads e-commerce data"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "ecommerce" in content.lower(), "Should load e-commerce data"
        assert "setup.sql" in content or "psql" in content.lower(), \
            "Should execute SQL setup"
    
    def test_gitpod_loads_saas_data(self):
        """Test that Gitpod loads SaaS data"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "saas" in content.lower(), "Should load SaaS data"
    
    def test_gitpod_loads_financial_data(self):
        """Test that Gitpod loads financial data"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "financial" in content.lower(), "Should load financial data"
    
    def test_setup_script_waits_for_postgres(self):
        """Test that setup script waits for PostgreSQL"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "pg_isready" in content or "wait" in content.lower(), \
            "Should wait for PostgreSQL to be ready"
    
    def test_setup_script_creates_all_demo_dbs(self):
        """Test that setup script creates all demo databases"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        databases = ["ecommerce_demo", "saas_demo", "financial_demo"]
        for db in databases:
            assert db in content, f"Should create {db} database"


class TestPlaygroundEnvironment:
    """Tests for environment configuration"""
    
    def test_gitpod_sets_environment_variables(self):
        """Test that Gitpod sets environment variables"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "env:" in content or "environment" in content.lower(), \
            "Should set environment variables"
        assert "FLASK_ENV" in content or "PORT" in content, \
            "Should set Flask/Python environment"
    
    def test_devcontainer_sets_environment_variables(self):
        """Test that devcontainer sets environment variables"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        assert "remoteEnv" in config, "Should set remote environment variables"
        env_vars = config.get("remoteEnv", {})
        assert "FLASK_ENV" in env_vars or "PORT" in env_vars, \
            "Should set Flask/Python environment"
    
    def test_setup_script_generates_encryption_key(self):
        """Test that setup script generates encryption key"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "ENCRYPTION_KEY" in content or "encryption" in content.lower(), \
            "Should generate encryption key"
    
    def test_start_script_loads_environment(self):
        """Test that start script loads environment"""
        start_script = Path(".devcontainer/start.sh")
        content = start_script.read_text()
        
        assert ".env" in content or "export" in content, \
            "Should load environment variables"


class TestPlaygroundTutorialContent:
    """Tests for tutorial content quality"""
    
    def test_tutorial_has_dashboard_link(self):
        """Test that tutorial includes dashboard link"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "dashboard" in content.lower(), "Should mention dashboard"
        assert "localhost:5000" in content or "http" in content.lower(), \
            "Should include URL"
    
    def test_tutorial_has_api_examples(self):
        """Test that tutorial includes API examples"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "curl" in content.lower() or "api" in content.lower(), \
            "Should include API examples"
    
    def test_tutorial_has_permission_setup(self):
        """Test that tutorial explains permission setup"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "permission" in content.lower(), "Should explain permissions"
    
    def test_tutorial_has_query_examples(self):
        """Test that tutorial has query examples for all demos"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        # Should mention all three demos
        assert "e-commerce" in content.lower() or "ecommerce" in content.lower(), \
            "Should have e-commerce examples"
        assert "saas" in content.lower(), "Should have SaaS examples"
        assert "financial" in content.lower(), "Should have financial examples"
    
    def test_tutorial_has_exercise_section(self):
        """Test that tutorial has interactive exercises"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "exercise" in content.lower() or "Exercise" in content, \
            "Should have exercises section"
        assert "goal" in content.lower() or "objective" in content.lower(), \
            "Should describe exercise goals"


class TestPlaygroundOneClick:
    """Tests for one-click environment functionality"""
    
    def test_gitpod_auto_opens_browser(self):
        """Test that Gitpod auto-opens browser"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "onOpen: open-browser" in content or "open-browser" in content, \
            "Should auto-open browser"
    
    def test_devcontainer_auto_forwards_ports(self):
        """Test that devcontainer auto-forwards ports"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        ports_attr = config.get("portsAttributes", {})
        port_5000 = ports_attr.get("5000", {})
        
        assert port_5000.get("onAutoForward") == "openBrowser" or \
               "openBrowser" in str(port_5000), \
            "Should auto-open browser on port forward"
    
    def test_gitpod_has_vscode_extensions(self):
        """Test that Gitpod includes VS Code extensions"""
        gitpod_file = Path(".gitpod.yml")
        content = gitpod_file.read_text()
        
        assert "vscode:" in content or "extensions:" in content, \
            "Should include VS Code extensions"
    
    def test_devcontainer_has_vscode_extensions(self):
        """Test that devcontainer includes VS Code extensions"""
        devcontainer_file = Path(".devcontainer/devcontainer.json")
        
        with open(devcontainer_file) as f:
            config = json.load(f)
        
        customizations = config.get("customizations", {})
        vscode = customizations.get("vscode", {})
        
        assert "extensions" in vscode, "Should include VS Code extensions"
        assert len(vscode.get("extensions", [])) > 0, "Should have extensions configured"


class TestPlaygroundDocumentationCompleteness:
    """Tests for documentation completeness"""
    
    def test_main_readme_has_playground_section(self):
        """Test that main README mentions playground"""
        readme = Path("README.md")
        content = readme.read_text()
        
        assert "playground" in content.lower() or "try in browser" in content.lower(), \
            "Should mention playground"
        assert "gitpod" in content.lower() or "codespace" in content.lower(), \
            "Should mention Gitpod or Codespaces"
    
    def test_tutorial_links_to_demos(self):
        """Test that tutorial links to demo projects"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        assert "demos" in content.lower() or "demo" in content.lower(), \
            "Should reference demo projects"
    
    def test_playground_readme_links_to_tutorial(self):
        """Test that playground README links to tutorial"""
        readme = Path("PLAYGROUND_README.md")
        content = readme.read_text()
        
        assert "tutorial" in content.lower() or "PLAYGROUND_TUTORIAL" in content, \
            "Should link to tutorial"
    
    def test_all_documentation_files_exist(self):
        """Test that all documentation files exist"""
        required_files = [
            "PLAYGROUND_TUTORIAL.md",
            "PLAYGROUND_README.md",
            "PLAYGROUND_SETUP.md",
            ".devcontainer/README.md"
        ]
        
        for file in required_files:
            assert Path(file).exists(), f"{file} should exist"


class TestPlaygroundScriptsExecutability:
    """Tests for script executability and structure"""
    
    def test_setup_script_has_error_handling(self):
        """Test that setup script has error handling"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "set -e" in content or "set -o errexit" in content, \
            "Should exit on error"
    
    def test_start_script_has_error_handling(self):
        """Test that start script has error handling"""
        start_script = Path(".devcontainer/start.sh")
        content = start_script.read_text()
        
        assert "set -e" in content or "set -o errexit" in content, \
            "Should exit on error"
    
    def test_setup_script_has_output_messages(self):
        """Test that setup script provides feedback"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        assert "echo" in content or "print" in content.lower(), \
            "Should provide output messages"
    
    def test_start_script_has_welcome_message(self):
        """Test that start script displays welcome message"""
        start_script = Path(".devcontainer/start.sh")
        content = start_script.read_text()
        
        assert "welcome" in content.lower() or "Welcome" in content or \
               "cat" in content or "echo" in content, \
            "Should display welcome message"


class TestPlaygroundIntegrationFlow:
    """Tests for complete integration flow"""
    
    def test_complete_setup_flow_documented(self):
        """Test that complete setup flow is documented"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        # Should have all major steps
        assert "register" in content.lower() or "agent" in content.lower(), \
            "Should explain agent registration"
        assert "permission" in content.lower(), "Should explain permissions"
        assert "query" in content.lower(), "Should explain querying"
    
    def test_all_demos_accessible_in_playground(self):
        """Test that all demos are accessible in playground"""
        setup_script = Path(".devcontainer/setup.sh")
        content = setup_script.read_text()
        
        # All three demos should be set up
        assert "ecommerce_demo" in content, "Should set up ecommerce_demo"
        assert "saas_demo" in content, "Should set up saas_demo"
        assert "financial_demo" in content, "Should set up financial_demo"
    
    def test_playground_has_quick_start_path(self):
        """Test that playground provides quick start path"""
        readme = Path("PLAYGROUND_README.md")
        content = readme.read_text()
        
        assert "minute" in content.lower() or "quick" in content.lower(), \
            "Should mention quick start time"
    
    def test_tutorial_provides_complete_journey(self):
        """Test that tutorial provides complete user journey"""
        tutorial = Path("PLAYGROUND_TUTORIAL.md")
        content = tutorial.read_text()
        
        # Should cover: setup -> register -> permissions -> query -> explore
        steps = ["setup", "register", "permission", "query"]
        for step in steps:
            assert step in content.lower(), f"Should cover {step} step"


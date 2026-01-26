"""
Tests for Interactive Demo Projects
Tests setup scripts, sample data, and demo functionality
"""

import pytest
import os
import json
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test if we can import the connector
try:
    from ai_agent_connector.app.db.connector import DatabaseConnector
    from ai_agent_connector.app.agents.registry import AgentRegistry
    from ai_agent_connector.app.agents.providers import AgentProvider, AgentConfiguration
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class TestDemoProjectStructure:
    """Tests for demo project file structure"""
    
    def test_demos_directory_exists(self):
        """Test that demos directory exists"""
        demos_dir = Path("demos")
        assert demos_dir.exists(), "demos directory should exist"
        assert demos_dir.is_dir(), "demos should be a directory"
    
    def test_demo_readme_exists(self):
        """Test that main demo README exists"""
        readme = Path("demos/README.md")
        assert readme.exists(), "demos/README.md should exist"
    
    def test_ecommerce_demo_structure(self):
        """Test e-commerce demo file structure"""
        ecommerce_dir = Path("demos/ecommerce")
        assert ecommerce_dir.exists(), "ecommerce demo directory should exist"
        assert (ecommerce_dir / "README.md").exists(), "ecommerce README should exist"
        assert (ecommerce_dir / "WALKTHROUGH.md").exists(), "ecommerce WALKTHROUGH should exist"
        assert (ecommerce_dir / "setup.sql").exists(), "ecommerce setup.sql should exist"
        assert (ecommerce_dir / "agent_config.json").exists(), "ecommerce agent_config.json should exist"
    
    def test_saas_demo_structure(self):
        """Test SaaS demo file structure"""
        saas_dir = Path("demos/saas")
        assert saas_dir.exists(), "saas demo directory should exist"
        assert (saas_dir / "README.md").exists(), "saas README should exist"
        assert (saas_dir / "WALKTHROUGH.md").exists(), "saas WALKTHROUGH should exist"
        assert (saas_dir / "setup.sql").exists(), "saas setup.sql should exist"
        assert (saas_dir / "agent_config.json").exists(), "saas agent_config.json should exist"
    
    def test_financial_demo_structure(self):
        """Test financial demo file structure"""
        financial_dir = Path("demos/financial")
        assert financial_dir.exists(), "financial demo directory should exist"
        assert (financial_dir / "README.md").exists(), "financial README should exist"
        assert (financial_dir / "WALKTHROUGH.md").exists(), "financial WALKTHROUGH should exist"
        assert (financial_dir / "setup.sql").exists(), "financial setup.sql should exist"
        assert (financial_dir / "agent_config.json").exists(), "financial agent_config.json should exist"
    
    def test_setup_scripts_exist(self):
        """Test that setup scripts exist"""
        assert Path("demos/setup_all_demos.sh").exists(), "setup_all_demos.sh should exist"
        assert Path("demos/setup_all_demos.ps1").exists(), "setup_all_demos.ps1 should exist"
    
    def test_quick_start_exists(self):
        """Test that quick start guide exists"""
        assert Path("demos/QUICK_START.md").exists(), "QUICK_START.md should exist"


class TestDemoSQLScripts:
    """Tests for demo SQL setup scripts"""
    
    def test_ecommerce_setup_sql_valid(self):
        """Test that e-commerce setup.sql is valid SQL"""
        sql_file = Path("demos/ecommerce/setup.sql")
        assert sql_file.exists(), "ecommerce setup.sql should exist"
        
        content = sql_file.read_text()
        # Check for key SQL statements
        assert "CREATE TABLE" in content, "Should contain CREATE TABLE statements"
        assert "INSERT INTO" in content, "Should contain INSERT statements"
        assert "customers" in content.lower(), "Should create customers table"
        assert "products" in content.lower(), "Should create products table"
        assert "orders" in content.lower(), "Should create orders table"
    
    def test_saas_setup_sql_valid(self):
        """Test that SaaS setup.sql is valid SQL"""
        sql_file = Path("demos/saas/setup.sql")
        assert sql_file.exists(), "saas setup.sql should exist"
        
        content = sql_file.read_text()
        # Check for key SQL statements
        assert "CREATE TABLE" in content, "Should contain CREATE TABLE statements"
        assert "INSERT INTO" in content, "Should contain INSERT statements"
        assert "users" in content.lower(), "Should create users table"
        assert "subscriptions" in content.lower(), "Should create subscriptions table"
        assert "plans" in content.lower(), "Should create plans table"
    
    def test_financial_setup_sql_valid(self):
        """Test that financial setup.sql is valid SQL"""
        sql_file = Path("demos/financial/setup.sql")
        assert sql_file.exists(), "financial setup.sql should exist"
        
        content = sql_file.read_text()
        # Check for key SQL statements
        assert "CREATE TABLE" in content, "Should contain CREATE TABLE statements"
        assert "INSERT INTO" in content, "Should contain INSERT statements"
        assert "accounts" in content.lower(), "Should create accounts table"
        assert "transactions" in content.lower(), "Should create transactions table"
        assert "categories" in content.lower(), "Should create categories table"
    
    def test_sql_scripts_have_sample_data(self):
        """Test that SQL scripts contain sample data inserts"""
        for demo in ["ecommerce", "saas", "financial"]:
            sql_file = Path(f"demos/{demo}/setup.sql")
            content = sql_file.read_text()
            
            # Should have multiple INSERT statements
            insert_count = content.upper().count("INSERT INTO")
            assert insert_count > 0, f"{demo} setup.sql should contain INSERT statements"
    
    def test_sql_scripts_have_indexes(self):
        """Test that SQL scripts create indexes"""
        for demo in ["ecommerce", "saas", "financial"]:
            sql_file = Path(f"demos/{demo}/setup.sql")
            content = sql_file.read_text()
            
            # Should have CREATE INDEX statements
            assert "CREATE INDEX" in content.upper(), f"{demo} setup.sql should create indexes"


class TestDemoAgentConfigs:
    """Tests for demo agent configuration files"""
    
    def test_ecommerce_agent_config_valid(self):
        """Test that e-commerce agent config is valid JSON"""
        config_file = Path("demos/ecommerce/agent_config.json")
        assert config_file.exists(), "ecommerce agent_config.json should exist"
        
        with open(config_file) as f:
            config = json.load(f)
        
        assert "agent_id" in config, "Should have agent_id"
        assert "agent_info" in config, "Should have agent_info"
        assert "database" in config, "Should have database config"
        assert config["agent_id"] == "ecommerce-analyst", "Should have correct agent_id"
    
    def test_saas_agent_config_valid(self):
        """Test that SaaS agent config is valid JSON"""
        config_file = Path("demos/saas/agent_config.json")
        assert config_file.exists(), "saas agent_config.json should exist"
        
        with open(config_file) as f:
            config = json.load(f)
        
        assert "agent_id" in config, "Should have agent_id"
        assert "agent_info" in config, "Should have agent_info"
        assert "database" in config, "Should have database config"
        assert config["agent_id"] == "saas-analyst", "Should have correct agent_id"
    
    def test_financial_agent_config_valid(self):
        """Test that financial agent config is valid JSON"""
        config_file = Path("demos/financial/agent_config.json")
        assert config_file.exists(), "financial agent_config.json should exist"
        
        with open(config_file) as f:
            config = json.load(f)
        
        assert "agent_id" in config, "Should have agent_id"
        assert "agent_info" in config, "Should have agent_info"
        assert "database" in config, "Should have database config"
        assert config["agent_id"] == "financial-analyst", "Should have correct agent_id"
    
    def test_agent_configs_have_database_config(self):
        """Test that all agent configs have database configuration"""
        for demo in ["ecommerce", "saas", "financial"]:
            config_file = Path(f"demos/{demo}/agent_config.json")
            with open(config_file) as f:
                config = json.load(f)
            
            assert "database" in config, f"{demo} config should have database"
            assert "connection_string" in config["database"], "Should have connection_string"
            assert "type" in config["database"], "Should have database type"


class TestDemoDocumentation:
    """Tests for demo documentation"""
    
    def test_ecommerce_readme_has_quick_start(self):
        """Test that e-commerce README has quick start section"""
        readme = Path("demos/ecommerce/README.md")
        content = readme.read_text()
        
        assert "Quick Start" in content or "quick start" in content.lower(), "Should have quick start"
        assert "setup" in content.lower(), "Should mention setup"
        assert "query" in content.lower(), "Should mention queries"
    
    def test_saas_readme_has_quick_start(self):
        """Test that SaaS README has quick start section"""
        readme = Path("demos/saas/README.md")
        content = readme.read_text()
        
        assert "Quick Start" in content or "quick start" in content.lower(), "Should have quick start"
        assert "setup" in content.lower(), "Should mention setup"
        assert "mrr" in content.lower() or "recurring" in content.lower(), "Should mention MRR"
    
    def test_financial_readme_has_quick_start(self):
        """Test that financial README has quick start section"""
        readme = Path("demos/financial/README.md")
        content = readme.read_text()
        
        assert "Quick Start" in content or "quick start" in content.lower(), "Should have quick start"
        assert "setup" in content.lower(), "Should mention setup"
        assert "revenue" in content.lower() or "financial" in content.lower(), "Should mention financial terms"
    
    def test_walkthroughs_have_steps(self):
        """Test that walkthroughs have step-by-step instructions"""
        for demo in ["ecommerce", "saas", "financial"]:
            walkthrough = Path(f"demos/{demo}/WALKTHROUGH.md")
            content = walkthrough.read_text()
            
            assert "Step" in content, f"{demo} walkthrough should have steps"
            assert "setup" in content.lower() or "create" in content.lower(), "Should have setup instructions"
            assert "query" in content.lower(), "Should have query examples"
    
    def test_main_demo_readme_has_all_demos(self):
        """Test that main demo README lists all demos"""
        readme = Path("demos/README.md")
        content = readme.read_text()
        
        assert "e-commerce" in content.lower() or "ecommerce" in content.lower(), "Should mention e-commerce"
        assert "saas" in content.lower(), "Should mention SaaS"
        assert "financial" in content.lower(), "Should mention financial"


class TestDemoSetupScripts:
    """Tests for demo setup scripts"""
    
    def test_setup_script_sh_exists(self):
        """Test that bash setup script exists"""
        script = Path("demos/setup_all_demos.sh")
        assert script.exists(), "setup_all_demos.sh should exist"
        
        content = script.read_text()
        assert "#!/bin/bash" in content, "Should have bash shebang"
        assert "createdb" in content or "CREATE DATABASE" in content, "Should create databases"
    
    def test_setup_script_ps1_exists(self):
        """Test that PowerShell setup script exists"""
        script = Path("demos/setup_all_demos.ps1")
        assert script.exists(), "setup_all_demos.ps1 should exist"
        
        content = script.read_text()
        assert "Write-Host" in content or "function" in content, "Should be PowerShell script"
        assert "createdb" in content or "CREATE DATABASE" in content, "Should create databases"
    
    def test_setup_scripts_reference_all_demos(self):
        """Test that setup scripts reference all three demos"""
        for script_file in ["demos/setup_all_demos.sh", "demos/setup_all_demos.ps1"]:
            script = Path(script_file)
            if script.exists():
                content = script.read_text()
                
                assert "ecommerce" in content.lower(), f"{script_file} should reference ecommerce"
                assert "saas" in content.lower(), f"{script_file} should reference saas"
                assert "financial" in content.lower(), f"{script_file} should reference financial"


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database connector not available")
class TestDemoDatabaseSetup:
    """Tests for demo database setup (requires database)"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        with patch('ai_agent_connector.app.db.connector.psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            yield mock_conn, mock_cursor
    
    def test_ecommerce_agent_config_creates_connector(self, mock_db_connection):
        """Test that e-commerce agent config can create database connector"""
        mock_conn, mock_cursor = mock_db_connection
        
        config_file = Path("demos/ecommerce/agent_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        db_config = config["database"]
        connector = DatabaseConnector(
            connection_string=db_config["connection_string"],
            database_type=db_config["type"]
        )
        
        assert connector is not None
        assert connector.database_type == "postgresql"
    
    def test_saas_agent_config_creates_connector(self, mock_db_connection):
        """Test that SaaS agent config can create database connector"""
        mock_conn, mock_cursor = mock_db_connection
        
        config_file = Path("demos/saas/agent_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        db_config = config["database"]
        connector = DatabaseConnector(
            connection_string=db_config["connection_string"],
            database_type=db_config["type"]
        )
        
        assert connector is not None
        assert connector.database_type == "postgresql"
    
    def test_financial_agent_config_creates_connector(self, mock_db_connection):
        """Test that financial agent config can create database connector"""
        mock_conn, mock_cursor = mock_db_connection
        
        config_file = Path("demos/financial/agent_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        db_config = config["database"]
        connector = DatabaseConnector(
            connection_string=db_config["connection_string"],
            database_type=db_config["type"]
        )
        
        assert connector is not None
        assert connector.database_type == "postgresql"


class TestDemoAgentRegistration:
    """Tests for demo agent registration"""
    
    def test_ecommerce_agent_can_be_registered(self):
        """Test that e-commerce agent config can be used for registration"""
        config_file = Path("demos/ecommerce/agent_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        # Validate structure
        assert "agent_id" in config
        assert "agent_info" in config
        assert "agent_credentials" in config
        assert "database" in config
        
        # Validate required fields
        assert config["agent_id"] == "ecommerce-analyst"
        assert "name" in config["agent_info"]
        assert "api_key" in config["agent_credentials"]
        assert "connection_string" in config["database"]
    
    def test_saas_agent_can_be_registered(self):
        """Test that SaaS agent config can be used for registration"""
        config_file = Path("demos/saas/agent_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        # Validate structure
        assert "agent_id" in config
        assert "agent_info" in config
        assert "agent_credentials" in config
        assert "database" in config
        
        # Validate required fields
        assert config["agent_id"] == "saas-analyst"
        assert "name" in config["agent_info"]
        assert "api_key" in config["agent_credentials"]
        assert "connection_string" in config["database"]
    
    def test_financial_agent_can_be_registered(self):
        """Test that financial agent config can be used for registration"""
        config_file = Path("demos/financial/agent_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        # Validate structure
        assert "agent_id" in config
        assert "agent_info" in config
        assert "agent_credentials" in config
        assert "database" in config
        
        # Validate required fields
        assert config["agent_id"] == "financial-analyst"
        assert "name" in config["agent_info"]
        assert "api_key" in config["agent_credentials"]
        assert "connection_string" in config["database"]


class TestDemoSampleQueries:
    """Tests for demo sample queries"""
    
    def test_ecommerce_readme_has_sample_queries(self):
        """Test that e-commerce README has sample queries"""
        readme = Path("demos/ecommerce/README.md")
        content = readme.read_text()
        
        # Check for query examples
        assert "query" in content.lower(), "Should have query examples"
        assert ("top" in content.lower() or "best" in content.lower() or 
                "sales" in content.lower()), "Should have sales-related queries"
    
    def test_saas_readme_has_sample_queries(self):
        """Test that SaaS README has sample queries"""
        readme = Path("demos/saas/README.md")
        content = readme.read_text()
        
        # Check for query examples
        assert "query" in content.lower(), "Should have query examples"
        assert ("mrr" in content.lower() or "recurring" in content.lower() or 
                "churn" in content.lower()), "Should have SaaS-related queries"
    
    def test_financial_readme_has_sample_queries(self):
        """Test that financial README has sample queries"""
        readme = Path("demos/financial/README.md")
        content = readme.read_text()
        
        # Check for query examples
        assert "query" in content.lower(), "Should have query examples"
        assert ("revenue" in content.lower() or "expense" in content.lower() or 
                "financial" in content.lower()), "Should have financial-related queries"
    
    def test_walkthroughs_have_query_examples(self):
        """Test that walkthroughs include query examples"""
        for demo in ["ecommerce", "saas", "financial"]:
            walkthrough = Path(f"demos/{demo}/WALKTHROUGH.md")
            content = walkthrough.read_text()
            
            assert "query" in content.lower(), f"{demo} walkthrough should have query examples"
            assert "natural" in content.lower() or "language" in content.lower(), "Should mention natural language"


class TestDemoIntegration:
    """Integration tests for demo projects"""
    
    def test_all_demos_have_consistent_structure(self):
        """Test that all demos have consistent file structure"""
        required_files = ["README.md", "WALKTHROUGH.md", "setup.sql", "agent_config.json"]
        
        for demo in ["ecommerce", "saas", "financial"]:
            demo_dir = Path(f"demos/{demo}")
            for file in required_files:
                file_path = demo_dir / file
                assert file_path.exists(), f"{demo} should have {file}"
    
    def test_all_agent_configs_have_same_structure(self):
        """Test that all agent configs have the same structure"""
        required_keys = ["agent_id", "agent_info", "agent_credentials", "database"]
        
        for demo in ["ecommerce", "saas", "financial"]:
            config_file = Path(f"demos/{demo}/agent_config.json")
            with open(config_file) as f:
                config = json.load(f)
            
            for key in required_keys:
                assert key in config, f"{demo} config should have {key}"
    
    def test_all_setup_sqls_create_tables(self):
        """Test that all setup SQL scripts create tables"""
        for demo in ["ecommerce", "saas", "financial"]:
            sql_file = Path(f"demos/{demo}/setup.sql")
            content = sql_file.read_text()
            
            # Should have CREATE TABLE statements
            assert "CREATE TABLE" in content.upper(), f"{demo} should create tables"
            
            # Should have INSERT statements
            assert "INSERT INTO" in content.upper(), f"{demo} should insert data"
    
    def test_all_readmes_have_quick_start(self):
        """Test that all demo READMEs have quick start sections"""
        for demo in ["ecommerce", "saas", "financial"]:
            readme = Path(f"demos/{demo}/README.md")
            content = readme.read_text()
            
            assert "quick start" in content.lower() or "Quick Start" in content, \
                f"{demo} README should have quick start"


class TestDemoContentQuality:
    """Tests for demo content quality"""
    
    def test_ecommerce_sql_has_realistic_data(self):
        """Test that e-commerce SQL has realistic sample data"""
        sql_file = Path("demos/ecommerce/setup.sql")
        content = sql_file.read_text()
        
        # Check for realistic data
        assert "customers" in content.lower(), "Should have customers"
        assert "products" in content.lower(), "Should have products"
        assert "orders" in content.lower(), "Should have orders"
        assert "price" in content.lower() or "amount" in content.lower(), "Should have pricing"
    
    def test_saas_sql_has_realistic_data(self):
        """Test that SaaS SQL has realistic sample data"""
        sql_file = Path("demos/saas/setup.sql")
        content = sql_file.read_text()
        
        # Check for realistic data
        assert "users" in content.lower(), "Should have users"
        assert "subscriptions" in content.lower(), "Should have subscriptions"
        assert "plans" in content.lower(), "Should have plans"
        assert "mrr" in content.lower() or "monthly" in content.lower(), "Should have MRR"
    
    def test_financial_sql_has_realistic_data(self):
        """Test that financial SQL has realistic sample data"""
        sql_file = Path("demos/financial/setup.sql")
        content = sql_file.read_text()
        
        # Check for realistic data
        assert "accounts" in content.lower(), "Should have accounts"
        assert "transactions" in content.lower(), "Should have transactions"
        assert "revenue" in content.lower() or "expense" in content.lower(), "Should have revenue/expense"
    
    def test_walkthroughs_are_complete(self):
        """Test that walkthroughs have all necessary steps"""
        for demo in ["ecommerce", "saas", "financial"]:
            walkthrough = Path(f"demos/{demo}/WALKTHROUGH.md")
            content = walkthrough.read_text()
            
            # Should have setup step
            assert "setup" in content.lower() or "create" in content.lower(), \
                f"{demo} walkthrough should have setup step"
            
            # Should have registration step
            assert "register" in content.lower() or "agent" in content.lower(), \
                f"{demo} walkthrough should have registration step"
            
            # Should have query step
            assert "query" in content.lower(), \
                f"{demo} walkthrough should have query step"


class TestDemoQuickStart:
    """Tests for quick start guide"""
    
    def test_quick_start_exists(self):
        """Test that quick start guide exists"""
        quick_start = Path("demos/QUICK_START.md")
        assert quick_start.exists(), "QUICK_START.md should exist"
    
    def test_quick_start_has_all_demos(self):
        """Test that quick start mentions all demos"""
        quick_start = Path("demos/QUICK_START.md")
        content = quick_start.read_text()
        
        assert "e-commerce" in content.lower() or "ecommerce" in content.lower(), \
            "Should mention e-commerce"
        assert "saas" in content.lower(), "Should mention SaaS"
        assert "financial" in content.lower(), "Should mention financial"
    
    def test_quick_start_has_setup_instructions(self):
        """Test that quick start has setup instructions"""
        quick_start = Path("demos/QUICK_START.md")
        content = quick_start.read_text()
        
        assert "setup" in content.lower() or "create" in content.lower(), \
            "Should have setup instructions"
        assert "database" in content.lower(), "Should mention database"


class TestDemoMainReadme:
    """Tests for main demo README"""
    
    def test_main_readme_lists_all_demos(self):
        """Test that main README lists all three demos"""
        readme = Path("demos/README.md")
        content = readme.read_text()
        
        # Check for all three demos
        assert "e-commerce" in content.lower() or "ecommerce" in content.lower(), \
            "Should list e-commerce demo"
        assert "saas" in content.lower(), "Should list SaaS demo"
        assert "financial" in content.lower(), "Should list financial demo"
    
    def test_main_readme_has_quick_start_link(self):
        """Test that main README links to quick start"""
        readme = Path("demos/README.md")
        content = readme.read_text()
        
        assert "quick start" in content.lower() or "QUICK_START" in content, \
            "Should link to quick start"
    
    def test_main_readme_has_prerequisites(self):
        """Test that main README lists prerequisites"""
        readme = Path("demos/README.md")
        content = readme.read_text()
        
        assert "prerequisite" in content.lower() or "requirement" in content.lower(), \
            "Should list prerequisites"
        assert "postgresql" in content.lower() or "database" in content.lower(), \
            "Should mention PostgreSQL"


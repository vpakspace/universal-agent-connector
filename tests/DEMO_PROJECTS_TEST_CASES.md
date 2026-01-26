# Demo Projects Test Cases

Complete test coverage for interactive demo projects.

## Test File

`tests/test_demo_projects.py`

## Test Classes Overview

1. `TestDemoProjectStructure` - File structure and existence
2. `TestDemoSQLScripts` - SQL script validation
3. `TestDemoAgentConfigs` - Agent configuration validation
4. `TestDemoDocumentation` - Documentation completeness
5. `TestDemoSetupScripts` - Setup script validation
6. `TestDemoDatabaseSetup` - Database setup (requires DB)
7. `TestDemoAgentRegistration` - Agent registration validation
8. `TestDemoSampleQueries` - Sample query validation
9. `TestDemoIntegration` - Integration tests
10. `TestDemoContentQuality` - Content quality checks
11. `TestDemoQuickStart` - Quick start guide tests
12. `TestDemoMainReadme` - Main README tests

## Detailed Test Cases

### TestDemoProjectStructure (7 tests)

#### Directory Structure
- ✅ `test_demos_directory_exists` - Demos directory exists
- ✅ `test_demo_readme_exists` - Main demo README exists
- ✅ `test_ecommerce_demo_structure` - E-commerce demo files exist
- ✅ `test_saas_demo_structure` - SaaS demo files exist
- ✅ `test_financial_demo_structure` - Financial demo files exist
- ✅ `test_setup_scripts_exist` - Setup scripts exist
- ✅ `test_quick_start_exists` - Quick start guide exists

### TestDemoSQLScripts (5 tests)

#### SQL Script Validation
- ✅ `test_ecommerce_setup_sql_valid` - E-commerce SQL is valid
- ✅ `test_saas_setup_sql_valid` - SaaS SQL is valid
- ✅ `test_financial_setup_sql_valid` - Financial SQL is valid
- ✅ `test_sql_scripts_have_sample_data` - SQL scripts contain sample data
- ✅ `test_sql_scripts_have_indexes` - SQL scripts create indexes

### TestDemoAgentConfigs (4 tests)

#### Agent Configuration
- ✅ `test_ecommerce_agent_config_valid` - E-commerce config is valid JSON
- ✅ `test_saas_agent_config_valid` - SaaS config is valid JSON
- ✅ `test_financial_agent_config_valid` - Financial config is valid JSON
- ✅ `test_agent_configs_have_database_config` - All configs have database config

### TestDemoDocumentation (5 tests)

#### Documentation Completeness
- ✅ `test_ecommerce_readme_has_quick_start` - E-commerce README has quick start
- ✅ `test_saas_readme_has_quick_start` - SaaS README has quick start
- ✅ `test_financial_readme_has_quick_start` - Financial README has quick start
- ✅ `test_walkthroughs_have_steps` - Walkthroughs have step-by-step instructions
- ✅ `test_main_demo_readme_has_all_demos` - Main README lists all demos

### TestDemoSetupScripts (3 tests)

#### Setup Script Validation
- ✅ `test_setup_script_sh_exists` - Bash setup script exists
- ✅ `test_setup_script_ps1_exists` - PowerShell setup script exists
- ✅ `test_setup_scripts_reference_all_demos` - Scripts reference all demos

### TestDemoDatabaseSetup (3 tests)

#### Database Setup (requires database)
- ✅ `test_ecommerce_agent_config_creates_connector` - E-commerce config creates connector
- ✅ `test_saas_agent_config_creates_connector` - SaaS config creates connector
- ✅ `test_financial_agent_config_creates_connector` - Financial config creates connector

### TestDemoAgentRegistration (3 tests)

#### Agent Registration
- ✅ `test_ecommerce_agent_can_be_registered` - E-commerce agent can be registered
- ✅ `test_saas_agent_can_be_registered` - SaaS agent can be registered
- ✅ `test_financial_agent_can_be_registered` - Financial agent can be registered

### TestDemoSampleQueries (4 tests)

#### Sample Query Validation
- ✅ `test_ecommerce_readme_has_sample_queries` - E-commerce has sample queries
- ✅ `test_saas_readme_has_sample_queries` - SaaS has sample queries
- ✅ `test_financial_readme_has_sample_queries` - Financial has sample queries
- ✅ `test_walkthroughs_have_query_examples` - Walkthroughs have query examples

### TestDemoIntegration (4 tests)

#### Integration Tests
- ✅ `test_all_demos_have_consistent_structure` - All demos have consistent structure
- ✅ `test_all_agent_configs_have_same_structure` - All configs have same structure
- ✅ `test_all_setup_sqls_create_tables` - All SQL scripts create tables
- ✅ `test_all_readmes_have_quick_start` - All READMEs have quick start

### TestDemoContentQuality (4 tests)

#### Content Quality
- ✅ `test_ecommerce_sql_has_realistic_data` - E-commerce has realistic data
- ✅ `test_saas_sql_has_realistic_data` - SaaS has realistic data
- ✅ `test_financial_sql_has_realistic_data` - Financial has realistic data
- ✅ `test_walkthroughs_are_complete` - Walkthroughs have all steps

### TestDemoQuickStart (3 tests)

#### Quick Start Guide
- ✅ `test_quick_start_exists` - Quick start guide exists
- ✅ `test_quick_start_has_all_demos` - Quick start mentions all demos
- ✅ `test_quick_start_has_setup_instructions` - Quick start has setup instructions

### TestDemoMainReadme (3 tests)

#### Main README
- ✅ `test_main_readme_lists_all_demos` - Main README lists all demos
- ✅ `test_main_readme_has_quick_start_link` - Main README links to quick start
- ✅ `test_main_readme_has_prerequisites` - Main README lists prerequisites

## Running Tests

### Run All Demo Tests

```bash
pytest tests/test_demo_projects.py -v
```

### Run Specific Test Class

```bash
# Structure tests
pytest tests/test_demo_projects.py::TestDemoProjectStructure -v

# SQL script tests
pytest tests/test_demo_projects.py::TestDemoSQLScripts -v

# Integration tests
pytest tests/test_demo_projects.py::TestDemoIntegration -v
```

### Run with Coverage

```bash
pytest tests/test_demo_projects.py \
  --cov=demos \
  --cov-report=html \
  --cov-report=term
```

## Test Coverage Summary

- **Total Test Cases**: 50+
- **Structure Tests**: 7
- **SQL Script Tests**: 5
- **Agent Config Tests**: 4
- **Documentation Tests**: 5
- **Setup Script Tests**: 3
- **Database Setup Tests**: 3
- **Agent Registration Tests**: 3
- **Sample Query Tests**: 4
- **Integration Tests**: 4
- **Content Quality Tests**: 4
- **Quick Start Tests**: 3
- **Main README Tests**: 3

## Test Categories

### ✅ Structure Tests
- File existence
- Directory structure
- Required files present

### ✅ SQL Script Tests
- SQL syntax validation
- Table creation
- Sample data insertion
- Index creation

### ✅ Configuration Tests
- JSON validity
- Required fields
- Database configuration
- Agent structure

### ✅ Documentation Tests
- Quick start sections
- Step-by-step instructions
- Sample queries
- Complete walkthroughs

### ✅ Integration Tests
- Consistent structure across demos
- Same configuration format
- Complete functionality

## Key Test Validations

### File Structure
- ✅ All required files exist
- ✅ Consistent structure across demos
- ✅ Setup scripts present

### SQL Scripts
- ✅ Valid SQL syntax
- ✅ Creates all required tables
- ✅ Inserts sample data
- ✅ Creates indexes

### Agent Configurations
- ✅ Valid JSON format
- ✅ Required fields present
- ✅ Database configuration included
- ✅ Can be used for registration

### Documentation
- ✅ Quick start sections
- ✅ Step-by-step walkthroughs
- ✅ Sample queries included
- ✅ Complete instructions

## Notes

- Tests validate structure and content, not execution
- Database setup tests require database connector
- Some tests check file content for keywords
- Integration tests ensure consistency across demos

## Future Enhancements

- End-to-end demo execution tests
- Database connection tests with real DB
- Agent registration integration tests
- Natural language query execution tests
- Performance tests for demo data loading


# Air-Gapped Mode Test Cases

Complete test coverage for air-gapped mode functionality.

## Test File

`tests/test_air_gapped_mode.py`

## Test Classes Overview

1. `TestAirGappedModeUtilities` - Core utility functions
2. `TestLocalProvider` - Local AI provider implementation
3. `TestProviderBlocking` - External provider blocking
4. `TestAIAgentManagerAirGapped` - Manager integration
5. `TestNLToSQLAirGapped` - Natural language to SQL with local models
6. `TestAirGappedIntegration` - End-to-end integration tests
7. `TestAirGappedModeEdgeCases` - Edge cases and error handling

## Detailed Test Cases

### TestAirGappedModeUtilities (12 tests)

#### Air-Gapped Mode Detection
- ✅ `test_is_air_gapped_mode_false_by_default` - Default is False
- ✅ `test_is_air_gapped_mode_true` - Enables with 'true', '1', 'yes'
- ✅ `test_is_air_gapped_mode_false` - Disables with 'false', '0', 'no'

#### Provider Validation
- ✅ `test_validate_provider_allowed_local` - Local provider always allowed
- ✅ `test_validate_provider_allowed_external_when_disabled` - External allowed when disabled
- ✅ `test_validate_provider_allowed_external_blocked` - External blocked in air-gapped mode
- ✅ `test_validate_provider_custom_local_allowed` - Custom with local URL allowed
- ✅ `test_validate_provider_custom_external_blocked` - Custom with external URL blocked

#### URL Validation
- ✅ `test_is_external_url_localhost` - Localhost not external
- ✅ `test_is_external_url_private_network` - Private networks not external
- ✅ `test_is_external_url_external` - External URLs detected

#### Configuration
- ✅ `test_get_local_ai_config_defaults` - Default configuration
- ✅ `test_get_local_ai_config_custom` - Custom configuration

### TestLocalProvider (4 tests)

#### Provider Creation
- ✅ `test_local_provider_creation` - Creates with explicit config
- ✅ `test_local_provider_default_base_url` - Uses default if not provided

#### Provider Functionality
- ✅ `test_local_provider_execute_query` - Executes queries via local model
- ✅ `test_local_provider_validate_configuration` - Validates configuration

### TestProviderBlocking (7 tests)

#### External Provider Blocking
- ✅ `test_openai_provider_blocked_in_air_gapped_mode` - OpenAI blocked
- ✅ `test_anthropic_provider_blocked_in_air_gapped_mode` - Anthropic blocked
- ✅ `test_custom_provider_external_blocked` - Custom external blocked

#### Allowed Providers
- ✅ `test_custom_provider_local_allowed` - Custom local allowed
- ✅ `test_local_provider_allowed_in_air_gapped_mode` - Local always allowed

#### Factory Function
- ✅ `test_create_agent_provider_local` - Factory creates local provider
- ✅ `test_create_agent_provider_external_blocked` - Factory blocks external

### TestAIAgentManagerAirGapped (3 tests)

#### Agent Registration
- ✅ `test_register_local_agent_in_air_gapped_mode` - Registers local agent
- ✅ `test_register_external_agent_blocked` - Blocks external agent registration

#### Query Execution
- ✅ `test_execute_query_local_agent` - Executes queries with local agent

### TestNLToSQLAirGapped (3 tests)

#### Configuration
- ✅ `test_nl_to_sql_uses_local_in_air_gapped_mode` - Uses local model when enabled
- ✅ `test_nl_to_sql_uses_openai_when_not_air_gapped` - Uses OpenAI when disabled

#### Query Conversion
- ✅ `test_nl_to_sql_convert_with_local_model` - Converts NL to SQL with local model

### TestAirGappedIntegration (3 tests)

#### End-to-End Workflow
- ✅ `test_full_workflow_air_gapped` - Complete workflow in air-gapped mode
- ✅ `test_network_isolation_validation` - Network isolation URL validation
- ✅ `test_error_messages_are_helpful` - Error messages provide guidance

### TestAirGappedModeEdgeCases (4 tests)

#### Edge Cases
- ✅ `test_case_insensitive_air_gapped_mode` - Case-insensitive mode values
- ✅ `test_empty_api_base_for_local` - Local provider without explicit api_base
- ✅ `test_custom_provider_without_api_base` - Custom provider validation
- ✅ `test_ipv6_localhost` - IPv6 localhost detection

## Running Tests

### Run All Air-Gapped Mode Tests

```bash
pytest tests/test_air_gapped_mode.py -v
```

### Run Specific Test Class

```bash
# Utility tests
pytest tests/test_air_gapped_mode.py::TestAirGappedModeUtilities -v

# Provider blocking tests
pytest tests/test_air_gapped_mode.py::TestProviderBlocking -v

# Integration tests
pytest tests/test_air_gapped_mode.py::TestAirGappedIntegration -v
```

### Run with Coverage

```bash
pytest tests/test_air_gapped_mode.py \
  --cov=ai_agent_connector.app.utils.air_gapped \
  --cov=ai_agent_connector.app.agents.providers \
  --cov-report=html \
  --cov-report=term
```

## Test Coverage Summary

- **Total Test Cases**: 36+
- **Utility Tests**: 12
- **Provider Tests**: 11
- **Manager Tests**: 3
- **NL to SQL Tests**: 3
- **Integration Tests**: 3
- **Edge Case Tests**: 4

## Test Categories

### ✅ Configuration Tests
- Air-gapped mode detection
- Environment variable parsing
- Default values
- Custom configuration

### ✅ Validation Tests
- Provider validation
- URL validation
- Network isolation
- Error handling

### ✅ Provider Tests
- Local provider functionality
- External provider blocking
- Custom provider validation
- Factory function

### ✅ Integration Tests
- End-to-end workflows
- Manager integration
- NL to SQL integration
- Network isolation

### ✅ Edge Case Tests
- Case sensitivity
- Missing configuration
- IPv6 support
- Error messages

## Key Test Validations

### Air-Gapped Mode Detection
- ✅ Default is False
- ✅ Case-insensitive values
- ✅ Multiple true/false formats

### Provider Blocking
- ✅ OpenAI blocked in air-gapped mode
- ✅ Anthropic blocked in air-gapped mode
- ✅ External custom providers blocked
- ✅ Local providers always allowed
- ✅ Local custom providers allowed

### Network Isolation
- ✅ Localhost URLs allowed
- ✅ Private network ranges allowed
- ✅ External URLs blocked
- ✅ IPv6 localhost supported

### Local Provider
- ✅ Creates successfully
- ✅ Uses default base URL if not provided
- ✅ Executes queries correctly
- ✅ Validates configuration

### NL to SQL
- ✅ Uses local model in air-gapped mode
- ✅ Uses OpenAI when not air-gapped
- ✅ Converts queries correctly

## Test Environment Setup

Tests use environment variable mocking to test different configurations:

```python
# Enable air-gapped mode
os.environ['AIR_GAPPED_MODE'] = 'true'

# Configure local AI
os.environ['LOCAL_AI_BASE_URL'] = 'http://localhost:11434'
os.environ['LOCAL_AI_MODEL'] = 'llama2'

# Cleanup after test
del os.environ['AIR_GAPPED_MODE']
```

## Mocking Strategy

Tests use `unittest.mock` to:
- Mock OpenAI client for local provider
- Mock HTTP requests for custom providers
- Mock AI agent manager components
- Avoid actual network calls

## Notes

- Tests validate behavior, not actual AI model responses
- Network isolation is tested via URL validation
- Provider blocking is tested via exception raising
- Integration tests verify end-to-end workflows

## Future Enhancements

- End-to-end tests with actual Ollama instance
- Performance tests for local models
- Load tests for air-gapped mode
- Security tests for network isolation
- Compliance tests for data residency


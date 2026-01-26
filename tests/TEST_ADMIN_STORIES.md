# Admin Database Management Stories - Test Documentation

This document describes the test coverage for the three admin database management stories.

## Stories Tested

1. **Connection Pooling and Timeout Configuration**: As an Admin, I want to configure connection pooling and timeout settings per database, so that performance is optimized for different workloads.

2. **Encrypted Credentials at Rest**: As an Admin, I want to store database credentials securely (encrypted at rest), so that sensitive information is protected.

3. **Credential Rotation**: As an Admin, I want to update or rotate database credentials without breaking active agent connections, so that security practices don't disrupt operations.

## Test Files

### 1. Unit Tests

- **`test_pooling_and_timeouts.py`**: Tests for connection pooling and timeout configuration
  - PoolingConfig and TimeoutConfig classes
  - Configuration extraction and validation
  - PostgreSQL and MySQL connectors with pooling
  - Timeout settings

- **`test_credential_encryption.py`**: Tests for credential encryption
  - CredentialEncryptor class
  - Encryption/decryption operations
  - Database config encryption
  - AgentRegistry integration with encryption

- **`test_credential_rotation.py`**: Tests for credential rotation
  - Staging credentials
  - Activation process
  - Rollback functionality
  - Zero-downtime support

### 2. Integration Tests

- **`test_admin_database_stories_integration.py`**: Integration tests combining all three stories
  - Tests each story individually
  - Tests stories working together
  - End-to-end workflows

- **`test_admin_database_stories_api.py`**: API endpoint tests for all three stories
  - REST API endpoint testing
  - Admin permission verification
  - Complete API workflows

## Running Tests

### Run All Admin Story Tests

```bash
# Run all unit tests
pytest tests/test_pooling_and_timeouts.py -v
pytest tests/test_credential_encryption.py -v
pytest tests/test_credential_rotation.py -v

# Run integration tests
pytest tests/test_admin_database_stories_integration.py -v
pytest tests/test_admin_database_stories_api.py -v

# Run all admin story tests
pytest tests/test_pooling_and_timeouts.py tests/test_credential_encryption.py tests/test_credential_rotation.py tests/test_admin_database_stories_integration.py tests/test_admin_database_stories_api.py -v
```

### Run Specific Story Tests

```bash
# Story 1: Pooling and Timeouts
pytest tests/test_pooling_and_timeouts.py tests/test_admin_database_stories_integration.py::TestStory1_ConnectionPoolingAndTimeouts -v

# Story 2: Encrypted Credentials
pytest tests/test_credential_encryption.py tests/test_admin_database_stories_integration.py::TestStory2_EncryptedCredentials -v

# Story 3: Credential Rotation
pytest tests/test_credential_rotation.py tests/test_admin_database_stories_integration.py::TestStory3_CredentialRotation -v
```

## Test Coverage Summary

### Story 1: Connection Pooling and Timeouts

✅ **Coverage:**
- Registering agents with pooling configuration
- Updating pooling settings for existing agents
- Timeout configuration (connect, query, read, write)
- Configuration validation
- PostgreSQL and MySQL connector support
- API endpoint testing

**Key Test Cases:**
- `test_register_agent_with_pooling_and_timeouts`
- `test_update_pooling_settings_for_existing_agent`
- `test_pooling_config_validation`
- `test_timeout_config_validation`

### Story 2: Encrypted Credentials at Rest

✅ **Coverage:**
- Credentials encrypted when stored
- Credentials decrypted when retrieved
- Different encryption keys produce different ciphertext
- BigQuery credentials JSON encryption
- Backward compatibility with unencrypted data
- API endpoint testing

**Key Test Cases:**
- `test_credentials_encrypted_at_rest`
- `test_credentials_decrypted_when_retrieved`
- `test_encryption_with_different_master_keys`
- `test_bigquery_credentials_json_encrypted`

### Story 3: Credential Rotation

✅ **Coverage:**
- Staging new credentials
- Validating credentials before activation
- Activating staged credentials
- Rolling back rotation
- Zero-downtime support (active connections continue)
- Automatic fallback to active credentials
- Rotation status tracking
- API endpoint testing

**Key Test Cases:**
- `test_rotate_credentials_without_breaking_connections`
- `test_activate_rotated_credentials`
- `test_rollback_credential_rotation`
- `test_get_connector_uses_staged_credentials`
- `test_get_connector_fallback_to_active_on_staged_failure`

### Integration Tests

✅ **Coverage:**
- All three stories working together
- Full workflow: register → encrypt → rotate → activate
- Pooling config preserved during rotation
- Encrypted credentials during rotation
- Complete API workflows

**Key Test Cases:**
- `test_full_workflow_pooling_encryption_rotation`
- `test_rotate_credentials_with_pooling_config`
- `test_rotate_encrypted_credentials`
- `test_full_workflow_via_api`

## Test Execution Results

All tests use mocking to avoid requiring actual database connections, making them:
- **Fast**: No network I/O or database setup required
- **Reliable**: Consistent results across environments
- **Isolated**: Each test is independent
- **Comprehensive**: Covers all edge cases and error scenarios

## Expected Test Results

When running all tests, you should see:

```
tests/test_pooling_and_timeouts.py ................ [100%]
tests/test_credential_encryption.py ................ [100%]
tests/test_credential_rotation.py ................. [100%]
tests/test_admin_database_stories_integration.py ... [100%]
tests/test_admin_database_stories_api.py ............ [100%]

===== X passed in Y.YYs =====
```

## Notes

- All tests reset state between runs
- Encryption keys are reset before each test
- Mock connectors simulate database behavior
- Admin permissions are properly tested
- Error scenarios are thoroughly covered


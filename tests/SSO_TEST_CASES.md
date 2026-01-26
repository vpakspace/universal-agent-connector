# SSO Integration Test Cases

Comprehensive test cases for SSO integration feature.

## Test Coverage

### Unit Tests (`test_sso.py`)

#### SSOConfig Tests

1. **Configuration Creation**
   - ✅ Create SAML configuration
   - ✅ Create OAuth2 configuration
   - ✅ Create LDAP configuration
   - ✅ Convert config to dictionary
   - ✅ Mask secrets in dictionary
   - ✅ Create config from dictionary

#### AttributeMappingRule Tests

1. **Attribute Mapping**
   - ✅ Simple attribute mapping
   - ✅ Mapping with default value
   - ✅ Required attribute missing
   - ✅ Mapping with transformation

#### UserProfile Tests

1. **User Profile**
   - ✅ Create user profile
   - ✅ Convert profile to dictionary

#### SSOAuthenticator Tests

1. **SAML Authentication**
   - ✅ Initiate SAML authentication
   - ✅ Map attributes from SAML
   - ✅ Handle missing email
   - ✅ Handle groups

2. **Attribute Mapping**
   - ✅ Map attributes correctly
   - ✅ Handle missing required attributes
   - ✅ Extract groups

#### SSOManager Tests

1. **Configuration Management**
   - ✅ Add configuration
   - ✅ Enable/disable providers
   - ✅ Get configuration
   - ✅ List configurations
   - ✅ Delete configuration
   - ✅ Remove active provider on delete

2. **Authentication**
   - ✅ Authenticate with LDAP
   - ✅ Authenticate with OAuth2
   - ✅ Authenticate with SAML
   - ✅ Handle no active provider
   - ✅ Handle unsupported provider

#### LDAP Authentication Tests

1. **LDAP Authentication**
   - ✅ Successful authentication
   - ✅ Library not available
   - ✅ User not found
   - ✅ Invalid credentials

### Integration Tests (`test_sso_api.py`)

#### API Endpoint Tests

1. **Configuration Management**
   - ✅ List SSO configs (empty)
   - ✅ List SSO configs (with configs)
   - ✅ Create SSO config
   - ✅ Create config missing config_id
   - ✅ Create duplicate config
   - ✅ Get SSO config
   - ✅ Get config not found
   - ✅ Update SSO config
   - ✅ Update config not found
   - ✅ Delete SSO config
   - ✅ Delete config not found

2. **Authentication Endpoints**
   - ✅ LDAP authentication
   - ✅ LDAP missing credentials
   - ✅ LDAP wrong HTTP method
   - ✅ OAuth2 authentication redirect
   - ✅ Authentication failure
   - ✅ SAML callback
   - ✅ OAuth2 callback
   - ✅ OAuth2 callback missing code

3. **Metadata and User Info**
   - ✅ SAML metadata generation
   - ✅ SAML metadata config not found
   - ✅ SSO logout
   - ✅ Get SSO user
   - ✅ Get user not authenticated

## Test Scenarios

### Scenario 1: SAML Configuration and Authentication

**Setup:**
1. Create SAML configuration
2. Configure IdP with metadata

**Steps:**
1. POST to create SAML config
2. GET metadata endpoint
3. Initiate SAML authentication
4. Receive SAML response
5. Verify user profile created

**Expected:**
- Config created successfully
- Metadata generated correctly
- User authenticated
- Profile contains mapped attributes

### Scenario 2: OAuth2 Configuration and Authentication

**Setup:**
1. Create OAuth2 configuration
2. Register application with OAuth provider

**Steps:**
1. POST to create OAuth2 config
2. GET authentication endpoint (redirects to provider)
3. User authorizes application
4. Provider redirects to callback
5. Verify user profile created

**Expected:**
- Config created successfully
- Redirect to provider works
- Callback processes code
- User authenticated
- Profile contains mapped attributes

### Scenario 3: LDAP Configuration and Authentication

**Setup:**
1. Create LDAP configuration
2. Configure LDAP server connection

**Steps:**
1. POST to create LDAP config
2. POST credentials to authenticate
3. Verify user authenticated
4. Check user attributes retrieved

**Expected:**
- Config created successfully
- Authentication succeeds with valid credentials
- User profile created
- Groups retrieved

### Scenario 4: Attribute Mapping

**Setup:**
1. Create config with custom attribute mappings
2. Configure provider with custom attributes

**Steps:**
1. Create config with attribute mappings
2. Authenticate user
3. Verify attributes mapped correctly
4. Check transformations applied

**Expected:**
- Custom mappings applied
- Required attributes validated
- Default values used when needed
- Transformations work correctly

### Scenario 5: Multiple Providers

**Setup:**
1. Create multiple provider configs
2. Enable one provider per type

**Steps:**
1. Create SAML config (enabled)
2. Create OAuth2 config (enabled)
3. Create LDAP config (enabled)
4. Verify only enabled configs are active
5. Test authentication with each

**Expected:**
- Multiple configs stored
- Only enabled configs active
- Each provider type has one active config
- Authentication works for each

## Test Data

### Sample SAML Configuration

```json
{
  "config_id": "okta-saml",
  "provider_type": "saml",
  "enabled": true,
  "name": "Okta SAML",
  "saml_entity_id": "https://org.okta.com/app/abc123",
  "saml_sso_url": "https://org.okta.com/app/saml/sso",
  "saml_x509_cert": "-----BEGIN CERTIFICATE-----..."
}
```

### Sample OAuth2 Configuration

```json
{
  "config_id": "google-oauth",
  "provider_type": "oauth2",
  "enabled": true,
  "name": "Google OAuth",
  "oauth2_client_id": "client-id.apps.googleusercontent.com",
  "oauth2_client_secret": "client-secret",
  "oauth2_authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
  "oauth2_token_url": "https://oauth2.googleapis.com/token",
  "oauth2_userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
}
```

### Sample LDAP Configuration

```json
{
  "config_id": "ad-ldap",
  "provider_type": "ldap",
  "enabled": true,
  "name": "Active Directory",
  "ldap_server_url": "ldap://ad.example.com:389",
  "ldap_base_dn": "DC=example,DC=com",
  "ldap_bind_dn": "CN=ServiceAccount,CN=Users,DC=example,DC=com",
  "ldap_bind_password": "password",
  "ldap_user_search_base": "CN=Users,DC=example,DC=com",
  "ldap_attributes": ["cn", "mail", "givenName", "sn"]
}
```

## Edge Cases

1. **Missing Required Fields**
   - Config ID missing
   - Provider type missing
   - Required authentication fields missing

2. **Invalid Configurations**
   - Duplicate config IDs
   - Invalid provider types
   - Missing required provider-specific fields

3. **Authentication Failures**
   - Invalid credentials
   - Provider unavailable
   - Network errors
   - Invalid tokens/codes

4. **Library Availability**
   - SAML library not installed
   - LDAP library not installed
   - OAuth requests library missing

5. **Multiple Configs**
   - Multiple configs of same type
   - Enabling/disabling configs
   - Switching active providers

## Security Tests

1. **Secret Masking**
   - Secrets not exposed in API responses
   - Passwords masked in configs
   - Client secrets masked

2. **Authentication Security**
   - Invalid credentials rejected
   - State parameter validated (OAuth2)
   - Session management
   - CSRF protection

3. **Input Validation**
   - SQL injection prevention
   - XSS prevention
   - Path traversal prevention

## Performance Tests

1. **Configuration Loading**
   - Multiple configs loaded quickly
   - Metadata generation performance

2. **Authentication Performance**
   - LDAP connection time
   - OAuth token exchange time
   - SAML processing time

## Running Tests

### Unit Tests

```bash
python -m pytest tests/test_sso.py -v
```

### Integration Tests

```bash
python -m pytest tests/test_sso_api.py -v
```

### All Tests

```bash
python -m pytest tests/test_sso.py tests/test_sso_api.py -v
```

### With Coverage

```bash
python -m pytest tests/test_sso.py tests/test_sso_api.py \
    --cov=ai_agent_connector.app.auth.sso \
    --cov=ai_agent_connector.app.api.routes \
    --cov-report=html \
    --cov-report=term
```

## Test Metrics

### Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Critical Paths**: 100% coverage

### Test Categories

- **Unit Tests**: 40+ test cases
- **Integration Tests**: 25+ test cases
- **Edge Cases**: 10+ test cases
- **Security Tests**: 5+ test cases

## Continuous Integration

Tests should run:
- On every commit
- Before merging PRs
- On scheduled basis (nightly)

## Test Maintenance

### When to Update Tests

1. New provider types added
2. New authentication methods
3. Attribute mapping changes
4. API changes
5. Bug fixes

### Test Documentation

- Keep test cases documented
- Update when features change
- Document test data requirements
- Document test environment setup


# SSO Integration Guide

Complete guide for integrating Single Sign-On (SSO) with SAML 2.0, OAuth 2.0, and LDAP authentication.

## 🎯 Overview

SSO integration allows centralized authentication using enterprise identity providers:

- **SAML 2.0**: Standard enterprise SSO protocol
- **OAuth 2.0**: Modern authorization framework
- **LDAP/Active Directory**: Directory service authentication

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# For SAML 2.0
pip install python3-saml

# For OAuth 2.0 (uses requests, already in Flask)
pip install requests

# For LDAP
pip install ldap3
```

### 2. Create SSO Configuration

```bash
POST /api/sso/configs
Headers: X-API-Key: your-admin-api-key
Body: {
  "config_id": "okta-saml",
  "provider_type": "saml",
  "enabled": true,
  "name": "Okta SAML",
  "saml_entity_id": "https://dev-123456.okta.com/app/abc123",
  "saml_sso_url": "https://dev-123456.okta.com/app/saml/sso",
  "saml_x509_cert": "-----BEGIN CERTIFICATE-----\n..."
}
```

### 3. Initiate Authentication

```bash
GET /api/sso/authenticate/saml?return_to=/dashboard
```

## 📚 Provider Types

### SAML 2.0

**Use Cases**: Enterprise SSO with Okta, Azure AD, OneLogin, etc.

**Configuration:**
```json
{
  "config_id": "okta-saml",
  "provider_type": "saml",
  "enabled": true,
  "name": "Okta SAML",
  "saml_entity_id": "https://your-org.okta.com/app/abc123",
  "saml_sso_url": "https://your-org.okta.com/app/saml/sso",
  "saml_slo_url": "https://your-org.okta.com/app/saml/slo",
  "saml_x509_cert": "-----BEGIN CERTIFICATE-----\n...",
  "attribute_mappings": [
    {
      "sso_attribute": "email",
      "user_attribute": "email",
      "required": true
    },
    {
      "sso_attribute": "firstName",
      "user_attribute": "first_name"
    }
  ]
}
```

**Flow:**
1. User visits `/api/sso/authenticate/saml`
2. System redirects to IdP login page
3. User authenticates with IdP
4. IdP posts SAML response to `/api/sso/callback/saml`
5. System validates and creates session
6. User redirected to `return_to` URL

### OAuth 2.0

**Use Cases**: Google, Microsoft, GitHub, custom OAuth providers

**Configuration:**
```json
{
  "config_id": "google-oauth",
  "provider_type": "oauth2",
  "enabled": true,
  "name": "Google OAuth",
  "oauth2_client_id": "your-client-id.apps.googleusercontent.com",
  "oauth2_client_secret": "your-client-secret",
  "oauth2_authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
  "oauth2_token_url": "https://oauth2.googleapis.com/token",
  "oauth2_userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
  "oauth2_scopes": ["openid", "profile", "email"],
  "oauth2_redirect_uri": "https://your-app.com/api/sso/callback/oauth2"
}
```

**Flow:**
1. User visits `/api/sso/authenticate/oauth2`
2. System redirects to OAuth provider authorization URL
3. User authorizes application
4. Provider redirects to `/api/sso/callback/oauth2` with code
5. System exchanges code for access token
6. System fetches user info
7. System creates session

### LDAP / Active Directory

**Use Cases**: Internal directory services, Active Directory

**Configuration:**
```json
{
  "config_id": "ad-ldap",
  "provider_type": "ldap",
  "enabled": true,
  "name": "Active Directory",
  "ldap_server_url": "ldap://ad.example.com:389",
  "ldap_base_dn": "DC=example,DC=com",
  "ldap_bind_dn": "CN=ServiceAccount,CN=Users,DC=example,DC=com",
  "ldap_bind_password": "service-password",
  "ldap_user_search_base": "CN=Users,DC=example,DC=com",
  "ldap_user_search_filter": "(sAMAccountName={username})",
  "ldap_group_search_base": "CN=Groups,DC=example,DC=com",
  "ldap_group_search_filter": "(member={user_dn})",
  "ldap_attributes": ["cn", "mail", "givenName", "sn", "memberOf"]
}
```

**Flow:**
1. User POSTs credentials to `/api/sso/authenticate/ldap`
2. System binds to LDAP server with service account
3. System searches for user
4. System attempts to bind as user with provided password
5. System retrieves user attributes and groups
6. System creates session

## 🔧 Attribute Mapping

Attribute mapping allows you to map SSO provider attributes to user profile attributes.

### Default Mappings

**SAML:**
- `email` → `email` (required)
- `name` → `name`
- `givenName` → `first_name`
- `surname` → `last_name`
- `groups` → `groups`

**OAuth2:**
- `email` → `email` (required)
- `name` → `name`
- `given_name` → `first_name`
- `family_name` → `last_name`
- `groups` → `groups`

**LDAP:**
- `mail` → `email` (required)
- `cn` → `name`
- `givenName` → `first_name`
- `sn` → `last_name`
- `memberOf` → `groups`

### Custom Mappings

```json
{
  "attribute_mappings": [
    {
      "sso_attribute": "customEmail",
      "user_attribute": "email",
      "required": true
    },
    {
      "sso_attribute": "department",
      "user_attribute": "department",
      "default": "Unknown"
    },
    {
      "sso_attribute": "employeeId",
      "user_attribute": "employee_id",
      "transform": "string"
    }
  ]
}
```

## 📡 API Reference

### List SSO Configurations

```
GET /api/sso/configs
```

**Response:**
```json
{
  "configs": [
    {
      "config_id": "okta-saml",
      "provider_type": "saml",
      "enabled": true,
      "name": "Okta SAML",
      ...
    }
  ]
}
```

### Create SSO Configuration

```
POST /api/sso/configs
```

**Request Body:** See provider-specific examples above

**Response:**
```json
{
  "config_id": "okta-saml",
  "message": "SSO configuration created successfully",
  "config": {...}
}
```

### Get SSO Configuration

```
GET /api/sso/configs/{config_id}
```

### Update SSO Configuration

```
PUT /api/sso/configs/{config_id}
```

### Delete SSO Configuration

```
DELETE /api/sso/configs/{config_id}
```

### Initiate Authentication

```
GET /api/sso/authenticate/{provider_type}?return_to=/dashboard
POST /api/sso/authenticate/ldap
```

**LDAP POST Body:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

### SAML Callback

```
POST /api/sso/callback/saml
```

### OAuth2 Callback

```
GET /api/sso/callback/oauth2?code=xxx&state=yyy
```

### Get SAML Metadata

```
GET /api/sso/metadata/saml/{config_id}
```

Returns SAML XML metadata for configuring IdP.

### Get Current User

```
GET /api/sso/user
```

**Response:**
```json
{
  "user": {
    "user_id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "attributes": {...},
    "groups": ["admin", "users"],
    "provider": "saml",
    "provider_user_id": "user@example.com"
  }
}
```

### Logout

```
POST /api/sso/logout
```

## 🔍 Examples

### Example 1: Okta SAML Integration

```python
import requests

# Create SAML configuration
response = requests.post(
    'http://localhost:5000/api/sso/configs',
    headers={'X-API-Key': 'admin-key'},
    json={
        'config_id': 'okta-saml',
        'provider_type': 'saml',
        'enabled': True,
        'name': 'Okta SAML',
        'saml_entity_id': 'https://dev-123456.okta.com/app/abc123',
        'saml_sso_url': 'https://dev-123456.okta.com/app/saml/sso',
        'saml_x509_cert': '-----BEGIN CERTIFICATE-----\n...',
        'attribute_mappings': [
            {
                'sso_attribute': 'email',
                'user_attribute': 'email',
                'required': True
            }
        ]
    }
)

# Get SAML metadata for Okta configuration
metadata_response = requests.get(
    'http://localhost:5000/api/sso/metadata/saml/okta-saml'
)

# Initiate login (redirects to Okta)
login_url = 'http://localhost:5000/api/sso/authenticate/saml?return_to=/dashboard'
```

### Example 2: Google OAuth2 Integration

```python
# Create OAuth2 configuration
response = requests.post(
    'http://localhost:5000/api/sso/configs',
    headers={'X-API-Key': 'admin-key'},
    json={
        'config_id': 'google-oauth',
        'provider_type': 'oauth2',
        'enabled': True,
        'name': 'Google OAuth',
        'oauth2_client_id': 'your-client-id.apps.googleusercontent.com',
        'oauth2_client_secret': 'your-client-secret',
        'oauth2_authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'oauth2_token_url': 'https://oauth2.googleapis.com/token',
        'oauth2_userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'oauth2_scopes': ['openid', 'profile', 'email'],
        'oauth2_redirect_uri': 'https://your-app.com/api/sso/callback/oauth2'
    }
)

# Initiate login (redirects to Google)
login_url = 'http://localhost:5000/api/sso/authenticate/oauth2?return_to=/dashboard'
```

### Example 3: Active Directory LDAP Integration

```python
# Create LDAP configuration
response = requests.post(
    'http://localhost:5000/api/sso/configs',
    headers={'X-API-Key': 'admin-key'},
    json={
        'config_id': 'ad-ldap',
        'provider_type': 'ldap',
        'enabled': True,
        'name': 'Active Directory',
        'ldap_server_url': 'ldap://ad.example.com:389',
        'ldap_base_dn': 'DC=example,DC=com',
        'ldap_bind_dn': 'CN=ServiceAccount,CN=Users,DC=example,DC=com',
        'ldap_bind_password': 'service-password',
        'ldap_user_search_base': 'CN=Users,DC=example,DC=com',
        'ldap_user_search_filter': '(sAMAccountName={username})',
        'ldap_group_search_base': 'CN=Groups,DC=example,DC=com',
        'ldap_attributes': ['cn', 'mail', 'givenName', 'sn', 'memberOf']
    }
)

# Authenticate user
auth_response = requests.post(
    'http://localhost:5000/api/sso/authenticate/ldap',
    json={
        'username': 'jdoe',
        'password': 'user-password'
    }
)

user_profile = auth_response.json()
```

## 🎨 Best Practices

### Security

1. **Use HTTPS**: Always use HTTPS in production
2. **Secure Secrets**: Store client secrets securely (environment variables, secrets manager)
3. **Validate Certificates**: Enable certificate validation in production
4. **State Parameter**: OAuth2 uses state parameter for CSRF protection
5. **Session Security**: Use secure, HttpOnly cookies for sessions

### Configuration

1. **One Active Provider**: Only one active provider per type
2. **Test Configuration**: Test configurations in development first
3. **Metadata Exchange**: Use SAML metadata for easier IdP configuration
4. **Attribute Mapping**: Map only required attributes for security

### Error Handling

1. **Validation Errors**: Validate all configuration fields
2. **Authentication Failures**: Log authentication failures
3. **Timeout Handling**: Set appropriate timeouts for LDAP connections
4. **Fallback**: Consider fallback authentication methods

## 🐛 Troubleshooting

### SAML Issues

**Problem**: "SAML authentication errors"
**Solution**: Check certificate format, entity ID, and URLs match IdP configuration

**Problem**: "Invalid SAML response"
**Solution**: Verify SAML response is being posted to correct endpoint

### OAuth2 Issues

**Problem**: "Invalid authorization code"
**Solution**: Verify redirect_uri matches exactly, check code hasn't expired

**Problem**: "Token exchange failed"
**Solution**: Verify client_id and client_secret are correct

### LDAP Issues

**Problem**: "Connection refused"
**Solution**: Check LDAP server URL and port are correct

**Problem**: "Invalid credentials"
**Solution**: Verify bind DN and password, check user exists

**Problem**: "User not found"
**Solution**: Verify user_search_filter and user_search_base are correct

## 📈 Production Considerations

### High Availability

- Use connection pooling for LDAP
- Implement retry logic for token exchanges
- Cache user profiles when appropriate

### Monitoring

- Log all authentication attempts
- Monitor authentication success/failure rates
- Alert on authentication failures

### Performance

- Use LDAP connection pooling
- Cache SAML metadata
- Implement token caching for OAuth2

---

**Questions?** Check [GitHub Discussions](https://github.com/your-repo/ai-agent-connector/discussions) or open an issue!


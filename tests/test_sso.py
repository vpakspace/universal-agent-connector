"""
Unit tests for SSO authentication module
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from ai_agent_connector.app.auth.sso import (
    SSOConfig,
    SSOProviderType,
    UserProfile,
    AttributeMappingRule,
    SSOAuthenticator,
    SSOManager,
    SSO_AVAILABLE,
    LDAP_AVAILABLE
)


class TestSSOConfig(unittest.TestCase):
    """Test cases for SSOConfig"""
    
    def test_create_saml_config(self):
        """Test creating SAML configuration"""
        config = SSOConfig(
            provider_type="saml",
            enabled=True,
            name="Okta SAML",
            saml_entity_id="https://org.okta.com/app/abc",
            saml_sso_url="https://org.okta.com/app/saml/sso",
            saml_x509_cert="-----BEGIN CERTIFICATE-----\n..."
        )
        
        self.assertEqual(config.provider_type, "saml")
        self.assertTrue(config.enabled)
        self.assertEqual(config.name, "Okta SAML")
        self.assertIsNotNone(config.saml_entity_id)
    
    def test_create_oauth2_config(self):
        """Test creating OAuth2 configuration"""
        config = SSOConfig(
            provider_type="oauth2",
            enabled=True,
            name="Google OAuth",
            oauth2_client_id="client-id",
            oauth2_client_secret="secret",
            oauth2_authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            oauth2_token_url="https://oauth2.googleapis.com/token",
            oauth2_userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo"
        )
        
        self.assertEqual(config.provider_type, "oauth2")
        self.assertEqual(config.oauth2_client_id, "client-id")
        self.assertEqual(len(config.oauth2_scopes), 3)
    
    def test_create_ldap_config(self):
        """Test creating LDAP configuration"""
        config = SSOConfig(
            provider_type="ldap",
            enabled=True,
            name="Active Directory",
            ldap_server_url="ldap://ad.example.com:389",
            ldap_base_dn="DC=example,DC=com",
            ldap_bind_dn="CN=ServiceAccount,CN=Users,DC=example,DC=com",
            ldap_bind_password="password"
        )
        
        self.assertEqual(config.provider_type, "ldap")
        self.assertEqual(config.ldap_server_url, "ldap://ad.example.com:389")
    
    def test_config_to_dict(self):
        """Test converting config to dictionary"""
        config = SSOConfig(
            provider_type="saml",
            enabled=True,
            name="Test SAML",
            saml_entity_id="test-id"
        )
        
        config_dict = config.to_dict()
        self.assertIn('provider_type', config_dict)
        self.assertIn('enabled', config_dict)
        self.assertEqual(config_dict['provider_type'], 'saml')
    
    def test_config_to_dict_masks_secrets(self):
        """Test that secrets are masked in to_dict"""
        config = SSOConfig(
            provider_type="oauth2",
            enabled=True,
            oauth2_client_secret="secret123"
        )
        
        config_dict = config.to_dict()
        self.assertEqual(config_dict.get('oauth2_client_secret'), '***')
    
    def test_config_from_dict(self):
        """Test creating config from dictionary"""
        data = {
            'provider_type': 'saml',
            'enabled': True,
            'name': 'Test SAML',
            'saml_entity_id': 'test-id'
        }
        
        config = SSOConfig.from_dict(data)
        self.assertEqual(config.provider_type, 'saml')
        self.assertEqual(config.name, 'Test SAML')


class TestAttributeMappingRule(unittest.TestCase):
    """Test cases for AttributeMappingRule"""
    
    def test_map_value_simple(self):
        """Test simple attribute mapping"""
        rule = AttributeMappingRule(
            sso_attribute='email',
            user_attribute='email'
        )
        
        sso_attrs = {'email': 'user@example.com'}
        attr_name, value = rule.map_value(sso_attrs)
        
        self.assertEqual(attr_name, 'email')
        self.assertEqual(value, 'user@example.com')
    
    def test_map_value_with_default(self):
        """Test mapping with default value"""
        rule = AttributeMappingRule(
            sso_attribute='department',
            user_attribute='department',
            default='Unknown'
        )
        
        sso_attrs = {}
        attr_name, value = rule.map_value(sso_attrs)
        
        self.assertEqual(value, 'Unknown')
    
    def test_map_value_required_missing(self):
        """Test required attribute that is missing"""
        rule = AttributeMappingRule(
            sso_attribute='email',
            user_attribute='email',
            required=True
        )
        
        sso_attrs = {}
        
        with self.assertRaises(ValueError) as context:
            rule.map_value(sso_attrs)
        
        self.assertIn('Required attribute', str(context.exception))
    
    def test_map_value_with_transform(self):
        """Test mapping with transformation"""
        rule = AttributeMappingRule(
            sso_attribute='username',
            user_attribute='email',
            transform=lambda x: f"{x}@example.com"
        )
        
        sso_attrs = {'username': 'jdoe'}
        attr_name, value = rule.map_value(sso_attrs)
        
        self.assertEqual(value, 'jdoe@example.com')


class TestUserProfile(unittest.TestCase):
    """Test cases for UserProfile"""
    
    def test_create_user_profile(self):
        """Test creating user profile"""
        profile = UserProfile(
            user_id="user123",
            email="user@example.com",
            name="John Doe",
            provider="saml",
            provider_user_id="user@example.com"
        )
        
        self.assertEqual(profile.user_id, "user123")
        self.assertEqual(profile.email, "user@example.com")
        self.assertEqual(profile.provider, "saml")
    
    def test_user_profile_to_dict(self):
        """Test converting profile to dictionary"""
        profile = UserProfile(
            user_id="user123",
            email="user@example.com",
            provider="oauth2"
        )
        
        profile_dict = profile.to_dict()
        self.assertIn('user_id', profile_dict)
        self.assertIn('email', profile_dict)
        self.assertEqual(profile_dict['email'], 'user@example.com')


class TestSSOAuthenticator(unittest.TestCase):
    """Test cases for SSOAuthenticator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.authenticator = SSOAuthenticator()
        self.mock_registry = Mock()
    
    @patch('ai_agent_connector.app.auth.sso.SAML_AVAILABLE', True)
    @patch('ai_agent_connector.app.auth.sso.OneLogin_Saml2_Auth')
    def test_authenticate_saml_initiate(self, mock_saml_auth_class):
        """Test initiating SAML authentication"""
        mock_auth = Mock()
        mock_auth.login.return_value = Mock(status_code=302)
        mock_saml_auth_class.return_value = mock_auth
        
        config = SSOConfig(
            provider_type="saml",
            saml_entity_id="test-idp",
            saml_sso_url="https://idp.example.com/sso"
        )
        
        self.authenticator.register_config("test-config", config)
        
        with patch('ai_agent_connector.app.auth.sso.request') as mock_request:
            mock_request.scheme = 'https'
            mock_request.host = 'app.example.com'
            mock_request.path = '/sso/authenticate'
            mock_request.args = {}
            mock_request.form = {}
            
            result = self.authenticator.authenticate_saml("test-config")
            
            mock_auth.login.assert_called_once()
    
    def test_map_attributes(self):
        """Test attribute mapping"""
        config = SSOConfig(
            provider_type="saml",
            attribute_mappings=[
                {
                    'sso_attribute': 'email',
                    'user_attribute': 'email',
                    'required': True
                }
            ]
        )
        
        self.authenticator.register_config("test-config", config)
        
        sso_attrs = {'email': 'user@example.com'}
        user_id = 'user123'
        
        profile = self.authenticator._map_attributes("test-config", sso_attrs, user_id)
        
        self.assertEqual(profile.email, 'user@example.com')
        self.assertEqual(profile.user_id, user_id)
    
    def test_map_attributes_missing_email(self):
        """Test mapping fails when email is missing"""
        config = SSOConfig(provider_type="saml")
        self.authenticator.register_config("test-config", config)
        
        sso_attrs = {}
        user_id = 'user123'
        
        with self.assertRaises(ValueError) as context:
            self.authenticator._map_attributes("test-config", sso_attrs, user_id)
        
        self.assertIn('Email attribute', str(context.exception))
    
    def test_map_attributes_with_groups(self):
        """Test mapping with groups"""
        config = SSOConfig(provider_type="saml")
        self.authenticator.register_config("test-config", config)
        
        sso_attrs = {
            'email': 'user@example.com',
            'groups': ['admin', 'users']
        }
        
        profile = self.authenticator._map_attributes("test-config", sso_attrs, 'user123')
        
        self.assertEqual(len(profile.groups), 2)
        self.assertIn('admin', profile.groups)


class TestSSOManager(unittest.TestCase):
    """Test cases for SSOManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = SSOManager()
    
    def test_add_config(self):
        """Test adding SSO configuration"""
        config = SSOConfig(
            provider_type="saml",
            enabled=True,
            name="Test SAML"
        )
        
        self.manager.add_config("test-config", config)
        
        retrieved = self.manager.get_config("test-config")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test SAML")
    
    def test_add_config_enables_provider(self):
        """Test that enabled config becomes active provider"""
        config = SSOConfig(
            provider_type="saml",
            enabled=True
        )
        
        self.manager.add_config("test-config", config)
        
        self.assertIn("saml", self.manager.active_providers)
        self.assertEqual(self.manager.active_providers["saml"], "test-config")
    
    def test_add_config_disabled_not_active(self):
        """Test that disabled config doesn't become active"""
        config = SSOConfig(
            provider_type="saml",
            enabled=False
        )
        
        self.manager.add_config("test-config", config)
        
        self.assertNotIn("saml", self.manager.active_providers)
    
    def test_get_config_not_found(self):
        """Test getting non-existent configuration"""
        config = self.manager.get_config("non-existent")
        self.assertIsNone(config)
    
    def test_list_configs(self):
        """Test listing all configurations"""
        config1 = SSOConfig(provider_type="saml", name="SAML 1")
        config2 = SSOConfig(provider_type="oauth2", name="OAuth2 1")
        
        self.manager.add_config("config1", config1)
        self.manager.add_config("config2", config2)
        
        configs = self.manager.list_configs()
        self.assertEqual(len(configs), 2)
    
    def test_delete_config(self):
        """Test deleting configuration"""
        config = SSOConfig(provider_type="saml")
        self.manager.add_config("test-config", config)
        
        result = self.manager.delete_config("test-config")
        self.assertTrue(result)
        
        retrieved = self.manager.get_config("test-config")
        self.assertIsNone(retrieved)
    
    def test_delete_config_removes_active_provider(self):
        """Test that deleting active config removes it from active providers"""
        config = SSOConfig(provider_type="saml", enabled=True)
        self.manager.add_config("test-config", config)
        
        self.manager.delete_config("test-config")
        
        self.assertNotIn("saml", self.manager.active_providers)
    
    def test_delete_config_not_found(self):
        """Test deleting non-existent configuration"""
        result = self.manager.delete_config("non-existent")
        self.assertFalse(result)
    
    def test_authenticate_no_active_provider(self):
        """Test authentication with no active provider"""
        with self.assertRaises(ValueError) as context:
            self.manager.authenticate("saml")
        
        self.assertIn("No active", str(context.exception))
    
    @patch.object(SSOAuthenticator, 'authenticate_ldap')
    def test_authenticate_ldap(self, mock_authenticate):
        """Test LDAP authentication"""
        mock_profile = UserProfile(
            user_id="jdoe",
            email="jdoe@example.com",
            provider="ldap"
        )
        mock_authenticate.return_value = mock_profile
        
        config = SSOConfig(provider_type="ldap", enabled=True)
        self.manager.add_config("ldap-config", config)
        
        result = self.manager.authenticate("ldap", username="jdoe", password="pass")
        
        self.assertIsNotNone(result)
        mock_authenticate.assert_called_once_with("ldap-config", "jdoe", "pass")
    
    @patch.object(SSOAuthenticator, 'authenticate_oauth2')
    def test_authenticate_oauth2(self, mock_authenticate):
        """Test OAuth2 authentication"""
        config = SSOConfig(provider_type="oauth2", enabled=True)
        self.manager.add_config("oauth-config", config)
        
        self.manager.authenticate("oauth2", code="auth-code", state="state")
        
        mock_authenticate.assert_called_once_with("oauth-config", "auth-code", "state")
    
    @patch.object(SSOAuthenticator, 'authenticate_saml')
    def test_authenticate_saml(self, mock_authenticate):
        """Test SAML authentication"""
        config = SSOConfig(provider_type="saml", enabled=True)
        self.manager.add_config("saml-config", config)
        
        self.manager.authenticate("saml", saml_response="response")
        
        mock_authenticate.assert_called_once_with("saml-config", "response")
    
    def test_authenticate_unsupported_provider(self):
        """Test authentication with unsupported provider type"""
        config = SSOConfig(provider_type="custom", enabled=True)
        self.manager.add_config("custom-config", config)
        
        with self.assertRaises(ValueError) as context:
            self.manager.authenticate("custom")
        
        self.assertIn("Unsupported provider type", str(context.exception))


class TestLDAPAuthentication(unittest.TestCase):
    """Test cases for LDAP authentication"""
    
    @patch('ai_agent_connector.app.auth.sso.LDAP_AVAILABLE', True)
    @patch('ai_agent_connector.app.auth.sso.ldap3')
    def test_authenticate_ldap_success(self, mock_ldap3):
        """Test successful LDAP authentication"""
        # Mock LDAP connection
        mock_server = Mock()
        mock_conn = Mock()
        mock_entry = Mock()
        mock_entry.entry_dn = "CN=John Doe,CN=Users,DC=example,DC=com"
        mock_entry.cn.value = "John Doe"
        mock_entry.mail.value = "jdoe@example.com"
        
        mock_conn.entries = [mock_entry]
        mock_conn.search.return_value = True
        mock_ldap3.Server.return_value = mock_server
        mock_ldap3.Connection.side_effect = [mock_conn, mock_conn]  # Bind conn, user conn
        
        authenticator = SSOAuthenticator()
        
        config = SSOConfig(
            provider_type="ldap",
            ldap_server_url="ldap://ad.example.com:389",
            ldap_base_dn="DC=example,DC=com",
            ldap_bind_dn="CN=ServiceAccount,CN=Users,DC=example,DC=com",
            ldap_bind_password="password",
            ldap_user_search_base="CN=Users,DC=example,DC=com",
            ldap_user_search_filter="(sAMAccountName={username})",
            ldap_attributes=["cn", "mail"]
        )
        
        authenticator.register_config("ldap-config", config)
        
        with patch('ai_agent_connector.app.auth.sso.request') as mock_request:
            mock_request.scheme = 'https'
            mock_request.host = 'app.example.com'
            
            profile = authenticator.authenticate_ldap("ldap-config", "jdoe", "password")
            
            self.assertIsNotNone(profile)
            self.assertEqual(profile.email, "jdoe@example.com")
    
    @patch('ai_agent_connector.app.auth.sso.LDAP_AVAILABLE', False)
    def test_authenticate_ldap_not_available(self):
        """Test LDAP authentication when library not available"""
        authenticator = SSOAuthenticator()
        config = SSOConfig(provider_type="ldap")
        authenticator.register_config("ldap-config", config)
        
        with self.assertRaises(RuntimeError) as context:
            authenticator.authenticate_ldap("ldap-config", "user", "pass")
        
        self.assertIn("LDAP library not available", str(context.exception))
    
    @patch('ai_agent_connector.app.auth.sso.LDAP_AVAILABLE', True)
    @patch('ai_agent_connector.app.auth.sso.ldap3')
    def test_authenticate_ldap_user_not_found(self, mock_ldap3):
        """Test LDAP authentication when user not found"""
        mock_server = Mock()
        mock_conn = Mock()
        mock_conn.entries = []  # No users found
        mock_conn.search.return_value = True
        mock_ldap3.Server.return_value = mock_server
        mock_ldap3.Connection.return_value = mock_conn
        
        authenticator = SSOAuthenticator()
        config = SSOConfig(
            provider_type="ldap",
            ldap_server_url="ldap://ad.example.com:389",
            ldap_base_dn="DC=example,DC=com",
            ldap_bind_dn="CN=ServiceAccount,CN=Users,DC=example,DC=com",
            ldap_bind_password="password",
            ldap_user_search_base="CN=Users,DC=example,DC=com",
            ldap_attributes=["cn", "mail"]
        )
        authenticator.register_config("ldap-config", config)
        
        with patch('ai_agent_connector.app.auth.sso.request'):
            profile = authenticator.authenticate_ldap("ldap-config", "nonexistent", "pass")
            self.assertIsNone(profile)


if __name__ == '__main__':
    unittest.main()


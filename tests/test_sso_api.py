"""
Integration tests for SSO API endpoints
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import json

from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.auth.sso import (
    SSOConfig,
    SSOProviderType,
    UserProfile,
    sso_manager
)


class TestSSOAPI(unittest.TestCase):
    """Test cases for SSO API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        # Clear SSO manager state
        sso_manager.configs.clear()
        sso_manager.active_providers.clear()
    
    def test_list_sso_configs_empty(self):
        """Test listing SSO configs when none exist"""
        response = self.client.get('/api/sso/configs')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('configs', data)
        self.assertEqual(len(data['configs']), 0)
    
    def test_list_sso_configs(self):
        """Test listing SSO configs"""
        config = SSOConfig(provider_type="saml", name="Test SAML")
        sso_manager.add_config("test-config", config)
        
        response = self.client.get('/api/sso/configs')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['configs']), 1)
        self.assertEqual(data['configs'][0]['name'], 'Test SAML')
    
    def test_create_sso_config(self):
        """Test creating SSO configuration"""
        response = self.client.post(
            '/api/sso/configs',
            json={
                'config_id': 'test-config',
                'provider_type': 'saml',
                'enabled': True,
                'name': 'Test SAML',
                'saml_entity_id': 'test-entity-id',
                'saml_sso_url': 'https://idp.example.com/sso'
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['config_id'], 'test-config')
        self.assertIn('message', data)
    
    def test_create_sso_config_missing_config_id(self):
        """Test creating config without config_id"""
        response = self.client.post(
            '/api/sso/configs',
            json={
                'provider_type': 'saml'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('config_id', data['error'])
    
    def test_create_sso_config_duplicate(self):
        """Test creating duplicate config"""
        config = SSOConfig(provider_type="saml")
        sso_manager.add_config("test-config", config)
        
        response = self.client.post(
            '/api/sso/configs',
            json={
                'config_id': 'test-config',
                'provider_type': 'saml'
            }
        )
        
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_sso_config(self):
        """Test getting SSO configuration"""
        config = SSOConfig(provider_type="saml", name="Test SAML")
        sso_manager.add_config("test-config", config)
        
        response = self.client.get('/api/sso/configs/test-config')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['config']['name'], 'Test SAML')
    
    def test_get_sso_config_not_found(self):
        """Test getting non-existent configuration"""
        response = self.client.get('/api/sso/configs/non-existent')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_update_sso_config(self):
        """Test updating SSO configuration"""
        config = SSOConfig(provider_type="saml", name="Old Name")
        sso_manager.add_config("test-config", config)
        
        response = self.client.put(
            '/api/sso/configs/test-config',
            json={'name': 'New Name'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['config']['name'], 'New Name')
    
    def test_update_sso_config_not_found(self):
        """Test updating non-existent configuration"""
        response = self.client.put(
            '/api/sso/configs/non-existent',
            json={'name': 'New Name'}
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_sso_config(self):
        """Test deleting SSO configuration"""
        config = SSOConfig(provider_type="saml")
        sso_manager.add_config("test-config", config)
        
        response = self.client.delete('/api/sso/configs/test-config')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        # Verify it's deleted
        get_response = self.client.get('/api/sso/configs/test-config')
        self.assertEqual(get_response.status_code, 404)
    
    def test_delete_sso_config_not_found(self):
        """Test deleting non-existent configuration"""
        response = self.client.delete('/api/sso/configs/non-existent')
        
        self.assertEqual(response.status_code, 404)
    
    @patch.object(sso_manager, 'authenticate')
    def test_sso_authenticate_ldap(self, mock_authenticate):
        """Test LDAP authentication"""
        mock_profile = UserProfile(
            user_id="jdoe",
            email="jdoe@example.com",
            provider="ldap"
        )
        mock_authenticate.return_value = mock_profile
        
        config = SSOConfig(provider_type="ldap", enabled=True)
        sso_manager.add_config("ldap-config", config)
        
        response = self.client.post(
            '/api/sso/authenticate/ldap',
            json={
                'username': 'jdoe',
                'password': 'password123'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['user']['email'], 'jdoe@example.com')
        mock_authenticate.assert_called_once_with('ldap', username='jdoe', password='password123')
    
    def test_sso_authenticate_ldap_missing_credentials(self):
        """Test LDAP authentication without credentials"""
        config = SSOConfig(provider_type="ldap", enabled=True)
        sso_manager.add_config("ldap-config", config)
        
        response = self.client.post(
            '/api/sso/authenticate/ldap',
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_sso_authenticate_ldap_wrong_method(self):
        """Test LDAP authentication with GET instead of POST"""
        config = SSOConfig(provider_type="ldap", enabled=True)
        sso_manager.add_config("ldap-config", config)
        
        response = self.client.get('/api/sso/authenticate/ldap')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch.object(sso_manager, 'authenticate')
    def test_sso_authenticate_oauth2_redirect(self, mock_authenticate):
        """Test OAuth2 authentication initiates redirect"""
        from flask import redirect
        mock_redirect = Mock(return_value=redirect('https://oauth.example.com/auth'))
        mock_authenticate.return_value = mock_redirect.return_value
        
        config = SSOConfig(provider_type="oauth2", enabled=True)
        sso_manager.add_config("oauth-config", config)
        
        with self.app.test_request_context():
            response = self.client.get('/api/sso/authenticate/oauth2')
            
            # OAuth2 should redirect
            self.assertIn(response.status_code, [302, 200])
            mock_authenticate.assert_called_once_with('oauth2')
    
    @patch.object(sso_manager, 'authenticate')
    def test_sso_authenticate_failed(self, mock_authenticate):
        """Test authentication failure"""
        mock_authenticate.return_value = None
        
        config = SSOConfig(provider_type="ldap", enabled=True)
        sso_manager.add_config("ldap-config", config)
        
        response = self.client.post(
            '/api/sso/authenticate/ldap',
            json={
                'username': 'user',
                'password': 'wrong'
            }
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch.object(sso_manager, 'authenticate')
    def test_saml_callback(self, mock_authenticate):
        """Test SAML callback endpoint"""
        mock_profile = UserProfile(
            user_id="user123",
            email="user@example.com",
            provider="saml"
        )
        mock_authenticate.return_value = mock_profile
        
        config = SSOConfig(provider_type="saml", enabled=True)
        sso_manager.add_config("saml-config", config)
        
        with self.app.test_request_context('/api/sso/callback/saml', method='POST'):
            response = self.client.post('/api/sso/callback/saml')
            
            # Should redirect after successful auth
            self.assertIn(response.status_code, [302, 200])
    
    @patch.object(sso_manager, 'authenticate')
    def test_oauth2_callback(self, mock_authenticate):
        """Test OAuth2 callback endpoint"""
        mock_profile = UserProfile(
            user_id="user123",
            email="user@example.com",
            provider="oauth2"
        )
        mock_authenticate.return_value = mock_profile
        
        config = SSOConfig(provider_type="oauth2", enabled=True)
        sso_manager.add_config("oauth-config", config)
        
        response = self.client.get('/api/sso/callback/oauth2?code=abc123&state=xyz')
        
        # Should redirect after successful auth
        self.assertIn(response.status_code, [302, 200])
        mock_authenticate.assert_called_once_with('oauth2', code='abc123', state='xyz')
    
    def test_oauth2_callback_missing_code(self):
        """Test OAuth2 callback without code"""
        config = SSOConfig(provider_type="oauth2", enabled=True)
        sso_manager.add_config("oauth-config", config)
        
        response = self.client.get('/api/sso/callback/oauth2')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_saml_metadata_not_found(self):
        """Test SAML metadata for non-existent config"""
        response = self.client.get('/api/sso/metadata/saml/non-existent')
        
        self.assertEqual(response.status_code, 404)
    
    @patch('ai_agent_connector.app.auth.sso.SAML_AVAILABLE', True)
    @patch('ai_agent_connector.app.auth.sso.OneLogin_Saml2_Settings')
    @patch('ai_agent_connector.app.auth.sso.OneLogin_Saml2_Metadata')
    def test_saml_metadata(self, mock_metadata_class, mock_settings_class):
        """Test SAML metadata generation"""
        mock_metadata = Mock()
        mock_metadata.builder.return_value = b'<?xml version="1.0"?><EntityDescriptor>...</EntityDescriptor>'
        mock_metadata_class.return_value = mock_metadata
        
        config = SSOConfig(
            provider_type="saml",
            saml_entity_id="test-entity-id",
            saml_sso_url="https://sp.example.com/sso/callback/saml"
        )
        sso_manager.add_config("saml-config", config)
        
        response = self.client.get('/api/sso/metadata/saml/saml-config')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/xml')
    
    def test_sso_logout(self):
        """Test SSO logout"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['sso_user'] = {'email': 'user@example.com'}
        
        response = self.client.post('/api/sso/logout')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
    
    def test_get_sso_user_not_authenticated(self):
        """Test getting user when not authenticated"""
        response = self.client.get('/api/sso/user')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_sso_user(self):
        """Test getting authenticated user"""
        with self.client.session_transaction() as sess:
            sess['authenticated'] = True
            sess['sso_user'] = {
                'user_id': 'user123',
                'email': 'user@example.com',
                'name': 'John Doe'
            }
        
        response = self.client.get('/api/sso/user')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'user@example.com')


if __name__ == '__main__':
    unittest.main()


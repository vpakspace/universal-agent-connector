"""
SSO Integration Module
Supports SAML 2.0, OAuth 2.0, and LDAP authentication
"""

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import urlencode, parse_qs, urlparse

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False

try:
    import ldap3
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False

from flask import request, session, redirect, url_for, current_app
import uuid


class SSOProviderType(Enum):
    """SSO provider types"""
    SAML = "saml"
    OAUTH2 = "oauth2"
    LDAP = "ldap"


class AttributeMappingRule:
    """Rule for mapping SSO attributes to user attributes"""
    
    def __init__(
        self,
        sso_attribute: str,
        user_attribute: str,
        transform: Optional[Callable[[Any], Any]] = None,
        required: bool = False,
        default: Optional[Any] = None
    ):
        """
        Initialize attribute mapping rule
        
        Args:
            sso_attribute: Name of attribute in SSO response
            user_attribute: Name of attribute in user profile
            transform: Optional function to transform the value
            required: Whether this attribute is required
            default: Default value if attribute is missing
        """
        self.sso_attribute = sso_attribute
        self.user_attribute = user_attribute
        self.transform = transform or (lambda x: x)
        self.required = required
        self.default = default
    
    def map_value(self, sso_attributes: Dict[str, Any]) -> tuple[str, Any]:
        """
        Map SSO attribute to user attribute
        
        Returns:
            Tuple of (user_attribute, value)
        """
        value = sso_attributes.get(self.sso_attribute)
        
        if value is None:
            if self.required and self.default is None:
                raise ValueError(f"Required attribute '{self.sso_attribute}' not found")
            value = self.default
        
        if value is not None:
            value = self.transform(value)
        
        return (self.user_attribute, value)


@dataclass
class SSOConfig:
    """SSO configuration"""
    provider_type: str
    enabled: bool = True
    name: str = ""
    description: str = ""
    
    # SAML specific
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_slo_url: Optional[str] = None
    saml_x509_cert: Optional[str] = None
    saml_private_key: Optional[str] = None
    saml_attribute_map: Dict[str, str] = field(default_factory=dict)
    
    # OAuth2 specific
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_authorization_url: Optional[str] = None
    oauth2_token_url: Optional[str] = None
    oauth2_userinfo_url: Optional[str] = None
    oauth2_scopes: List[str] = field(default_factory=lambda: ["openid", "profile", "email"])
    oauth2_redirect_uri: Optional[str] = None
    
    # LDAP specific
    ldap_server_url: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_user_search_base: Optional[str] = None
    ldap_user_search_filter: Optional[str] = None
    ldap_group_search_base: Optional[str] = None
    ldap_group_search_filter: Optional[str] = None
    ldap_attributes: List[str] = field(default_factory=lambda: ["cn", "mail", "givenName", "sn"])
    
    # Attribute mapping
    attribute_mappings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        # Don't expose secrets in dict
        if result.get('saml_private_key'):
            result['saml_private_key'] = '***'
        if result.get('oauth2_client_secret'):
            result['oauth2_client_secret'] = '***'
        if result.get('ldap_bind_password'):
            result['ldap_bind_password'] = '***'
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SSOConfig':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class UserProfile:
    """User profile from SSO"""
    user_id: str
    email: str
    name: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    groups: List[str] = field(default_factory=list)
    provider: str = ""
    provider_user_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class SSOAuthenticator:
    """Main SSO authenticator"""
    
    def __init__(self):
        """Initialize SSO authenticator"""
        self.configs: Dict[str, SSOConfig] = {}
        self._attribute_mappings: Dict[str, List[AttributeMappingRule]] = {}
    
    def register_config(self, config_id: str, config: SSOConfig) -> None:
        """Register SSO configuration"""
        self.configs[config_id] = config
        self._build_attribute_mappings(config_id, config)
    
    def _build_attribute_mappings(self, config_id: str, config: SSOConfig) -> None:
        """Build attribute mapping rules from config"""
        rules = []
        
        # Default mappings based on provider type
        if config.provider_type == SSOProviderType.SAML.value:
            default_mappings = {
                'email': ('email', True),
                'name': ('name', False),
                'givenName': ('first_name', False),
                'surname': ('last_name', False),
                'groups': ('groups', False)
            }
        elif config.provider_type == SSOProviderType.OAUTH2.value:
            default_mappings = {
                'email': ('email', True),
                'name': ('name', False),
                'given_name': ('first_name', False),
                'family_name': ('last_name', False),
                'groups': ('groups', False)
            }
        else:  # LDAP
            default_mappings = {
                'mail': ('email', True),
                'cn': ('name', False),
                'givenName': ('first_name', False),
                'sn': ('last_name', False),
                'memberOf': ('groups', False)
            }
        
        # Apply custom mappings from config
        custom_mappings = {}
        for mapping in config.attribute_mappings:
            sso_attr = mapping.get('sso_attribute')
            user_attr = mapping.get('user_attribute')
            required = mapping.get('required', False)
            default = mapping.get('default')
            
            if sso_attr and user_attr:
                custom_mappings[sso_attr] = (user_attr, required, default)
        
        # Build rules
        for sso_attr, (user_attr, required) in default_mappings.items():
            if sso_attr not in custom_mappings:
                rules.append(AttributeMappingRule(sso_attr, user_attr, required=required))
        
        for sso_attr, (user_attr, required, default) in custom_mappings.items():
            rules.append(AttributeMappingRule(sso_attr, user_attr, required=required, default=default))
        
        self._attribute_mappings[config_id] = rules
    
    def authenticate_saml(self, config_id: str, saml_response: Optional[str] = None) -> Optional[Any]:
        """Authenticate using SAML 2.0"""
        if not SAML_AVAILABLE:
            raise RuntimeError("SAML library not available. Install python3-saml package.")
        
        config = self.configs.get(config_id)
        if not config or config.provider_type != SSOProviderType.SAML.value:
            raise ValueError(f"Invalid SAML config: {config_id}")
        
        # Prepare SAML request
        req = {
            'https': 'on' if request.scheme == 'https' else 'off',
            'http_host': request.host,
            'script_name': request.path,
            'get_data': dict(request.args),
            'post_data': dict(request.form)
        }
        
        # SAML settings
        saml_settings = {
            'sp': {
                'entityId': config.saml_entity_id or f"{request.scheme}://{request.host}/saml/metadata",
                'assertionConsumerService': {
                    'url': config.saml_sso_url or f"{request.scheme}://{request.host}/sso/callback/saml",
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
                },
                'singleLogoutService': {
                    'url': config.saml_slo_url or f"{request.scheme}://{request.host}/saml/sls",
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                }
            },
            'idp': {
                'entityId': config.saml_entity_id,
                'singleSignOnService': {
                    'url': config.saml_sso_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                },
                'x509cert': config.saml_x509_cert
            }
        }
        
        auth = OneLogin_Saml2_Auth(req, saml_settings)
        
        if not saml_response:
            # Initiate SSO - returns redirect
            return auth.login(return_to=request.args.get('return_to', '/'))
        
        # Process response
        auth.process_response()
        errors = auth.get_errors()
        
        if errors:
            raise ValueError(f"SAML authentication errors: {errors}")
        
        if not auth.is_authenticated():
            return None
        
        # Extract attributes
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        
        # Map attributes
        user_profile = self._map_attributes(config_id, attributes, name_id)
        user_profile.provider = SSOProviderType.SAML.value
        user_profile.provider_user_id = name_id
        
        return user_profile
    
    def authenticate_oauth2(self, config_id: str, code: Optional[str] = None, state: Optional[str] = None) -> Optional[Any]:
        """Authenticate using OAuth 2.0"""
        config = self.configs.get(config_id)
        if not config or config.provider_type != SSOProviderType.OAUTH2.value:
            raise ValueError(f"Invalid OAuth2 config: {config_id}")
        
        if not code:
            # Initiate OAuth flow
            state = str(uuid.uuid4())
            session['oauth2_state'] = state
            session['oauth2_config_id'] = config_id
            
            params = {
                'client_id': config.oauth2_client_id,
                'redirect_uri': config.oauth2_redirect_uri or f"{request.scheme}://{request.host}/sso/callback/oauth2",
                'response_type': 'code',
                'scope': ' '.join(config.oauth2_scopes),
                'state': state
            }
            
            auth_url = f"{config.oauth2_authorization_url}?{urlencode(params)}"
            return redirect(auth_url)
        
        # Verify state
        if state != session.get('oauth2_state'):
            raise ValueError("Invalid OAuth2 state parameter")
        
        # Exchange code for token
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests library required for OAuth2. Install with: pip install requests")
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': config.oauth2_redirect_uri or f"{request.scheme}://{request.host}/sso/callback/oauth2",
            'client_id': config.oauth2_client_id,
            'client_secret': config.oauth2_client_secret
        }
        
        response = requests.post(config.oauth2_token_url, data=token_data)
        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.text}")
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        
        # Get user info
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(config.oauth2_userinfo_url, headers=headers)
        if userinfo_response.status_code != 200:
            raise ValueError(f"Userinfo request failed: {userinfo_response.text}")
        
        userinfo = userinfo_response.json()
        
        # Map attributes
        user_profile = self._map_attributes(config_id, userinfo, userinfo.get('sub') or userinfo.get('id'))
        user_profile.provider = SSOProviderType.OAUTH2.value
        user_profile.provider_user_id = userinfo.get('sub') or userinfo.get('id', '')
        
        return user_profile
    
    def authenticate_ldap(self, config_id: str, username: str, password: str) -> Optional[UserProfile]:
        """Authenticate using LDAP"""
        if not LDAP_AVAILABLE:
            raise RuntimeError("LDAP library not available. Install ldap3 package.")
        
        config = self.configs.get(config_id)
        if not config or config.provider_type != SSOProviderType.LDAP.value:
            raise ValueError(f"Invalid LDAP config: {config_id}")
        
        # Connect to LDAP server
        from ldap3 import Server, Connection, ALL, SUBTREE
        
        server = Server(config.ldap_server_url, get_info=ALL)
        
        # Bind with service account
        conn = Connection(server, config.ldap_bind_dn, config.ldap_bind_password, auto_bind=True)
        
        # Search for user
        search_filter = config.ldap_user_search_filter or f"(uid={username})"
        search_base = config.ldap_user_search_base or config.ldap_base_dn
        
        conn.search(search_base, search_filter, attributes=config.ldap_attributes)
        
        if len(conn.entries) == 0:
            return None
        
        user_dn = conn.entries[0].entry_dn
        
        # Try to bind as user
        user_conn = Connection(server, user_dn, password, auto_bind=True)
        
        if not user_conn:
            return None
        
        # Get user attributes
        user_conn.search(user_dn, '(objectClass=*)', attributes=config.ldap_attributes)
        user_attrs = {}
        for attr in config.ldap_attributes:
            if hasattr(conn.entries[0], attr):
                value = getattr(conn.entries[0], attr)
                if isinstance(value, list) and len(value) == 1:
                    user_attrs[attr] = value[0]
                else:
                    user_attrs[attr] = value
        
        # Get groups
        groups = []
        if config.ldap_group_search_base:
            group_filter = config.ldap_group_search_filter or f"(member={user_dn})"
            conn.search(config.ldap_group_search_base, group_filter, attributes=['cn'])
            groups = [entry.cn.value for entry in conn.entries if hasattr(entry, 'cn')]
        
        # Map attributes
        user_profile = self._map_attributes(config_id, user_attrs, username)
        user_profile.provider = SSOProviderType.LDAP.value
        user_profile.provider_user_id = username
        user_profile.groups = groups
        
        user_conn.unbind()
        conn.unbind()
        
        return user_profile
    
    def _map_attributes(self, config_id: str, sso_attributes: Dict[str, Any], user_id: str) -> UserProfile:
        """Map SSO attributes to user profile"""
        mappings = self._attribute_mappings.get(config_id, [])
        
        user_attrs = {}
        email = None
        name = None
        
        for rule in mappings:
            try:
                attr_name, value = rule.map_value(sso_attributes)
                user_attrs[attr_name] = value
                
                if attr_name == 'email':
                    email = value
                elif attr_name == 'name':
                    name = value
            except ValueError:
                # Skip required attributes that are missing
                pass
        
        if not email:
            raise ValueError("Email attribute is required but not found in SSO response")
        
        profile = UserProfile(
            user_id=user_id,
            email=email,
            name=name,
            attributes=user_attrs,
            provider_user_id=user_id
        )
        
        # Extract groups if available
        if 'groups' in user_attrs:
            groups = user_attrs['groups']
            if isinstance(groups, list):
                profile.groups = groups
            elif isinstance(groups, str):
                profile.groups = [groups]
        
        return profile


class SSOManager:
    """Manager for SSO configurations and authentication"""
    
    def __init__(self):
        """Initialize SSO manager"""
        self.authenticator = SSOAuthenticator()
        self.configs: Dict[str, SSOConfig] = {}
        self.active_providers: Dict[str, str] = {}  # provider_type -> config_id
    
    def add_config(self, config_id: str, config: SSOConfig) -> None:
        """Add SSO configuration"""
        self.configs[config_id] = config
        self.authenticator.register_config(config_id, config)
        
        if config.enabled:
            self.active_providers[config.provider_type] = config_id
    
    def get_config(self, config_id: str) -> Optional[SSOConfig]:
        """Get SSO configuration"""
        return self.configs.get(config_id)
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """List all SSO configurations"""
        return [config.to_dict() for config in self.configs.values()]
    
    def delete_config(self, config_id: str) -> bool:
        """Delete SSO configuration"""
        if config_id in self.configs:
            config = self.configs[config_id]
            del self.configs[config_id]
            
            # Remove from active providers if it was active
            if config.provider_type in self.active_providers:
                if self.active_providers[config.provider_type] == config_id:
                    del self.active_providers[config.provider_type]
            
            return True
        return False
    
    def authenticate(self, provider_type: str, **kwargs) -> Optional[UserProfile]:
        """Authenticate using specified provider type"""
        config_id = self.active_providers.get(provider_type)
        if not config_id:
            raise ValueError(f"No active {provider_type} provider configured")
        
        if provider_type == SSOProviderType.SAML.value:
            return self.authenticator.authenticate_saml(config_id, kwargs.get('saml_response'))
        elif provider_type == SSOProviderType.OAUTH2.value:
            return self.authenticator.authenticate_oauth2(config_id, kwargs.get('code'), kwargs.get('state'))
        elif provider_type == SSOProviderType.LDAP.value:
            return self.authenticator.authenticate_ldap(config_id, kwargs.get('username'), kwargs.get('password'))
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")


# Global instance
sso_manager = SSOManager()


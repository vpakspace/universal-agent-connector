"""
SSO Authentication Module
"""

from .sso import (
    SSOManager,
    SSOAuthenticator,
    SSOConfig,
    SSOProviderType,
    UserProfile,
    AttributeMappingRule,
    sso_manager
)

__all__ = [
    'SSOManager',
    'SSOAuthenticator',
    'SSOConfig',
    'SSOProviderType',
    'UserProfile',
    'AttributeMappingRule',
    'sso_manager'
]


"""
JWT Authentication Module for Universal Agent Connector.

Provides JWT token generation, validation, and middleware for secure API access.
Supports both access tokens (short-lived) and refresh tokens (long-lived).
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
from functools import wraps

import jwt
from flask import request, jsonify, current_app, g


# Default configuration
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7
DEFAULT_ALGORITHM = "HS256"


@dataclass
class JWTConfig:
    """JWT configuration settings."""
    secret_key: str = field(default_factory=lambda: os.getenv('JWT_SECRET_KEY', secrets.token_hex(32)))
    algorithm: str = DEFAULT_ALGORITHM
    access_token_expire_minutes: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
    refresh_token_expire_days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
    issuer: str = "universal-agent-connector"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding secret)."""
        return {
            'algorithm': self.algorithm,
            'access_token_expire_minutes': self.access_token_expire_minutes,
            'refresh_token_expire_days': self.refresh_token_expire_days,
            'issuer': self.issuer,
        }


@dataclass
class TokenPayload:
    """Decoded token payload."""
    agent_id: str
    role: Optional[str] = None
    token_type: str = "access"  # "access" or "refresh"
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None  # JWT ID for token revocation

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenPayload':
        """Create TokenPayload from dictionary."""
        return cls(
            agent_id=data.get('sub', ''),
            role=data.get('role'),
            token_type=data.get('type', 'access'),
            exp=datetime.fromtimestamp(data['exp'], tz=timezone.utc) if 'exp' in data else None,
            iat=datetime.fromtimestamp(data['iat'], tz=timezone.utc) if 'iat' in data else None,
            jti=data.get('jti'),
        )


class JWTManager:
    """JWT token manager for authentication."""

    def __init__(self, config: Optional[JWTConfig] = None):
        """Initialize JWT manager with config."""
        self.config = config or JWTConfig()
        self._revoked_tokens: set = set()  # In-memory revocation list (use Redis in production)

    def generate_access_token(
        self,
        agent_id: str,
        role: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a short-lived access token.

        Args:
            agent_id: Agent identifier (becomes 'sub' claim)
            role: Optional user role for RBAC
            additional_claims: Optional extra claims to include

        Returns:
            JWT access token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = {
            'sub': agent_id,
            'type': 'access',
            'iat': now,
            'exp': expire,
            'iss': self.config.issuer,
            'jti': secrets.token_hex(16),
        }

        if role:
            payload['role'] = role

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

    def generate_refresh_token(
        self,
        agent_id: str,
        role: Optional[str] = None
    ) -> str:
        """
        Generate a long-lived refresh token.

        Args:
            agent_id: Agent identifier
            role: Optional user role

        Returns:
            JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.config.refresh_token_expire_days)

        payload = {
            'sub': agent_id,
            'type': 'refresh',
            'iat': now,
            'exp': expire,
            'iss': self.config.issuer,
            'jti': secrets.token_hex(16),
        }

        if role:
            payload['role'] = role

        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

    def generate_token_pair(
        self,
        agent_id: str,
        role: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate both access and refresh tokens.

        Args:
            agent_id: Agent identifier
            role: Optional user role

        Returns:
            Dictionary with 'access_token' and 'refresh_token'
        """
        return {
            'access_token': self.generate_access_token(agent_id, role),
            'refresh_token': self.generate_refresh_token(agent_id, role),
            'token_type': 'Bearer',
            'expires_in': self.config.access_token_expire_minutes * 60,  # seconds
        }

    def verify_token(
        self,
        token: str,
        expected_type: str = "access"
    ) -> Tuple[bool, Optional[TokenPayload], Optional[str]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            expected_type: Expected token type ("access" or "refresh")

        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
            )

            # Check token type
            token_type = payload.get('type', 'access')
            if token_type != expected_type:
                return False, None, f"Invalid token type: expected {expected_type}, got {token_type}"

            # Check if token is revoked
            jti = payload.get('jti')
            if jti and jti in self._revoked_tokens:
                return False, None, "Token has been revoked"

            return True, TokenPayload.from_dict(payload), None

        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidIssuerError:
            return False, None, "Invalid token issuer"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"

    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
        """
        Generate new access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (success, new_tokens_dict, error_message)
        """
        is_valid, payload, error = self.verify_token(refresh_token, expected_type="refresh")

        if not is_valid or payload is None:
            return False, None, error or "Invalid refresh token"

        # Generate new access token (keep the same role)
        new_tokens = {
            'access_token': self.generate_access_token(payload.agent_id, payload.role),
            'token_type': 'Bearer',
            'expires_in': self.config.access_token_expire_minutes * 60,
        }

        return True, new_tokens, None

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding its JTI to the revocation list.

        Args:
            token: Token to revoke

        Returns:
            True if revoked successfully
        """
        try:
            # Decode without verification to get JTI
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                options={"verify_exp": False}
            )
            jti = payload.get('jti')
            if jti:
                self._revoked_tokens.add(jti)
                return True
            return False
        except jwt.InvalidTokenError:
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get JWT configuration (excluding secret)."""
        return self.config.to_dict()


# Global JWT manager instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """Get or create global JWT manager instance."""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


def init_jwt_manager(config: Optional[JWTConfig] = None) -> JWTManager:
    """Initialize global JWT manager with optional config."""
    global _jwt_manager
    _jwt_manager = JWTManager(config)
    return _jwt_manager


def jwt_required(f):
    """
    Decorator to require valid JWT access token.

    Sets g.jwt_payload with the decoded token payload.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid Authorization header. Use: Bearer <token>'
            }), 401

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        jwt_mgr = get_jwt_manager()
        is_valid, payload, error = jwt_mgr.verify_token(token, expected_type="access")

        if not is_valid:
            return jsonify({
                'error': 'Unauthorized',
                'message': error or 'Invalid token'
            }), 401

        # Store payload in Flask's g object for access in route
        g.jwt_payload = payload

        return f(*args, **kwargs)

    return decorated


def jwt_or_api_key_required(f):
    """
    Decorator to require either JWT access token OR API Key.

    Checks Authorization header for Bearer token first,
    then falls back to X-API-Key header.

    Sets g.auth_type ('jwt' or 'api_key') and g.jwt_payload (if JWT).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')

        # Try JWT first
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            jwt_mgr = get_jwt_manager()
            is_valid, payload, error = jwt_mgr.verify_token(token, expected_type="access")

            if is_valid and payload:
                g.auth_type = 'jwt'
                g.jwt_payload = payload
                return f(*args, **kwargs)

        # Fall back to API Key
        if api_key:
            g.auth_type = 'api_key'
            g.jwt_payload = None
            return f(*args, **kwargs)

        return jsonify({
            'error': 'Unauthorized',
            'message': 'Missing authentication. Provide Authorization: Bearer <token> or X-API-Key header.'
        }), 401

    return decorated


def get_current_agent_id() -> Optional[str]:
    """Get current agent ID from JWT payload or None."""
    payload = getattr(g, 'jwt_payload', None)
    if payload:
        return payload.agent_id
    return None


def get_current_role() -> Optional[str]:
    """Get current role from JWT payload or X-User-Role header."""
    payload = getattr(g, 'jwt_payload', None)
    if payload and payload.role:
        return payload.role
    return request.headers.get('X-User-Role')

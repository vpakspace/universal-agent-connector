"""
Unit tests for JWT Authentication module.

Tests JWT token generation, validation, refresh, and revocation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import time

from ai_agent_connector.app.security.jwt_auth import (
    JWTManager,
    JWTConfig,
    TokenPayload,
    get_jwt_manager,
    init_jwt_manager,
)


class TestJWTConfig:
    """Test JWT configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = JWTConfig()
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7
        assert config.issuer == "universal-agent-connector"
        assert len(config.secret_key) == 64  # 32 bytes hex

    def test_custom_config(self):
        """Test custom configuration."""
        config = JWTConfig(
            secret_key="test-secret-key",
            algorithm="HS384",
            access_token_expire_minutes=15,
            refresh_token_expire_days=30,
        )
        assert config.secret_key == "test-secret-key"
        assert config.algorithm == "HS384"
        assert config.access_token_expire_minutes == 15
        assert config.refresh_token_expire_days == 30

    def test_to_dict_excludes_secret(self):
        """Test that to_dict excludes secret key."""
        config = JWTConfig(secret_key="super-secret")
        d = config.to_dict()
        assert 'secret_key' not in d
        assert 'algorithm' in d
        assert 'access_token_expire_minutes' in d


class TestTokenPayload:
    """Test TokenPayload dataclass."""

    def test_from_dict(self):
        """Test creating TokenPayload from dictionary."""
        now = datetime.now(timezone.utc)
        data = {
            'sub': 'agent-123',
            'role': 'Doctor',
            'type': 'access',
            'exp': now.timestamp(),
            'iat': now.timestamp(),
            'jti': 'token-id-123',
        }
        payload = TokenPayload.from_dict(data)
        assert payload.agent_id == 'agent-123'
        assert payload.role == 'Doctor'
        assert payload.token_type == 'access'
        assert payload.jti == 'token-id-123'

    def test_from_dict_minimal(self):
        """Test creating TokenPayload with minimal data."""
        data = {'sub': 'agent-456'}
        payload = TokenPayload.from_dict(data)
        assert payload.agent_id == 'agent-456'
        assert payload.role is None
        assert payload.token_type == 'access'


class TestJWTManager:
    """Test JWTManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = JWTConfig(
            secret_key="test-secret-key-for-testing",
            access_token_expire_minutes=5,
            refresh_token_expire_days=1,
        )
        self.manager = JWTManager(self.config)

    def test_generate_access_token(self):
        """Test access token generation."""
        token = self.manager.generate_access_token("agent-123", role="Doctor")
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        is_valid, payload, error = self.manager.verify_token(token)
        assert is_valid is True
        assert payload.agent_id == "agent-123"
        assert payload.role == "Doctor"
        assert payload.token_type == "access"

    def test_generate_refresh_token(self):
        """Test refresh token generation."""
        token = self.manager.generate_refresh_token("agent-123", role="Admin")
        assert isinstance(token, str)

        # Verify token
        is_valid, payload, error = self.manager.verify_token(token, expected_type="refresh")
        assert is_valid is True
        assert payload.agent_id == "agent-123"
        assert payload.token_type == "refresh"

    def test_generate_token_pair(self):
        """Test token pair generation."""
        tokens = self.manager.generate_token_pair("agent-123", role="Nurse")
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['token_type'] == 'Bearer'
        assert tokens['expires_in'] == 5 * 60  # 5 minutes in seconds

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        # Create manager with very short expiration
        short_config = JWTConfig(
            secret_key="test-secret",
            access_token_expire_minutes=0,  # Immediate expiration
        )
        short_manager = JWTManager(short_config)

        # Generate token and wait
        token = short_manager.generate_access_token("agent-123")
        time.sleep(0.1)

        # Should be expired
        is_valid, payload, error = short_manager.verify_token(token)
        assert is_valid is False
        assert "expired" in error.lower()

    def test_verify_wrong_token_type(self):
        """Test that wrong token type is rejected."""
        access_token = self.manager.generate_access_token("agent-123")

        # Try to verify as refresh token
        is_valid, payload, error = self.manager.verify_token(access_token, expected_type="refresh")
        assert is_valid is False
        assert "type" in error.lower()

    def test_verify_invalid_token(self):
        """Test that invalid tokens are rejected."""
        is_valid, payload, error = self.manager.verify_token("invalid-token")
        assert is_valid is False
        assert error is not None

    def test_verify_tampered_token(self):
        """Test that tampered tokens are rejected."""
        token = self.manager.generate_access_token("agent-123")
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"

        is_valid, payload, error = self.manager.verify_token(tampered)
        assert is_valid is False

    def test_refresh_access_token(self):
        """Test refreshing access token."""
        tokens = self.manager.generate_token_pair("agent-123", role="Doctor")

        success, new_tokens, error = self.manager.refresh_access_token(tokens['refresh_token'])
        assert success is True
        assert 'access_token' in new_tokens
        assert error is None

        # Verify new access token
        is_valid, payload, _ = self.manager.verify_token(new_tokens['access_token'])
        assert is_valid is True
        assert payload.agent_id == "agent-123"
        assert payload.role == "Doctor"

    def test_refresh_with_access_token_fails(self):
        """Test that refreshing with access token fails."""
        access_token = self.manager.generate_access_token("agent-123")

        success, new_tokens, error = self.manager.refresh_access_token(access_token)
        assert success is False
        assert "type" in error.lower()

    def test_revoke_token(self):
        """Test token revocation."""
        token = self.manager.generate_access_token("agent-123")

        # Token should be valid
        is_valid, _, _ = self.manager.verify_token(token)
        assert is_valid is True

        # Revoke token
        revoked = self.manager.revoke_token(token)
        assert revoked is True

        # Token should be invalid now
        is_valid, _, error = self.manager.verify_token(token)
        assert is_valid is False
        assert "revoked" in error.lower()

    def test_additional_claims(self):
        """Test adding additional claims to token."""
        token = self.manager.generate_access_token(
            "agent-123",
            role="Doctor",
            additional_claims={'department': 'Cardiology', 'level': 3}
        )

        is_valid, payload, _ = self.manager.verify_token(token)
        assert is_valid is True

    def test_get_config(self):
        """Test getting configuration."""
        config = self.manager.get_config()
        assert 'algorithm' in config
        assert 'access_token_expire_minutes' in config
        assert 'secret_key' not in config


class TestGlobalJWTManager:
    """Test global JWT manager functions."""

    def test_get_jwt_manager_singleton(self):
        """Test that get_jwt_manager returns same instance."""
        mgr1 = get_jwt_manager()
        mgr2 = get_jwt_manager()
        # Should be same instance
        assert mgr1 is mgr2

    def test_init_jwt_manager(self):
        """Test initializing JWT manager with config."""
        config = JWTConfig(
            secret_key="custom-secret",
            access_token_expire_minutes=60,
        )
        mgr = init_jwt_manager(config)
        assert mgr.config.access_token_expire_minutes == 60


class TestJWTAPIEndpoints:
    """Test JWT API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        from flask import Flask
        from ai_agent_connector.app.api import api_bp

        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp, url_prefix='/api')
        self.client = self.app.test_client()

        # Initialize JWT manager
        init_jwt_manager(JWTConfig(
            secret_key="test-secret-for-api",
            access_token_expire_minutes=30,
        ))

    def test_get_token_without_api_key(self):
        """Test that token endpoint requires API key."""
        response = self.client.post('/api/auth/token')
        assert response.status_code == 401
        data = response.get_json()
        assert 'X-API-Key required' in data['message']

    def test_refresh_token_missing_body(self):
        """Test refresh endpoint without body."""
        response = self.client.post('/api/auth/refresh', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'refresh_token is required' in data['message']

    def test_refresh_token_invalid(self):
        """Test refresh with invalid token."""
        response = self.client.post('/api/auth/refresh', json={
            'refresh_token': 'invalid-token'
        })
        assert response.status_code == 401

    def test_verify_token_missing_body(self):
        """Test verify endpoint without body."""
        response = self.client.post('/api/auth/verify', json={})
        assert response.status_code == 400

    def test_verify_token_invalid(self):
        """Test verify with invalid token."""
        response = self.client.post('/api/auth/verify', json={
            'token': 'invalid-token'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is False
        assert 'error' in data

    def test_verify_token_valid(self):
        """Test verify with valid token."""
        mgr = get_jwt_manager()
        token = mgr.generate_access_token("test-agent", role="Doctor")

        response = self.client.post('/api/auth/verify', json={
            'token': token
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is True
        assert data['payload']['agent_id'] == 'test-agent'
        assert data['payload']['role'] == 'Doctor'

    def test_get_jwt_config(self):
        """Test getting JWT configuration."""
        response = self.client.get('/api/auth/config')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'config' in data
        assert 'algorithm' in data['config']
        assert 'secret_key' not in data['config']

    def test_revoke_token_unauthenticated(self):
        """Test revoke endpoint without authentication."""
        response = self.client.post('/api/auth/revoke', json={
            'token': 'some-token'
        })
        assert response.status_code == 401

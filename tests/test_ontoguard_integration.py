"""
Tests for OntoGuard integration with Universal Agent Connector.

This module contains unit tests and integration tests for the OntoGuard
semantic validation functionality.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_ontology(tmp_path) -> str:
    """
    Create a sample OWL ontology for testing.

    This creates a minimal ontology with Users, Orders, and basic action rules.
    """
    ontology_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rdf:RDF [
    <!ENTITY owl "http://www.w3.org/2002/07/owl#">
    <!ENTITY rdf "http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <!ENTITY rdfs "http://www.w3.org/2000/01/rdf-schema#">
    <!ENTITY xsd "http://www.w3.org/2001/XMLSchema#">
]>
<rdf:RDF xmlns="http://example.org/ecommerce#"
     xml:base="http://example.org/ecommerce"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">

    <owl:Ontology rdf:about="http://example.org/ecommerce"/>

    <!-- Classes -->
    <owl:Class rdf:about="#User">
        <rdfs:label>User</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="#Order">
        <rdfs:label>Order</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="#Admin">
        <rdfs:label>Admin</rdfs:label>
    </owl:Class>

    <owl:Class rdf:about="#Customer">
        <rdfs:label>Customer</rdfs:label>
    </owl:Class>

    <!-- Properties -->
    <owl:ObjectProperty rdf:about="#requiresRole">
        <rdfs:label>requiresRole</rdfs:label>
    </owl:ObjectProperty>

    <owl:ObjectProperty rdf:about="#appliesTo">
        <rdfs:label>appliesTo</rdfs:label>
    </owl:ObjectProperty>

    <!-- Action Individuals -->
    <owl:NamedIndividual rdf:about="#deleteUserAction">
        <rdfs:label>delete user</rdfs:label>
        <requiresRole rdf:resource="#Admin"/>
        <appliesTo rdf:resource="#User"/>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="#createOrderAction">
        <rdfs:label>create order</rdfs:label>
        <requiresRole rdf:resource="#Customer"/>
        <appliesTo rdf:resource="#Order"/>
    </owl:NamedIndividual>

</rdf:RDF>
'''

    ontology_file = tmp_path / "test_ontology.owl"
    ontology_file.write_text(ontology_content)
    return str(ontology_file)


@pytest.fixture
def adapter():
    """Create a fresh OntoGuard adapter for testing."""
    from ai_agent_connector.app.security import (
        OntoGuardAdapter,
        reset_ontoguard_adapter
    )
    reset_ontoguard_adapter()
    return OntoGuardAdapter()


@pytest.fixture
def initialized_adapter(adapter, sample_ontology):
    """Create an adapter initialized with the sample ontology."""
    adapter.initialize([sample_ontology])
    return adapter


# ============================================================================
# Unit Tests - OntoGuardAdapter
# ============================================================================

class TestOntoGuardAdapter:
    """Tests for the OntoGuardAdapter class."""

    def test_initialization_without_ontoguard(self):
        """Test graceful degradation when OntoGuard is not installed."""
        from ai_agent_connector.app.security import OntoGuardAdapter

        adapter = OntoGuardAdapter()
        # Without initialization, should be in pass-through mode
        assert not adapter._initialized

    def test_initialization_with_nonexistent_file(self, adapter):
        """Test initialization with non-existent ontology file."""
        result = adapter.initialize(["/nonexistent/path/ontology.owl"])

        # Should initialize but in pass-through mode
        assert adapter._initialized
        assert adapter._pass_through_mode

    def test_pass_through_mode_allows_all(self, adapter):
        """Test that pass-through mode allows all actions."""
        adapter._initialized = True
        adapter._pass_through_mode = True

        result = adapter.validate_action('delete', 'User', {'role': 'Customer'})

        assert result.allowed is True
        assert 'pass' in result.reason.lower()

    @pytest.mark.skipif(
        not os.path.exists('/home/vladspace_ubuntu24/ontoguard-ai'),
        reason="OntoGuard not installed"
    )
    def test_initialization_with_valid_ontology(self, adapter, sample_ontology):
        """Test successful initialization with valid ontology."""
        result = adapter.initialize([sample_ontology])

        assert result is True
        assert adapter._initialized
        assert not adapter._pass_through_mode

    @pytest.mark.skipif(
        not os.path.exists('/home/vladspace_ubuntu24/ontoguard-ai'),
        reason="OntoGuard not installed"
    )
    def test_validation_admin_can_delete_user(self, initialized_adapter):
        """Test that Admin role can delete User."""
        result = initialized_adapter.validate_action(
            action='delete user',
            entity_type='User',
            context={'role': 'Admin', 'user_id': '123'}
        )

        assert result.allowed is True

    @pytest.mark.skipif(
        not os.path.exists('/home/vladspace_ubuntu24/ontoguard-ai'),
        reason="OntoGuard not installed"
    )
    def test_validation_customer_cannot_delete_user(self, initialized_adapter):
        """Test that Customer role cannot delete User."""
        result = initialized_adapter.validate_action(
            action='delete user',
            entity_type='User',
            context={'role': 'Customer', 'user_id': '456'}
        )

        assert result.allowed is False
        assert 'role' in result.reason.lower() or 'permission' in result.reason.lower()


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        from ai_agent_connector.app.security import ValidationResult

        result = ValidationResult(
            allowed=True,
            reason="Action is permitted",
            constraints=["constraint1"],
            suggestions=["suggestion1"],
            metadata={"key": "value"}
        )

        assert result.allowed is True
        assert result.reason == "Action is permitted"
        assert result.constraints == ["constraint1"]
        assert result.suggestions == ["suggestion1"]
        assert result.metadata == {"key": "value"}

    def test_validation_result_to_dict(self):
        """Test converting ValidationResult to dictionary."""
        from ai_agent_connector.app.security import ValidationResult

        result = ValidationResult(
            allowed=False,
            reason="Permission denied"
        )

        result_dict = result.to_dict()

        assert result_dict['allowed'] is False
        assert result_dict['reason'] == "Permission denied"
        assert 'constraints' in result_dict
        assert 'suggestions' in result_dict


class TestCheckPermissions:
    """Tests for the check_permissions method."""

    def test_check_permissions_pass_through(self, adapter):
        """Test check_permissions in pass-through mode."""
        adapter._initialized = True
        adapter._pass_through_mode = True

        result = adapter.check_permissions('Customer', 'delete', 'User')

        # Pass-through mode should allow all
        assert result is True

    @pytest.mark.skipif(
        not os.path.exists('/home/vladspace_ubuntu24/ontoguard-ai'),
        reason="OntoGuard not installed"
    )
    def test_check_permissions_admin_delete(self, initialized_adapter):
        """Test Admin has delete permission on User."""
        result = initialized_adapter.check_permissions('Admin', 'delete user', 'User')
        assert result is True


class TestGetAllowedActions:
    """Tests for the get_allowed_actions method."""

    def test_get_allowed_actions_pass_through(self, adapter):
        """Test get_allowed_actions in pass-through mode."""
        adapter._initialized = True
        adapter._pass_through_mode = True

        actions = adapter.get_allowed_actions('Customer', 'Order')

        # Pass-through mode should return wildcard
        assert '*' in actions or len(actions) > 0


# ============================================================================
# Unit Tests - Exceptions
# ============================================================================

class TestExceptions:
    """Tests for OntoGuard exceptions."""

    def test_validation_denied_error(self):
        """Test ValidationDeniedError creation and properties."""
        from ai_agent_connector.app.security.exceptions import ValidationDeniedError

        error = ValidationDeniedError(
            action='delete',
            entity_type='User',
            reason='Requires Admin role',
            suggestions=['Use read instead']
        )

        assert error.action == 'delete'
        assert error.entity_type == 'User'
        assert 'Admin' in error.reason
        assert 'read' in error.suggestions[0]
        assert 'delete' in str(error)

    def test_ontology_load_error(self):
        """Test OntologyLoadError creation."""
        from ai_agent_connector.app.security.exceptions import OntologyLoadError

        error = OntologyLoadError(
            path='/invalid/path.owl',
            error='File not found'
        )

        assert error.path == '/invalid/path.owl'
        assert 'File not found' in error.error
        assert '/invalid/path.owl' in str(error)

    def test_configuration_error(self):
        """Test ConfigurationError creation."""
        from ai_agent_connector.app.security.exceptions import ConfigurationError

        error = ConfigurationError(
            error='Invalid field',
            config_path='/path/to/config.yaml',
            field='ontologies'
        )

        assert error.config_path == '/path/to/config.yaml'
        assert error.field == 'ontologies'
        assert 'Invalid field' in str(error)

    def test_permission_denied_error(self):
        """Test PermissionDeniedError creation."""
        from ai_agent_connector.app.security.exceptions import PermissionDeniedError

        error = PermissionDeniedError(
            role='Customer',
            action='delete',
            entity_type='User',
            required_role='Admin'
        )

        assert error.role == 'Customer'
        assert error.required_role == 'Admin'
        assert 'Customer' in str(error)
        assert 'Admin' in str(error)


# ============================================================================
# Unit Tests - MCP Tools
# ============================================================================

class TestMCPTools:
    """Tests for OntoGuard MCP tools."""

    def test_validate_action_tool_without_adapter(self):
        """Test validate_action_tool when OntoGuard not available."""
        from ai_agent_connector.app.security import reset_ontoguard_adapter
        reset_ontoguard_adapter()

        from ai_agent_connector.app.mcp.tools import validate_action_tool

        result = validate_action_tool('delete', 'User', {'role': 'Customer'})

        # Should return pass-through result
        assert result['allowed'] is True
        assert 'pass' in result['reason'].lower() or 'not available' in result['reason'].lower()

    def test_check_permissions_tool(self):
        """Test check_permissions_tool."""
        from ai_agent_connector.app.mcp.tools import check_permissions_tool

        result = check_permissions_tool('Admin', 'delete', 'User')

        assert 'role' in result
        assert 'action' in result
        assert 'entity_type' in result
        assert 'allowed' in result

    def test_get_allowed_actions_tool(self):
        """Test get_allowed_actions_tool."""
        from ai_agent_connector.app.mcp.tools import get_allowed_actions_tool

        result = get_allowed_actions_tool('Customer', 'Order')

        assert 'role' in result
        assert 'entity_type' in result
        assert 'allowed_actions' in result

    def test_ontoguard_tools_list(self):
        """Test that ONTOGUARD_TOOLS is properly defined."""
        from ai_agent_connector.app.mcp.tools import ONTOGUARD_TOOLS

        assert isinstance(ONTOGUARD_TOOLS, list)
        assert len(ONTOGUARD_TOOLS) >= 4

        # Check tool structure
        for tool in ONTOGUARD_TOOLS:
            assert 'name' in tool
            assert 'description' in tool
            assert 'function' in tool
            assert 'parameters' in tool


# ============================================================================
# Integration Tests
# ============================================================================

class TestAPIIntegration:
    """Integration tests for API endpoints with OntoGuard."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        try:
            from main_simple import create_app
            app = create_app('testing')
            app.config['TESTING'] = True
            with app.test_client() as client:
                yield client
        except Exception as e:
            pytest.skip(f"Could not create test client: {e}")

    def test_ontoguard_status_endpoint(self, client):
        """Test /api/ontoguard/status endpoint."""
        response = client.get('/api/ontoguard/status')

        assert response.status_code == 200
        data = response.get_json()
        assert 'enabled' in data
        assert 'active' in data

    def test_ontoguard_validate_endpoint(self, client):
        """Test /api/ontoguard/validate endpoint."""
        response = client.post('/api/ontoguard/validate', json={
            'action': 'read',
            'entity_type': 'User',
            'context': {'role': 'Admin'}
        })

        assert response.status_code in [200, 403]
        data = response.get_json()
        assert 'allowed' in data
        assert 'reason' in data

    def test_ontoguard_validate_missing_params(self, client):
        """Test /api/ontoguard/validate with missing parameters."""
        response = client.post('/api/ontoguard/validate', json={
            'action': 'read'
            # Missing entity_type
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_ontoguard_permissions_endpoint(self, client):
        """Test /api/ontoguard/permissions endpoint."""
        response = client.post('/api/ontoguard/permissions', json={
            'role': 'Admin',
            'action': 'delete',
            'entity_type': 'User'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'allowed' in data

    def test_ontoguard_allowed_actions_endpoint(self, client):
        """Test /api/ontoguard/allowed-actions endpoint."""
        response = client.get('/api/ontoguard/allowed-actions?role=Admin&entity_type=User')

        assert response.status_code == 200
        data = response.get_json()
        assert 'allowed_actions' in data


# ============================================================================
# Policy Engine Integration Tests
# ============================================================================

class TestPolicyEngineIntegration:
    """Tests for OntoGuard integration with PolicyEngine."""

    def test_ontoguard_validator_creation(self):
        """Test creating OntoGuardValidator."""
        from policy_engine import OntoGuardValidator

        validator = OntoGuardValidator()
        assert validator is not None

    def test_ontoguard_validator_validate_pass_through(self):
        """Test OntoGuardValidator in pass-through mode."""
        from policy_engine import OntoGuardValidator, ValidationResult

        validator = OntoGuardValidator()

        result = validator.validate(
            action='delete',
            entity_type='User',
            context={'role': 'Customer'},
            policy={'ontoguard_enabled': True}
        )

        assert isinstance(result, ValidationResult)

    def test_extended_policy_engine_creation(self):
        """Test creating ExtendedPolicyEngine."""
        from policy_engine import ExtendedPolicyEngine

        engine = ExtendedPolicyEngine(
            max_calls_per_hour=100,
            max_complexity_score=100,
            enable_ontoguard=True
        )

        assert engine._ontoguard_enabled is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

"""Unit tests for OntoGuard adapter and exceptions (no OntoGuard library needed)."""

from unittest.mock import MagicMock, patch

import pytest
from ai_agent_connector.app.security.ontoguard_adapter import (
    ValidationResult,
    OntoGuardAdapter,
    get_ontoguard_adapter,
    reset_ontoguard_adapter,
)
from ai_agent_connector.app.security.exceptions import (
    OntoGuardError,
    ValidationDeniedError,
    OntologyLoadError,
    OntologyParseError,
    ConfigurationError,
    PermissionDeniedError,
    ApprovalRequiredError,
)


class TestValidationResult:
    def test_creation(self):
        r = ValidationResult(allowed=True, reason="ok")
        assert r.allowed is True
        assert r.reason == "ok"
        assert r.constraints == []
        assert r.suggestions == []

    def test_to_dict(self):
        r = ValidationResult(allowed=False, reason="denied", constraints=["c1"])
        d = r.to_dict()
        assert d["allowed"] is False
        assert d["constraints"] == ["c1"]

    def test_with_metadata(self):
        r = ValidationResult(allowed=True, reason="ok", metadata={"key": "val"})
        assert r.to_dict()["metadata"] == {"key": "val"}


class TestOntoGuardAdapter:
    def test_init(self):
        adapter = OntoGuardAdapter()
        assert adapter.validator is None
        assert adapter._initialized is False

    def test_is_active_before_init(self):
        adapter = OntoGuardAdapter()
        assert adapter.is_active is False

    def test_validate_action_uninitialized(self):
        adapter = OntoGuardAdapter()
        result = adapter.validate_action("read", "User", {"role": "Admin"})
        assert result.allowed is True
        assert "not initialized" in result.reason

    def test_pass_through_mode_no_paths(self):
        adapter = OntoGuardAdapter()
        success = adapter.initialize(ontology_paths=[])
        assert success is True
        assert adapter._pass_through_mode is True
        assert adapter.is_active is False

    def test_pass_through_validate(self):
        adapter = OntoGuardAdapter()
        adapter.initialize(ontology_paths=[])
        result = adapter.validate_action("delete", "User", {"role": "Admin"})
        assert result.allowed is True
        assert "pass-through" in result.reason

    def test_check_permissions_pass_through(self):
        adapter = OntoGuardAdapter()
        adapter.initialize(ontology_paths=[])
        assert adapter.check_permissions("Admin", "delete", "User") is True

    def test_get_allowed_actions_pass_through(self):
        adapter = OntoGuardAdapter()
        adapter.initialize(ontology_paths=[])
        assert adapter.get_allowed_actions("Admin", "User") == ["*"]

    def test_explain_rule_pass_through(self):
        adapter = OntoGuardAdapter()
        adapter.initialize(ontology_paths=[])
        explanation = adapter.explain_rule("delete", "User", {"role": "Admin"})
        assert "not active" in explanation

    def test_initialize_import_error(self):
        adapter = OntoGuardAdapter()
        with patch.dict("sys.modules", {"ontoguard": None, "ontoguard.validator": None}):
            result = adapter.initialize(ontology_paths=["/fake/path.owl"])
        assert adapter._pass_through_mode is True

    def test_with_mock_validator(self):
        adapter = OntoGuardAdapter()
        adapter._initialized = True
        adapter._pass_through_mode = False

        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.reason = "denied by OWL"
        mock_result.suggested_actions = ["try read"]
        mock_result.metadata = {"constraint_type": "role_based", "required_role": "Admin"}

        adapter.validator = MagicMock()
        adapter.validator.validate.return_value = mock_result

        result = adapter.validate_action("delete", "User", {"role": "Customer", "user_id": "1"})
        assert result.allowed is False
        assert "denied by OWL" in result.reason
        assert "try read" in result.suggestions

    def test_check_permissions_with_mock(self):
        adapter = OntoGuardAdapter()
        adapter._initialized = True
        adapter._pass_through_mode = False

        mock_result = MagicMock()
        mock_result.allowed = True
        mock_result.reason = "allowed"
        mock_result.suggested_actions = []
        mock_result.metadata = {}

        adapter.validator = MagicMock()
        adapter.validator.validate.return_value = mock_result

        assert adapter.check_permissions("Admin", "delete", "User") is True


class TestSingleton:
    def setup_method(self):
        reset_ontoguard_adapter()

    def teardown_method(self):
        reset_ontoguard_adapter()

    def test_get_returns_same(self):
        a = get_ontoguard_adapter()
        b = get_ontoguard_adapter()
        assert a is b

    def test_reset(self):
        a = get_ontoguard_adapter()
        reset_ontoguard_adapter()
        b = get_ontoguard_adapter()
        assert a is not b


class TestExceptions:
    def test_base_error(self):
        e = OntoGuardError("fail", {"key": "val"})
        assert e.message == "fail"
        d = e.to_dict()
        assert d["error_type"] == "OntoGuardError"
        assert d["details"]["key"] == "val"

    def test_validation_denied(self):
        e = ValidationDeniedError("delete", "User", "not allowed", ["try read"])
        assert "delete" in str(e)
        assert e.suggestions == ["try read"]
        d = e.to_dict()
        assert d["details"]["action"] == "delete"

    def test_ontology_load_error(self):
        e = OntologyLoadError("/path.owl", "file not found")
        assert "/path.owl" in str(e)
        assert e.to_dict()["details"]["path"] == "/path.owl"

    def test_ontology_parse_error(self):
        e = OntologyParseError("/p.owl", "bad xml", line=42)
        assert "line 42" in str(e)

    def test_ontology_parse_error_no_line(self):
        e = OntologyParseError("/p.owl", "bad xml")
        assert "line" not in str(e)

    def test_configuration_error(self):
        e = ConfigurationError("bad", config_path="/c.yaml", field="ontologies")
        assert "field: ontologies" in str(e)

    def test_permission_denied(self):
        e = PermissionDeniedError("Customer", "delete", "User", required_role="Admin")
        assert "Customer" in str(e)
        assert "Admin" in str(e)

    def test_approval_required(self):
        e = ApprovalRequiredError("delete", "User", "Manager")
        assert "Manager" in str(e)
        d = e.to_dict()
        assert d["details"]["approver_role"] == "Manager"

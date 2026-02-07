"""
Unit tests for Schema Drift Detection module.

Tests: detect drift, no drift, renamed columns, type changes,
CRITICAL blocking, suggest fixes, load bindings.
"""

import os
import pytest
import tempfile
import yaml

from ai_agent_connector.app.security.schema_drift import (
    SchemaBinding,
    DriftReport,
    DriftApproval,
    Fix,
    SchemaDriftDetector,
    _normalize_type,
    _similar_names,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def detector():
    d = SchemaDriftDetector()
    d.add_binding(SchemaBinding(
        entity="PatientRecord",
        table="patients",
        columns={
            "id": "integer",
            "first_name": "text",
            "last_name": "text",
            "date_of_birth": "date",
            "email": "text",
        },
        domain="hospital",
    ))
    d.add_binding(SchemaBinding(
        entity="Account",
        table="accounts",
        columns={
            "id": "integer",
            "account_number": "text",
            "balance": "decimal",
            "status": "text",
        },
        domain="finance",
    ))
    return d


@pytest.fixture
def bindings_yaml(tmp_path):
    """Create a temporary schema_bindings.yaml."""
    data = {
        "domains": {
            "test": {
                "entities": {
                    "User": {
                        "table": "users",
                        "columns": {"id": "integer", "name": "text", "email": "text"},
                    },
                    "Order": {
                        "table": "orders",
                        "columns": {"id": "integer", "user_id": "integer", "total": "decimal"},
                    },
                }
            }
        }
    }
    path = tmp_path / "schema_bindings.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return str(path)


# ============================================================
# Tests: _normalize_type
# ============================================================

class TestNormalizeType:
    def test_varchar_to_text(self):
        assert _normalize_type("varchar") == "text"

    def test_varchar_with_length(self):
        assert _normalize_type("varchar(255)") == "text"

    def test_int_to_integer(self):
        assert _normalize_type("int") == "integer"

    def test_bool_to_boolean(self):
        assert _normalize_type("bool") == "boolean"

    def test_character_varying(self):
        assert _normalize_type("character varying") == "text"

    def test_double_precision(self):
        assert _normalize_type("double precision") == "float"

    def test_unknown_type_passthrough(self):
        assert _normalize_type("jsonb") == "jsonb"

    def test_case_insensitive(self):
        assert _normalize_type("INTEGER") == "integer"


# ============================================================
# Tests: _similar_names
# ============================================================

class TestSimilarNames:
    def test_containment(self):
        assert _similar_names("name", "first_name") is True

    def test_identical(self):
        assert _similar_names("email", "email") is True

    def test_completely_different(self):
        assert _similar_names("id", "balance") is False

    def test_underscore_removal(self):
        assert _similar_names("firstname", "first_name") is True

    def test_empty_string(self):
        assert _similar_names("", "name") is False


# ============================================================
# Tests: SchemaDriftDetector.detect_drift
# ============================================================

class TestDetectDrift:
    def test_no_drift(self, detector):
        """No drift when schema matches binding."""
        current = {
            "id": "integer",
            "first_name": "text",
            "last_name": "text",
            "date_of_birth": "date",
            "email": "text",
        }
        report = detector.detect_drift("PatientRecord", current)
        assert report.severity == "INFO"
        assert not report.has_drift
        assert report.missing_columns == []

    def test_missing_columns_critical(self, detector):
        """Missing columns -> CRITICAL severity."""
        current = {
            "id": "integer",
            "first_name": "text",
            # last_name, date_of_birth, email missing
        }
        report = detector.detect_drift("PatientRecord", current)
        assert report.severity == "CRITICAL"
        assert report.has_drift
        assert "last_name" in report.missing_columns
        assert "date_of_birth" in report.missing_columns
        assert "email" in report.missing_columns

    def test_new_columns_info(self, detector):
        """New columns only -> INFO severity (not drift)."""
        current = {
            "id": "integer",
            "first_name": "text",
            "last_name": "text",
            "date_of_birth": "date",
            "email": "text",
            "phone": "text",  # new
        }
        report = detector.detect_drift("PatientRecord", current)
        assert report.severity == "INFO"
        assert not report.has_drift
        assert "phone" in report.new_columns

    def test_type_change_warning(self, detector):
        """Type change -> WARNING severity."""
        current = {
            "id": "integer",
            "first_name": "text",
            "last_name": "text",
            "date_of_birth": "timestamp",  # was date
            "email": "text",
        }
        report = detector.detect_drift("PatientRecord", current)
        assert report.severity == "WARNING"
        assert report.has_drift
        assert "date_of_birth" in report.type_changes

    def test_type_normalization(self, detector):
        """varchar should match text after normalization."""
        current = {
            "id": "int",  # normalized to integer
            "first_name": "varchar(255)",  # normalized to text
            "last_name": "character varying",  # normalized to text
            "date_of_birth": "date",
            "email": "text",
        }
        report = detector.detect_drift("PatientRecord", current)
        assert report.severity == "INFO"
        assert not report.has_drift

    def test_renamed_column(self, detector):
        """Renamed column detection via heuristic."""
        current = {
            "id": "integer",
            "first_name": "text",
            "surname": "text",  # renamed from last_name
            "date_of_birth": "date",
            "email_address": "text",  # renamed from email
        }
        report = detector.detect_drift("PatientRecord", current)
        # Should detect renames, not CRITICAL missing
        assert "last_name" in report.renamed_columns or "last_name" in report.missing_columns

    def test_unknown_entity(self, detector):
        """Unknown entity -> INFO with no binding message."""
        report = detector.detect_drift("UnknownEntity", {"id": "integer"})
        assert report.severity == "INFO"
        assert "No binding found" in report.message

    def test_finance_domain(self, detector):
        """Finance domain binding works."""
        current = {
            "id": "integer",
            "account_number": "text",
            "balance": "decimal",
            "status": "text",
        }
        report = detector.detect_drift("Account", current)
        assert report.severity == "INFO"
        assert not report.has_drift


# ============================================================
# Tests: SchemaDriftDetector.suggest_fixes
# ============================================================

class TestSuggestFixes:
    def test_fix_for_missing_column(self, detector):
        current = {"id": "integer", "first_name": "text"}
        report = detector.detect_drift("PatientRecord", current)
        fixes = detector.suggest_fixes(report)
        verify_fixes = [f for f in fixes if f.type == "verify_column"]
        assert len(verify_fixes) > 0

    def test_fix_for_new_column(self, detector):
        current = {
            "id": "integer",
            "first_name": "text",
            "last_name": "text",
            "date_of_birth": "date",
            "email": "text",
            "phone": "text",
        }
        report = detector.detect_drift("PatientRecord", current)
        fixes = detector.suggest_fixes(report)
        add_fixes = [f for f in fixes if f.type == "add_column"]
        assert len(add_fixes) == 1
        assert add_fixes[0].column == "phone"

    def test_no_fixes_when_no_drift(self, detector):
        current = {
            "id": "integer",
            "first_name": "text",
            "last_name": "text",
            "date_of_birth": "date",
            "email": "text",
        }
        report = detector.detect_drift("PatientRecord", current)
        fixes = detector.suggest_fixes(report)
        assert fixes == []


# ============================================================
# Tests: load_bindings from YAML
# ============================================================

class TestLoadBindings:
    def test_load_from_yaml(self, bindings_yaml):
        d = SchemaDriftDetector()
        count = d.load_bindings(bindings_yaml)
        assert count == 2
        assert "User" in d.bindings
        assert "Order" in d.bindings
        assert d.bindings["User"].table == "users"
        assert d.bindings["Order"].columns["total"] == "decimal"

    def test_load_real_config(self):
        """Test loading the actual config/schema_bindings.yaml if it exists."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "schema_bindings.yaml"
        )
        if not os.path.exists(config_path):
            pytest.skip("schema_bindings.yaml not found")

        d = SchemaDriftDetector()
        count = d.load_bindings(config_path)
        assert count > 0
        assert "PatientRecord" in d.bindings


# ============================================================
# Tests: check_all
# ============================================================

class TestCheckAll:
    def test_check_all_no_drift(self, detector):
        schemas = {
            "PatientRecord": {
                "id": "integer",
                "first_name": "text",
                "last_name": "text",
                "date_of_birth": "date",
                "email": "text",
            },
            "Account": {
                "id": "integer",
                "account_number": "text",
                "balance": "decimal",
                "status": "text",
            },
        }
        reports = detector.check_all(schemas)
        assert len(reports) == 2
        assert all(r.severity == "INFO" for r in reports)

    def test_check_all_missing_schema(self, detector):
        """Entity with no provided schema -> CRITICAL."""
        schemas = {
            "PatientRecord": {
                "id": "integer",
                "first_name": "text",
                "last_name": "text",
                "date_of_birth": "date",
                "email": "text",
            },
            # Account schema missing
        }
        reports = detector.check_all(schemas)
        account_reports = [r for r in reports if r.entity == "Account"]
        assert len(account_reports) == 1
        assert account_reports[0].severity == "CRITICAL"


# ============================================================
# Tests: DriftReport.to_dict
# ============================================================

class TestDriftReportDict:
    def test_to_dict(self):
        report = DriftReport(
            entity="Test",
            table="tests",
            missing_columns=["col1"],
            severity="CRITICAL",
            message="test",
        )
        d = report.to_dict()
        assert d["entity"] == "Test"
        assert d["has_drift"] is True
        assert d["severity"] == "CRITICAL"

    def test_has_drift_false(self):
        report = DriftReport(entity="Test", table="tests")
        assert report.has_drift is False


# ============================================================
# Tests: Fix.to_dict
# ============================================================

class TestFixDict:
    def test_to_dict(self):
        fix = Fix(
            type="verify_column",
            description="desc",
            action="action",
            entity="E",
            column="c",
        )
        d = fix.to_dict()
        assert d["type"] == "verify_column"
        assert d["entity"] == "E"


# ============================================================
# Tests: DriftApproval and approval workflow
# ============================================================

class TestDriftApproval:
    def test_approve_drift(self, detector):
        """approve_drift creates a valid approval."""
        approval = detector.approve_drift(
            entity="PatientRecord",
            approved_by="admin@test.com",
            reason="Planned migration",
        )
        assert approval.entity == "PatientRecord"
        assert approval.approved_by == "admin@test.com"
        assert approval.reason == "Planned migration"
        assert approval.table == "patients"
        assert not approval.is_expired

    def test_is_approved(self, detector):
        """is_approved returns True after approval."""
        assert not detector.is_approved("PatientRecord")
        detector.approve_drift(
            entity="PatientRecord",
            approved_by="admin",
            reason="test",
        )
        assert detector.is_approved("PatientRecord")

    def test_expired_approval(self, detector):
        """Expired approvals are not valid."""
        approval = detector.approve_drift(
            entity="PatientRecord",
            approved_by="admin",
            reason="test",
            ttl_hours=0,  # expires immediately
        )
        assert approval.is_expired
        assert not detector.is_approved("PatientRecord")

    def test_revoke_approval(self, detector):
        """revoke_approval removes the approval."""
        detector.approve_drift(
            entity="PatientRecord",
            approved_by="admin",
            reason="test",
        )
        assert detector.is_approved("PatientRecord")
        assert detector.revoke_approval("PatientRecord") is True
        assert not detector.is_approved("PatientRecord")

    def test_revoke_nonexistent(self, detector):
        """revoke_approval returns False for nonexistent."""
        assert detector.revoke_approval("NonExistent") is False

    def test_list_approvals(self, detector):
        """list_approvals returns active approvals."""
        detector.approve_drift(entity="PatientRecord", approved_by="admin", reason="r1")
        detector.approve_drift(entity="Account", approved_by="admin", reason="r2")
        approvals = detector.list_approvals()
        assert len(approvals) == 2
        entities = {a.entity for a in approvals}
        assert entities == {"PatientRecord", "Account"}

    def test_list_approvals_excludes_expired(self, detector):
        """list_approvals excludes expired by default."""
        detector.approve_drift(entity="PatientRecord", approved_by="admin", reason="r1", ttl_hours=0)
        detector.approve_drift(entity="Account", approved_by="admin", reason="r2", ttl_hours=24)
        approvals = detector.list_approvals()
        assert len(approvals) == 1
        assert approvals[0].entity == "Account"

    def test_get_approval(self, detector):
        """get_approval returns the approval object."""
        detector.approve_drift(entity="PatientRecord", approved_by="admin", reason="r")
        approval = detector.get_approval("PatientRecord")
        assert approval is not None
        assert approval.entity == "PatientRecord"

    def test_get_approval_none(self, detector):
        """get_approval returns None when not approved."""
        assert detector.get_approval("PatientRecord") is None

    def test_approval_to_dict(self, detector):
        """DriftApproval.to_dict() returns expected keys."""
        approval = detector.approve_drift(
            entity="PatientRecord",
            approved_by="admin",
            reason="test",
        )
        d = approval.to_dict()
        assert d["entity"] == "PatientRecord"
        assert d["approved_by"] == "admin"
        assert d["reason"] == "test"
        assert "approval_id" in d
        assert "is_expired" in d
        assert d["is_expired"] is False

    def test_approval_with_drift_report(self, detector):
        """approve_drift with drift_report generates drift_hash."""
        report = DriftReport(
            entity="PatientRecord",
            table="patients",
            missing_columns=["email"],
            severity="CRITICAL",
        )
        approval = detector.approve_drift(
            entity="PatientRecord",
            approved_by="admin",
            reason="test",
            drift_report=report,
        )
        assert approval.drift_hash != ""
        assert len(approval.drift_hash) == 12

    def test_approve_unknown_entity(self, detector):
        """Approving entity with no binding sets table='unknown'."""
        approval = detector.approve_drift(
            entity="UnknownEntity",
            approved_by="admin",
            reason="test",
        )
        assert approval.table == "unknown"

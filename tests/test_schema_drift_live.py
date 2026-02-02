"""Tests for live schema drift detection (fetch_live_schema, check_live)."""

import pytest
from unittest.mock import MagicMock

from ai_agent_connector.app.security.schema_drift import (
    SchemaDriftDetector,
    SchemaBinding,
)


@pytest.fixture
def detector():
    d = SchemaDriftDetector()
    d.add_binding(SchemaBinding(
        entity="PatientRecord",
        table="patients",
        columns={"id": "integer", "name": "text", "dob": "date"},
        domain="hospital",
    ))
    d.add_binding(SchemaBinding(
        entity="Staff",
        table="staff",
        columns={"id": "integer", "role": "text"},
        domain="hospital",
    ))
    return d


@pytest.fixture
def mock_connector():
    return MagicMock()


class TestFetchLiveSchema:
    def test_returns_column_dict(self, detector, mock_connector):
        mock_connector.execute_query.return_value = [
            {"column_name": "id", "data_type": "integer"},
            {"column_name": "name", "data_type": "character varying"},
        ]
        result = detector.fetch_live_schema(mock_connector, "patients")
        assert result == {"id": "integer", "name": "character varying"}
        mock_connector.execute_query.assert_called_once()

    def test_empty_result_for_missing_table(self, detector, mock_connector):
        mock_connector.execute_query.return_value = []
        result = detector.fetch_live_schema(mock_connector, "nonexistent")
        assert result == {}

    def test_none_result_handled(self, detector, mock_connector):
        mock_connector.execute_query.return_value = None
        result = detector.fetch_live_schema(mock_connector, "patients")
        assert result == {}


class TestCheckLive:
    def test_no_drift(self, detector, mock_connector):
        mock_connector.execute_query.return_value = [
            {"column_name": "id", "data_type": "integer"},
            {"column_name": "name", "data_type": "text"},
            {"column_name": "dob", "data_type": "date"},
        ]
        reports = detector.check_live(mock_connector, ["PatientRecord"])
        assert len(reports) == 1
        assert not reports[0].has_drift
        assert reports[0].severity == "INFO"

    def test_missing_column_detected(self, detector, mock_connector):
        mock_connector.execute_query.return_value = [
            {"column_name": "id", "data_type": "integer"},
            # "name" and "dob" missing
        ]
        reports = detector.check_live(mock_connector, ["PatientRecord"])
        assert len(reports) == 1
        assert reports[0].has_drift
        assert reports[0].severity == "CRITICAL"
        assert set(reports[0].missing_columns) == {"name", "dob"}

    def test_type_change_detected(self, detector, mock_connector):
        mock_connector.execute_query.return_value = [
            {"column_name": "id", "data_type": "bigint"},
            {"column_name": "name", "data_type": "text"},
            {"column_name": "dob", "data_type": "date"},
        ]
        reports = detector.check_live(mock_connector, ["PatientRecord"])
        assert len(reports) == 1
        r = reports[0]
        assert r.has_drift
        assert "id" in r.type_changes

    def test_table_not_found_empty_schema(self, detector, mock_connector):
        mock_connector.execute_query.return_value = []
        reports = detector.check_live(mock_connector, ["PatientRecord"])
        assert len(reports) == 1
        assert reports[0].severity == "CRITICAL"
        assert len(reports[0].missing_columns) == 3  # all columns missing

    def test_multiple_entities(self, detector, mock_connector):
        def side_effect(query, **kwargs):
            table = kwargs.get("params", (None,))[0]
            if table == "patients":
                return [
                    {"column_name": "id", "data_type": "integer"},
                    {"column_name": "name", "data_type": "text"},
                    {"column_name": "dob", "data_type": "date"},
                ]
            elif table == "staff":
                return [
                    {"column_name": "id", "data_type": "integer"},
                    {"column_name": "role", "data_type": "text"},
                ]
            return []

        mock_connector.execute_query.side_effect = side_effect
        reports = detector.check_live(mock_connector)
        assert len(reports) == 2
        assert all(not r.has_drift for r in reports)

    def test_unknown_entity_skipped(self, detector, mock_connector):
        reports = detector.check_live(mock_connector, ["NonExistent"])
        assert len(reports) == 0
        mock_connector.execute_query.assert_not_called()

"""Unit tests for helper utilities."""

import re

import pytest
from ai_agent_connector.app.utils.helpers import (
    format_response,
    validate_json,
    get_timestamp,
    safe_json_loads,
)


class TestFormatResponse:
    def test_dict_input(self):
        data, code = format_response({"key": "val"})
        assert data == {"key": "val"}
        assert code == 200

    def test_non_dict_input(self):
        data, code = format_response("hello")
        assert data == {"data": "hello"}
        assert code == 200

    def test_custom_status(self):
        _, code = format_response({"ok": True}, 201)
        assert code == 201

    def test_list_input(self):
        data, _ = format_response([1, 2, 3])
        assert data == {"data": [1, 2, 3]}


class TestValidateJson:
    def test_valid(self):
        assert validate_json({"a": 1, "b": 2}, ["a", "b"]) is None

    def test_missing_field(self):
        result = validate_json({"a": 1}, ["a", "b"])
        assert result is not None
        assert "b" in result

    def test_empty_required(self):
        assert validate_json({}, []) is None


class TestGetTimestamp:
    def test_format(self):
        ts = get_timestamp()
        assert ts.endswith("Z")
        # Should match ISO format like 2026-01-30T12:00:00.123456Z
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts)


class TestSafeJsonLoads:
    def test_valid(self):
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_invalid(self):
        assert safe_json_loads("not json") is None

    def test_empty(self):
        assert safe_json_loads("") is None

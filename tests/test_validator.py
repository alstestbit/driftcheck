"""Tests for driftcheck.validator."""

import pytest

from driftcheck.validator import (
    ValidationResult,
    validate_definition,
    validate_all,
)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_validation_result_valid_when_no_errors():
    result = ValidationResult(resource="svc")
    assert result.valid is True


def test_validation_result_invalid_when_errors_present():
    result = ValidationResult(resource="svc", errors=["missing key: 'name'"])
    assert result.valid is False


def test_validation_result_str_ok():
    result = ValidationResult(resource="svc")
    assert str(result) == "svc: OK"


def test_validation_result_str_invalid():
    result = ValidationResult(resource="svc", errors=["missing key: 'name'"])
    assert "INVALID" in str(result)
    assert "missing key: 'name'" in str(result)


# ---------------------------------------------------------------------------
# validate_definition
# ---------------------------------------------------------------------------

def test_validate_definition_valid_dict():
    result = validate_definition({"name": "app", "replicas": 3}, resource="deploy.yaml")
    assert result.valid is True


def test_validate_definition_non_dict_is_invalid():
    result = validate_definition(["not", "a", "dict"], resource="bad.yaml")
    assert result.valid is False
    assert any("mapping" in e for e in result.errors)


def test_validate_definition_empty_dict_is_invalid():
    result = validate_definition({}, resource="empty.yaml")
    assert result.valid is False
    assert any("empty" in e for e in result.errors)


def test_validate_definition_required_keys_present():
    result = validate_definition(
        {"name": "app", "version": "1.0"},
        resource="svc.yaml",
        required_keys=["name", "version"],
    )
    assert result.valid is True


def test_validate_definition_missing_required_key():
    result = validate_definition(
        {"name": "app"},
        resource="svc.yaml",
        required_keys=["name", "version"],
    )
    assert result.valid is False
    assert any("version" in e for e in result.errors)


def test_validate_definition_multiple_missing_keys():
    result = validate_definition(
        {},
        resource="svc.yaml",
        required_keys=["name", "version"],
    )
    # empty dict error + two missing key errors
    assert len(result.errors) >= 2


# ---------------------------------------------------------------------------
# validate_all
# ---------------------------------------------------------------------------

def test_validate_all_returns_one_result_per_definition():
    definitions = {
        "svc-a": {"name": "a"},
        "svc-b": {"name": "b"},
    }
    results = validate_all(definitions)
    assert len(results) == 2


def test_validate_all_reports_invalid_entries():
    definitions = {
        "good": {"name": "ok"},
        "bad": "not-a-dict",
    }
    results = validate_all(definitions)
    valid_map = {r.resource: r.valid for r in results}
    assert valid_map["good"] is True
    assert valid_map["bad"] is False


def test_validate_all_empty_input_returns_empty_list():
    assert validate_all({}) == []

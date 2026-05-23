"""Tests for driftcheck.comparator module."""

import pytest
from driftcheck.comparator import DriftResult, compare


def test_compare_identical_dicts_no_drift():
    definition = {"instance_type": "t3.micro", "region": "us-east-1"}
    deployed = {"instance_type": "t3.micro", "region": "us-east-1"}
    result = compare(definition, deployed, resource_id="server-1")
    assert not result.has_drift
    assert result.missing_keys == []
    assert result.extra_keys == []
    assert result.changed_values == {}


def test_compare_detects_changed_value():
    definition = {"instance_type": "t3.micro", "region": "us-east-1"}
    deployed = {"instance_type": "t3.large", "region": "us-east-1"}
    result = compare(definition, deployed, resource_id="server-1")
    assert result.has_drift
    assert "instance_type" in result.changed_values
    assert result.changed_values["instance_type"]["expected"] == "t3.micro"
    assert result.changed_values["instance_type"]["actual"] == "t3.large"


def test_compare_detects_missing_key():
    definition = {"instance_type": "t3.micro", "region": "us-east-1"}
    deployed = {"instance_type": "t3.micro"}
    result = compare(definition, deployed)
    assert result.has_drift
    assert "region" in result.missing_keys


def test_compare_detects_extra_key():
    definition = {"instance_type": "t3.micro"}
    deployed = {"instance_type": "t3.micro", "region": "us-east-1"}
    result = compare(definition, deployed)
    assert result.has_drift
    assert "region" in result.extra_keys


def test_compare_nested_dict_drift():
    definition = {"tags": {"env": "prod", "team": "platform"}}
    deployed = {"tags": {"env": "staging", "team": "platform"}}
    result = compare(definition, deployed, resource_id="bucket-1")
    assert result.has_drift
    assert "tags" in result.changed_values


def test_compare_nested_dict_no_drift():
    definition = {"tags": {"env": "prod", "team": "platform"}}
    deployed = {"tags": {"env": "prod", "team": "platform"}}
    result = compare(definition, deployed)
    assert not result.has_drift


def test_drift_result_summary_no_drift():
    result = DriftResult(resource_id="db-1", has_drift=False)
    assert "[OK]" in result.summary()
    assert "db-1" in result.summary()


def test_drift_result_summary_with_drift():
    result = DriftResult(
        resource_id="db-1",
        has_drift=True,
        missing_keys=["backup_enabled"],
        changed_values={"size": {"expected": "small", "actual": "large"}},
    )
    summary = result.summary()
    assert "[DRIFT]" in summary
    assert "db-1" in summary
    assert "backup_enabled" in summary


def test_compare_empty_dicts():
    result = compare({}, {})
    assert not result.has_drift


def test_compare_uses_resource_id():
    result = compare({"key": "a"}, {"key": "b"}, resource_id="my-resource")
    assert result.resource_id == "my-resource"

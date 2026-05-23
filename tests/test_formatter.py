"""Tests for driftcheck.formatter."""

import json

import pytest
from driftcheck.differ import Change
from driftcheck.formatter import changes_to_dict, render_json, render_text


def _changes() -> list[Change]:
    return [
        Change(path="replicas", expected=3, actual=1, kind="changed"),
        Change(path="image", expected="nginx:1.25", actual=None, kind="missing"),
    ]


def test_changes_to_dict_structure():
    result = changes_to_dict(_changes())
    assert len(result) == 2
    assert result[0] == {
        "path": "replicas",
        "kind": "changed",
        "expected": 3,
        "actual": 1,
    }


def test_changes_to_dict_empty():
    assert changes_to_dict([]) == []


def test_render_text_no_drift():
    output = render_text([], title="my-service")
    assert "No drift detected" in output
    assert "my-service" in output


def test_render_text_with_drift():
    output = render_text(_changes())
    assert "changed" in output
    assert "missing" in output
    assert "replicas" in output


def test_render_text_summary_line():
    output = render_text(_changes())
    assert "Summary:" in output
    assert "1 changed" in output
    assert "1 missing" in output


def test_render_text_no_title():
    output = render_text([])
    assert "==" not in output


def test_render_json_no_drift():
    output = render_json([], resource="svc-a")
    data = json.loads(output)
    assert data["drift_detected"] is False
    assert data["resource"] == "svc-a"
    assert data["changes"] == []


def test_render_json_with_drift():
    output = render_json(_changes(), resource="deploy-x")
    data = json.loads(output)
    assert data["drift_detected"] is True
    assert len(data["changes"]) == 2
    assert data["summary"]["changed"] == 1
    assert data["summary"]["missing"] == 1


def test_render_json_is_valid_json():
    output = render_json(_changes())
    parsed = json.loads(output)
    assert isinstance(parsed, dict)

"""Tests for driftcheck.drift_summary."""

import pytest
from driftcheck.comparator import DriftResult
from driftcheck.differ import Change
from driftcheck.drift_summary import DriftSummary, build_summary, format_summary


def _clean(resource: str) -> DriftResult:
    return DriftResult(resource=resource, drifted=False, changes=[], error=None)


def _drifted(resource: str) -> DriftResult:
    change = Change(key="port", expected=80, actual=8080, change_type="changed")
    return DriftResult(resource=resource, drifted=True, changes=[change], error=None)


def _errored(resource: str) -> DriftResult:
    return DriftResult(resource=resource, drifted=False, changes=[], error="timeout")


def test_build_summary_all_clean():
    results = [_clean("svc-a"), _clean("svc-b")]
    s = build_summary(results)
    assert s.total == 2
    assert s.clean == 2
    assert s.drifted == 0
    assert s.errored == 0
    assert s.drifted_resources == []


def test_build_summary_mixed():
    results = [_clean("svc-a"), _drifted("svc-b"), _errored("svc-c")]
    s = build_summary(results)
    assert s.total == 3
    assert s.clean == 1
    assert s.drifted == 1
    assert s.errored == 1
    assert s.drifted_resources == ["svc-b"]


def test_drift_rate_no_eligible():
    s = DriftSummary(total=2, errored=2)
    assert s.drift_rate == 0.0


def test_drift_rate_calculation():
    results = [_drifted("a"), _drifted("b"), _clean("c"), _clean("d")]
    s = build_summary(results)
    assert s.drift_rate == pytest.approx(0.5)


def test_to_dict_keys():
    s = build_summary([_clean("x"), _drifted("y")])
    d = s.to_dict()
    assert set(d.keys()) == {
        "total", "drifted", "clean", "errored", "drift_rate", "drifted_resources"
    }


def test_to_dict_values():
    s = build_summary([_drifted("svc-a")])
    d = s.to_dict()
    assert d["total"] == 1
    assert d["drifted"] == 1
    assert d["drifted_resources"] == ["svc-a"]
    assert d["drift_rate"] == 1.0


def test_format_summary_contains_counts():
    s = build_summary([_clean("a"), _drifted("b")])
    text = format_summary(s)
    assert "Total resources" in text
    assert "Clean" in text
    assert "Drifted" in text
    assert "Drift rate" in text


def test_format_summary_lists_drifted_resources():
    s = build_summary([_drifted("svc-b")])
    text = format_summary(s)
    assert "svc-b" in text


def test_format_summary_no_drifted_resources_omits_section():
    s = build_summary([_clean("svc-a")])
    text = format_summary(s)
    assert "Drifted resources" not in text


def test_build_summary_empty():
    s = build_summary([])
    assert s.total == 0
    assert s.drift_rate == 0.0

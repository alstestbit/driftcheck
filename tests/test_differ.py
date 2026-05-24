"""Tests for driftcheck.differ."""

import pytest
from driftcheck.differ import Change, diff, summarise_changes


def test_diff_identical_dicts_returns_empty():
    result = diff({"a": 1, "b": 2}, {"a": 1, "b": 2})
    assert result == []


def test_diff_detects_changed_value():
    changes = diff({"a": 1}, {"a": 99})
    assert len(changes) == 1
    assert changes[0].kind == "changed"
    assert changes[0].path == "a"
    assert changes[0].expected == 1
    assert changes[0].actual == 99


def test_diff_detects_missing_key():
    changes = diff({"a": 1, "b": 2}, {"a": 1})
    assert len(changes) == 1
    assert changes[0].kind == "missing"
    assert changes[0].path == "b"


def test_diff_detects_extra_key():
    changes = diff({"a": 1}, {"a": 1, "z": 99})
    assert len(changes) == 1
    assert changes[0].kind == "extra"
    assert changes[0].path == "z"
    assert changes[0].actual == 99


def test_diff_ignore_extra_suppresses_extra_keys():
    changes = diff({"a": 1}, {"a": 1, "z": 99}, ignore_extra=True)
    assert changes == []


def test_diff_nested_dict_changed():
    expected = {"meta": {"version": "1.0", "env": "prod"}}
    actual = {"meta": {"version": "2.0", "env": "prod"}}
    changes = diff(expected, actual)
    assert len(changes) == 1
    assert changes[0].path == "meta.version"
    assert changes[0].kind == "changed"


def test_diff_nested_missing_key():
    expected = {"meta": {"version": "1.0", "region": "us-east"}}
    actual = {"meta": {"version": "1.0"}}
    changes = diff(expected, actual)
    assert len(changes) == 1
    assert changes[0].path == "meta.region"
    assert changes[0].kind == "missing"


def test_diff_deep_nesting():
    expected = {"a": {"b": {"c": "x"}}}
    actual = {"a": {"b": {"c": "y"}}}
    changes = diff(expected, actual)
    assert changes[0].path == "a.b.c"
    assert changes[0].kind == "changed"


def test_diff_returns_list_of_change_objects():
    """Ensure every item returned by diff is a Change instance."""
    expected = {"a": 1, "b": {"c": 2}}
    actual = {"a": 9, "b": {"c": 2}, "d": 5}
    changes = diff(expected, actual)
    assert all(isinstance(c, Change) for c in changes)


def test_change_str_changed():
    c = Change(path="foo.bar", expected="old", actual="new", kind="changed")
    assert "changed" in str(c)
    assert "foo.bar" in str(c)


def test_change_str_missing():
    c = Change(path="foo.bar", expected="old", actual=None, kind="missing")
    assert "missing" in str(c)


def test_change_str_extra():
    c = Change(path="foo.bar", expected=None, actual="surprise", kind="extra")
    assert "extra" in str(c)


def test_summarise_changes_counts_correctly():
    changes = [
        Change("a", 1, 2, "changed"),
        Change("b", 1, None, "missing"),
        Change("c", None, 3, "extra"),
        Change("d", 1, 2, "changed"),
    ]
    summary = summarise_changes(changes)
    assert summary["changed"] == 2
    assert summary["missing"] == 1
    assert summary["extra"] == 1


def test_summarise_changes_empty():
    summary = summarise_changes([])
    assert summary == {"changed": 0, "missing": 0, "extra": 0}

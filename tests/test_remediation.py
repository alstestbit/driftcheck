"""Tests for driftcheck.remediation."""
import pytest

from driftcheck.differ import Change
from driftcheck.remediation import (
    RemediationHint,
    _suggestion_for,
    hints_from_changes,
    format_hints,
)


def _change(key, change_type, expected=None, actual=None):
    return Change(key=key, change_type=change_type, expected=expected, actual=actual)


def test_suggestion_for_changed():
    c = _change("replicas", "changed", expected=3, actual=1)
    s = _suggestion_for(c)
    assert "replicas" in s
    assert "3" in s
    assert "1" in s


def test_suggestion_for_missing():
    c = _change("env", "missing", expected="prod")
    s = _suggestion_for(c)
    assert "Add" in s
    assert "env" in s


def test_suggestion_for_extra():
    c = _change("debug", "extra", actual=True)
    s = _suggestion_for(c)
    assert "Remove" in s
    assert "debug" in s


def test_suggestion_for_unknown_type():
    c = _change("x", "unknown")
    s = _suggestion_for(c)
    assert "x" in s


def test_hints_from_changes_empty():
    assert hints_from_changes([]) == []


def test_hints_from_changes_produces_hints():
    changes = [
        _change("replicas", "changed", expected=3, actual=1),
        _change("image", "missing", expected="nginx"),
    ]
    hints = hints_from_changes(changes, severity="error")
    assert len(hints) == 2
    assert all(h.severity == "error" for h in hints)
    assert hints[0].key == "replicas"
    assert hints[1].key == "image"


def test_hint_to_dict_has_expected_keys():
    h = RemediationHint(
        key="k", change_type="changed", expected=1, actual=2, suggestion="fix it"
    )
    d = h.to_dict()
    for key in ("key", "change_type", "expected", "actual", "suggestion", "severity"):
        assert key in d


def test_format_hints_empty():
    assert format_hints([]) == "No remediation required."


def test_format_hints_shows_suggestions():
    hints = hints_from_changes([_change("replicas", "changed", expected=3, actual=1)])
    out = format_hints(hints)
    assert "Remediation hints:" in out
    assert "replicas" in out

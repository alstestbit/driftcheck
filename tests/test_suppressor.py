"""Tests for driftcheck.suppressor."""
import pytest

from driftcheck.differ import Change
from driftcheck.suppressor import (
    SuppressionRule,
    Suppressor,
    suppressor_from_dicts,
)


def _change(key: str, old="a", new="b") -> Change:
    return Change(key=key, old_value=old, new_value=new)


# ---------------------------------------------------------------------------
# SuppressionRule
# ---------------------------------------------------------------------------

def test_suppression_rule_requires_at_least_one_field():
    with pytest.raises(ValueError, match="at least one"):
        SuppressionRule()


def test_suppression_rule_matches_by_key_only():
    rule = SuppressionRule(key="metadata.*")
    assert rule.matches("any-resource", _change("metadata.version"))
    assert not rule.matches("any-resource", _change("spec.replicas"))


def test_suppression_rule_matches_by_resource_only():
    rule = SuppressionRule(resource="prod-*")
    assert rule.matches("prod-api", _change("anything"))
    assert not rule.matches("staging-api", _change("anything"))


def test_suppression_rule_matches_both_required():
    rule = SuppressionRule(resource="prod-*", key="metadata.*")
    assert rule.matches("prod-api", _change("metadata.ts"))
    assert not rule.matches("prod-api", _change("spec.image"))
    assert not rule.matches("staging-api", _change("metadata.ts"))


def test_suppression_rule_exact_key_match():
    rule = SuppressionRule(key="spec.replicas")
    assert rule.matches("svc", _change("spec.replicas"))
    assert not rule.matches("svc", _change("spec.replicas.extra"))


# ---------------------------------------------------------------------------
# Suppressor
# ---------------------------------------------------------------------------

def test_suppressor_is_suppressed_true():
    s = Suppressor(rules=[SuppressionRule(key="metadata.*")])
    assert s.is_suppressed("res", _change("metadata.ts"))


def test_suppressor_is_suppressed_false():
    s = Suppressor(rules=[SuppressionRule(key="metadata.*")])
    assert not s.is_suppressed("res", _change("spec.image"))


def test_suppressor_filter_changes_removes_suppressed():
    s = Suppressor(rules=[SuppressionRule(key="metadata.*")])
    changes = [_change("metadata.ts"), _change("spec.image"), _change("metadata.rev")]
    result = s.filter_changes("res", changes)
    assert len(result) == 1
    assert result[0].key == "spec.image"


def test_suppressor_suppressed_changes_returns_only_suppressed():
    s = Suppressor(rules=[SuppressionRule(key="metadata.*")])
    changes = [_change("metadata.ts"), _change("spec.image")]
    suppressed = s.suppressed_changes("res", changes)
    assert len(suppressed) == 1
    assert suppressed[0].key == "metadata.ts"


def test_suppressor_empty_rules_suppresses_nothing():
    s = Suppressor()
    changes = [_change("a"), _change("b")]
    assert s.filter_changes("res", changes) == changes


# ---------------------------------------------------------------------------
# suppressor_from_dicts
# ---------------------------------------------------------------------------

def test_suppressor_from_dicts_builds_rules():
    raw = [
        {"key": "metadata.*", "reason": "auto-managed"},
        {"resource": "prod-*", "key": "spec.ts"},
    ]
    s = suppressor_from_dicts(raw)
    assert len(s.rules) == 2
    assert s.rules[0].reason == "auto-managed"
    assert s.rules[1].resource == "prod-*"


def test_suppressor_from_dicts_empty():
    s = suppressor_from_dicts([])
    assert s.rules == []

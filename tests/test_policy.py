"""Tests for driftcheck.policy."""

import pytest

from driftcheck.differ import Change
from driftcheck.policy import (
    Policy,
    PolicyRule,
    SEVERITY_ERROR,
    SEVERITY_IGNORE,
    SEVERITY_WARN,
    policy_from_dict,
)


def _change(key: str = "replicas", kind: str = "changed") -> Change:
    return Change(key=key, kind=kind, expected=1, actual=2)


# ---------------------------------------------------------------------------
# PolicyRule
# ---------------------------------------------------------------------------

def test_policy_rule_invalid_severity_raises():
    with pytest.raises(ValueError, match="Invalid severity"):
        PolicyRule(severity="critical")


def test_policy_rule_matches_key_pattern():
    rule = PolicyRule(severity=SEVERITY_IGNORE, key_pattern="metadata.*")
    assert rule.matches(_change("metadata.labels"))
    assert not rule.matches(_change("spec.replicas"))


def test_policy_rule_matches_resource_pattern():
    rule = PolicyRule(severity=SEVERITY_ERROR, resource_pattern="prod-*")
    assert rule.matches(_change(), resource="prod-api")
    assert not rule.matches(_change(), resource="staging-api")


def test_policy_rule_matches_both_patterns():
    rule = PolicyRule(
        severity=SEVERITY_WARN,
        key_pattern="spec.*",
        resource_pattern="staging-*",
    )
    assert rule.matches(_change("spec.replicas"), resource="staging-api")
    assert not rule.matches(_change("spec.replicas"), resource="prod-api")
    assert not rule.matches(_change("metadata.name"), resource="staging-api")


def test_policy_rule_no_patterns_matches_everything():
    rule = PolicyRule(severity=SEVERITY_WARN)
    assert rule.matches(_change("anything"), resource="any-resource")


# ---------------------------------------------------------------------------
# Policy.evaluate
# ---------------------------------------------------------------------------

def test_policy_default_severity_when_no_rules():
    policy = Policy(default_severity=SEVERITY_WARN)
    assert policy.evaluate(_change()) == SEVERITY_WARN


def test_policy_first_matching_rule_wins():
    policy = Policy(
        rules=[
            PolicyRule(severity=SEVERITY_IGNORE, key_pattern="metadata.*"),
            PolicyRule(severity=SEVERITY_WARN),
        ],
        default_severity=SEVERITY_ERROR,
    )
    assert policy.evaluate(_change("metadata.labels")) == SEVERITY_IGNORE
    assert policy.evaluate(_change("spec.replicas")) == SEVERITY_WARN


def test_policy_falls_through_to_default():
    policy = Policy(
        rules=[PolicyRule(severity=SEVERITY_IGNORE, key_pattern="metadata.*")],
        default_severity=SEVERITY_ERROR,
    )
    assert policy.evaluate(_change("spec.replicas")) == SEVERITY_ERROR


# ---------------------------------------------------------------------------
# policy_from_dict
# ---------------------------------------------------------------------------

def test_policy_from_dict_empty():
    policy = policy_from_dict({})
    assert policy.default_severity == SEVERITY_ERROR
    assert policy.rules == []


def test_policy_from_dict_full():
    data = {
        "default_severity": "warn",
        "rules": [
            {"severity": "ignore", "key_pattern": "metadata.*"},
            {"severity": "error", "resource_pattern": "prod-*"},
        ],
    }
    policy = policy_from_dict(data)
    assert policy.default_severity == SEVERITY_WARN
    assert len(policy.rules) == 2
    assert policy.rules[0].key_pattern == "metadata.*"
    assert policy.rules[1].resource_pattern == "prod-*"


def test_policy_from_dict_invalid_severity_raises():
    with pytest.raises(ValueError, match="Invalid severity"):
        policy_from_dict({"rules": [{"severity": "critical"}]})

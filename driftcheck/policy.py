"""Policy engine for driftcheck.

Allows users to define rules that classify drift severity
(e.g. 'warn' vs 'error') based on key patterns or resource names.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from driftcheck.differ import Change


SEVERITY_ERROR = "error"
SEVERITY_WARN = "warn"
SEVERITY_IGNORE = "ignore"

VALID_SEVERITIES = {SEVERITY_ERROR, SEVERITY_WARN, SEVERITY_IGNORE}


@dataclass
class PolicyRule:
    """A single policy rule that matches changes and assigns a severity."""

    severity: str
    key_pattern: Optional[str] = None   # fnmatch pattern against change.key
    resource_pattern: Optional[str] = None  # fnmatch pattern against resource name

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity {self.severity!r}. "
                f"Must be one of {sorted(VALID_SEVERITIES)}."
            )

    def matches(self, change: Change, resource: str = "") -> bool:
        """Return True when this rule applies to *change* for *resource*."""
        if self.key_pattern and not fnmatch.fnmatch(change.key, self.key_pattern):
            return False
        if self.resource_pattern and not fnmatch.fnmatch(resource, self.resource_pattern):
            return False
        return True


@dataclass
class Policy:
    """An ordered collection of PolicyRules.

    Rules are evaluated in order; the first match wins.
    If no rule matches, *default_severity* is returned.
    """

    rules: List[PolicyRule] = field(default_factory=list)
    default_severity: str = SEVERITY_ERROR

    def evaluate(self, change: Change, resource: str = "") -> str:
        """Return the severity string for *change*."""
        for rule in self.rules:
            if rule.matches(change, resource):
                return rule.severity
        return self.default_severity


def policy_from_dict(data: dict) -> Policy:
    """Build a :class:`Policy` from a plain dictionary (e.g. loaded from YAML).

    Expected structure::

        default_severity: warn
        rules:
          - severity: ignore
            key_pattern: "metadata.*"
          - severity: error
            resource_pattern: "prod-*"
    """
    default_severity = data.get("default_severity", SEVERITY_ERROR)
    rules = [
        PolicyRule(
            severity=r["severity"],
            key_pattern=r.get("key_pattern"),
            resource_pattern=r.get("resource_pattern"),
        )
        for r in data.get("rules", [])
    ]
    return Policy(rules=rules, default_severity=default_severity)

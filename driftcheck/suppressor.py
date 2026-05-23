"""Suppression rules for known/accepted drift.

Allows users to declare known drift that should be ignored during reporting,
keeping the signal-to-noise ratio high for actionable findings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Iterable, List, Optional

from driftcheck.differ import Change


@dataclass
class SuppressionRule:
    """A single suppression rule matching resource and/or key patterns."""

    resource: Optional[str] = None  # glob pattern, e.g. "prod-*"
    key: Optional[str] = None       # glob pattern, e.g. "metadata.*"
    reason: str = ""

    def __post_init__(self) -> None:
        if self.resource is None and self.key is None:
            raise ValueError(
                "SuppressionRule must specify at least one of 'resource' or 'key'"
            )

    def matches(self, resource: str, change: Change) -> bool:
        """Return True if this rule suppresses the given change for resource."""
        resource_ok = self.resource is None or fnmatch(resource, self.resource)
        key_ok = self.key is None or fnmatch(change.key, self.key)
        return resource_ok and key_ok


@dataclass
class Suppressor:
    """Collection of suppression rules applied to a list of changes."""

    rules: List[SuppressionRule] = field(default_factory=list)

    def add(self, rule: SuppressionRule) -> None:
        self.rules.append(rule)

    def is_suppressed(self, resource: str, change: Change) -> bool:
        """Return True if any rule suppresses this change."""
        return any(r.matches(resource, change) for r in self.rules)

    def filter_changes(
        self, resource: str, changes: Iterable[Change]
    ) -> List[Change]:
        """Return only the changes that are NOT suppressed."""
        return [c for c in changes if not self.is_suppressed(resource, c)]

    def suppressed_changes(
        self, resource: str, changes: Iterable[Change]
    ) -> List[Change]:
        """Return only the changes that ARE suppressed."""
        return [c for c in changes if self.is_suppressed(resource, c)]


def suppressor_from_dicts(rules: Iterable[dict]) -> Suppressor:
    """Build a Suppressor from a list of plain dicts (e.g. loaded from YAML)."""
    s = Suppressor()
    for raw in rules:
        s.add(
            SuppressionRule(
                resource=raw.get("resource"),
                key=raw.get("key"),
                reason=raw.get("reason", ""),
            )
        )
    return s

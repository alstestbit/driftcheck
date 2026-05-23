"""Low-level diff utilities that produce structured Change objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Change:
    """Represents a single detected difference between expected and actual state."""

    key: str
    change_type: str  # 'changed' | 'missing' | 'extra'
    expected: Optional[Any] = None
    actual: Optional[Any] = None

    def __str__(self) -> str:  # noqa: D401
        if self.change_type == "changed":
            return f"{self.key}: expected={self.expected!r}, actual={self.actual!r}"
        if self.change_type == "missing":
            return f"{self.key}: missing in actual (expected={self.expected!r})"
        if self.change_type == "extra":
            return f"{self.key}: extra in actual (actual={self.actual!r})"
        return f"{self.key}: {self.change_type}"


def diff(
    expected: Dict[str, Any],
    actual: Dict[str, Any],
    *,
    prefix: str = "",
    ignore_extra: bool = False,
) -> List[Change]:
    """Recursively diff two dicts and return a list of Change objects."""
    changes: List[Change] = []

    for key, exp_val in expected.items():
        full_key = f"{prefix}{key}" if prefix else key
        if key not in actual:
            changes.append(Change(key=full_key, change_type="missing", expected=exp_val))
        elif isinstance(exp_val, dict) and isinstance(actual[key], dict):
            changes.extend(
                diff(exp_val, actual[key], prefix=f"{full_key}.", ignore_extra=ignore_extra)
            )
        elif exp_val != actual[key]:
            changes.append(
                Change(key=full_key, change_type="changed", expected=exp_val, actual=actual[key])
            )

    if not ignore_extra:
        for key in actual:
            if key not in expected:
                full_key = f"{prefix}{key}" if prefix else key
                changes.append(Change(key=full_key, change_type="extra", actual=actual[key]))

    return changes


def summarise_changes(changes: List[Change]) -> Dict[str, int]:
    """Return a count of each change_type present in *changes*."""
    summary: Dict[str, int] = {}
    for change in changes:
        summary[change.change_type] = summary.get(change.change_type, 0) + 1
    return summary

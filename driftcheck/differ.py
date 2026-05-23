"""Deep diff utilities for producing human-readable change descriptions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class Change:
    """Represents a single field-level change between expected and actual state."""

    path: str
    expected: Any
    actual: Any
    kind: str  # 'changed' | 'missing' | 'extra'

    def __str__(self) -> str:
        if self.kind == "changed":
            return f"[changed] {self.path}: expected={self.expected!r}, actual={self.actual!r}"
        if self.kind == "missing":
            return f"[missing] {self.path}: expected={self.expected!r}, not present in actual"
        if self.kind == "extra":
            return f"[extra]   {self.path}: not expected, actual={self.actual!r}"
        return f"[{self.kind}] {self.path}"


def diff(
    expected: dict[str, Any],
    actual: dict[str, Any],
    *,
    prefix: str = "",
    ignore_extra: bool = False,
) -> list[Change]:
    """Recursively diff two dicts and return a list of Change objects."""
    changes: list[Change] = []

    for key, exp_val in expected.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if key not in actual:
            changes.append(Change(path=full_key, expected=exp_val, actual=None, kind="missing"))
        elif isinstance(exp_val, dict) and isinstance(actual[key], dict):
            changes.extend(
                diff(exp_val, actual[key], prefix=full_key, ignore_extra=ignore_extra)
            )
        elif exp_val != actual[key]:
            changes.append(
                Change(path=full_key, expected=exp_val, actual=actual[key], kind="changed")
            )

    if not ignore_extra:
        for key in actual:
            if key not in expected:
                full_key = f"{prefix}.{key}" if prefix else key
                changes.append(
                    Change(path=full_key, expected=None, actual=actual[key], kind="extra")
                )

    return changes


def summarise_changes(changes: list[Change]) -> dict[str, int]:
    """Return counts of each change kind."""
    counts: dict[str, int] = {"changed": 0, "missing": 0, "extra": 0}
    for change in changes:
        counts[change.kind] = counts.get(change.kind, 0) + 1
    return counts

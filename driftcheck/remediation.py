"""Remediation hint generation for detected drift."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftcheck.differ import Change


@dataclass
class RemediationHint:
    key: str
    change_type: str  # "changed", "missing", "extra"
    expected: object
    actual: object
    suggestion: str
    severity: str = "warning"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "change_type": self.change_type,
            "expected": self.expected,
            "actual": self.actual,
            "suggestion": self.suggestion,
            "severity": self.severity,
        }


def _suggestion_for(change: Change) -> str:
    if change.change_type == "changed":
        return (
            f"Update '{change.key}' from {change.actual!r} to {change.expected!r} "
            "to match the definition."
        )
    if change.change_type == "missing":
        return (
            f"Add '{change.key}' with value {change.expected!r} "
            "to the deployed resource."
        )
    if change.change_type == "extra":
        return (
            f"Remove '{change.key}' (value {change.actual!r}) "
            "from the deployed resource — it is not in the definition."
        )
    return f"Review '{change.key}' manually."


def hints_from_changes(
    changes: List[Change],
    severity: str = "warning",
) -> List[RemediationHint]:
    """Convert a list of Change objects into RemediationHint objects."""
    return [
        RemediationHint(
            key=c.key,
            change_type=c.change_type,
            expected=c.expected,
            actual=c.actual,
            suggestion=_suggestion_for(c),
            severity=severity,
        )
        for c in changes
    ]


def format_hints(hints: List[RemediationHint]) -> str:
    """Render hints as a human-readable string."""
    if not hints:
        return "No remediation required."
    lines = ["Remediation hints:"]
    for h in hints:
        lines.append(f"  [{h.severity.upper()}] {h.suggestion}")
    return "\n".join(lines)

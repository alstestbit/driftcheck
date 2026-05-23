"""Utilities for rendering Change lists as structured text or JSON."""

from __future__ import annotations

import json
from typing import Any

from driftcheck.differ import Change, summarise_changes


def changes_to_dict(changes: list[Change]) -> list[dict[str, Any]]:
    """Serialise a list of Change objects to plain dicts."""
    return [
        {"path": c.path, "kind": c.kind, "expected": c.expected, "actual": c.actual}
        for c in changes
    ]


def render_text(changes: list[Change], *, title: str = "") -> str:
    """Render changes as a human-readable text block."""
    lines: list[str] = []
    if title:
        lines.append(f"=== {title} ===")
    if not changes:
        lines.append("  No drift detected.")
        return "\n".join(lines)
    for change in changes:
        lines.append(f"  {change}")
    summary = summarise_changes(changes)
    totals = ", ".join(f"{v} {k}" for k, v in summary.items() if v > 0)
    lines.append(f"  Summary: {totals}")
    return "\n".join(lines)


def render_json(
    changes: list[Change],
    *,
    resource: str = "",
    indent: int = 2,
) -> str:
    """Render changes as a JSON string."""
    payload: dict[str, Any] = {
        "resource": resource,
        "drift_detected": len(changes) > 0,
        "summary": summarise_changes(changes),
        "changes": changes_to_dict(changes),
    }
    return json.dumps(payload, indent=indent)

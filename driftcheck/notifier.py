"""Notification dispatch for drift scan results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from driftcheck.scanner import ScanError
from driftcheck.comparator import DriftResult


@dataclass
class Notification:
    """Represents a notification message produced from a scan result."""

    resource: str
    status: str  # 'clean' | 'drifted' | 'error'
    message: str
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "resource": self.resource,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


NotifyHandler = Callable[[Notification], None]


def notification_from_result(result: DriftResult) -> Notification:
    """Build a Notification from a DriftResult."""
    if result.drifted:
        details = [
            f"  [{c.kind}] {c.key}: {c.expected!r} -> {c.actual!r}"
            for c in (result.changes if hasattr(result, "changes") else [])
        ]
        return Notification(
            resource=result.resource,
            status="drifted",
            message=f"Drift detected in '{result.resource}'",
            details=details,
        )
    return Notification(
        resource=result.resource,
        status="clean",
        message=f"No drift in '{result.resource}'",
    )


def notification_from_error(resource: str, error: Exception) -> Notification:
    """Build a Notification from a scan error."""
    return Notification(
        resource=resource,
        status="error",
        message=f"Error scanning '{resource}': {error}",
    )


def dispatch(
    notifications: List[Notification],
    handler: NotifyHandler,
    only_drifted: bool = False,
) -> None:
    """Send notifications through the provided handler.

    Args:
        notifications: List of Notification objects to dispatch.
        handler: Callable that accepts a single Notification.
        only_drifted: When True, skip clean notifications.
    """
    for note in notifications:
        if only_drifted and note.status == "clean":
            continue
        handler(note)

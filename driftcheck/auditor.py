"""Audit log support for drift check runs.

Records scan events with timestamps and outcomes for traceability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEvent:
    """A single audit log entry for a scanned resource."""

    timestamp: str
    resource: str
    source_file: str
    drifted: bool
    drift_count: int
    changed_keys: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "resource": self.resource,
            "source_file": self.source_file,
            "drifted": self.drifted,
            "drift_count": self.drift_count,
            "changed_keys": self.changed_keys,
            "error": self.error,
        }


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def make_event(
    resource: str,
    source_file: str,
    drifted: bool,
    changed_keys: List[str] | None = None,
    error: str | None = None,
    *,
    timestamp: str | None = None,
) -> AuditEvent:
    """Create an AuditEvent for a scanned resource."""
    keys = changed_keys or []
    return AuditEvent(
        timestamp=timestamp or _now_iso(),
        resource=resource,
        source_file=source_file,
        drifted=drifted,
        drift_count=len(keys),
        changed_keys=keys,
        error=error,
    )


def write_audit_log(events: List[AuditEvent], path: str) -> None:
    """Write audit events to a JSON-lines file at *path*."""
    with open(path, "w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event.to_dict()) + "\n")


def read_audit_log(path: str) -> List[AuditEvent]:
    """Read audit events from a JSON-lines file at *path*."""
    events: List[AuditEvent] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            events.append(
                AuditEvent(
                    timestamp=data["timestamp"],
                    resource=data["resource"],
                    source_file=data["source_file"],
                    drifted=data["drifted"],
                    drift_count=data["drift_count"],
                    changed_keys=data.get("changed_keys", []),
                    error=data.get("error"),
                )
            )
    return events

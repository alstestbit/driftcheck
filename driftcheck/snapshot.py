"""Snapshot management for drift baseline capture and comparison."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class SnapshotError(Exception):
    """Raised when snapshot operations fail."""


@dataclass
class Snapshot:
    """A point-in-time capture of a resource's live state."""

    resource: str
    state: Dict[str, Any]
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource": self.resource,
            "state": self.state,
            "captured_at": self.captured_at,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        return cls(
            resource=data["resource"],
            state=data["state"],
            captured_at=data.get("captured_at", ""),
            tags=data.get("tags", {}),
        )


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshot.to_dict(), fh, indent=2)
    except OSError as exc:
        raise SnapshotError(f"Failed to write snapshot to {path!r}: {exc}") from exc


def load_snapshot(path: str) -> Snapshot:
    """Load a snapshot from a JSON file."""
    if not os.path.exists(path):
        raise SnapshotError(f"Snapshot file not found: {path!r}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Failed to read snapshot from {path!r}: {exc}") from exc
    return Snapshot.from_dict(data)


def list_snapshots(directory: str) -> List[str]:
    """Return paths to all .json snapshot files in a directory."""
    if not os.path.isdir(directory):
        raise SnapshotError(f"Snapshot directory not found: {directory!r}")
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json")
    )

"""Compare two snapshots to detect state changes over time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from driftcheck.snapshot import Snapshot
from driftcheck.differ import Change, diff


@dataclass
class SnapshotDiff:
    """Result of comparing two snapshots for the same resource."""

    resource: str
    before_captured_at: str
    after_captured_at: str
    changes: List[Change]

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def summary(self) -> str:
        if not self.has_changes:
            return f"{self.resource}: no changes between snapshots"
        return (
            f"{self.resource}: {len(self.changes)} change(s) "
            f"between {self.before_captured_at} and {self.after_captured_at}"
        )


def diff_snapshots(
    before: Snapshot,
    after: Snapshot,
    ignore_keys: Optional[List[str]] = None,
    ignore_extra: bool = False,
) -> SnapshotDiff:
    """Compute the difference between two snapshots.

    Args:
        before: Earlier snapshot.
        after:  Later snapshot.
        ignore_keys: Keys to exclude from comparison.
        ignore_extra: If True, extra keys in *after* are not reported.

    Returns:
        A SnapshotDiff describing what changed.
    """
    if before.resource != after.resource:
        raise ValueError(
            f"Cannot diff snapshots for different resources: "
            f"{before.resource!r} vs {after.resource!r}"
        )

    changes = diff(
        before.state,
        after.state,
        ignore_keys=ignore_keys or [],
        ignore_extra=ignore_extra,
    )
    return SnapshotDiff(
        resource=before.resource,
        before_captured_at=before.captured_at,
        after_captured_at=after.captured_at,
        changes=changes,
    )

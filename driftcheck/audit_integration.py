"""Helpers to build AuditEvents from pipeline / scanner results.

Bridges the auditor module with the existing DriftResult / ScanError types
so callers don't need to know the internal structure of either.
"""

from __future__ import annotations

from typing import List, Sequence

from driftcheck.auditor import AuditEvent, make_event
from driftcheck.comparator import DriftResult
from driftcheck.scanner import ScanError


def event_from_drift_result(
    result: DriftResult,
    source_file: str,
    *,
    timestamp: str | None = None,
) -> AuditEvent:
    """Convert a DriftResult into an AuditEvent.

    Args:
        result:      The drift comparison result.
        source_file: Path to the YAML definition that was scanned.
        timestamp:   Optional ISO timestamp override (useful in tests).
    """
    changed_keys = list(result.diff.keys()) if result.drifted else []
    return make_event(
        resource=result.resource,
        source_file=source_file,
        drifted=result.drifted,
        changed_keys=changed_keys,
        timestamp=timestamp,
    )


def event_from_scan_error(
    error: ScanError,
    source_file: str,
    *,
    timestamp: str | None = None,
) -> AuditEvent:
    """Convert a ScanError into an AuditEvent flagged with the error message."""
    return make_event(
        resource=getattr(error, "resource", source_file),
        source_file=source_file,
        drifted=False,
        error=str(error),
        timestamp=timestamp,
    )


def events_from_results(
    results: Sequence[DriftResult],
    source_file: str,
    *,
    timestamp: str | None = None,
) -> List[AuditEvent]:
    """Bulk-convert a list of DriftResults to AuditEvents."""
    return [
        event_from_drift_result(r, source_file, timestamp=timestamp)
        for r in results
    ]

"""Baseline management: save and load known-good drift snapshots.

A baseline captures the set of drift results at a point in time so that
subsequent runs can distinguish *new* drift from previously acknowledged drift.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


class BaselineError(Exception):
    """Raised when a baseline file cannot be read or written."""


@dataclass(frozen=True)
class BaselineEntry:
    resource: str
    key: str
    expected: object
    actual: object

    def to_dict(self) -> dict:
        return {
            "resource": self.resource,
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BaselineEntry":
        return cls(
            resource=d["resource"],
            key=d["key"],
            expected=d["expected"],
            actual=d["actual"],
        )


def save_baseline(entries: List[BaselineEntry], path: str) -> None:
    """Persist *entries* as a JSON baseline file at *path*."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([e.to_dict() for e in entries], fh, indent=2)
    except OSError as exc:
        raise BaselineError(f"Could not write baseline to {path!r}: {exc}") from exc


def load_baseline(path: str) -> List[BaselineEntry]:
    """Load a baseline file from *path* and return a list of :class:`BaselineEntry`."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Could not read baseline from {path!r}: {exc}") from exc

    if not isinstance(raw, list):
        raise BaselineError(f"Baseline file {path!r} must contain a JSON array.")

    return [BaselineEntry.from_dict(item) for item in raw]


def is_acknowledged(entry: BaselineEntry, baseline: List[BaselineEntry]) -> bool:
    """Return True if *entry* is present in *baseline* (i.e. previously acknowledged)."""
    return entry in baseline


def filter_new_entries(
    entries: List[BaselineEntry], baseline: List[BaselineEntry]
) -> List[BaselineEntry]:
    """Return only the entries that are *not* present in the existing baseline."""
    baseline_set = set(baseline)
    return [e for e in entries if e not in baseline_set]

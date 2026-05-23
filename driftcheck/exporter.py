"""Export drift scan results to various output formats (JSON, CSV, plain text)."""

from __future__ import annotations

import csv
import io
import json
from typing import List

from driftcheck.scanner import ScanError
from driftcheck.differ import Change


def results_to_records(results: list) -> List[dict]:
    """Flatten a list of scan result dicts into exportable records.

    Each record contains: resource, key, change_type, expected, actual.
    """
    records = []
    for result in results:
        resource = result.get("resource", "unknown")
        changes: List[Change] = result.get("changes", [])
        if not changes:
            records.append(
                {
                    "resource": resource,
                    "key": "",
                    "change_type": "clean",
                    "expected": "",
                    "actual": "",
                }
            )
        for change in changes:
            records.append(
                {
                    "resource": resource,
                    "key": change.key,
                    "change_type": change.change_type,
                    "expected": str(change.expected) if change.expected is not None else "",
                    "actual": str(change.actual) if change.actual is not None else "",
                }
            )
    return records


def export_json(results: list, indent: int = 2) -> str:
    """Serialise scan results to a JSON string."""
    records = results_to_records(results)
    return json.dumps(records, indent=indent)


def export_csv(results: list) -> str:
    """Serialise scan results to a CSV string."""
    records = results_to_records(results)
    fieldnames = ["resource", "key", "change_type", "expected", "actual"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue()


def export_text(results: list) -> str:
    """Serialise scan results to a human-readable plain-text string."""
    lines = []
    for result in results:
        resource = result.get("resource", "unknown")
        changes: List[Change] = result.get("changes", [])
        if not changes:
            lines.append(f"[CLEAN] {resource}")
        else:
            lines.append(f"[DRIFT] {resource}")
            for change in changes:
                lines.append(f"  {change}")
    return "\n".join(lines)

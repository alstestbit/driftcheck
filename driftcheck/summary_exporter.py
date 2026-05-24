"""Exports a DriftSummary to JSON or plain-text files."""

from __future__ import annotations

import json
import csv
import io
from pathlib import Path
from typing import Union

from driftcheck.drift_summary import DriftSummary, format_summary


def export_summary_json(summary: DriftSummary, dest: Union[str, Path]) -> None:
    """Write summary as JSON to *dest*."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(summary.to_dict(), fh, indent=2)
        fh.write("\n")


def export_summary_text(summary: DriftSummary, dest: Union[str, Path]) -> None:
    """Write human-readable summary to *dest*."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(format_summary(summary))
        fh.write("\n")


def export_summary_csv(summary: DriftSummary, dest: Union[str, Path]) -> None:
    """Write summary metrics as a single-row CSV to *dest*."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = summary.to_dict()
    # Flatten drifted_resources list to a pipe-separated string
    data["drifted_resources"] = "|".join(data["drifted_resources"])
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(data.keys()))
        writer.writeheader()
        writer.writerow(data)


def summary_to_json_string(summary: DriftSummary) -> str:
    """Return the summary serialised as a JSON string (no file I/O)."""
    return json.dumps(summary.to_dict(), indent=2)

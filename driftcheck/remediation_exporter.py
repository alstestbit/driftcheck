"""Export remediation reports to JSON, text, or CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from driftcheck.remediation_report import RemediationReport


def export_remediation_json(reports: List[RemediationReport]) -> str:
    """Serialise reports to a JSON string."""
    return json.dumps([r.to_dict() for r in reports], indent=2, default=str)


def export_remediation_text(reports: List[RemediationReport]) -> str:
    """Render reports as a human-readable text block."""
    if not reports:
        return "No remediation reports."
    sections = [r.formatted() for r in reports]
    return "\n\n".join(sections)


def export_remediation_csv(reports: List[RemediationReport]) -> str:
    """Flatten reports to CSV rows (one row per hint, or one row if clean/error)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["resource", "drifted", "key", "change_type", "suggestion", "severity", "error"])
    for r in reports:
        if r.error:
            writer.writerow([r.resource, False, "", "", "", "", r.error])
        elif not r.hints:
            writer.writerow([r.resource, False, "", "", "", "", ""])
        else:
            for h in r.hints:
                writer.writerow(
                    [r.resource, True, h.key, h.change_type, h.suggestion, h.severity, ""]
                )
    return buf.getvalue()

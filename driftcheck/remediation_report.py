"""Combine scanner results with remediation hints into a structured report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from driftcheck.differ import Change, diff
from driftcheck.remediation import RemediationHint, hints_from_changes, format_hints
from driftcheck.scanner import ScanError


@dataclass
class RemediationReport:
    resource: str
    drifted: bool
    hints: List[RemediationHint] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "resource": self.resource,
            "drifted": self.drifted,
            "error": self.error,
            "hints": [h.to_dict() for h in self.hints],
        }

    def formatted(self) -> str:
        header = f"Resource: {self.resource}"
        if self.error:
            return f"{header}\n  ERROR: {self.error}"
        status = "DRIFTED" if self.drifted else "CLEAN"
        body = format_hints(self.hints)
        return f"{header} [{status}]\n{body}"


def build_remediation_report(
    resource: str,
    definition: dict,
    live: dict,
    severity: str = "warning",
) -> RemediationReport:
    """Diff definition vs live state and produce a RemediationReport."""
    changes: List[Change] = diff(definition, live)
    hints = hints_from_changes(changes, severity=severity)
    return RemediationReport(
        resource=resource,
        drifted=bool(hints),
        hints=hints,
    )


def build_remediation_report_from_error(
    resource: str,
    error: ScanError,
) -> RemediationReport:
    return RemediationReport(
        resource=resource,
        drifted=False,
        error=str(error),
    )

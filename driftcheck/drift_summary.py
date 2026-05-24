"""Aggregates drift results into a structured summary report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from driftcheck.comparator import DriftResult


@dataclass
class DriftSummary:
    total: int = 0
    drifted: int = 0
    clean: int = 0
    errored: int = 0
    resources: List[str] = field(default_factory=list)
    drifted_resources: List[str] = field(default_factory=list)

    @property
    def drift_rate(self) -> float:
        """Fraction of non-errored resources that have drifted."""
        eligible = self.total - self.errored
        if eligible <= 0:
            return 0.0
        return self.drifted / eligible

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "drifted": self.drifted,
            "clean": self.clean,
            "errored": self.errored,
            "drift_rate": round(self.drift_rate, 4),
            "drifted_resources": self.drifted_resources,
        }


def build_summary(results: List[DriftResult]) -> DriftSummary:
    """Build a DriftSummary from a list of DriftResult objects."""
    summary = DriftSummary()
    for result in results:
        summary.total += 1
        resource = result.resource
        summary.resources.append(resource)

        if result.error:
            summary.errored += 1
        elif result.drifted:
            summary.drifted += 1
            summary.drifted_resources.append(resource)
        else:
            summary.clean += 1

    return summary


def format_summary(summary: DriftSummary) -> str:
    """Render a DriftSummary as a human-readable string."""
    lines = [
        f"Drift Summary",
        f"  Total resources : {summary.total}",
        f"  Clean           : {summary.clean}",
        f"  Drifted         : {summary.drifted}",
        f"  Errored         : {summary.errored}",
        f"  Drift rate      : {summary.drift_rate:.1%}",
    ]
    if summary.drifted_resources:
        lines.append("  Drifted resources:")
        for r in summary.drifted_resources:
            lines.append(f"    - {r}")
    return "\n".join(lines)

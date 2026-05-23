"""Formats and outputs drift detection results."""

from typing import Iterable
from driftcheck.comparator import DriftResult


def format_report(results: Iterable[DriftResult], *, verbose: bool = False) -> str:
    """Generate a human-readable drift report from a list of DriftResult objects.

    Args:
        results: Iterable of DriftResult instances to include in the report.
        verbose: If True, include details even for resources with no drift.

    Returns:
        A formatted multi-line string report.
    """
    lines: list[str] = []
    drift_count = 0
    ok_count = 0

    for result in results:
        if result.has_drift:
            drift_count += 1
            lines.append(result.summary())
            if result.changed_values:
                for key, diff in result.changed_values.items():
                    lines.append(f"    {key}:")
                    lines.append(f"      expected: {diff['expected']}")
                    lines.append(f"      actual:   {diff['actual']}")
        else:
            ok_count += 1
            if verbose:
                lines.append(result.summary())

    lines.append("")
    lines.append(f"Summary: {drift_count} resource(s) with drift, {ok_count} resource(s) clean.")
    return "\n".join(lines)


def has_any_drift(results: Iterable[DriftResult]) -> bool:
    """Return True if any result in the iterable contains drift."""
    return any(r.has_drift for r in results)

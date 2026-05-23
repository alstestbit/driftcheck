"""Filtering utilities for drift results."""

from typing import List, Optional
from driftcheck.comparator import DriftResult


def filter_by_status(
    results: List[DriftResult],
    *,
    include_clean: bool = True,
    include_drifted: bool = True,
) -> List[DriftResult]:
    """Return only results matching the requested drift status."""
    out = []
    for result in results:
        has_drift = bool(result.drifted_keys or result.missing_keys or result.extra_keys)
        if has_drift and include_drifted:
            out.append(result)
        elif not has_drift and include_clean:
            out.append(result)
    return out


def filter_by_resource(
    results: List[DriftResult],
    resource_name: str,
) -> List[DriftResult]:
    """Return only results whose resource name contains *resource_name* (case-insensitive)."""
    needle = resource_name.lower()
    return [r for r in results if needle in r.resource.lower()]


def filter_by_key_prefix(
    results: List[DriftResult],
    prefix: str,
) -> List[DriftResult]:
    """Return results that have at least one drifted/missing/extra key matching *prefix*."""
    out = []
    for result in results:
        all_keys = (
            list(result.drifted_keys.keys())
            + result.missing_keys
            + result.extra_keys
        )
        if any(k.startswith(prefix) for k in all_keys):
            out.append(result)
    return out


def apply_ignore_keys(
    result: DriftResult,
    ignore_keys: List[str],
) -> DriftResult:
    """Return a new DriftResult with the specified keys removed from all drift sets."""
    ignore_set = set(ignore_keys)
    return DriftResult(
        resource=result.resource,
        drifted_keys={k: v for k, v in result.drifted_keys.items() if k not in ignore_set},
        missing_keys=[k for k in result.missing_keys if k not in ignore_set],
        extra_keys=[k for k in result.extra_keys if k not in ignore_set],
    )

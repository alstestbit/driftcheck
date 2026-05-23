"""High-level scan pipeline that wires loader, resolver, and scanner together."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from driftcheck.loader import load_definition
from driftcheck.resolver import resolve_definition
from driftcheck.scanner import ScanError, scan_file
from driftcheck.comparator import DriftResult


Fetcher = Callable[[Dict[str, Any]], Dict[str, Any]]


def run_pipeline(
    paths: List[Path],
    fetcher: Fetcher,
    variables: Optional[Dict[str, str]] = None,
    *,
    env: bool = True,
    strict: bool = False,
    ignore_extra: bool = False,
) -> List[DriftResult]:
    """Load, resolve, and scan each path in *paths*.

    Parameters
    ----------
    paths:
        YAML definition files to process.
    fetcher:
        Callable that accepts a definition dict and returns the live state.
    variables:
        Explicit variable substitutions applied before scanning.
    env:
        Whether OS environment variables are used for placeholder resolution.
    strict:
        Raise :class:`~driftcheck.resolver.ResolveError` on unresolved
        placeholders when ``True``; leave them intact otherwise.
    ignore_extra:
        When ``True``, keys present in live state but absent from the
        definition are not reported as drift.

    Returns a flat list of :class:`~driftcheck.comparator.DriftResult`.
    """
    results: List[DriftResult] = []

    for path in paths:
        definition = load_definition(path)
        resolved = resolve_definition(
            definition, variables=variables, env=env, strict=strict
        )
        result = scan_file(
            path,
            fetcher=fetcher,
            ignore_extra=ignore_extra,
            _definition_override=resolved,
        )
        results.append(result)

    return results

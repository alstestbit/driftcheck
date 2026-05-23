"""Scanner module: orchestrates loading definitions and comparing against live state."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

from driftcheck.comparator import DriftResult, compare
from driftcheck.loader import load_definition, load_definitions_from_dir


class ScanError(Exception):
    """Raised when a scan cannot be completed."""


StateFetcher = Callable[[str], Dict[str, Any]]


def scan_file(
    definition_path: Path,
    fetcher: StateFetcher,
    resource_key: str = "name",
) -> DriftResult:
    """Load a single YAML definition and compare it against live state.

    Args:
        definition_path: Path to the YAML definition file.
        fetcher: Callable that accepts a resource identifier and returns the
                 live state as a dict.
        resource_key: Key inside the definition used as the resource identifier
                      passed to *fetcher*. Defaults to ``"name"``.

    Returns:
        A :class:`~driftcheck.comparator.DriftResult` describing any drift.

    Raises:
        ScanError: If the definition is missing the resource key or the fetcher
                   raises an exception.
    """
    definition = load_definition(definition_path)

    if resource_key not in definition:
        raise ScanError(
            f"Definition '{definition_path}' is missing required key '{resource_key}'."
        )

    resource_id: str = definition[resource_key]

    try:
        live_state = fetcher(resource_id)
    except Exception as exc:  # pragma: no cover – fetcher errors are caller-controlled
        raise ScanError(
            f"Fetcher raised an error for resource '{resource_id}': {exc}"
        ) from exc

    return compare(definition, live_state, source=str(definition_path))


def scan_directory(
    definitions_dir: Path,
    fetcher: StateFetcher,
    resource_key: str = "name",
) -> List[DriftResult]:
    """Scan all YAML definitions in a directory against live state.

    Args:
        definitions_dir: Directory containing YAML definition files.
        fetcher: Callable that accepts a resource identifier and returns the
                 live state as a dict.
        resource_key: Key inside each definition used as the resource identifier.

    Returns:
        A list of :class:`~driftcheck.comparator.DriftResult` objects, one per
        definition file found in *definitions_dir*.
    """
    definitions = load_definitions_from_dir(definitions_dir)
    results: List[DriftResult] = []

    for path, definition in definitions.items():
        if resource_key not in definition:
            raise ScanError(
                f"Definition '{path}' is missing required key '{resource_key}'."
            )
        resource_id: str = definition[resource_key]
        live_state = fetcher(resource_id)
        results.append(compare(definition, live_state, source=path))

    return results

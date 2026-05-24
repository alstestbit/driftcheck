"""Minimal CLI entry-point for driftcheck.

Usage (example with a stub fetcher):
    python -m driftcheck.cli --dir definitions/ --verbose

Real deployments should supply a custom fetcher via the Python API.
The CLI ships a no-op fetcher that always returns an empty live state so
users can validate definition files and see what *would* be flagged as
missing from live infrastructure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

from driftcheck.reporter import format_report, has_any_drift
from driftcheck.scanner import ScanError, scan_directory, scan_file


def _noop_fetcher(_resource_id: str) -> Dict[str, Any]:
    """Stub fetcher that always returns an empty live state."""
    return {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="driftcheck",
        description="Detect configuration drift between YAML definitions and live state.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file", "-f",
        type=Path,
        metavar="PATH",
        help="Path to a single YAML definition file.",
    )
    group.add_argument(
        "--dir", "-d",
        type=Path,
        metavar="DIR",
        help="Directory containing YAML definition files.",
    )
    parser.add_argument(
        "--resource-key",
        default="name",
        metavar="KEY",
        help="YAML key used as the resource identifier (default: 'name').",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show clean (no-drift) results as well.",
    )
    return parser


def _validate_paths(args: argparse.Namespace) -> str | None:
    """Validate that the supplied file/directory path exists and is the right type.

    Returns an error message string if validation fails, otherwise ``None``.
    """
    if args.file:
        if not args.file.exists():
            return f"File not found: {args.file}"
        if not args.file.is_file():
            return f"Path is not a file: {args.file}"
    else:
        if not args.dir.exists():
            return f"Directory not found: {args.dir}"
        if not args.dir.is_dir():
            return f"Path is not a directory: {args.dir}"
    return None


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)

    path_error = _validate_paths(args)
    if path_error:
        print(f"[error] {path_error}", file=sys.stderr)
        return 2

    try:
        if args.file:
            results = [scan_file(args.file, _noop_fetcher, resource_key=args.resource_key)]
        else:
            results = scan_directory(args.dir, _noop_fetcher, resource_key=args.resource_key)
    except ScanError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    print(format_report(results, verbose=args.verbose))
    return 1 if has_any_drift(results) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

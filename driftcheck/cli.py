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


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args(argv)

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

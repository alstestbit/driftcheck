"""Loads and parses YAML definition files for infrastructure configuration."""

import os
from pathlib import Path
from typing import Any

import yaml


class YAMLLoadError(Exception):
    """Raised when a YAML definition file cannot be loaded or parsed."""


def load_definition(path: str | Path) -> dict[str, Any]:
    """Load a single YAML definition file and return its contents as a dict.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        YAMLLoadError: If the file is missing, unreadable, or contains invalid YAML.
    """
    path = Path(path)

    if not path.exists():
        raise YAMLLoadError(f"Definition file not found: {path}")

    if not path.is_file():
        raise YAMLLoadError(f"Path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise YAMLLoadError(f"Failed to parse YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise YAMLLoadError(f"Cannot read file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise YAMLLoadError(
            f"Expected a YAML mapping at the top level in {path}, got {type(data).__name__}"
        )

    return data


def load_definitions_from_dir(directory: str | Path) -> dict[str, dict[str, Any]]:
    """Recursively load all YAML definition files from a directory.

    Args:
        directory: Root directory to search for .yaml / .yml files.

    Returns:
        Mapping of relative file path (str) -> parsed definition dict.

    Raises:
        YAMLLoadError: If the directory does not exist.
    """
    directory = Path(directory)

    if not directory.is_dir():
        raise YAMLLoadError(f"Definitions directory not found: {directory}")

    definitions: dict[str, dict[str, Any]] = {}

    for root, _, files in os.walk(directory):
        for filename in sorted(files):
            if filename.endswith((".yaml", ".yml")):
                full_path = Path(root) / filename
                rel_path = str(full_path.relative_to(directory))
                definitions[rel_path] = load_definition(full_path)

    return definitions

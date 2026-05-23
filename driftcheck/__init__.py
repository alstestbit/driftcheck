"""driftcheck — Detects configuration drift between deployed infra state
and version-controlled YAML definitions.
"""

__version__ = "0.1.0"

from driftcheck.loader import (
    YAMLLoadError,
    load_definition,
    load_definitions_from_dir,
)

__all__ = [
    "__version__",
    "YAMLLoadError",
    "load_definition",
    "load_definitions_from_dir",
]

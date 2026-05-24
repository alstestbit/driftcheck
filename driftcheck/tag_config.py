"""Load tag-filter configuration from a YAML or dict definition."""
from __future__ import annotations

from typing import Any, Dict, Optional

from driftcheck.tag_filter import TagFilter, build_tag_filter


class TagConfigError(Exception):
    """Raised when a tag-filter configuration block is malformed."""


def _require_dict(value: Any, label: str) -> Dict[str, str]:
    """Validate that *value* is a flat string→string mapping."""
    if not isinstance(value, dict):
        raise TagConfigError(
            f"'{label}' must be a mapping of string keys to string values, "
            f"got {type(value).__name__!r}"
        )
    result: Dict[str, str] = {}
    for k, v in value.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise TagConfigError(
                f"'{label}' entries must be strings; "
                f"got key={k!r} value={v!r}"
            )
        result[k] = v
    return result


def tag_filter_from_config(config: Optional[Dict[str, Any]]) -> TagFilter:
    """Build a :class:`TagFilter` from a parsed configuration dict.

    Expected shape::

        tag_filter:
          required:
            env: prod
          excluded:
            debug: "true"

    Both ``required`` and ``excluded`` are optional; omitting either is
    equivalent to passing an empty mapping.

    Args:
        config: The ``tag_filter`` sub-dict from a YAML config, or ``None``.

    Returns:
        A :class:`TagFilter` instance.

    Raises:
        TagConfigError: If the config block is not a dict or contains
            non-string entries.
    """
    if config is None:
        return build_tag_filter()

    if not isinstance(config, dict):
        raise TagConfigError(
            f"tag_filter config must be a mapping, got {type(config).__name__!r}"
        )

    required = _require_dict(config.get("required", {}), "required")
    excluded = _require_dict(config.get("excluded", {}), "excluded")

    unknown = set(config.keys()) - {"required", "excluded"}
    if unknown:
        raise TagConfigError(
            f"Unknown keys in tag_filter config: {sorted(unknown)}"
        )

    return build_tag_filter(required=required, excluded=excluded)

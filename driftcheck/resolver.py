"""Resolves variable placeholders in YAML definitions before comparison."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


class ResolveError(Exception):
    """Raised when a required variable cannot be resolved."""


def resolve_value(value: str, variables: Dict[str, str], strict: bool = True) -> str:
    """Replace ${VAR} placeholders in *value* using *variables*.

    If *strict* is True (default) an unresolvable placeholder raises
    :class:`ResolveError`.  Otherwise the placeholder is left as-is.
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        if not strict:
            return match.group(0)
        raise ResolveError(
            f"Variable '{key}' is not defined and strict mode is enabled."
        )

    return _PLACEHOLDER_RE.sub(_replace, value)


def resolve_definition(
    definition: Dict[str, Any],
    variables: Optional[Dict[str, str]] = None,
    *,
    env: bool = True,
    strict: bool = True,
) -> Dict[str, Any]:
    """Recursively resolve placeholders in a definition dict.

    Variables are looked up first in *variables*, then (if *env* is True)
    in :data:`os.environ`.

    Returns a new dict; the original is not mutated.
    """
    merged: Dict[str, str] = {}
    if env:
        merged.update(os.environ)
    if variables:
        merged.update(variables)

    return _resolve_node(definition, merged, strict=strict)


def _resolve_node(node: Any, variables: Dict[str, str], *, strict: bool) -> Any:
    if isinstance(node, dict):
        return {
            k: _resolve_node(v, variables, strict=strict)
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_resolve_node(item, variables, strict=strict) for item in node]
    if isinstance(node, str):
        return resolve_value(node, variables, strict=strict)
    return node

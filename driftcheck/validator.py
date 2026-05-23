"""Validates YAML definition structure before comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ValidationError(Exception):
    """Raised when a definition fails structural validation."""


@dataclass
class ValidationResult:
    resource: str
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        if self.valid:
            return f"{self.resource}: OK"
        joined = "; ".join(self.errors)
        return f"{self.resource}: INVALID ({joined})"


def validate_definition(
    definition: Any,
    resource: str,
    required_keys: list[str] | None = None,
) -> ValidationResult:
    """Validate a single loaded YAML definition dict.

    Args:
        definition: The parsed YAML object to validate.
        resource: A label used in error messages (e.g. filename).
        required_keys: Optional list of top-level keys that must be present.

    Returns:
        A ValidationResult indicating whether the definition is valid.
    """
    errors: list[str] = []

    if not isinstance(definition, dict):
        errors.append("definition must be a mapping")
        return ValidationResult(resource=resource, errors=errors)

    if not definition:
        errors.append("definition must not be empty")

    for key in required_keys or []:
        if key not in definition:
            errors.append(f"missing required key: '{key}'")

    return ValidationResult(resource=resource, errors=errors)


def validate_all(
    definitions: dict[str, Any],
    required_keys: list[str] | None = None,
) -> list[ValidationResult]:
    """Validate a mapping of resource names to definitions.

    Args:
        definitions: Dict of resource_name -> parsed definition.
        required_keys: Keys that every definition must contain.

    Returns:
        List of ValidationResult, one per definition.
    """
    return [
        validate_definition(defn, resource=name, required_keys=required_keys)
        for name, defn in definitions.items()
    ]

"""Compares deployed infrastructure state against YAML definitions to detect drift."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DriftResult:
    """Holds the result of a drift comparison for a single resource."""

    resource_id: str
    has_drift: bool
    missing_keys: list[str] = field(default_factory=list)
    extra_keys: list[str] = field(default_factory=list)
    changed_values: dict[str, dict[str, Any]] = field(default_factory=dict)

    def summary(self) -> str:
        if not self.has_drift:
            return f"[OK] {self.resource_id}: no drift detected"
        parts = []
        if self.missing_keys:
            parts.append(f"missing keys: {self.missing_keys}")
        if self.extra_keys:
            parts.append(f"extra keys: {self.extra_keys}")
        if self.changed_values:
            parts.append(f"changed values: {self.changed_values}")
        return f"[DRIFT] {self.resource_id}: " + "; ".join(parts)


def compare(definition: dict[str, Any], deployed: dict[str, Any], resource_id: str = "resource") -> DriftResult:
    """Compare a YAML definition dict against a deployed state dict.

    Args:
        definition: The expected state loaded from a YAML definition file.
        deployed: The actual deployed state retrieved from infrastructure.
        resource_id: A label identifying the resource being compared.

    Returns:
        A DriftResult describing any detected drift.
    """
    def_keys = set(definition.keys())
    dep_keys = set(deployed.keys())

    missing_keys = sorted(def_keys - dep_keys)
    extra_keys = sorted(dep_keys - def_keys)
    changed_values: dict[str, dict[str, Any]] = {}

    for key in def_keys & dep_keys:
        def_val = definition[key]
        dep_val = deployed[key]
        if isinstance(def_val, dict) and isinstance(dep_val, dict):
            nested = compare(def_val, dep_val, resource_id=key)
            if nested.has_drift:
                changed_values[key] = {
                    "expected": def_val,
                    "actual": dep_val,
                }
        elif def_val != dep_val:
            changed_values[key] = {"expected": def_val, "actual": dep_val}

    has_drift = bool(missing_keys or extra_keys or changed_values)
    return DriftResult(
        resource_id=resource_id,
        has_drift=has_drift,
        missing_keys=missing_keys,
        extra_keys=extra_keys,
        changed_values=changed_values,
    )

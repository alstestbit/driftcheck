"""Tag-based filtering for drift results and snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftcheck.comparator import DriftResult


@dataclass
class TagFilter:
    """Matches resources by required and/or excluded tag key-value pairs."""

    required: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)

    def matches(self, tags: Dict[str, str]) -> bool:
        """Return True if *tags* satisfies all required and no excluded rules."""
        for key, value in self.required.items():
            if tags.get(key) != value:
                return False
        for key, value in self.excluded.items():
            if tags.get(key) == value:
                return False
        return True


def filter_results_by_tags(
    results: List[DriftResult],
    tag_filter: TagFilter,
    tag_key: str = "tags",
) -> List[DriftResult]:
    """Return only the results whose definition contains matching tags.

    Args:
        results:    List of DriftResult objects to filter.
        tag_filter: TagFilter specifying required / excluded tags.
        tag_key:    Key inside each result's *definition* dict that holds
                    the tag mapping (defaults to ``"tags"``).
    """
    filtered: List[DriftResult] = []
    for result in results:
        definition_tags: Dict[str, str] = {}
        if isinstance(result.definition, dict):
            raw = result.definition.get(tag_key, {})
            if isinstance(raw, dict):
                definition_tags = {str(k): str(v) for k, v in raw.items()}
        if tag_filter.matches(definition_tags):
            filtered.append(result)
    return filtered


def build_tag_filter(
    required: Optional[Dict[str, str]] = None,
    excluded: Optional[Dict[str, str]] = None,
) -> TagFilter:
    """Convenience constructor for TagFilter."""
    return TagFilter(
        required=required or {},
        excluded=excluded or {},
    )

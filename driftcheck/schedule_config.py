"""Load scheduler configuration from a YAML file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from driftcheck.loader import load_definition, YAMLLoadError


@dataclass
class JobConfig:
    """Configuration for a single scheduled scan job."""

    name: str
    path: str
    interval_seconds: int
    fetcher_url: str = ""


class ScheduleConfigError(Exception):
    """Raised when schedule configuration is invalid."""


def load_schedule_config(config_path: str) -> List[JobConfig]:
    """Parse a YAML schedule config file and return a list of JobConfig.

    Expected YAML structure::

        jobs:
          - name: prod-scan
            path: definitions/
            interval_seconds: 300
            fetcher_url: http://api/state/{resource}

    Raises:
        ScheduleConfigError: if the file is missing, invalid, or malformed.
    """
    try:
        raw = load_definition(config_path)
    except YAMLLoadError as exc:
        raise ScheduleConfigError(str(exc)) from exc

    if "jobs" not in raw:
        raise ScheduleConfigError("Schedule config must contain a top-level 'jobs' key")

    jobs_raw = raw["jobs"]
    if not isinstance(jobs_raw, list):
        raise ScheduleConfigError("'jobs' must be a list")

    configs: List[JobConfig] = []
    for idx, entry in enumerate(jobs_raw):
        if not isinstance(entry, dict):
            raise ScheduleConfigError(f"Job entry {idx} must be a mapping")
        _require_keys(entry, idx)
        configs.append(
            JobConfig(
                name=str(entry["name"]),
                path=str(entry["path"]),
                interval_seconds=int(entry["interval_seconds"]),
                fetcher_url=str(entry.get("fetcher_url", "")),
            )
        )
    return configs


def _require_keys(entry: dict, idx: int) -> None:
    required = {"name", "path", "interval_seconds"}
    missing = required - entry.keys()
    if missing:
        raise ScheduleConfigError(
            f"Job entry {idx} is missing required keys: {sorted(missing)}"
        )
    if not isinstance(entry["interval_seconds"], int) or entry["interval_seconds"] <= 0:
        raise ScheduleConfigError(
            f"Job entry {idx}: 'interval_seconds' must be a positive integer"
        )

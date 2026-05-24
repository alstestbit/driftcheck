"""Periodic scan scheduling utilities for driftcheck."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class ScheduledJob:
    """Represents a recurring scan job."""

    name: str
    interval_seconds: int
    callback: Callable[[], None]
    _timer: Optional[threading.Timer] = field(default=None, init=False, repr=False)
    _running: bool = field(default=False, init=False, repr=False)

    def start(self) -> None:
        """Start the recurring job."""
        if self._running:
            return
        self._running = True
        self._schedule_next()

    def stop(self) -> None:
        """Stop the recurring job."""
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self) -> None:
        if not self._running:
            return
        self._timer = threading.Timer(self.interval_seconds, self._run)
        self._timer.daemon = True
        self._timer.start()

    def _run(self) -> None:
        try:
            self.callback()
        finally:
            self._schedule_next()


class Scheduler:
    """Manages a collection of scheduled scan jobs."""

    def __init__(self) -> None:
        self._jobs: List[ScheduledJob] = []

    def register(self, name: str, interval_seconds: int, callback: Callable[[], None]) -> ScheduledJob:
        """Register a new job and return it."""
        if interval_seconds <= 0:
            raise ValueError(f"interval_seconds must be positive, got {interval_seconds}")
        job = ScheduledJob(name=name, interval_seconds=interval_seconds, callback=callback)
        self._jobs.append(job)
        return job

    def start_all(self) -> None:
        """Start all registered jobs."""
        for job in self._jobs:
            job.start()

    def stop_all(self) -> None:
        """Stop all registered jobs."""
        for job in self._jobs:
            job.stop()

    @property
    def jobs(self) -> List[ScheduledJob]:
        return list(self._jobs)

    def __len__(self) -> int:
        return len(self._jobs)

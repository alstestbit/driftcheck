"""Tests for driftcheck.scheduler."""

import threading
import time
import pytest

from driftcheck.scheduler import Scheduler, ScheduledJob


# ---------------------------------------------------------------------------
# ScheduledJob unit tests
# ---------------------------------------------------------------------------

def test_scheduled_job_runs_callback():
    event = threading.Event()
    job = ScheduledJob(name="test", interval_seconds=1, callback=event.set)
    # Manually invoke internal run to avoid real timer delay
    job._running = True
    job._run()
    assert event.is_set()


def test_scheduled_job_stop_prevents_reschedule():
    calls = []
    job = ScheduledJob(name="test", interval_seconds=60, callback=lambda: calls.append(1))
    job.start()
    job.stop()
    assert not job._running
    assert job._timer is None


def test_scheduled_job_start_is_idempotent():
    job = ScheduledJob(name="test", interval_seconds=60, callback=lambda: None)
    job.start()
    timer_before = job._timer
    job.start()  # second call should be a no-op
    assert job._timer is timer_before
    job.stop()


# ---------------------------------------------------------------------------
# Scheduler unit tests
# ---------------------------------------------------------------------------

def test_scheduler_register_returns_job():
    s = Scheduler()
    job = s.register("scan", 30, lambda: None)
    assert isinstance(job, ScheduledJob)
    assert job.name == "scan"
    assert job.interval_seconds == 30


def test_scheduler_register_invalid_interval_raises():
    s = Scheduler()
    with pytest.raises(ValueError, match="interval_seconds must be positive"):
        s.register("bad", 0, lambda: None)


def test_scheduler_register_negative_interval_raises():
    s = Scheduler()
    with pytest.raises(ValueError):
        s.register("bad", -5, lambda: None)


def test_scheduler_len():
    s = Scheduler()
    s.register("a", 10, lambda: None)
    s.register("b", 20, lambda: None)
    assert len(s) == 2


def test_scheduler_jobs_returns_copy():
    s = Scheduler()
    s.register("a", 10, lambda: None)
    jobs = s.jobs
    jobs.clear()
    assert len(s) == 1


def test_scheduler_start_and_stop_all():
    s = Scheduler()
    s.register("x", 60, lambda: None)
    s.register("y", 60, lambda: None)
    s.start_all()
    for job in s.jobs:
        assert job._running
    s.stop_all()
    for job in s.jobs:
        assert not job._running


def test_scheduler_callback_invoked_via_timer(monkeypatch):
    """Verify callback fires when the job runs."""
    results = []
    s = Scheduler()
    job = s.register("quick", 60, lambda: results.append(True))
    # Simulate a single fire without waiting for real timer
    job._running = True
    job._run()
    assert results == [True]
    job.stop()

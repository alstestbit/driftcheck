"""Tests for driftcheck.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from driftcheck.comparator import DriftResult
from driftcheck.notifier import (
    Notification,
    dispatch,
    notification_from_error,
    notification_from_result,
)


def _clean_result(resource: str = "svc/web") -> DriftResult:
    return DriftResult(resource=resource, drifted=False, changes=[])


def _drift_result(resource: str = "svc/web") -> DriftResult:
    from driftcheck.differ import Change

    return DriftResult(
        resource=resource,
        drifted=True,
        changes=[Change(kind="changed", key="replicas", expected=2, actual=3)],
    )


# --- notification_from_result ---


def test_notification_from_clean_result_is_clean():
    note = notification_from_result(_clean_result())
    assert note.status == "clean"
    assert note.resource == "svc/web"
    assert "No drift" in note.message
    assert note.details == []


def test_notification_from_drift_result_is_drifted():
    note = notification_from_result(_drift_result())
    assert note.status == "drifted"
    assert "Drift detected" in note.message


def test_notification_from_drift_result_includes_details():
    note = notification_from_result(_drift_result())
    assert any("replicas" in d for d in note.details)


def test_notification_from_drift_result_resource_matches():
    note = notification_from_result(_drift_result("db/primary"))
    assert note.resource == "db/primary"


# --- notification_from_error ---


def test_notification_from_error_status_is_error():
    note = notification_from_error("svc/broken", ValueError("bad"))
    assert note.status == "error"


def test_notification_from_error_message_contains_resource():
    note = notification_from_error("svc/broken", ValueError("bad"))
    assert "svc/broken" in note.message


def test_notification_from_error_message_contains_error():
    note = notification_from_error("svc/broken", ValueError("timeout"))
    assert "timeout" in note.message


# --- dispatch ---


def test_dispatch_calls_handler_for_each_notification():
    handler = MagicMock()
    notes = [notification_from_result(_clean_result(f"svc/{i}")) for i in range(3)]
    dispatch(notes, handler)
    assert handler.call_count == 3


def test_dispatch_only_drifted_skips_clean():
    handler = MagicMock()
    notes = [
        notification_from_result(_clean_result()),
        notification_from_result(_drift_result()),
    ]
    dispatch(notes, handler, only_drifted=True)
    assert handler.call_count == 1
    args, _ = handler.call_args
    assert args[0].status == "drifted"


def test_dispatch_only_drifted_false_includes_clean():
    handler = MagicMock()
    notes = [
        notification_from_result(_clean_result()),
        notification_from_result(_drift_result()),
    ]
    dispatch(notes, handler, only_drifted=False)
    assert handler.call_count == 2


# --- Notification.to_dict ---


def test_notification_to_dict_keys():
    note = notification_from_result(_clean_result())
    d = note.to_dict()
    assert set(d.keys()) == {"resource", "status", "message", "details"}

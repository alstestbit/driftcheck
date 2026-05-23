"""Tests for driftcheck.auditor."""

import json
import os
import tempfile

import pytest

from driftcheck.auditor import (
    AuditEvent,
    make_event,
    read_audit_log,
    write_audit_log,
)

FIXED_TS = "2024-01-15T10:00:00+00:00"


# ---------------------------------------------------------------------------
# make_event
# ---------------------------------------------------------------------------

def test_make_event_clean():
    ev = make_event("svc/web", "web.yaml", drifted=False, timestamp=FIXED_TS)
    assert ev.resource == "svc/web"
    assert ev.source_file == "web.yaml"
    assert ev.drifted is False
    assert ev.drift_count == 0
    assert ev.changed_keys == []
    assert ev.error is None
    assert ev.timestamp == FIXED_TS


def test_make_event_drifted():
    ev = make_event(
        "svc/api",
        "api.yaml",
        drifted=True,
        changed_keys=["replicas", "image"],
        timestamp=FIXED_TS,
    )
    assert ev.drifted is True
    assert ev.drift_count == 2
    assert ev.changed_keys == ["replicas", "image"]


def test_make_event_with_error():
    ev = make_event(
        "svc/db", "db.yaml", drifted=False, error="fetch failed", timestamp=FIXED_TS
    )
    assert ev.error == "fetch failed"


def test_make_event_auto_timestamp():
    ev = make_event("r", "f.yaml", drifted=False)
    assert ev.timestamp  # not empty
    assert "+" in ev.timestamp or "Z" in ev.timestamp or "00:00" in ev.timestamp


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_audit_event_to_dict_keys():
    ev = make_event("svc/web", "web.yaml", drifted=False, timestamp=FIXED_TS)
    d = ev.to_dict()
    assert set(d.keys()) == {
        "timestamp", "resource", "source_file",
        "drifted", "drift_count", "changed_keys", "error",
    }


# ---------------------------------------------------------------------------
# write / read round-trip
# ---------------------------------------------------------------------------

def _make_events():
    return [
        make_event("svc/web", "web.yaml", drifted=False, timestamp=FIXED_TS),
        make_event(
            "svc/api",
            "api.yaml",
            drifted=True,
            changed_keys=["replicas"],
            timestamp=FIXED_TS,
        ),
    ]


def test_write_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audit.jsonl")
        write_audit_log(_make_events(), path)
        assert os.path.exists(path)


def test_write_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audit.jsonl")
        events = _make_events()
        write_audit_log(events, path)
        loaded = read_audit_log(path)
        assert len(loaded) == 2
        assert loaded[0].resource == "svc/web"
        assert loaded[1].drifted is True
        assert loaded[1].changed_keys == ["replicas"]


def test_write_produces_valid_jsonlines():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audit.jsonl")
        write_audit_log(_make_events(), path)
        with open(path) as fh:
            lines = [l.strip() for l in fh if l.strip()]
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "resource" in obj


def test_read_empty_file_returns_empty_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "empty.jsonl")
        open(path, "w").close()
        assert read_audit_log(path) == []

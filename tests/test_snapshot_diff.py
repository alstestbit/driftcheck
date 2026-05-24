"""Tests for driftcheck.snapshot_diff and driftcheck.snapshot_store."""

import pytest

from driftcheck.snapshot import Snapshot, SnapshotError
from driftcheck.snapshot_diff import diff_snapshots, SnapshotDiff
from driftcheck.snapshot_store import SnapshotStore


def _snap(resource: str, state: dict, ts: str = "2024-01-01T00:00:00+00:00") -> Snapshot:
    return Snapshot(resource=resource, state=state, captured_at=ts)


# --- snapshot_diff tests ---

def test_diff_identical_snapshots_no_changes():
    s = _snap("svc", {"replicas": 2})
    result = diff_snapshots(s, s)
    assert not result.has_changes


def test_diff_detects_changed_value():
    before = _snap("svc", {"replicas": 2}, "2024-01-01T00:00:00+00:00")
    after = _snap("svc", {"replicas": 5}, "2024-01-02T00:00:00+00:00")
    result = diff_snapshots(before, after)
    assert result.has_changes
    assert any(c.key == "replicas" for c in result.changes)


def test_diff_summary_no_changes():
    s = _snap("svc", {"x": 1})
    result = diff_snapshots(s, s)
    assert "no changes" in result.summary()


def test_diff_summary_with_changes():
    before = _snap("svc", {"x": 1}, "T1")
    after = _snap("svc", {"x": 9}, "T2")
    result = diff_snapshots(before, after)
    assert "1 change" in result.summary()
    assert "T1" in result.summary()


def test_diff_different_resources_raises():
    a = _snap("svc-a", {})
    b = _snap("svc-b", {})
    with pytest.raises(ValueError, match="different resources"):
        diff_snapshots(a, b)


def test_diff_ignore_keys_suppresses_key():
    before = _snap("svc", {"replicas": 2, "ts": "old"})
    after = _snap("svc", {"replicas": 2, "ts": "new"})
    result = diff_snapshots(before, after, ignore_keys=["ts"])
    assert not result.has_changes


# --- snapshot_store tests ---

def test_store_save_and_load(tmp_path):
    store = SnapshotStore(str(tmp_path))
    snap = _snap("service/web", {"replicas": 3})
    store.save(snap)
    loaded = store.load("service/web")
    assert loaded.state == {"replicas": 3}


def test_store_exists(tmp_path):
    store = SnapshotStore(str(tmp_path))
    assert not store.exists("svc")
    store.save(_snap("svc", {}))
    assert store.exists("svc")


def test_store_delete(tmp_path):
    store = SnapshotStore(str(tmp_path))
    store.save(_snap("svc", {}))
    store.delete("svc")
    assert not store.exists("svc")


def test_store_delete_missing_raises(tmp_path):
    store = SnapshotStore(str(tmp_path))
    with pytest.raises(SnapshotError):
        store.delete("ghost")


def test_store_list_resources(tmp_path):
    store = SnapshotStore(str(tmp_path))
    store.save(_snap("alpha", {}))
    store.save(_snap("beta", {}))
    resources = store.list_resources()
    assert "alpha" in resources
    assert "beta" in resources

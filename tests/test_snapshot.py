"""Tests for driftcheck.snapshot."""

import json
import os
import pytest

from driftcheck.snapshot import (
    Snapshot,
    SnapshotError,
    load_snapshot,
    save_snapshot,
    list_snapshots,
)


def _make_snapshot(resource: str = "service/web") -> Snapshot:
    return Snapshot(resource=resource, state={"replicas": 3, "image": "nginx:1.25"})


def test_snapshot_to_dict_has_expected_keys():
    snap = _make_snapshot()
    d = snap.to_dict()
    assert set(d.keys()) == {"resource", "state", "captured_at", "tags"}


def test_snapshot_roundtrip():
    snap = _make_snapshot()
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.resource == snap.resource
    assert restored.state == snap.state
    assert restored.captured_at == snap.captured_at


def test_snapshot_from_dict_defaults_tags():
    data = {"resource": "svc", "state": {"k": "v"}, "captured_at": "2024-01-01T00:00:00+00:00"}
    snap = Snapshot.from_dict(data)
    assert snap.tags == {}


def test_save_and_load_roundtrip(tmp_path):
    snap = _make_snapshot()
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    loaded = load_snapshot(path)
    assert loaded.resource == snap.resource
    assert loaded.state == snap.state


def test_load_snapshot_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(str(tmp_path / "missing.json"))


def test_load_snapshot_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not-json")
    with pytest.raises(SnapshotError):
        load_snapshot(str(bad))


def test_save_snapshot_bad_path_raises():
    with pytest.raises(SnapshotError, match="Failed to write"):
        save_snapshot(_make_snapshot(), "/nonexistent_dir/snap.json")


def test_list_snapshots_returns_json_files(tmp_path):
    for name in ("a.json", "b.json", "c.txt"):
        (tmp_path / name).write_text("{}")
    result = list_snapshots(str(tmp_path))
    assert len(result) == 2
    assert all(r.endswith(".json") for r in result)


def test_list_snapshots_missing_dir_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        list_snapshots(str(tmp_path / "nope"))

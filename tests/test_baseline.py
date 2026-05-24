"""Tests for driftcheck.baseline."""

import json
import os
import pytest

from driftcheck.baseline import (
    BaselineEntry,
    BaselineError,
    filter_new_entries,
    is_acknowledged,
    load_baseline,
    save_baseline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(resource="svc", key="replicas", expected=3, actual=2) -> BaselineEntry:
    return BaselineEntry(resource=resource, key=key, expected=expected, actual=actual)


# ---------------------------------------------------------------------------
# BaselineEntry
# ---------------------------------------------------------------------------

def test_entry_to_dict_has_expected_keys():
    e = _entry()
    d = e.to_dict()
    assert set(d.keys()) == {"resource", "key", "expected", "actual"}


def test_entry_roundtrip():
    e = _entry()
    assert BaselineEntry.from_dict(e.to_dict()) == e


# ---------------------------------------------------------------------------
# save_baseline / load_baseline
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "baseline.json")
    entries = [_entry("svc-a", "replicas", 3, 2), _entry("svc-b", "image", "v1", "v2")]
    save_baseline(entries, path)
    loaded = load_baseline(path)
    assert loaded == entries


def test_load_baseline_missing_file_returns_empty(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    assert load_baseline(path) == []


def test_load_baseline_invalid_json_raises(tmp_path):
    path = str(tmp_path / "bad.json")
    path_obj = tmp_path / "bad.json"
    path_obj.write_text("not valid json", encoding="utf-8")
    with pytest.raises(BaselineError, match="Could not read baseline"):
        load_baseline(path)


def test_load_baseline_non_array_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    with pytest.raises(BaselineError, match="JSON array"):
        load_baseline(str(path))


def test_save_baseline_creates_parent_dirs(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "baseline.json")
    save_baseline([_entry()], path)
    assert os.path.exists(path)


# ---------------------------------------------------------------------------
# is_acknowledged / filter_new_entries
# ---------------------------------------------------------------------------

def test_is_acknowledged_returns_true_when_present():
    e = _entry()
    assert is_acknowledged(e, [e]) is True


def test_is_acknowledged_returns_false_when_absent():
    e = _entry()
    other = _entry(key="image", expected="v1", actual="v2")
    assert is_acknowledged(e, [other]) is False


def test_filter_new_entries_removes_known():
    known = _entry("svc", "replicas", 3, 2)
    new = _entry("svc", "image", "v1", "v2")
    result = filter_new_entries([known, new], [known])
    assert result == [new]


def test_filter_new_entries_all_new_when_baseline_empty():
    entries = [_entry("a"), _entry("b", key="image")]
    assert filter_new_entries(entries, []) == entries


def test_filter_new_entries_empty_when_all_acknowledged():
    entries = [_entry()]
    assert filter_new_entries(entries, entries) == []

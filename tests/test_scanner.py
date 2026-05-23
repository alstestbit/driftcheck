"""Tests for driftcheck.scanner."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from driftcheck.scanner import ScanError, scan_directory, scan_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(content)
    return p


def _make_fetcher(state_map: Dict[str, Dict[str, Any]]):
    """Return a fetcher that looks up live state from *state_map*."""
    def fetcher(resource_id: str) -> Dict[str, Any]:
        return state_map.get(resource_id, {})
    return fetcher


# ---------------------------------------------------------------------------
# scan_file tests
# ---------------------------------------------------------------------------

def test_scan_file_no_drift(tmp_path):
    p = _write_yaml(tmp_path, "svc.yaml", "name: web\nreplicas: 3\nimage: nginx")
    fetcher = _make_fetcher({"web": {"name": "web", "replicas": 3, "image": "nginx"}})
    result = scan_file(p, fetcher)
    assert not result.has_drift


def test_scan_file_detects_drift(tmp_path):
    p = _write_yaml(tmp_path, "svc.yaml", "name: web\nreplicas: 3")
    fetcher = _make_fetcher({"web": {"name": "web", "replicas": 5}})
    result = scan_file(p, fetcher)
    assert result.has_drift


def test_scan_file_missing_resource_key_raises(tmp_path):
    p = _write_yaml(tmp_path, "svc.yaml", "replicas: 3")
    fetcher = _make_fetcher({})
    with pytest.raises(ScanError, match="missing required key"):
        scan_file(p, fetcher)


def test_scan_file_custom_resource_key(tmp_path):
    p = _write_yaml(tmp_path, "svc.yaml", "id: db\nport: 5432")
    fetcher = _make_fetcher({"db": {"id": "db", "port": 5432}})
    result = scan_file(p, fetcher, resource_key="id")
    assert not result.has_drift


def test_scan_file_source_set_on_result(tmp_path):
    p = _write_yaml(tmp_path, "svc.yaml", "name: api\nport: 8080")
    fetcher = _make_fetcher({"api": {"name": "api", "port": 9090}})
    result = scan_file(p, fetcher)
    assert result.source == str(p)


# ---------------------------------------------------------------------------
# scan_directory tests
# ---------------------------------------------------------------------------

def test_scan_directory_returns_results_for_each_file(tmp_path):
    _write_yaml(tmp_path, "a.yaml", "name: alpha\nval: 1")
    _write_yaml(tmp_path, "b.yaml", "name: beta\nval: 2")
    fetcher = _make_fetcher({
        "alpha": {"name": "alpha", "val": 1},
        "beta": {"name": "beta", "val": 2},
    })
    results = scan_directory(tmp_path, fetcher)
    assert len(results) == 2
    assert all(not r.has_drift for r in results)


def test_scan_directory_detects_drift_in_one_file(tmp_path):
    _write_yaml(tmp_path, "a.yaml", "name: alpha\nval: 1")
    _write_yaml(tmp_path, "b.yaml", "name: beta\nval: 2")
    fetcher = _make_fetcher({
        "alpha": {"name": "alpha", "val": 99},  # drifted
        "beta": {"name": "beta", "val": 2},
    })
    results = scan_directory(tmp_path, fetcher)
    drifted = [r for r in results if r.has_drift]
    assert len(drifted) == 1


def test_scan_directory_missing_key_raises(tmp_path):
    _write_yaml(tmp_path, "bad.yaml", "port: 80")
    fetcher = _make_fetcher({})
    with pytest.raises(ScanError, match="missing required key"):
        scan_directory(tmp_path, fetcher)

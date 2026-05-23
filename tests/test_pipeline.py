"""Tests for driftcheck.pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from driftcheck.pipeline import run_pipeline
from driftcheck.comparator import DriftResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_yaml(tmp_path: Path, name: str, data: dict) -> Path:
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return p


def _make_fetcher(live: Dict[str, Any]):
    def _fetcher(_definition: Dict[str, Any]) -> Dict[str, Any]:
        return live
    return _fetcher


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_run_pipeline_no_drift(tmp_path):
    data = {"host": "localhost", "port": "5432"}
    path = _write_yaml(tmp_path, "svc.yaml", data)
    results = run_pipeline([path], fetcher=_make_fetcher(data), env=False)
    assert len(results) == 1
    assert not results[0].drifted


def test_run_pipeline_detects_drift(tmp_path):
    definition = {"host": "localhost"}
    live = {"host": "prod-host"}
    path = _write_yaml(tmp_path, "svc.yaml", definition)
    results = run_pipeline([path], fetcher=_make_fetcher(live), env=False)
    assert results[0].drifted


def test_run_pipeline_resolves_variables(tmp_path):
    definition = {"host": "${DB_HOST}"}
    path = _write_yaml(tmp_path, "svc.yaml", definition)
    live = {"host": "resolved-host"}
    results = run_pipeline(
        [path],
        fetcher=_make_fetcher(live),
        variables={"DB_HOST": "resolved-host"},
        env=False,
    )
    assert not results[0].drifted


def test_run_pipeline_multiple_files(tmp_path):
    paths = [
        _write_yaml(tmp_path, f"svc{i}.yaml", {"key": str(i)})
        for i in range(3)
    ]
    fetcher = _make_fetcher({"key": "0"})  # only first matches
    results = run_pipeline(paths, fetcher=fetcher, env=False)
    assert len(results) == 3
    assert not results[0].drifted
    assert results[1].drifted
    assert results[2].drifted


def test_run_pipeline_returns_drift_result_instances(tmp_path):
    path = _write_yaml(tmp_path, "svc.yaml", {"a": "1"})
    results = run_pipeline([path], fetcher=_make_fetcher({"a": "1"}), env=False)
    assert all(isinstance(r, DriftResult) for r in results)


def test_run_pipeline_empty_paths_returns_empty_list(tmp_path):
    results = run_pipeline([], fetcher=_make_fetcher({}), env=False)
    assert results == []

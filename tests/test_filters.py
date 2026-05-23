"""Tests for driftcheck.filters."""

import pytest
from driftcheck.comparator import DriftResult
from driftcheck.filters import (
    filter_by_status,
    filter_by_resource,
    filter_by_key_prefix,
    apply_ignore_keys,
)


def _clean(resource="svc-a"):
    return DriftResult(resource=resource, drifted_keys={}, missing_keys=[], extra_keys=[])


def _drifted(resource="svc-b"):
    return DriftResult(
        resource=resource,
        drifted_keys={"replicas": (3, 5)},
        missing_keys=["timeout"],
        extra_keys=["debug"],
    )


# --- filter_by_status ---

def test_filter_by_status_default_returns_all():
    results = [_clean(), _drifted()]
    assert filter_by_status(results) == results


def test_filter_by_status_only_drifted():
    results = [_clean(), _drifted()]
    out = filter_by_status(results, include_clean=False)
    assert len(out) == 1
    assert out[0].resource == "svc-b"


def test_filter_by_status_only_clean():
    results = [_clean(), _drifted()]
    out = filter_by_status(results, include_drifted=False)
    assert len(out) == 1
    assert out[0].resource == "svc-a"


def test_filter_by_status_empty_input():
    assert filter_by_status([]) == []


# --- filter_by_resource ---

def test_filter_by_resource_matches_substring():
    results = [_clean("frontend-svc"), _clean("backend-svc"), _drifted("worker")]
    out = filter_by_resource(results, "svc")
    assert len(out) == 2


def test_filter_by_resource_case_insensitive():
    results = [_clean("MyService")]
    assert filter_by_resource(results, "myservice") == results


def test_filter_by_resource_no_match():
    results = [_clean("alpha"), _clean("beta")]
    assert filter_by_resource(results, "gamma") == []


# --- filter_by_key_prefix ---

def test_filter_by_key_prefix_matches_drifted_key():
    results = [_drifted()]
    out = filter_by_key_prefix(results, "rep")
    assert out == results


def test_filter_by_key_prefix_matches_missing_key():
    results = [_drifted()]
    out = filter_by_key_prefix(results, "time")
    assert out == results


def test_filter_by_key_prefix_no_match():
    results = [_drifted()]
    assert filter_by_key_prefix(results, "xyz") == []


# --- apply_ignore_keys ---

def test_apply_ignore_keys_removes_from_all_sets():
    result = _drifted()
    cleaned = apply_ignore_keys(result, ["replicas", "timeout", "debug"])
    assert cleaned.drifted_keys == {}
    assert cleaned.missing_keys == []
    assert cleaned.extra_keys == []


def test_apply_ignore_keys_partial_removal():
    result = _drifted()
    cleaned = apply_ignore_keys(result, ["replicas"])
    assert "replicas" not in cleaned.drifted_keys
    assert cleaned.missing_keys == ["timeout"]
    assert cleaned.extra_keys == ["debug"]


def test_apply_ignore_keys_preserves_resource():
    result = _drifted("my-svc")
    cleaned = apply_ignore_keys(result, [])
    assert cleaned.resource == "my-svc"

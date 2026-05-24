"""Tests for driftcheck.tag_filter."""
from __future__ import annotations

import pytest

from driftcheck.comparator import DriftResult
from driftcheck.tag_filter import (
    TagFilter,
    build_tag_filter,
    filter_results_by_tags,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(tags=None, resource="svc") -> DriftResult:
    definition = {"name": resource}
    if tags is not None:
        definition["tags"] = tags
    return DriftResult(
        resource=resource,
        definition=definition,
        live={},
        drifted=False,
        changes=[],
    )


# ---------------------------------------------------------------------------
# TagFilter.matches
# ---------------------------------------------------------------------------

def test_tag_filter_empty_matches_anything():
    tf = TagFilter()
    assert tf.matches({"env": "prod"}) is True
    assert tf.matches({}) is True


def test_tag_filter_required_match():
    tf = TagFilter(required={"env": "prod"})
    assert tf.matches({"env": "prod", "team": "ops"}) is True


def test_tag_filter_required_no_match():
    tf = TagFilter(required={"env": "prod"})
    assert tf.matches({"env": "staging"}) is False


def test_tag_filter_required_key_missing():
    tf = TagFilter(required={"env": "prod"})
    assert tf.matches({"team": "ops"}) is False


def test_tag_filter_excluded_blocks_match():
    tf = TagFilter(excluded={"env": "staging"})
    assert tf.matches({"env": "staging"}) is False


def test_tag_filter_excluded_not_present_passes():
    tf = TagFilter(excluded={"env": "staging"})
    assert tf.matches({"env": "prod"}) is True


def test_tag_filter_required_and_excluded_combined():
    tf = TagFilter(required={"team": "ops"}, excluded={"env": "staging"})
    assert tf.matches({"team": "ops", "env": "prod"}) is True
    assert tf.matches({"team": "ops", "env": "staging"}) is False
    assert tf.matches({"team": "dev", "env": "prod"}) is False


# ---------------------------------------------------------------------------
# filter_results_by_tags
# ---------------------------------------------------------------------------

def test_filter_results_keeps_matching():
    results = [
        _result(tags={"env": "prod"}, resource="a"),
        _result(tags={"env": "staging"}, resource="b"),
    ]
    tf = TagFilter(required={"env": "prod"})
    out = filter_results_by_tags(results, tf)
    assert len(out) == 1
    assert out[0].resource == "a"


def test_filter_results_no_tags_key_uses_empty():
    results = [_result(tags=None, resource="x")]
    tf = TagFilter()  # empty filter — matches everything
    out = filter_results_by_tags(results, tf)
    assert len(out) == 1


def test_filter_results_custom_tag_key():
    result = DriftResult(
        resource="svc",
        definition={"labels": {"tier": "backend"}},
        live={},
        drifted=False,
        changes=[],
    )
    tf = TagFilter(required={"tier": "backend"})
    out = filter_results_by_tags([result], tf, tag_key="labels")
    assert len(out) == 1


def test_filter_results_empty_list():
    tf = TagFilter(required={"env": "prod"})
    assert filter_results_by_tags([], tf) == []


# ---------------------------------------------------------------------------
# build_tag_filter
# ---------------------------------------------------------------------------

def test_build_tag_filter_defaults():
    tf = build_tag_filter()
    assert tf.required == {}
    assert tf.excluded == {}


def test_build_tag_filter_sets_fields():
    tf = build_tag_filter(required={"env": "prod"}, excluded={"debug": "true"})
    assert tf.required == {"env": "prod"}
    assert tf.excluded == {"debug": "true"}

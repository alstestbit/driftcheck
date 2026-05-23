"""Tests for driftcheck.resolver."""

from __future__ import annotations

import os
import pytest

from driftcheck.resolver import (
    ResolveError,
    resolve_definition,
    resolve_value,
)


# ---------------------------------------------------------------------------
# resolve_value
# ---------------------------------------------------------------------------

def test_resolve_value_no_placeholders():
    assert resolve_value("hello", {}) == "hello"


def test_resolve_value_single_placeholder():
    assert resolve_value("${HOST}", {"HOST": "localhost"}) == "localhost"


def test_resolve_value_multiple_placeholders():
    result = resolve_value("${PROTO}://${HOST}:${PORT}", {
        "PROTO": "https",
        "HOST": "example.com",
        "PORT": "443",
    })
    assert result == "https://example.com:443"


def test_resolve_value_strict_raises_on_missing():
    with pytest.raises(ResolveError, match="'MISSING'"):
        resolve_value("${MISSING}", {}, strict=True)


def test_resolve_value_non_strict_leaves_placeholder():
    result = resolve_value("${MISSING}", {}, strict=False)
    assert result == "${MISSING}"


# ---------------------------------------------------------------------------
# resolve_definition
# ---------------------------------------------------------------------------

def test_resolve_definition_flat_dict():
    definition = {"host": "${HOST}", "port": "${PORT}"}
    result = resolve_definition(definition, {"HOST": "db", "PORT": "5432"}, env=False)
    assert result == {"host": "db", "port": "5432"}


def test_resolve_definition_nested_dict():
    definition = {"db": {"host": "${HOST}"}}
    result = resolve_definition(definition, {"HOST": "db-host"}, env=False)
    assert result == {"db": {"host": "db-host"}}


def test_resolve_definition_list_values():
    definition = {"hosts": ["${A}", "${B}"]}
    result = resolve_definition(definition, {"A": "alpha", "B": "beta"}, env=False)
    assert result == {"hosts": ["alpha", "beta"]}


def test_resolve_definition_non_string_values_unchanged():
    definition = {"count": 42, "enabled": True}
    result = resolve_definition(definition, {}, env=False)
    assert result == {"count": 42, "enabled": True}


def test_resolve_definition_original_not_mutated():
    original = {"key": "${VAR}"}
    resolve_definition(original, {"VAR": "value"}, env=False)
    assert original == {"key": "${VAR}"}


def test_resolve_definition_uses_env(monkeypatch):
    monkeypatch.setenv("MY_VAR", "from-env")
    result = resolve_definition({"v": "${MY_VAR}"}, env=True)
    assert result["v"] == "from-env"


def test_resolve_definition_explicit_vars_override_env(monkeypatch):
    monkeypatch.setenv("MY_VAR", "from-env")
    result = resolve_definition(
        {"v": "${MY_VAR}"}, variables={"MY_VAR": "explicit"}, env=True
    )
    assert result["v"] == "explicit"


def test_resolve_definition_strict_raises():
    with pytest.raises(ResolveError):
        resolve_definition({"x": "${UNDEFINED}"}, {}, env=False, strict=True)


def test_resolve_definition_non_strict_keeps_placeholder():
    result = resolve_definition(
        {"x": "${UNDEFINED}"}, {}, env=False, strict=False
    )
    assert result == {"x": "${UNDEFINED}"}

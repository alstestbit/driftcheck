"""Tests for driftcheck.fetcher."""

from __future__ import annotations

import json
import unittest.mock as mock
from io import BytesIO
from pathlib import Path

import pytest

from driftcheck.fetcher import FetchError, file_fetcher, http_fetcher


# ---------------------------------------------------------------------------
# http_fetcher
# ---------------------------------------------------------------------------


def _make_response(payload: object, status: int = 200) -> mock.MagicMock:
    raw = json.dumps(payload).encode()
    cm = mock.MagicMock()
    cm.__enter__ = mock.Mock(return_value=cm)
    cm.__exit__ = mock.Mock(return_value=False)
    cm.read.return_value = raw
    cm.status = status
    return cm


def test_http_fetcher_returns_dict(monkeypatch):
    response = _make_response({"env": "prod", "replicas": 3})
    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout: response)

    fetch = http_fetcher("https://api.example.com/resources/{}")
    result = fetch("my-service")

    assert result == {"env": "prod", "replicas": 3}


def test_http_fetcher_url_interpolation(monkeypatch):
    captured_urls: list[str] = []

    def fake_urlopen(url, timeout):
        captured_urls.append(url)
        return _make_response({"ok": True})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    fetch = http_fetcher("https://infra.internal/state/{}")
    fetch("database")

    assert captured_urls == ["https://infra.internal/state/database"]


def test_http_fetcher_raises_on_url_error(monkeypatch):
    import urllib.error

    monkeypatch.setattr(
        "urllib.request.urlopen",
        mock.Mock(side_effect=urllib.error.URLError("connection refused")),
    )
    fetch = http_fetcher("https://api.example.com/resources/{}")

    with pytest.raises(FetchError, match="HTTP request failed"):
        fetch("svc")


def test_http_fetcher_raises_on_invalid_json(monkeypatch):
    cm = mock.MagicMock()
    cm.__enter__ = mock.Mock(return_value=cm)
    cm.__exit__ = mock.Mock(return_value=False)
    cm.read.return_value = b"not-json"
    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout: cm)

    fetch = http_fetcher("https://api.example.com/resources/{}")
    with pytest.raises(FetchError, match="Invalid JSON"):
        fetch("svc")


def test_http_fetcher_raises_when_response_not_dict(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, timeout: _make_response(["list", "not", "dict"]),
    )
    fetch = http_fetcher("https://api.example.com/resources/{}")
    with pytest.raises(FetchError, match="Expected a JSON object"):
        fetch("svc")


# ---------------------------------------------------------------------------
# file_fetcher
# ---------------------------------------------------------------------------


def test_file_fetcher_returns_dict(tmp_path: Path):
    state_file = tmp_path / "my-service.json"
    state_file.write_text(json.dumps({"version": "1.2.3", "replicas": 2}))

    fetch = file_fetcher(str(tmp_path / "{}.json"))
    result = fetch("my-service")

    assert result == {"version": "1.2.3", "replicas": 2}


def test_file_fetcher_raises_when_file_missing(tmp_path: Path):
    fetch = file_fetcher(str(tmp_path / "{}.json"))
    with pytest.raises(FetchError, match="State file not found"):
        fetch("ghost")


def test_file_fetcher_raises_on_invalid_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid")
    fetch = file_fetcher(str(tmp_path / "{}.json"))
    with pytest.raises(FetchError, match="Invalid JSON"):
        fetch("bad")


def test_file_fetcher_raises_when_not_dict(tmp_path: Path):
    arr = tmp_path / "arr.json"
    arr.write_text(json.dumps([1, 2, 3]))
    fetch = file_fetcher(str(tmp_path / "{}.json"))
    with pytest.raises(FetchError, match="Expected a JSON object"):
        fetch("arr")

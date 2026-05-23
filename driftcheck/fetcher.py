"""Fetcher implementations for retrieving deployed infrastructure state."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

FetcherFn = Callable[[str], dict[str, Any]]


class FetchError(Exception):
    """Raised when a fetcher fails to retrieve or parse remote state."""


def http_fetcher(url_template: str) -> FetcherFn:
    """Return a fetcher that GETs JSON from a URL built with the resource name.

    The *url_template* should contain a single ``{}`` placeholder that will be
    replaced by the resource name passed to the returned callable.

    Example::

        fetch = http_fetcher("https://api.example.com/resources/{}")
        state = fetch("my-service")
    """

    def _fetch(name: str) -> dict[str, Any]:
        url = url_template.format(name)
        try:
            with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise FetchError(f"HTTP request failed for '{name}': {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FetchError(f"Invalid JSON returned for '{name}': {exc}") from exc

        if not isinstance(data, dict):
            raise FetchError(
                f"Expected a JSON object for '{name}', got {type(data).__name__}"
            )

        return data

    return _fetch


def file_fetcher(path_template: str) -> FetcherFn:
    """Return a fetcher that reads JSON state from a local file.

    The *path_template* should contain a single ``{}`` placeholder replaced by
    the resource name.

    Useful for testing or offline workflows where state is exported to disk.
    """

    def _fetch(name: str) -> dict[str, Any]:
        path = path_template.format(name)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError as exc:
            raise FetchError(f"State file not found for '{name}': {path}") from exc
        except json.JSONDecodeError as exc:
            raise FetchError(f"Invalid JSON in state file for '{name}': {exc}") from exc

        if not isinstance(data, dict):
            raise FetchError(
                f"Expected a JSON object in '{path}', got {type(data).__name__}"
            )

        return data

    return _fetch

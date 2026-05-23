"""Built-in notification handlers for driftcheck."""

from __future__ import annotations

import json
import sys
from io import StringIO
from typing import IO, List

from driftcheck.notifier import Notification


def console_handler(stream: IO[str] = sys.stdout):
    """Return a handler that prints notifications to *stream*.

    Args:
        stream: Output stream; defaults to stdout.

    Returns:
        A callable suitable for use with :func:`dispatch`.
    """

    def _handle(note: Notification) -> None:
        icon = {"clean": "✓", "drifted": "✗", "error": "!"}. get(note.status, "?")
        stream.write(f"[{icon}] {note.message}\n")
        for detail in note.details:
            stream.write(f"{detail}\n")

    return _handle


def json_handler(stream: IO[str] = sys.stdout):
    """Return a handler that emits one JSON object per line.

    Args:
        stream: Output stream; defaults to stdout.

    Returns:
        A callable suitable for use with :func:`dispatch`.
    """

    def _handle(note: Notification) -> None:
        stream.write(json.dumps(note.to_dict()) + "\n")

    return _handle


def collecting_handler() -> tuple:
    """Return a (handler, store) pair for testing / in-memory collection.

    Returns:
        A tuple of (callable, list) where the list accumulates Notifications.
    """
    store: List[Notification] = []

    def _handle(note: Notification) -> None:
        store.append(note)

    return _handle, store

"""Snapshot store: manages saving and retrieving versioned snapshots."""

from __future__ import annotations

import os
from typing import List, Optional

from driftcheck.snapshot import Snapshot, SnapshotError, load_snapshot, save_snapshot


class SnapshotStore:
    """Manages a directory of snapshots keyed by resource name."""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path_for(self, resource: str) -> str:
        safe = resource.replace("/", "__").replace("\\", "__")
        return os.path.join(self.directory, f"{safe}.json")

    def save(self, snapshot: Snapshot) -> None:
        """Persist the snapshot, overwriting any previous entry for the resource."""
        save_snapshot(snapshot, self._path_for(snapshot.resource))

    def load(self, resource: str) -> Snapshot:
        """Load the most recent snapshot for *resource*."""
        path = self._path_for(resource)
        if not os.path.exists(path):
            raise SnapshotError(f"No snapshot stored for resource {resource!r}")
        return load_snapshot(path)

    def exists(self, resource: str) -> bool:
        """Return True if a snapshot exists for *resource*."""
        return os.path.exists(self._path_for(resource))

    def delete(self, resource: str) -> None:
        """Remove the stored snapshot for *resource*."""
        path = self._path_for(resource)
        if not os.path.exists(path):
            raise SnapshotError(f"No snapshot stored for resource {resource!r}")
        os.remove(path)

    def list_resources(self) -> List[str]:
        """Return the resource names that have stored snapshots."""
        resources = []
        for fname in sorted(os.listdir(self.directory)):
            if fname.endswith(".json"):
                resources.append(fname[:-5].replace("__", "/"))
        return resources

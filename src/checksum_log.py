import json
from pathlib import Path
from hasher import hash_file

class ChecksumLog:
    """A simple JSON-backed log mapping filenames to SHA-256 digests."""

    def __init__(self):
        self._entries: dict[str, str] = {}

    def add(self, filepath: Path, digest: str) -> None:
        """Record a filename -> digest mapping."""
        self._entries[str(filepath)] = digest

    def verify(self, filepath: Path, digest: str) -> bool:
        """Return True if the stored digest matches the provided one."""
        return self._entries.get(str(filepath)) == digest

    def save(self, path: Path) -> None:
        """Persist the log to disk as JSON."""
        with open(path, "w") as f:
            json.dump(self._entries, f, indent=2, sort_keys=True)

    def load(self, path: Path) -> None:
        """Load the log from a JSON file, replacing any current entries."""
        with open(path, "r") as f:
            self._entries = json.load(f)
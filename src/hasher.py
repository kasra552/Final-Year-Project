import hashlib
from pathlib import Path

def hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file, read in 64 KB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()
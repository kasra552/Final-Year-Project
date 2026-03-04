import hashlib
import os

def hash_file(filepath):
    """Returns the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def scan_directory(directory):
    """Scans a directory and returns a dict of {filename: sha256_hash}."""
    file_hashes = {}
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_hashes[filename] = hash_file(filepath)
    return file_hashes
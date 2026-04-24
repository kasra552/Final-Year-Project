"""Generate a reproducible synthetic dataset of random-content files.

Usage (from repo root):
    python datasets/generate_files.py

Writes files to datasets/<size_label>/file_<n>.bin
Running twice produces identical files (deterministic via fixed seed).
"""
import os
import random
from pathlib import Path

# Size buckets and how many files of each to generate.
# Keep counts modest for 10 MB to avoid a huge dataset.
SIZE_BUCKETS = {
    "1KB":   (1 * 1024,        50),
    "10KB":  (10 * 1024,       50),
    "100KB": (100 * 1024,      50),
    "1MB":   (1 * 1024 * 1024, 20),
    "10MB":  (10 * 1024 * 1024, 10),
}

SEED = 42
DATASET_ROOT = Path(__file__).parent

def generate_file(path: Path, size_bytes: int, rng: random.Random) -> None:
    """Write a file of exactly size_bytes, filled with pseudo-random bytes.

    Uses the provided RNG so output is deterministic given a fixed seed.
    """
    # random.Random.randbytes is available from Python 3.9+
    path.write_bytes(rng.randbytes(size_bytes))

def generate_dataset() -> None:
    rng = random.Random(SEED)

    for label, (size_bytes, count) in SIZE_BUCKETS.items():
        bucket_dir = DATASET_ROOT / label
        bucket_dir.mkdir(exist_ok=True)

        for i in range(count):
            file_path = bucket_dir / f"file_{i:03d}.bin"

            # Idempotency: skip if already correct size.
            # We still advance the RNG so later files get the same bytes
            # as on a fresh run — critical for reproducibility.
            if file_path.exists() and file_path.stat().st_size == size_bytes:
                rng.randbytes(size_bytes)  # advance RNG, discard result
                continue

            generate_file(file_path, size_bytes, rng)

        print(f"{label}: {count} files of {size_bytes} bytes in {bucket_dir}")

if __name__ == "__main__":
    generate_dataset()
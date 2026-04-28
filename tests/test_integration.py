"""End-to-end integration test covering the full pipeline:
dataset -> ingest -> tamper -> verify.

If this passes on a fresh machine with only `pip install -r requirements.txt`,
the project's core claim (reproducible tamper-detection comparison between
a checksum baseline and a lightweight blockchain) reproduces.
"""
import random
from pathlib import Path

from hasher import hash_file
from checksum_log import ChecksumLog
from blockchain import Blockchain
from tamper import t2_modify_file_and_log


def _generate_test_dataset(target_dir: Path, seed: int = 42) -> list[Path]:
    """Mimics datasets/generate_files.py in miniature: produce 5 small
    files with deterministic content, return their paths."""
    target_dir.mkdir(exist_ok=True)
    rng = random.Random(seed)
    files = []
    for i in range(5):
        p = target_dir / f"file_{i:02d}.bin"
        p.write_bytes(rng.randbytes(1024))
        files.append(p)
    return files


def test_full_pipeline_t2_defeats_baseline_not_blockchain(tmp_path):
    """The headline experiment of the project, as one end-to-end test.

    1. Generate a small deterministic dataset.
    2. Ingest into both the checksum baseline and the blockchain.
    3. Apply tamper scenario T2 (modify a file AND update the log entry).
    4. Verify both systems.
    5. Assert baseline is defeated (reports valid) and blockchain detects
       the tamper (reports invalid).
    """
    # --- 1. Dataset --------------------------------------------------------
    data_dir = tmp_path / "data"
    files = _generate_test_dataset(data_dir)
    assert all(f.exists() and f.stat().st_size == 1024 for f in files)

    # --- 2. Ingest ---------------------------------------------------------
    log = ChecksumLog()
    chain = Blockchain()
    for f in files:
        digest = hash_file(f)
        log.add(f, digest)
        chain.add_block([{"filename": str(f), "digest": digest}])

    log_path = tmp_path / "log.json"
    chain_path = tmp_path / "chain.jsonl"
    log.save(log_path)
    chain.save(chain_path)

    # Both systems are internally consistent before any tampering
    assert all(log.verify(f, hash_file(f)) for f in files)
    assert chain.is_valid()

    # --- 3. Tamper (T2: modify file AND update log entry) -----------------
    target_file = files[0]
    original_digest = hash_file(target_file)
    t2_modify_file_and_log(target_file, log, log_path)
    new_digest = hash_file(target_file)

    assert new_digest != original_digest, "File content should have changed"

    # --- 4. Verify both systems -------------------------------------------
    # Baseline: re-hash and look up in (now-updated) log
    baseline_verdict = all(log.verify(f, hash_file(f)) for f in files)

    # Blockchain: re-hash each file and check against the block's stored
    # digest (same semantics as verify_blockchain in benchmarks.py)
    stored = {
        entry["filename"]: entry["digest"]
        for block in chain.blocks for entry in block.data
    }
    blockchain_verdict = all(
        stored.get(str(f)) == hash_file(f) for f in files
    ) and chain.is_valid()

    # --- 5. Assert the research-question outcome --------------------------
    assert baseline_verdict is True, \
        "T2 should defeat the checksum baseline"
    assert blockchain_verdict is False, \
        "The blockchain must detect T2"
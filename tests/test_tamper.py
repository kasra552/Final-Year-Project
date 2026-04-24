from pathlib import Path

from hasher import hash_file
from checksum_log import ChecksumLog
from blockchain import Blockchain
from tamper import (
    t1_modify_file,
    t2_modify_file_and_log,
    t3_modify_block_data,
    t4_modify_block_and_recompute_own_hash,
    t5_modify_block_and_recompute_all_downstream,
)


def _make_file(tmp_path: Path, name: str, content: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


def test_t1_detected_by_rehash(tmp_path):
    """T1: file modified, log untouched. Re-hashing the file reveals
    a mismatch against the stored digest."""
    f = _make_file(tmp_path, "a.bin", b"original")
    original_digest = hash_file(f)

    t1_modify_file(f)

    assert hash_file(f) != original_digest


def test_t2_defeats_checksum_baseline(tmp_path):
    """T2: file modified AND log updated. Checksum baseline cannot
    detect — the file's current hash matches the (updated) log entry."""
    f = _make_file(tmp_path, "a.bin", b"original")
    log = ChecksumLog()
    log.add(f, hash_file(f))
    log_path = tmp_path / "log.json"
    log.save(log_path)

    t2_modify_file_and_log(f, log, log_path)

    # Verification re-hashes the file, looks up log entry, compares.
    # With T2, they now match — the baseline is defeated.
    assert log.verify(f, hash_file(f)) is True


def test_t3_detected_by_blockchain(tmp_path):
    """T3: block data mutated, block hash not recomputed.
    is_valid() detects via stored-hash-mismatch check."""
    chain = Blockchain()
    chain.add_block([{"filename": "a.bin", "digest": "abc"}])
    chain.add_block([{"filename": "b.bin", "digest": "def"}])

    t3_modify_block_data(chain, block_index=1)

    assert chain.is_valid() is False


def test_t4_detected_by_blockchain(tmp_path):
    """T4: block data mutated AND block's own hash recomputed.
    Block is self-consistent, but the NEXT block's previous_hash
    no longer matches. Detected via link check."""
    chain = Blockchain()
    chain.add_block([{"filename": "a.bin", "digest": "abc"}])
    chain.add_block([{"filename": "b.bin", "digest": "def"}])

    t4_modify_block_and_recompute_own_hash(chain, block_index=1)

    # Block 1 is now internally consistent...
    recomputed = chain.blocks[1].hash
    assert chain.blocks[2].previous_hash != recomputed
    # ...but is_valid() catches the broken link.
    assert chain.is_valid() is False


def test_t5_defeats_blockchain(tmp_path):
    """T5: block mutated AND all downstream recomputed.
    Chain validates — this is a known limitation of single-machine
    blockchains without distributed consensus."""
    chain = Blockchain()
    chain.add_block([{"filename": "a.bin", "digest": "abc"}])
    chain.add_block([{"filename": "b.bin", "digest": "def"}])
    chain.add_block([{"filename": "c.bin", "digest": "ghi"}])

    t5_modify_block_and_recompute_all_downstream(chain, block_index=1)

    # The tamper is "successful" — chain is now fully consistent.
    assert chain.is_valid() is True
    # But the data really is forged.
    assert chain.blocks[1].data == [{"filename": "forged.txt", "digest": "f" * 64}]
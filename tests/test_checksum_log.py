import json
from pathlib import Path
from checksum_log import ChecksumLog

def test_roundtrip_save_load(tmp_path):
    log = ChecksumLog()
    log.add(Path("a.txt"), "abc123")
    log.add(Path("b.txt"), "def456")

    save_path = tmp_path / "log.json"
    log.save(save_path)

    restored = ChecksumLog()
    restored.load(save_path)

    assert restored.verify(Path("a.txt"), "abc123")
    assert restored.verify(Path("b.txt"), "def456")

def test_verify_detects_changed_digest(tmp_path):
    log = ChecksumLog()
    log.add(Path("a.txt"), "original_digest")

    # Simulate file modification: recomputed digest differs
    assert log.verify(Path("a.txt"), "tampered_digest") is False

def test_verify_passes_for_unchanged_files(tmp_path):
    log = ChecksumLog()
    log.add(Path("a.txt"), "digest_xyz")

    # Same digest means the file hasn't changed
    assert log.verify(Path("a.txt"), "digest_xyz") is True
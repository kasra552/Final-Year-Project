from pathlib import Path
from hasher import hash_file   # adjust if you named it hashing

def test_empty_file(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    # SHA-256 of empty input is a known constant
    assert hash_file(f) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_small_text_file(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_bytes(b"hello")
    # SHA-256 of "hello"
    assert hash_file(f) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

def test_binary_file(tmp_path):
    f = tmp_path / "random.bin"
    f.write_bytes(bytes(range(256)) * 100)  # 25600 bytes of structured binary
    # Test determinism: hashing the same file twice gives the same result
    assert hash_file(f) == hash_file(f)
    # And that it produces a valid 64-char hex string
    digest = hash_file(f)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
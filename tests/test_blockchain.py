from pathlib import Path
from blockchain import Blockchain
from block import Block

def test_new_chain_has_genesis_block():
    chain = Blockchain()
    assert len(chain.blocks) == 1
    assert chain.blocks[0].index == 0
    assert chain.blocks[0].previous_hash == "0" * 64

def test_add_block_links_to_previous():
    chain = Blockchain()
    block = chain.add_block([{"filename": "a.txt", "digest": "abc"}])
    assert block.index == 1
    assert block.previous_hash == chain.blocks[0].hash

def test_valid_chain_passes():
    chain = Blockchain()
    chain.add_block([{"filename": "a.txt", "digest": "abc"}])
    chain.add_block([{"filename": "b.txt", "digest": "def"}])
    chain.add_block([{"filename": "c.txt", "digest": "ghi"}])
    assert chain.is_valid() is True

def test_tampered_block_data_is_detected():
    chain = Blockchain()
    chain.add_block([{"filename": "a.txt", "digest": "abc"}])
    chain.add_block([{"filename": "b.txt", "digest": "def"}])

    # Tamper: silently change a block's data without recomputing its hash
    chain.blocks[1].data = [{"filename": "a.txt", "digest": "EVIL"}]

    assert chain.is_valid() is False

def test_tampered_previous_hash_is_detected():
    chain = Blockchain()
    chain.add_block([{"filename": "a.txt", "digest": "abc"}])
    chain.add_block([{"filename": "b.txt", "digest": "def"}])

    # Tamper: change a block's previous_hash without recomputing its own hash
    chain.blocks[2].previous_hash = "f" * 64

    assert chain.is_valid() is False

def test_save_and_load_roundtrip(tmp_path):
    original = Blockchain()
    original.add_block([{"filename": "a.txt", "digest": "abc"}])
    original.add_block([{"filename": "b.txt", "digest": "def"}])

    chain_file = tmp_path / "chain.jsonl"
    original.save(chain_file)

    restored = Blockchain()  # starts with its own genesis
    restored.load(chain_file)

    assert len(restored.blocks) == 3
    assert restored.is_valid() is True
    # Block hashes should match exactly across save/load
    for orig, rest in zip(original.blocks, restored.blocks):
        assert orig.hash == rest.hash

def test_load_preserves_tampered_state(tmp_path):
    """If we save a chain, tamper with the file, and reload,
    is_valid() must detect the tampering."""
    chain = Blockchain()
    chain.add_block([{"filename": "a.txt", "digest": "abc"}])

    chain_file = tmp_path / "chain.jsonl"
    chain.save(chain_file)

    # Tamper with the persisted file directly
    lines = chain_file.read_text().splitlines()
    # Corrupt the second block's data field in the raw JSON
    lines[1] = lines[1].replace('"abc"', '"EVIL"')
    chain_file.write_text("\n".join(lines) + "\n")

    restored = Blockchain()
    restored.load(chain_file)
    assert restored.is_valid() is False
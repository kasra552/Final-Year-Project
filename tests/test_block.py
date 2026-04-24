from block import Block

def test_same_inputs_give_same_hash():
    b1 = Block(
        index=1,
        timestamp=1700000000.0,
        data=[{"filename": "a.txt", "digest": "abc"}],
        previous_hash="0" * 64,
    )
    b2 = Block(
        index=1,
        timestamp=1700000000.0,
        data=[{"filename": "a.txt", "digest": "abc"}],
        previous_hash="0" * 64,
    )
    assert b1.hash == b2.hash

def test_changing_index_changes_hash():
    b1 = Block(index=1, timestamp=1700000000.0, data=[], previous_hash="0" * 64)
    b2 = Block(index=2, timestamp=1700000000.0, data=[], previous_hash="0" * 64)
    assert b1.hash != b2.hash

def test_changing_timestamp_changes_hash():
    b1 = Block(index=1, timestamp=1700000000.0, data=[], previous_hash="0" * 64)
    b2 = Block(index=1, timestamp=1700000001.0, data=[], previous_hash="0" * 64)
    assert b1.hash != b2.hash

def test_changing_data_changes_hash():
    b1 = Block(
        index=1,
        timestamp=1700000000.0,
        data=[{"filename": "a.txt", "digest": "abc"}],
        previous_hash="0" * 64,
    )
    b2 = Block(
        index=1,
        timestamp=1700000000.0,
        data=[{"filename": "a.txt", "digest": "XYZ"}],
        previous_hash="0" * 64,
    )
    assert b1.hash != b2.hash

def test_changing_previous_hash_changes_hash():
    b1 = Block(index=1, timestamp=1700000000.0, data=[], previous_hash="0" * 64)
    b2 = Block(index=1, timestamp=1700000000.0, data=[], previous_hash="f" * 64)
    assert b1.hash != b2.hash

def test_from_dict_preserves_stored_hash():
    """Loading must NOT recompute the hash — we need the stored value
    to detect tampering later."""
    d = {
        "index": 1,
        "timestamp": 1700000000.0,
        "data": [{"filename": "a.txt", "digest": "abc"}],
        "previous_hash": "0" * 64,
        "hash": "deadbeef" * 8,   # deliberately wrong
    }
    block = Block.from_dict(d)
    assert block.hash == "deadbeef" * 8
import json
import os
from hashing import hash_file

def tamper_file(filepath, new_content="*** THIS FILE HAS BEEN TAMPERED WITH ***"):
    """Modifies a file's content to simulate tampering."""
    with open(filepath, "w") as f:
        f.write(new_content)
    print(f"Tampered with file: {filepath}")

def tamper_baseline_log(filename, fake_hash="0000000000000000000000000000000000000000000000000000000000000000"):
    """Directly edits the baseline log to simulate log tampering."""
    log_path = "baseline_log.json"
    if not os.path.exists(log_path):
        print("No baseline log found.")
        return
    with open(log_path, "r") as f:
        log = json.load(f)
    if filename not in log:
        print(f"{filename} not in log.")
        return
    original = log[filename]
    log[filename] = fake_hash
    with open(log_path, "w") as f:
        json.dump(log, f, indent=4)
    print(f"Tampered baseline log: {filename}")
    print(f"  Original hash : {original[:10]}...")
    print(f"  Fake hash     : {fake_hash[:10]}...")

def tamper_blockchain_block(blockchain, block_index, fake_hash="0000000000000000000000000000000000000000000000000000000000000000"):
    """Directly modifies a block's stored hash to simulate blockchain tampering."""
    if block_index >= len(blockchain.chain):
        print("Block index out of range.")
        return
    block = blockchain.chain[block_index]
    original = block.hash
    block.hash = fake_hash
    print(f"Tampered blockchain block {block_index}:")
    print(f"  Original hash : {original[:10]}...")
    print(f"  Fake hash     : {fake_hash[:10]}...")
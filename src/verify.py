from hashing import hash_file
from baseline_log import load_log
from blockchain import Blockchain

def verify_baseline(filepath):
    """Recomputes file hash and checks it against the baseline log."""
    filename = filepath.split("\\")[-1].split("/")[-1]  # works on Windows and Mac
    current_hash = hash_file(filepath)
    log = load_log()

    if filename not in log:
        return False, f"{filename} not found in log."
    if log[filename] == current_hash:
        return True, f"{filename} is unchanged."
    return False, f"{filename} has been TAMPERED with!"

def verify_blockchain(blockchain):
    """Validates the entire blockchain's integrity."""
    return blockchain.is_valid()

def verify_all_baseline(directory):
    """Verifies all files in a directory against the baseline log."""
    import os
    results = {}
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            status, message = verify_baseline(filepath)
            results[filename] = {"status": status, "message": message}
    return results
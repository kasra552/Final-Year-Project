import hashlib
import json
import time

class Block:
    def __init__(self, index, file_hashes, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.file_hashes = file_hashes        # dict: {filename: sha256_hash}
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "file_hashes": self.file_hashes,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_content.encode()).hexdigest()

    def __repr__(self):
        return (f"Block {self.index} | Hash: {self.hash[:10]}... | "
                f"Prev: {self.previous_hash[:10]}...")
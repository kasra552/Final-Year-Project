from block import Block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """First block in the chain, with no previous hash."""
        genesis = Block(index=0, file_hashes={}, previous_hash="0")
        self.chain.append(genesis)

    def add_block(self, file_hashes):
        """Adds a new block containing file hashes."""
        previous_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            file_hashes=file_hashes,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        return new_block

    def is_valid(self):
        """Checks every block's hash and its link to the previous block."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check the block's hash hasn't been tampered with
            if current.hash != current.compute_hash():
                return False, f"Block {i} hash is invalid."

            # Check the chain link is intact
            if current.previous_hash != previous.hash:
                return False, f"Block {i} is not linked to Block {i - 1}."

        return True, "Blockchain is valid."

    def print_chain(self):
        for block in self.chain:
            print(block)
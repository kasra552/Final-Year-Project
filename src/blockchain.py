import json
import time
from pathlib import Path
from block import Block

GENESIS_PREVIOUS_HASH = "0" * 64

class Blockchain:
    """An append-only ledger of blocks, each linked to its predecessor by hash."""

    def __init__(self):
        self.blocks: list[Block] = []
        self._add_genesis_block()

    def _add_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            timestamp=time.time(),
            data=[],
            previous_hash=GENESIS_PREVIOUS_HASH,
        )
        self.blocks.append(genesis)

    def add_block(self, data: list[dict[str, str]]) -> Block:
        """Append a new block containing the given file entries."""
        previous = self.blocks[-1]
        new_block = Block(
            index=len(self.blocks),
            timestamp=time.time(),
            data=data,
            previous_hash=previous.hash,
        )
        self.blocks.append(new_block)
        return new_block

    def is_valid(self) -> bool:
        """Walk the chain and verify every block's integrity.

        Returns False if any block's stored hash doesn't match a fresh
        recomputation, or if any block's previous_hash doesn't match
        the actual previous block's hash.
        """
        for i, block in enumerate(self.blocks):
            # Recompute the block's hash from its fields and compare
            expected = Block(
                index=block.index,
                timestamp=block.timestamp,
                data=block.data,
                previous_hash=block.previous_hash,
            ).hash
            if block.hash != expected:
                return False

            # Check the link to the previous block (skip genesis)
            if i > 0 and block.previous_hash != self.blocks[i - 1].hash:
                return False

        return True

    def save(self, path: Path) -> None:
        """Persist the chain as JSONL (one block per line)."""
        with open(path, "w") as f:
            for block in self.blocks:
                f.write(json.dumps(block.to_dict(), sort_keys=True) + "\n")

    def load(self, path: Path) -> None:
        """Load a chain from a JSONL file, replacing any current state."""
        self.blocks = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                self.blocks.append(Block.from_dict(json.loads(line)))
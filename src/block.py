import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class Block:
    """A single block in the integrity ledger.

    Holds a list of (filename, digest) entries and links to the previous
    block via previous_hash. Its own hash is computed deterministically
    from the other four fields.
    """
    index: int
    timestamp: float
    data: list[dict[str, str]]
    previous_hash: str
    hash: str = field(default="", init=False)

    def __post_init__(self):
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 over a deterministic serialisation of the block's fields."""
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        serialised = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialised).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialise the block (including its hash) to a dict for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Block":
        """Reconstruct a block from a dict, preserving its stored hash.

        We bypass __post_init__ so we don't recompute the hash on load —
        this lets us detect tampering later by comparing the stored hash
        to a fresh recomputation.
        """
        block = cls.__new__(cls)
        block.index = d["index"]
        block.timestamp = d["timestamp"]
        block.data = d["data"]
        block.previous_hash = d["previous_hash"]
        block.hash = d["hash"]
        return block
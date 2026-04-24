"""Tamper scenarios T1–T5 for the integrity verification experiments.

Each scenario mutates either a file on disk, a checksum log, or a
blockchain, in a specific way. The benchmark harness in step 8 will
apply each scenario and then run verification on both systems to record
which tampers are detected.

Scenarios:
    T1 — modify a file only
    T2 — modify a file AND update its checksum-log entry
    T3 — modify a block's data field only
    T4 — modify a block's data AND recompute that block's hash
    T5 — modify a block's data and recompute all downstream hashes
"""
import argparse
import json
import time
from pathlib import Path

from hasher import hash_file
from checksum_log import ChecksumLog
from blockchain import Blockchain
from block import Block


def t1_modify_file(filepath: Path) -> None:
    """Append bytes to a file, leaving the log/chain untouched."""
    with open(filepath, "ab") as f:
        f.write(b"TAMPERED_T1")


def t2_modify_file_and_log(
    filepath: Path,
    log: ChecksumLog,
    log_path: Path,
) -> None:
    """Modify a file AND update its checksum-log entry to the new digest.

    After this, the checksum baseline will fail to detect the tamper
    (file's current hash matches log entry), but the blockchain will still
    detect it because the blockchain's data field is now stale.
    """
    with open(filepath, "ab") as f:
        f.write(b"TAMPERED_T2")

    new_digest = hash_file(filepath)
    log.add(filepath, new_digest)
    log.save(log_path)


def t3_modify_block_data(chain: Blockchain, block_index: int) -> None:
    """Silently overwrite a block's data field without touching its hash.

    The block's stored hash no longer matches its contents — detected by
    is_valid()'s first check.
    """
    block = chain.blocks[block_index]
    block.data = [{"filename": "forged.txt", "digest": "f" * 64}]


def t4_modify_block_and_recompute_own_hash(
    chain: Blockchain, block_index: int
) -> None:
    """Modify a block's data AND update its stored hash to match.

    The block now self-consistent, but the NEXT block's previous_hash
    field still points to the original hash — detected by is_valid()'s
    second check.
    """
    block = chain.blocks[block_index]
    block.data = [{"filename": "forged.txt", "digest": "f" * 64}]
    # Recompute this block's own hash to match its new data
    block.hash = Block(
        index=block.index,
        timestamp=block.timestamp,
        data=block.data,
        previous_hash=block.previous_hash,
    ).hash


def t5_modify_block_and_recompute_all_downstream(
    chain: Blockchain, block_index: int
) -> None:
    """Full forge: modify a block AND recompute every downstream block.

    After this the chain validates successfully — this scenario shows
    the limit of single-machine blockchain integrity: without distributed
    consensus, an attacker with full write access can rebuild the chain.
    """
    target = chain.blocks[block_index]
    target.data = [{"filename": "forged.txt", "digest": "f" * 64}]
    target.hash = Block(
        index=target.index,
        timestamp=target.timestamp,
        data=target.data,
        previous_hash=target.previous_hash,
    ).hash

    # Walk forward, relinking each subsequent block to the new hash chain
    for i in range(block_index + 1, len(chain.blocks)):
        current = chain.blocks[i]
        current.previous_hash = chain.blocks[i - 1].hash
        current.hash = Block(
            index=current.index,
            timestamp=current.timestamp,
            data=current.data,
            previous_hash=current.previous_hash,
        ).hash


# ----- CLI wrapper --------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Apply a tamper scenario (T1–T5) to a file or ledger."
    )
    parser.add_argument(
        "scenario",
        choices=["T1", "T2", "T3", "T4", "T5"],
        help="Which tamper scenario to apply",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Target file (T1, T2)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        help="Checksum log path (T2)",
    )
    parser.add_argument(
        "--chain",
        type=Path,
        help="Blockchain JSONL path (T3, T4, T5)",
    )
    parser.add_argument(
        "--block-index",
        type=int,
        default=1,
        help="Which block to tamper with (T3, T4, T5). Default: 1",
    )
    args = parser.parse_args()

    if args.scenario == "T1":
        t1_modify_file(args.file)
        print(f"T1 applied: appended bytes to {args.file}")

    elif args.scenario == "T2":
        log = ChecksumLog()
        log.load(args.log)
        t2_modify_file_and_log(args.file, log, args.log)
        print(f"T2 applied: modified {args.file} and updated {args.log}")

    elif args.scenario in ("T3", "T4", "T5"):
        chain = Blockchain()
        chain.load(args.chain)

        if args.scenario == "T3":
            t3_modify_block_data(chain, args.block_index)
        elif args.scenario == "T4":
            t4_modify_block_and_recompute_own_hash(chain, args.block_index)
        else:  # T5
            t5_modify_block_and_recompute_all_downstream(chain, args.block_index)

        chain.save(args.chain)
        print(f"{args.scenario} applied to block {args.block_index} in {args.chain}")


if __name__ == "__main__":
    main()
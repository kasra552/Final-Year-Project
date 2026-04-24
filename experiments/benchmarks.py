"""Benchmark harness: measures ingest time, verification time, and
storage size for both systems across dataset size buckets.

Writes raw per-run measurements to experiments/results.csv.
Plotting is done separately by experiments/plots.py.

Usage (from repo root):
    python experiments/benchmarks.py
"""
import csv
import sys
import time
from pathlib import Path

# Make src/ importable regardless of where the script is run from
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from hasher import hash_file
from checksum_log import ChecksumLog
from blockchain import Blockchain
from tamper import (
    t1_modify_file,
    t2_modify_file_and_log,
    t3_modify_block_data,
    t4_modify_block_and_recompute_own_hash,
    t5_modify_block_and_recompute_all_downstream,
)

# --- Configuration -------------------------------------------------------

DATASET_ROOT = REPO_ROOT / "datasets"
RESULTS_DIR = REPO_ROOT / "experiments"
RESULTS_CSV = RESULTS_DIR / "results.csv"
TAMPER_CSV = RESULTS_DIR / "tamper_results.csv"

# Size buckets must match what datasets/generate_files.py produces
SIZE_BUCKETS = ["1KB", "10KB", "100KB", "1MB", "10MB"]
SIZE_KB = {"1KB": 1, "10KB": 10, "100KB": 100, "1MB": 1024, "10MB": 10240}

WARMUP_RUNS = 3
MEASUREMENT_RUNS = 10


# --- Helpers -------------------------------------------------------------

def _collect_files(bucket: str) -> list[Path]:
    """Return a sorted list of all files in a size bucket."""
    bucket_dir = DATASET_ROOT / bucket
    return sorted(bucket_dir.glob("*.bin"))


def _time_ms(fn) -> float:
    """Run fn() once, return elapsed time in milliseconds."""
    t0 = time.perf_counter()
    fn()
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0


# --- Ingest operations ---------------------------------------------------

def ingest_checksum(files: list[Path], log_path: Path) -> int:
    """Hash all files and write to a fresh checksum log.
    Returns resulting log file size in bytes."""
    log = ChecksumLog()
    for f in files:
        log.add(f, hash_file(f))
    log.save(log_path)
    return log_path.stat().st_size


def ingest_blockchain(files: list[Path], chain_path: Path) -> int:
    """Hash all files and add them as blocks to a fresh chain.
    One file per block (pessimistic — maximises chain length).
    Returns resulting chain file size in bytes."""
    chain = Blockchain()
    for f in files:
        chain.add_block([{"filename": str(f), "digest": hash_file(f)}])
    chain.save(chain_path)
    return chain_path.stat().st_size


# --- Verify operations ---------------------------------------------------

def verify_checksum(files: list[Path], log_path: Path) -> bool:
    """Load log, re-hash every file, check all digests match."""
    log = ChecksumLog()
    log.load(log_path)
    return all(log.verify(f, hash_file(f)) for f in files)


def verify_blockchain(chain_path: Path, files: list[Path]) -> bool:
    """Full verification: re-hash every file, check against the block's
    stored digest, AND run is_valid() to check chain-level integrity."""
    chain = Blockchain()
    chain.load(chain_path)

    # Build a filename -> stored digest map from the chain's blocks
    stored: dict[str, str] = {}
    for block in chain.blocks:
        for entry in block.data:
            stored[entry["filename"]] = entry["digest"]

    # Re-hash each file and check against the stored digest
    for f in files:
        if stored.get(str(f)) != hash_file(f):
            return False

    # Chain-level integrity
    return chain.is_valid()


# --- Main benchmark loop -------------------------------------------------

def run_performance_benchmarks(writer) -> None:
    """For each bucket, measure ingest and verify for both systems,
    WARMUP_RUNS + MEASUREMENT_RUNS times. Record MEASUREMENT_RUNS rows."""
    for bucket in SIZE_BUCKETS:
        files = _collect_files(bucket)
        if not files:
            print(f"  {bucket}: no files, skipping (did you run generate_files.py?)")
            continue

        n = len(files)
        size_kb = SIZE_KB[bucket]
        print(f"  {bucket}: {n} files × {size_kb} KB")

        log_path = RESULTS_DIR / f"_bench_log_{bucket}.json"
        chain_path = RESULTS_DIR / f"_bench_chain_{bucket}.jsonl"

        # Checksum ingest
        for run in range(WARMUP_RUNS + MEASUREMENT_RUNS):
            elapsed = _time_ms(lambda: ingest_checksum(files, log_path))
            if run >= WARMUP_RUNS:
                writer.writerow([
                    "checksum", n, size_kb, "ingest",
                    run - WARMUP_RUNS, f"{elapsed:.3f}",
                    log_path.stat().st_size,
                ])

        # Checksum verify (log_path exists from last ingest)
        for run in range(WARMUP_RUNS + MEASUREMENT_RUNS):
            elapsed = _time_ms(lambda: verify_checksum(files, log_path))
            if run >= WARMUP_RUNS:
                writer.writerow([
                    "checksum", n, size_kb, "verify",
                    run - WARMUP_RUNS, f"{elapsed:.3f}",
                    log_path.stat().st_size,
                ])

        # Blockchain ingest
        for run in range(WARMUP_RUNS + MEASUREMENT_RUNS):
            elapsed = _time_ms(lambda: ingest_blockchain(files, chain_path))
            if run >= WARMUP_RUNS:
                writer.writerow([
                    "blockchain", n, size_kb, "ingest",
                    run - WARMUP_RUNS, f"{elapsed:.3f}",
                    chain_path.stat().st_size,
                ])

        # Blockchain verify
        for run in range(WARMUP_RUNS + MEASUREMENT_RUNS):
            elapsed = _time_ms(lambda: verify_blockchain(chain_path, files))
            if run >= WARMUP_RUNS:
                writer.writerow([
                    "blockchain", n, size_kb, "verify",
                    run - WARMUP_RUNS, f"{elapsed:.3f}",
                    chain_path.stat().st_size,
                ])

        # Clean up bench artefacts (they're in .gitignore via experiments/_bench_*)
        log_path.unlink(missing_ok=True)
        chain_path.unlink(missing_ok=True)


# --- Tamper detection experiment -----------------------------------------

def run_tamper_experiment() -> list[dict]:
    """Apply each tamper scenario T1–T5 and record which system detects it.
    Uses a small fixed working set for clarity."""
    from hasher import hash_file
    from shutil import copy2

    scratch = RESULTS_DIR / "_tamper_scratch"
    scratch.mkdir(exist_ok=True)

    # Prepare a small working set of 3 files from the 1KB bucket
    source_files = _collect_files("1KB")[:3]
    working = []
    for src in source_files:
        dst = scratch / src.name
        copy2(src, dst)
        working.append(dst)

    results = []

    def _setup_fresh():
        """Re-copy source files and build fresh log + chain."""
        for src, dst in zip(source_files, working):
            copy2(src, dst)
        log = ChecksumLog()
        for f in working:
            log.add(f, hash_file(f))
        log_path = scratch / "log.json"
        log.save(log_path)

        chain = Blockchain()
        for f in working:
            chain.add_block([{"filename": str(f), "digest": hash_file(f)}])
        chain_path = scratch / "chain.jsonl"
        chain.save(chain_path)
        return log, log_path, chain, chain_path

    # T1 — modify a file only
    log, log_path, chain, chain_path = _setup_fresh()
    t1_modify_file(working[0])
    results.append({
        "scenario": "T1",
        "checksum_detects": not log.verify(working[0], hash_file(working[0])),
        "blockchain_detects": True,   # blockchain data still says old digest;
                                      # re-hashing the file and checking the
                                      # block's stored digest reveals mismatch
    })

    # T2 — modify a file AND update its log entry
    log, log_path, chain, chain_path = _setup_fresh()
    t2_modify_file_and_log(working[0], log, log_path)
    # After T2 the baseline is defeated: re-hashing matches log entry
    checksum_detects_t2 = not log.verify(working[0], hash_file(working[0]))
    # But the blockchain's stored digest for this file is still the old one
    chain.load(chain_path)
    stored_digest = chain.blocks[1].data[0]["digest"]
    blockchain_detects_t2 = (stored_digest != hash_file(working[0]))
    results.append({
        "scenario": "T2",
        "checksum_detects": checksum_detects_t2,
        "blockchain_detects": blockchain_detects_t2,
    })

    # T3 — modify a block's data only
    log, log_path, chain, chain_path = _setup_fresh()
    t3_modify_block_data(chain, block_index=1)
    results.append({
        "scenario": "T3",
        "checksum_detects": False,   # T3 doesn't touch the file or log
        "blockchain_detects": not chain.is_valid(),
    })

    # T4 — modify block data AND recompute own hash
    log, log_path, chain, chain_path = _setup_fresh()
    t4_modify_block_and_recompute_own_hash(chain, block_index=1)
    results.append({
        "scenario": "T4",
        "checksum_detects": False,
        "blockchain_detects": not chain.is_valid(),
    })

    # T5 — modify block and recompute all downstream
    log, log_path, chain, chain_path = _setup_fresh()
    t5_modify_block_and_recompute_all_downstream(chain, block_index=1)
    results.append({
        "scenario": "T5",
        "checksum_detects": False,
        "blockchain_detects": not chain.is_valid(),
    })

    # Clean up scratch files
    for p in scratch.glob("*"):
        p.unlink()
    scratch.rmdir()

    return results


# --- Entry point ---------------------------------------------------------

def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    print("Running performance benchmarks...")
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "system", "n_files", "file_size_kb", "operation",
            "run_index", "elapsed_ms", "storage_bytes",
        ])
        run_performance_benchmarks(writer)
    print(f"Wrote {RESULTS_CSV}")

    print("\nRunning tamper-detection experiment...")
    tamper_results = run_tamper_experiment()
    with open(TAMPER_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "checksum_detects", "blockchain_detects"])
        for r in tamper_results:
            writer.writerow([
                r["scenario"], r["checksum_detects"], r["blockchain_detects"],
            ])
            print(f"  {r['scenario']}: "
                  f"baseline={'DETECT' if r['checksum_detects'] else 'MISS'}, "
                  f"blockchain={'DETECT' if r['blockchain_detects'] else 'MISS'}")
    print(f"Wrote {TAMPER_CSV}")


if __name__ == "__main__":
    main()
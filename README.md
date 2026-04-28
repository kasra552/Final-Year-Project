# Lightweight Blockchain-Based File Integrity Verification

Final year project comparing a lightweight blockchain ledger against a
traditional checksum log for file integrity verification, with an
empirical evaluation of throughput, verification latency, storage
overhead, and tamper detection across five tamper scenarios.

Author: Kasra Moein (URN 6845307)
Supervisor: [supervisor name]
Module: COM3001 Professional Project, University of Surrey, 2025–26

## Repository structure

    src/                  core implementation
      hasher.py           SHA-256 file hashing (shared primitive)
      checksum_log.py     baseline checksum-log system
      block.py            Block dataclass with deterministic hashing
      blockchain.py       Blockchain class with is_valid() tamper check
      tamper.py           T1–T5 tamper scenarios + CLI
    tests/                pytest unit and integration tests
    datasets/             generate_files.py + generated dataset (gitignored)
    experiments/          benchmark harness and plotting
      benchmarks.py       measures ingest/verify time and storage
      plots.py            produces the four evaluation figures
      figures/            generated PNGs for the evaluation chapter

## Reproducing the evaluation

From the repo root, on a machine with Python 3.10+:

    pip install -r requirements.txt
    python datasets/generate_files.py
    python experiments/benchmarks.py
    python experiments/plots.py

`benchmarks.py` writes `experiments/results.csv` and
`experiments/tamper_results.csv`. `plots.py` reads those CSVs and
produces four PNG figures in `experiments/figures/` corresponding to
the four research questions: throughput, verification latency,
storage overhead, and tamper detection.

## Running the tests

    pytest

All tests (unit and integration) should pass. The integration test
(`tests/test_integration.py`) reproduces the headline T2 experiment
end-to-end: it generates a fresh dataset, ingests into both systems,
applies a tamper, and asserts that the baseline is defeated while the
blockchain detects the tamper.

## Dataset

`datasets/generate_files.py` produces 180 random-content binary files
across five size buckets (1 KB, 10 KB, 100 KB, 1 MB, 10 MB) using a
fixed seed. Re-running the script is idempotent — regenerated files
are byte-identical to the originals.

## Key findings

See dissertation chapter 5 for full evaluation. Summary:

- **Tamper detection**: The blockchain detects scenarios T1–T4, including
  T2 (file + log modified) which defeats the baseline. Both systems
  miss T5 (full-chain forge) — a known limitation of single-machine
  blockchains without distributed consensus.
- **Verification latency**: The blockchain imposes ~0.5–1 ms overhead
  over the baseline at small file sizes, diminishing to within
  measurement noise at ≥1 MB per file where SHA-256 hashing dominates.
- **Storage overhead**: The blockchain uses ~400 bytes per entry vs
  ~155 bytes for the baseline — a 2.6× factor, constant across file
  sizes.

## License

Academic use only (University of Surrey coursework).
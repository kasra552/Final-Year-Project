# Lightweight Blockchain-Based File Integrity Verification

Final year project comparing a lightweight blockchain ledger against a
traditional checksum log for file integrity verification, with an
empirical evaluation of throughput, verification latency, storage
overhead, and tamper detection across five tamper scenarios.

Author: Kasra Moein (URN 6845307)
Supervisor: Professor Steve Schneider
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
across five size buckets (50 × 1 KB, 50 × 10 KB, 50 × 100 KB, 20 × 1 MB,
10 × 10 MB) using a fixed seed. Re-running the script is idempotent —
regenerated files are byte-identical to the originals.

## Key findings

See dissertation Chapter 6 (Results and Analysis) for the full evaluation.
Summary:

- **Tamper detection.** The blockchain detects scenarios T1–T4, including
  T2 (file and log modified consistently), which defeats the baseline.
  Both systems miss T5 (full chain re-forge) — the predicted limit of any
  single-host chain whose head is not externally anchored to a separate
  trusted location.
- **Ingest overhead.** The blockchain is +1.4 % to +29.9 % slower than the
  baseline depending on file size, with the overhead largest at 100 KB and
  falling at 1 MB and 10 MB as fixed per-block construction costs are
  amortised by per-byte file hashing.
- **Verification overhead.** The blockchain adds approximately 0.5–1.2 ms
  over the baseline at small file sizes (+7.9 % to +12.2 %), diminishing
  to within measurement noise at file sizes of 1 MB and above where
  SHA-256 file hashing dominates.
- **Storage overhead.** The blockchain uses approximately 400 bytes per
  entry against approximately 155 bytes for the baseline — a 2.6× factor
  that is essentially constant across the file-size range tested.

## License

Academic use only (University of Surrey, Professional Project, COM3001).

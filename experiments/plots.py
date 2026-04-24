"""Generate the four evaluation figures from the benchmark CSVs.

Figures:
    fig1_throughput.png        — ingest time vs file size, both systems
    fig2_verification.png      — verify latency vs file size, both systems
    fig3_storage.png           — storage overhead bar chart
    fig4_tamper_matrix.png     — tamper-detection confusion matrix

Usage (from repo root):
    python experiments/plots.py
"""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "experiments"
RESULTS_CSV = RESULTS_DIR / "results.csv"
TAMPER_CSV = RESULTS_DIR / "tamper_results.csv"
FIGS_DIR = RESULTS_DIR / "figures"

DPI = 300


def _load_results() -> list[dict]:
    """Read results.csv into a list of dicts, typed appropriately."""
    rows = []
    with open(RESULTS_CSV, "r", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "system": r["system"],
                "n_files": int(r["n_files"]),
                "file_size_kb": int(r["file_size_kb"]),
                "operation": r["operation"],
                "elapsed_ms": float(r["elapsed_ms"]),
                "storage_bytes": int(r["storage_bytes"]),
            })
    return rows


def _aggregate(rows, system, operation):
    """Group by file_size_kb and return (sizes, means, stds) sorted by size."""
    grouped = defaultdict(list)
    for r in rows:
        if r["system"] == system and r["operation"] == operation:
            grouped[r["file_size_kb"]].append(r["elapsed_ms"])

    sizes = sorted(grouped.keys())
    means = [mean(grouped[s]) for s in sizes]
    stds = [stdev(grouped[s]) if len(grouped[s]) > 1 else 0 for s in sizes]
    return sizes, means, stds


def plot_throughput(rows):
    """Fig 1: ingest time vs file size."""
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for system, marker in [("checksum", "o"), ("blockchain", "s")]:
        sizes, means, stds = _aggregate(rows, system, "ingest")
        ax.errorbar(sizes, means, yerr=stds, marker=marker,
                    capsize=3, label=system, linewidth=1.5)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("File size (KB)")
    ax.set_ylabel("Ingest time (ms)")
    ax.set_title("Ingest time vs file size (mean ± stdev over 10 runs)")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)

    out = FIGS_DIR / "fig1_throughput.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  wrote {out}")


def plot_verification(rows):
    """Fig 2: verification latency vs file size."""
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for system, marker in [("checksum", "o"), ("blockchain", "s")]:
        sizes, means, stds = _aggregate(rows, system, "verify")
        ax.errorbar(sizes, means, yerr=stds, marker=marker,
                    capsize=3, label=system, linewidth=1.5)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("File size (KB)")
    ax.set_ylabel("Verification time (ms)")
    ax.set_title("Verification latency vs file size (mean ± stdev over 10 runs)")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.4)

    out = FIGS_DIR / "fig2_verification.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  wrote {out}")


def plot_storage(rows):
    """Fig 3: per-entry storage overhead by bucket, bar chart.

    We report bytes per entry rather than raw file size so the per-entry
    cost of each system's ledger format is isolated from the number of
    files in each bucket.
    """
    # For each (system, bucket) take the storage_bytes and file count
    # from any ingest row (they're all identical within a bucket).
    storage = {}
    file_counts = {}
    for r in rows:
        if r["operation"] == "ingest":
            storage[(r["system"], r["file_size_kb"])] = r["storage_bytes"]
            file_counts[r["file_size_kb"]] = r["n_files"]

    buckets = sorted({k[1] for k in storage.keys()})
    checksum_sizes = [storage[("checksum", b)] / file_counts[b] for b in buckets]
    blockchain_sizes = [storage[("blockchain", b)] / file_counts[b] for b in buckets]

    x = range(len(buckets))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar([i - width/2 for i in x], checksum_sizes, width, label="checksum")
    ax.bar([i + width/2 for i in x], blockchain_sizes, width, label="blockchain")
    
    for i, (c, b) in enumerate(zip(checksum_sizes, blockchain_sizes)):
        ax.text(i - width/2, c + 5, f"{c:.0f}", ha="center", fontsize=8)
        ax.text(i + width/2, b + 5, f"{b:.0f}", ha="center", fontsize=8)

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{b} KB" for b in buckets])
    ax.set_xlabel("File size bucket")
    ax.set_ylabel("Bytes per entry")
    ax.set_title("Per-entry storage overhead by file size bucket")
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    out = FIGS_DIR / "fig3_storage.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  wrote {out}")


def plot_tamper_matrix():
    """Fig 4: tamper-detection matrix."""
    scenarios = []
    baseline = []
    blockchain = []
    with open(TAMPER_CSV, "r", newline="") as f:
        for r in csv.DictReader(f):
            scenarios.append(r["scenario"])
            baseline.append(1 if r["checksum_detects"] == "True" else 0)
            blockchain.append(1 if r["blockchain_detects"] == "True" else 0)

    matrix = [baseline, blockchain]
    systems = ["checksum", "blockchain"]

    fig, ax = plt.subplots(figsize=(6, 2.8))
    # 1 = detect (green), 0 = miss (red)
    ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels(scenarios)
    ax.set_yticks(range(len(systems)))
    ax.set_yticklabels(systems)

    for i in range(len(systems)):
        for j in range(len(scenarios)):
            label = "DETECT" if matrix[i][j] == 1 else "MISS"
            ax.text(j, i, label, ha="center", va="center",
                    color="black", fontsize=10, fontweight="bold")

    ax.set_title("Tamper detection by scenario and system")
    out = FIGS_DIR / "fig4_tamper_matrix.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  wrote {out}")


def main():
    FIGS_DIR.mkdir(exist_ok=True)
    rows = _load_results()
    print("Generating figures...")
    plot_throughput(rows)
    plot_verification(rows)
    plot_storage(rows)
    plot_tamper_matrix()
    print("Done.")


if __name__ == "__main__":
    main()
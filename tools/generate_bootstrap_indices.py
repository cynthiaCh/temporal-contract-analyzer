#!/usr/bin/env python3
"""Generate one reusable paired bootstrap index collection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=here / "full_manual.csv")
    parser.add_argument("--output-dir", type=Path, default=here / "bootstrap_indices")
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument("--label-column", default="ground_truth_gos")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    if args.n_bootstrap < 1:
        raise ValueError("--n-bootstrap must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with args.reference.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"case_id", args.label_column}.issubset(rows[0]):
        raise ValueError(f"Reference CSV must contain case_id and {args.label_column}")
    case_ids = [str(row["case_id"]).strip() for row in rows]
    ground_truth = [int(row[args.label_column]) for row in rows]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Reference CSV contains duplicate case_id values")

    n = len(case_ids)
    rng = random.Random(args.seed)
    index_rows = [[rng.randrange(n) for _ in range(n)] for _ in range(args.n_bootstrap)]

    order_path = args.output_dir / "case_id_order.csv"
    with order_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_index", "case_id", args.label_column])
        writer.writerows((index, case_ids[index], ground_truth[index]) for index in range(n))

    header = ["replicate", *[f"draw_{position:03d}" for position in range(1, n + 1)]]
    index_path = args.output_dir / f"bootstrap_indices_{args.n_bootstrap}x{n}.csv"
    with index_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for replicate, indexes in enumerate(index_rows, start=1):
            writer.writerow([replicate, *indexes])

    case_path = args.output_dir / f"bootstrap_case_ids_{args.n_bootstrap}x{n}.csv"
    with case_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for replicate, indexes in enumerate(index_rows, start=1):
            writer.writerow([replicate, *[case_ids[index] for index in indexes]])

    metadata = {
        "reference_file": str(args.reference.resolve()),
        "reference_sha256": sha256(args.reference),
        "n_source_cases": n,
        "label_column": args.label_column,
        "n_bootstrap": args.n_bootstrap,
        "draws_per_replicate": n,
        "sampling": "case-representation-level sampling with replacement",
        "paired_use": "Use each replicate's identical indexes for every model.",
        "index_base": 0,
        "seed": args.seed,
        "random_generator": "Python random.Random (MT19937)",
        "case_id_order_file": order_path.name,
        "index_file": index_path.name,
        "case_id_file": case_path.name,
        "index_file_sha256": sha256(index_path),
        "case_id_file_sha256": sha256(case_path),
    }
    (args.output_dir / "bootstrap_indices_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {args.n_bootstrap} paired bootstrap replicates of {n} draws")
    print(f"Index matrix: {index_path}")
    print(f"Case-ID matrix: {case_path}")


if __name__ == "__main__":
    main()

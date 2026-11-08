#!/usr/bin/env python3
"""Offline catalog/metadata inventory; never imports or invokes an experiment runner."""
import argparse
import collections
import csv
import hashlib
import json
import os
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root):
    names = [n for n in ("case.json", "task.json", "case-record.json") if (root / n).is_file()]
    if set(names) == {"task.json", "case-record.json"}:
        return root / "task.json"
    if len(names) != 1:
        raise ValueError(f"ambiguous manifest: {root}")
    return root / names[0]


def csv_write(path, rows):
    if not rows:
        raise ValueError(f"empty table: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyzer", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--bench", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    analyzer = args.analyzer.resolve()
    bench = (args.bench or analyzer.parent / "temporal-contract-bench").resolve()
    out = args.out.resolve()
    if (out / "cases.csv").exists():
        raise FileExistsError("use a fresh output directory; preserve the existing inventory snapshot")
    out.mkdir(parents=True, exist_ok=True)
    sources = {}

    def source(path):
        sources[os.path.relpath(path, analyzer)] = digest(path)
        return path

    registry = read(source(bench / "experiments/temporal-diagnostics-v1/corpus.json"))["cases"]
    local = read(source(analyzer / "experiments/local-cases.json"))["cases"]
    registered = {r["id"]: r for r in registry}
    excluded = read(source(bench / "studies/case-admission-exclusions-v1/registry.json"))["cases"]
    blocked = {r["case_id"] for r in excluded if r.get("block_new_runs")}
    old = read(source(analyzer / "refine-logs/evidence/bench-inventory.json"))["records"]
    old_by_id = {r["case_id"]: r for r in old}
    locations = {}

    def add(cid, root, cluster, origin):
        if cid in locations:
            raise ValueError(f"duplicate case ID: {cid}")
        p = source(manifest(root))
        d = read(p)
        if d["id"] != cid:
            raise ValueError(f"case ID mismatch: {p}")
        locations[cid] = (p, d, cluster, origin)

    for p in sorted((bench / "case-clusters").glob("*/cluster.json")):
        d = read(source(p))
        for arm in d["arms"]:
            add(arm["id"], p.parent / arm["path"], d["id"], "bench")
    for root in sorted((bench / "cases").iterdir()):
        if root.is_dir() and any((root / n).is_file() for n in ("case.json", "task.json", "case-record.json")):
            add(root.name, root, "", "bench")
    for r in local:
        add(r["id"], (analyzer / r["manifest"]).parent, r["independent_unit_id"], "analyzer")
    assert set(registered) <= set(locations)

    rows = []
    for cid, (p, d, cluster, origin) in sorted(locations.items()):
        r = registered.get(cid, next((x for x in local if x["id"] == cid), {}))
        historical = old_by_id.get(cid, {})
        provenance = d.get("provenance", {})
        task_rel = d.get("diagnostic_tasks", {}).get("maintenance", {}).get("core_prompt")
        rows.append(dict(
            case_id=cid, origin=origin, cluster=cluster,
            independent_unit=d.get("independent_unit_id") or r.get("independent_unit_id") or historical.get("source_unit") or "UNKNOWN",
            runtime=d.get("framework", {}).get("runtime", historical.get("runtime", "UNKNOWN")),
            diagnostic_registry=bool(r), adapter=r.get("adapter", "NOT_REGISTERED"),
            blocked_new_runs=cid in blocked, base_exists=(p.parent / "base").is_dir(),
            manifest=os.path.relpath(p, analyzer), manifest_sha256=digest(p),
            task=os.path.relpath(p.parent / task_rel, analyzer) if task_rel else "NOT_RESOLVED",
            task_sha256=digest(p.parent / task_rel) if task_rel and (p.parent / task_rel).is_file() else "",
            source_kind=provenance.get("origin_kind", r.get("source_kind", "UNKNOWN")),
            explicit_parent=provenance.get("parent_case_id", "NOT_DECLARED"),
            old_inventory_role=historical.get("role", "NOT_IN_242_SNAPSHOT"),
            lineage_notes=json.dumps(provenance.get("abstraction_notes", provenance.get("notes", [])), ensure_ascii=False),
            semantic_admission="NOT_INFERRED_FROM_METADATA"))
    csv_write(out / "cases.csv", rows)
    grouped = collections.defaultdict(list)
    for r in rows:
        grouped[r["independent_unit"]].append(r)
    csv_write(out / "units.csv", [dict(independent_unit=unit, representations=len(rs),
        diagnostic_registered=sum(r["diagnostic_registry"] for r in rs),
        blocked=sum(r["blocked_new_runs"] for r in rs),
        runtimes="|".join(sorted({r["runtime"] for r in rs}))) for unit, rs in sorted(grouped.items())])

    # Bounded historical metadata scan: no execution, stdout, model cache or credentials.
    prune = {"base", "candidate", "reference", "references", "oracle", "mutants", "node_modules", "patch",
             "before", "after", "snapshots", "upstream", "runtime", "scorer", "score", "target", "dist",
             "build", "workspaces", "workspace", "isolated", "dependencies"}
    seen, history, duplicates = set(), [], 0
    results = bench / "results"
    for current, dirs, files in os.walk(results):
        dirs[:] = sorted(n for n in dirs if n not in prune and not n.startswith("."))
        if len(Path(current).relative_to(results).parts) >= 4:
            dirs[:] = []
        if "run.json" not in files:
            continue
        p = source(Path(current) / "run.json")
        d = read(p)
        keys = ("case_id", "run_id", "started_at_utc", "model", "reasoning_effort", "prompt_sha256", "base_tree_sha256")
        identity = tuple(d.get(k) for k in keys)
        if not d.get("started_at_utc"):
            identity += (str(p),)
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        sp = p.with_name("score.json")
        score = read(source(sp)) if sp.is_file() else {}
        verdict = d.get("verdict")
        corroborated = (d.get("status") == "COMPLETED" and d.get("agent_exit_code") == 0
            and verdict in {"PASS", "UNDERREACH", "OVERREACH", "UNDERREACH_AND_OVERREACH"}
            and score.get("verdict") == verdict)
        loc = locations.get(d.get("case_id"))
        history.append(dict(case_id=d.get("case_id"), run_id=d.get("run_id"),
            model=d.get("model"), effort=d.get("reasoning_effort"), condition=d.get("condition"),
            status=d.get("status"), verdict=verdict, sibling_score_corroborated=corroborated,
            current_manifest_match=bool(loc and digest(loc[0]) == d.get("case_manifest_sha256")),
            historical_manifest_sha256=d.get("case_manifest_sha256"),
            base_tree_sha256=d.get("base_tree_sha256"), prompt_sha256=d.get("prompt_sha256"),
            evidence=os.path.relpath(p, analyzer)))
    csv_write(out / "bench-history.csv", history)
    target = [r for r in history if r["model"] == "gpt-5.6-terra" and r["effort"] == "medium" and r["sibling_score_corroborated"]]
    summary = dict(
        status="OFFLINE_SELECTION_ONLY", model_calls=0, scoring_calls=0, run_enabled=False,
        bench_catalog_cases=sum(r["origin"] == "bench" for r in rows), local_cases=len(local),
        total_representations=len(rows), independent_unit_labels=len(grouped),
        unknown_unit_count=len(grouped.get("UNKNOWN", [])),
        registered_cases=len(registry) + len(local), blocked_registered_cases=sum(r["diagnostic_registry"] and r["blocked_new_runs"] for r in rows),
        old_static_analysis_inventory=len(old), historical_metadata_rows=len(history), duplicate_metadata_rows=duplicates,
        target_model_medium_score_corroborated_rows=len(target),
        target_model_medium_current_manifest_matches=sum(r["current_manifest_match"] for r in target),
        limitations=["Full case metadata coverage is not full semantic review.",
            "Historical scan: bench/results run.json to depth 4; hidden and runtime/candidate trees excluded.",
            "Sibling-score corroboration is not an independent scoring audit.",
            "Manifest mismatch requires version reconciliation, not an assumption that source changed.",
            "Research archives are examined separately in SELECTION.md, not silently merged into legacy-run counts."])
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "source-manifest.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

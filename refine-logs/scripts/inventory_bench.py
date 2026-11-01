"""Read benchmark metadata; scan only local candidate base trees with analyzer v0.

No target execution, model calls, oracle-driven selection, or benchmark writes.
Metadata is used by this researcher-side inventory, never fed to the analyzer.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import gzip
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from temporal_contract_analyzer.core import VERSION, scan, analyze_sources, collect, sha
from temporal_contract_analyzer.boundary_cards import cards


def run(args):
    bench = Path(args.bench).resolve()
    target = ROOT / "refine-logs" / "evidence"
    target.mkdir(parents=True, exist_ok=True)
    roster_path = bench / "benchmark/swe-tempoc.json"
    roster = json.loads(roster_path.read_text())["cases"]
    report_dir = target / "baseline-scans"
    report_dir.mkdir(exist_ok=True)
    expected_tool_hash = analyze_sources({})['tool_sha256']

    def inspect(row):
        manifest = bench / row["manifest"]
        meta = json.loads(manifest.read_text())
        base = manifest.parent / "base"
        record = dict(row, manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                      source_kind=meta.get("provenance", {}).get("origin_kind", meta.get("task_origin", meta.get("source_type"))),
                      base_available=base.is_dir(), analyzer_version=VERSION)
        if not base.is_dir():
            record.update(status="requires_upstream_materialization", files=0, findings=None)
            return record
        start = time.monotonic()
        try:
            report_path = report_dir / (row["case_id"] + ".json")
            compressed_path = report_path.with_suffix('.json.gz')
            if report_path.exists() or compressed_path.exists():
                # Resume only this invocation's own reports; no benchmark writes.
                if report_path.exists():report = json.loads(report_path.read_text())
                else:
                    with gzip.open(compressed_path, 'rt', encoding='utf-8') as handle:report=json.load(handle)
                sources, skipped = collect(base)
                current_inputs=[dict(path=name,sha256=sha(text.encode('utf-8'))) for name,text in sorted(sources.items())]
                if (report['tool_sha256'] != expected_tool_hash or report['inputs'] != current_inputs
                        or report.get('skipped', []) != skipped):
                    raise RuntimeError('Cached source/tool differs; use a new inventory output batch')
                record["resumed_from_current_inventory"] = True
            else:
                process = subprocess.Popen(
                    [sys.executable, "-B", str(Path(__file__).resolve()),
                     "--scan-one", str(base), "--report-file", str(report_path)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    start_new_session=True)
                try:
                    stdout, stderr = process.communicate(timeout=args.timeout_seconds)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.communicate()
                    record.update(status="scan_timeout", timeout_seconds=args.timeout_seconds,
                                  findings=None, elapsed_seconds=round(time.monotonic()-start, 6))
                    return record
                if process.returncode:
                    raise RuntimeError(stderr[-1000:] or stdout[-1000:])
                report = json.loads(report_path.read_text())
            card_list = cards(report)
            evidence = {event["id"]: event for file in report["files"] for event in file["events"]}
            record.update(status=report["status"], files=len(report["files"]),
                          parsed_files=sum(f["status"] == "parsed" for f in report["files"]),
                          file_statuses=dict(Counter(f["status"] for f in report["files"])),
                          findings=len(report["findings"]), rule_counts=dict(Counter(f["rule"] for f in report["findings"])),
                          candidate_call_links=len(report.get("call_links", [])),
                          cards=len(card_list), cards_with_effect=sum(bool(c["effects"]["evidence_ids"]) for c in card_list),
                          cards_with_guard=sum(bool(c["requirement_protection"]["evidence_ids"]) for c in card_list),
                          evidence_files=sorted({evidence[eid]["path"] for f in report["findings"] for eid in f["evidence"]}),
                          input_sha256=report["input_sha256"], skipped=report.get("skipped", []))
            if not compressed_path.exists():
                report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        except Exception as error:
            record.update(status="scan_error", error=type(error).__name__ + ": " + str(error), findings=None)
        record["elapsed_seconds"] = round(time.monotonic() - start, 6)
        return record

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(inspect, roster))
    summary = {
        "kind": "exploratory implementation inventory; not effectiveness evaluation",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "bench_root": str(bench), "analyzer_root": str(ROOT), "analyzer_version": VERSION,
        "roster_sha256": hashlib.sha256(roster_path.read_bytes()).hexdigest(),
        "representations": len(records), "roles": dict(Counter(r["role"] for r in records)),
        "source_units": len({r["source_unit"] for r in records}),
        "runtime_counts": dict(Counter(r["runtime"] for r in records)),
        "scan_statuses": dict(Counter(r["status"] for r in records)),
        "core_scan_statuses": dict(Counter(r["status"] for r in records if r["role"] == "core")),
        "records": records,
    }
    (target / "bench-inventory.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, ensure_ascii=False, indent=2))
    for r in records:
        if r["role"] == "core":
            print(r["case_id"], r["status"], r.get("findings"), r.get("cards_with_effect"), r.get("cards_with_guard"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench", default="/Volumes/Extreme/paper+survey/temporal-contract-bench")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--scan-one")
    parser.add_argument("--report-file")
    args = parser.parse_args()
    if args.scan_one:
        report = scan(Path(args.scan_one))
        Path(args.report_file).write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    else:
        run(args)

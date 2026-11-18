#!/usr/bin/env python3
"""Run the Python readiness base, reference, and mutant matrix."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASE = HERE.parent
ROWS = (
    ("base", None, "UNDERREACH"),
    ("reference/bounded", CASE / "reference" / "bounded", "PASS"),
    ("mutants/single-loop-yield", CASE / "mutants" / "single-loop-yield", "UNDERREACH"),
)


def execute(name, overlay, expected):
    with tempfile.TemporaryDirectory(prefix="python-readiness-pilot-") as temporary:
        candidate = Path(temporary) / "candidate"
        shutil.copytree(CASE / "base", candidate)
        if overlay is not None:
            shutil.copytree(overlay, candidate, dirs_exist_ok=True)
        completed = subprocess.run(
            [sys.executable, "-B", str(HERE / "probe.py"), str(candidate)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        if completed.returncode not in (0, 1):
            raise RuntimeError(completed.stderr.strip() or "probe execution failed")
        report = json.loads(completed.stdout)
    return {
        "candidate": name,
        "expected": expected,
        "actual": report["verdict"],
        "missing_required_effects": report["missing_required_effects"],
    }


def main():
    rows = [execute(*row) for row in ROWS]
    passed = all(row["expected"] == row["actual"] for row in rows)
    print(json.dumps({"case_id": CASE.name, "passed": passed, "rows": rows}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())


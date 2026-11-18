#!/usr/bin/env python3
"""Deterministic oracle for the Python local-config readiness pilot."""

import asyncio
import json
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / 'tempoc/python_candidate.py').is_file():
        sys.path.insert(0, str(parent))
        break
from tempoc.python_candidate import CandidateProcessError, PythonCandidate

CASE_ID = "local-config-readiness-python"
LOCAL_CONFIG = {
    "fields": ["parent_id", "parent_code", "parent_name"],
    "picker": "unit_lookup",
    "initial_values": {},
}
PARENT_VALUES = {
    "parent_id": "parent-7f3a",
    "parent_code": "code-29c1",
    "parent_name": "name-84d6",
}


class ControlledLoader:
    def __init__(self):
        self.called = asyncio.Event()
        self.release = asyncio.Event()
        self.requests = []

    async def __call__(self, name):
        self.requests.append(name)
        self.called.set()
        await self.release.wait()
        if name == "record-form":
            return dict(LOCAL_CONFIG)
        return {"fields": ["audit_id"]}


class ControlledForm:
    def __init__(self, ready=False):
        self._ready = asyncio.Event()
        if ready:
            self._ready.set()
        self.registration_count = 0
        self.ready_wait_started = asyncio.Event()
        self.ready_wait_count = 0
        self.applied_config = None
        self.values = {}
        self.writes = []

    def begin_registration(self):
        self.registration_count += 1

    async def ready(self):
        self.ready_wait_count += 1
        self.ready_wait_started.set()
        await self._ready.wait()

    def publish_ready(self):
        self._ready.set()
        self._hydrate()

    def _hydrate(self):
        if self.applied_config is not None:
            self.values.update(self.applied_config.get("initial_values", {}))

    def apply_config(self, config):
        self.applied_config = config
        if self._ready.is_set():
            self._hydrate()

    def write(self, values):
        if not self._ready.is_set():
            raise RuntimeError("form is not ready for imperative writes")
        self.writes.append(values)
        self.values.update(values)


async def settle(editor, form, loader, record):
    task = asyncio.create_task(editor.open(record))
    watches = [asyncio.create_task(event.wait()) for event in (loader.called, form.ready_wait_started)]
    try:
        await asyncio.wait([task, *watches], timeout=2, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for watch in watches:
            watch.cancel()
        await asyncio.gather(*watches, return_exceptions=True)
    if not task.done():
        form.publish_ready()
        loader.release.set()
    try:
        await asyncio.wait_for(task, timeout=2)
        error = None
    except CandidateProcessError:
        raise
    except Exception as caught:
        error = str(caught)
    form.publish_ready()
    return {
        "error": error,
        "remote_requests": list(loader.requests),
        "ready_wait_count": form.ready_wait_count,
        "registration_count": form.registration_count,
        "applied_config": form.applied_config,
        "values": dict(form.values),
        "writes": list(form.writes),
    }


async def execute_record(candidate, ready_before_open):
    form = ControlledForm(ready=ready_before_open)
    loader = ControlledLoader()
    editor = await candidate.editor('record', form, loader)
    return await settle(editor, form, loader, dict(PARENT_VALUES))


async def execute_audit(candidate):
    form = ControlledForm(ready=False)
    loader = ControlledLoader()
    editor = await candidate.editor('audit', form, loader)
    return await settle(editor, form, loader, {"audit_id": "audit-41"})


async def assess(candidate):
    observations = {
        "fresh-open": await execute_record(candidate, False),
        "reused-open": await execute_record(candidate, True),
        "audit-control": await execute_audit(candidate),
    }
    record_rows = [observations["fresh-open"], observations["reused-open"]]
    effects = {
        "record-remote-config-eliminated": all(
            row["remote_requests"] == [] for row in record_rows
        ),
        "record-form-ready": all(
            row["error"] is None
            and row["applied_config"] is not None
            and row["applied_config"]["fields"] == LOCAL_CONFIG["fields"]
            and row["applied_config"]["picker"] == LOCAL_CONFIG["picker"]
            for row in record_rows
        ),
        "record-parent-values-preserved": all(
            row["values"] == PARENT_VALUES and len(row["writes"]) <= 1
            for row in record_rows
        ),
        "audit-remote-config-preserved": (
            observations["audit-control"]["error"] is None
            and observations["audit-control"]["remote_requests"] == ["audit-form"]
            and observations["audit-control"]["values"] == {"audit_id": "audit-41"}
        ),
    }
    target_effects = [
        "record-remote-config-eliminated",
        "record-form-ready",
        "record-parent-values-preserved",
    ]
    missing = [name for name in target_effects if not effects[name]]
    overreach = [] if effects["audit-remote-config-preserved"] else [
        "audit-remote-config-preserved"
    ]
    if missing and overreach:
        verdict = "UNDERREACH_AND_OVERREACH"
    elif missing:
        verdict = "UNDERREACH"
    elif overreach:
        verdict = "OVERREACH"
    else:
        verdict = "PASS"
    return {
        "schema_version": "python-pilot-0.1",
        "case_id": CASE_ID,
        "verdict": verdict,
        "missing_required_effects": missing,
        "observed_forbidden_effects": overreach,
        "observed_effects": effects,
        "schedules": observations,
    }


def main():
    if len(sys.argv) != 2:
        print("usage: probe.py CANDIDATE_ROOT", file=sys.stderr)
        return 64
    try:
        async def execute():
            async with PythonCandidate(Path(sys.argv[1]), 'editors') as candidate:
                return await assess(candidate)
        report = asyncio.run(execute())
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

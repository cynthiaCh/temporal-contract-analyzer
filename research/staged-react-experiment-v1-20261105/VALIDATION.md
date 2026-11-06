# Validation and known execution deviation

No production implementation, scorer, source question bank or pre-existing archive is edited. No new dependency or Git commit. Python execution uses the existing `/home/sribd/anaconda3/bin/python3.11`; the default `python` is Python 2 and was rejected during initial read-only inspection. The existing scorer's configured runtime selection is retained; vanilla cases use pinned Node v16.20.2. Candidate-visible `node` remains the system Node, equally for both arms; trusted scoring has its own recorded runtime.

Preparation reused Workbench's snapshot and AST archive path. Existing facts/review files are research-side only. Local-config facts are empty and explicitly exclude Vue runtime behavior; transfer facts contain selected syntax and bounded relations. Both arms receive no AST text. Source BM25 and fixed-five-question rendering are byte copies from the latest validated experiment. All candidate starts and complete prompts are frozen before formal calls. `common-digests.json` records bytes of original prompt plus source and questions; `runs.json` records each complete A/B prompt hash and candidate inventory.

Initial offline check failed because installed bwrap lacks `--clearenv`. Replaced it by clearing inherited environment keys with supported `--unsetenv`; retained `offline-isolation.first-failure.json` and original freeze. Synthetic read-isolation/mutation/check test then passed, as did 16 prompt/budget checks and eight unchanged/reference calibrations. Four reference PASS and four unchanged UNDERREACH receipts are under calibration/.

**Offline coverage was insufficient:** `codex --version` did not exercise its sibling code-mode host. Formal slot 1, B/download/replicate 1, reported missing `/opt/codex-code-mode-host`, used no workspace tools and made no change. Although the existing runner marked its text-completed turn and unchanged oracle as behavior-failure, the analysis explicitly reclassifies it as `execution-tool-unavailable` and excludes it from semantic comparisons. Its raw result is preserved, never rewritten.

A freeze guard stopped subsequent scheduling. Mounted the complete pinned CLI runtime directory and added its `/opt` path to both remaining arms; confirmed helper executable and `--help` offline (`offline-isolation.runtime-fixed.json`). Reused existing calibration bytes; did not rerun models or tune prompts. `runtime-correction.json`, `protocol.pre-runtime-fix.json`, `run.pre-runtime-fix.txt`, and run.log preserve the correction. Continued only the remaining 15 unique IDs. Total remains exactly 16 formal slots, no retries, maximum seven valid pairs. The first pair is environment-unmatched and excluded from paired effectiveness and paired cost estimates. All-slot totals still include its measured cost.

Mount namespace exposes only system runtime, per-run copied CLI profile, candidate, output and stage directories. New PID namespace prevents `/proc` access to host processes. Synthetic checks reject host `/home/sribd`, sibling materials and host process root; stage files are outside the scored candidate. No researcher-side scoring, reference patches, source provenance or other run's output is mounted. Network namespace is shared for CLI model transport; this is a filesystem boundary, not an adversarial network isolation certification. Per-run profiles contain transient credentials solely for CLI authentication and are deleted after execution; credentials are never included in artifact manifests.

Stage control is prompt-only: no state callbacks in existing Workbench, no external semantic gate. The prompt asks at most six records of 1800 characters and two backward transitions, within the same 600 seconds. Actual compliance is audited separately. Raw malformed logs are retained; never silently normalized as valid JSONL. Additional controller model calls: zero. JSON validity does not establish correct evidence or decision quality.

Reproduce analysis only (no model calls):

```sh
/home/sribd/anaconda3/bin/python3.11 research/staged-react-experiment-v1-20261105/analyze.py
```

`run.py prepare` refuses to overwrite its frozen protocol. `execute` refuses an existing invocation ledger; `remaining` requires the explicit correction receipt and skips every already launched ID. Invocations are recorded before launch. Scoring stays outside the namespace and is never feedback to another slot.

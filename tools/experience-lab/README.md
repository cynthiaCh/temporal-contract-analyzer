# TempoEvo run workspace

A local English interface for configuring and launching training or testing through
TempoEvo's existing public CLI. Python's standard library serves the page; no new
runtime dependencies are needed. The layout follows the supplied Experience Lab
reference and includes a compact presentation view for screen recordings.

## Open

On macOS, double-click `launch-tempoevo-workspace.command` at the repository root.
Or, from this checkout:

```sh
python3 -B tools/experience-lab/serve.py --open
```

Open **http://127.0.0.1:8765**. Keep the server terminal open. Launching again
reopens the existing workspace when its checkout and run directory match.
It preserves active training and does not start a second server. If another
service or workspace occupies the port, the launcher explains the conflict
without a traceback; use `--port 8766` to start a separate workspace.

Closing the browser does not stop the server. Double-click
`stop-tempoevo-workspace.command` to close the default workspace, or run
`python3 -B tools/experience-lab/serve.py --stop`. For a custom port, add
`--port PORT` (and the matching `--runs PATH` if customized). Closing verifies
the workspace identity and preserves its records. It refuses while preparation
or training/testing is active; wait for completion, or request stop in the page
and wait before closing. The next launch uses port 8765 again.

The default benchmark uses `TCA_BENCH_ROOT` when set, otherwise an available
`temporal-contract-bench` or `temporal-contract-bench-git` checkout beside this
repository. Check or change this path under **Execution environment**.

The server binds to the loopback interface. To execute on an already provisioned
experiment server, run this same command there and forward its port:

```sh
ssh -L 8765:127.0.0.1:8765 YOUR_EXPERIMENT_HOST
```

Open the forwarded address using `127.0.0.1`, rather than `localhost`. All paths,
Docker images, credentials and outputs belong to the machine running the server.
On macOS, the workbench also detects Codex bundled with the local VS Code OpenAI
extension when Finder's PATH does not include it, and passes that path to preparation.
The workbench does not deploy files, configure credentials or install images.

### Local replacement images

When the historical pinned images are absent, build replacements from this
host's provisioned `swe-tempoc:grading-fix-final3` image without network access:

```sh
docker build --network none --pull=false --target solver -f containers/tempoevo/Dockerfile.local -t tempoevo-solver:local containers/tempoevo
docker build --network none --pull=false --target grader -f containers/tempoevo/Dockerfile.local -t tempoevo-grader:local containers/tempoevo
```

The solver retains public language toolchains and JS dependencies, removes the
benchmark directory, and copies the sanitized filesystem into a scratch image.
The grader retains the existing benchmark. These are new images; historical run
bindings remain unchanged. Preparation must pass the selected case's original,
reference and negative controls before execution.

Save their full immutable IDs as `solver_image` and `grader_image` in
`.tempoevo/docker-images.json` to override the page's defaults. Refresh the page
after changing that file. On macOS, provision a Linux x64 Codex executable and
its `codex-code-mode-host` companion in `.tempoevo/bin/linux-x64/`; the workbench
passes this binary explicitly to preparation instead of mounting the macOS CLI.
The selected-case CLI also accepts `--binary PATH` for other layouts.

## Launch a run

1. Select **Training** (70 development tasks) or **Testing** (30 test tasks).
2. Select the first case rank, number of cases, actual model profile, repair
   condition, and concurrent cases. Start with one case and one worker.
3. Check **Execution environment**. Point it at your benchmark, experience
   library, model-profile JSON and pinned solver/grader image IDs. Training also
   needs public-check descriptions for every selected case.
4. Click **Prepare training/testing**. This invokes
   `tools/tempoevo-docker/prepare_selected.py`, including its existing evaluator
   checks and snapshot preparation, without model requests.
   Testing reads the selected `test30.csv` cases from the benchmark's frozen
   `benchmark/swe-tempoc.json` roster, rather than the older partial case catalog.
5. When the batch says **prepared**, click **Start training/testing**. This
   explicitly authorizes model execution for the selected cases. Each case runs
   `python3 -B -m temporal_contract_analyzer tempoevo run --root ... --execute`.
6. Inspect a case's source/AST evidence, Auto-Contract, verified patch comparison,
   delivered experience, candidate proposal, and stage/execution logs as they
   become available. Run completion and behavioral success are separate states.

Prepare immediately shows its pending state. Invalid fields expand their environment
section, and preparation errors appear beside the button. The Run log shows
preparation events even before the first case exists, followed by preparation output.

The progress panel refreshes every 2.5 seconds and shows the current stage,
finished cases, measured completed/pending model requests, and elapsed execution
time. Its bar counts finished cases, so it can stay at zero while the first case
is running. A repair pass still waits for experience extraction to finish.
Completion leaves a result banner and updates the browser tab title. A run that
ends with failed or unscored cases asks you to review results. If the selected
run finishes while the page is open, an alert also appears at the top of the page;
these are page notifications, not operating-system notifications.

The defaults refer to this development checkout's research assets. A clean source
export may lack them; configure your own paths and model profiles. Environment
checks cover Docker availability, Codex presence and image availability, but do
not establish authentication, quota or completion of a real model run.

### Model profiles

#### Qoder Credits / built-in DeepSeek

Provision the pinned Qoder CLI (1.1.94), then sign in using its official browser
flow. The installer verifies the release archive SHA-256 against the official
version manifest; it adds no Python/Node dependencies:

```sh
python3 -B tools/experience-lab/setup_qoder.py --login
```

The workspace provides `qoder-deepseek-flash-low`,
`qoder-deepseek-flash-high`, and `qoder-deepseek-pro-high`. These select the
account's built-in `DeepSeek-Flash` / `DeepSeek-V4-Pro` models and spend Qoder
Credits. They do not use a DeepSeek API key or a custom provider endpoint.
Restart an idle workspace after provisioning, then prepare a fresh run.
Re-running setup without `--login` keeps the existing dedicated CLI account.

Each stage executes the Linux CLI in the pinned solver image, with only public
candidate files and isolated configuration. Its dedicated account files live
under `.tempoevo/qoder/account/.auth`; no IDE memory, user hooks, plugin settings,
benchmark/scorer, experience archive or Docker socket is mounted. Qoder manages
token refreshes in that dedicated account directory. Credentials are not written
to run logs or source files.

Qoder's budget counts **model turns**, as reported by its `stream-json` result,
and enforces `--max-turns` (24 per Action, 12 per analysis stage) and a maximum
600-second stage duration. Provider model-request retries are set to zero.
The page explicitly labels these as model turns: the underlying HTTP request
count is unknown. Live turn progress deduplicates completed assistant message
IDs; the final count comes from `num_turns`. Missing final counts or an
unconfirmed model fail the stage rather than reporting success. Reported Credits
are retained separately; unavailable token usage stays unknown.

Analysis has a read-only workspace, a guarded Bash reader and a Read tool confined
to public workspace paths (including checks against escaping symlinks). Actions have a
writable public workspace; existing protected-file checks and independent
evaluators still apply. CLI results must contain a JSON object matching the
stage schema. Raw output, errors, commands and container receipts are retained.
Actions may also use Read on their container-local `/tmp` scratch files, with
symlink confinement; analysis stages remain limited to the public workspace.
Prose or a Markdown fence around a single schema-valid JSON object is accepted,
but malformed JSON, additional objects and trailing prose are rejected. The raw
answer is always retained. After the container stops, owner read access is
restored on candidate files (including mode-000 `sed` temporary files), with
changes recorded in `candidate-permissions.json`; candidate files are not dropped.
All owned containers stop before their candidate files are accepted or assessed.
MCP tools are explicitly disabled. A model's request for an unavailable tool is
not treated as proof of execution: collection continues, and recovery is accepted
only if the CLI returns an explicit error for that request. Unexpected successful
tools, missing tool-gate records and workspace policy violations still invalidate
the stage. Collection errors retain their original cause instead of being hidden
by a secondary missing-final-result message.
For guarded Bash/Read requests, a refusal can also recover when both the host
ledger and a matching CLI hook-blocking error prove the request never executed.
The refusal remains archived and counted in `blocked_tool_requests`. Missing or
mismatched proof and hook-server failures still invalidate the stage. A final
CLI `network_failure` with complete turn accounting can use the existing bounded
stage retry policy, sharing the original time/turn budget; no per-request retries
are enabled. Previous test results are retained and are not relabeled after fixes.
After confirmed container shutdown, transient permission failures while removing
the isolated host profile are retried at most four times. `runtime-cleanup.json`
records the attempts and errors. Once container shutdown is confirmed, persistent
host-profile cleanup failures are reported as `cleanup_warning` with the runtime
retained for later cleanup; they do not discard an otherwise validated model
answer or candidate. Unconfirmed container shutdown still fails the stage.
An appended system instruction reinforces the exact output schema. For the
standard Action repair report only, undeclared fields are preserved separately
in `action_report_extra_fields` and `output-format.json`, with a `format_warnings`
entry. The declared `report` is still validated for presence, type and length;
only that validated report reaches the repair pipeline. The complete raw answer
remains archived. Additional metadata does not block independent candidate
scoring. Contract, experience and other schemas remain strict; malformed or
ambiguous JSON and invalid required fields remain invalid. This parsing policy
applies equally to memory-enabled and Auto-Contract-only Qoder runs; historical
scores are not rewritten.
The standard Action report also accepts literal newline, carriage-return and tab
characters inside its top-level `report` string. They are losslessly escaped in
memory for parsing, with `action_report_literal_whitespace` warnings recorded in
`output-format.json`; the raw answer stays unchanged. Control characters in
other fields/keys, other control characters, truncated JSON and multiple objects
remain invalid. This tolerance does not apply to other stage schemas.

Protocol references: [Qoder script execution](https://docs.qoder.com/cli/run-in-scripts),
[model selection](https://docs.qoder.com/cli/model), and
[authentication](https://docs.qoder.com/cli/authentication).

The initial workspace provides GPT-5.6 Sol and GPT-6.1 Sol profiles at low,
medium and high reasoning effort. `sol56-medium` matches the model name, effort,
service tier and provider settings used in the retained GPT-5.6 experiments.
Other presets are configuration choices; opening or saving does not check model
availability or account access.

Use **Edit profile** to change the selected model name, reasoning effort or service
tier. Use **+ Add profile** to create a separate ID using the selected profile as
its provider template. Empty effort/tier fields use the provider default.

Edits persist in `.tempoevo/model-profiles.json` with the default run directory
(or `model-profiles.json` beside a custom `--runs` directory). Prepared trajectories
retain their frozen settings; prepare a new batch to use an edit. The main runtime
configuration stays unchanged. Editing a profile loaded from an external file
copies that selected profile into the workspace, preserves its provider settings,
and uses the workspace retry policy. It does not overwrite the external file.
Stale saves are rejected; reload profiles and reopen the editor before retrying.
Saving makes no model requests. Credentials are not exposed in the editor.

## Execution and review boundaries

- Training uses the current V8-compatible construction recipe, with at most three
  repair Actions. Each Action is bounded by 24 requests and 600 seconds. Its
  approved input memory is frozen during the batch; this UI does not enable online
  admission or automatically accept extracted candidates.
- Testing uses one repair Action, frozen memory, and the existing independent
  final Gold scoring policy. It does not extract or learn experience.
- Workers run **different cases** concurrently (1–8); this is not the reference
  mockup's unimplemented “2N parallel runs per case.”
- To submit a retained success proposal for review, use the existing CLI with
  its actual trajectory root:

  ```sh
  python3 -B -m temporal_contract_analyzer tempoevo publish-candidate success \
    --root PATH_TO_TRAJECTORY
  python3 -B -m temporal_contract_analyzer experience-memory review \
    --store experience-memory/library
  ```

  Content acceptance and measured repair benefit remain distinct. The workspace
  does not record expert decisions on the user's behalf.
- **Request stop** requests cancellation through the public CLI. Active requests
  may need to return before stopping. Closing the page does not stop execution.
  Keep the server terminal open throughout a live batch. After a server restart,
  old active batches show `not monitored`; inspect their host processes and
  artifacts before creating another run. There is no automatic resume or retry.
- Outputs stay under `.tempoevo/runs/`, which Git ignores. Use `--runs PATH` to
  select a different output directory. Keep these artifacts for reproducibility.

## Recording an existing example

Two read-only entries appear if their source artifacts exist in this checkout:

- Five recovered training executions under
  `experiments/training-replays/tempoevo-gpt56-sol-medium-train70-error5-retry-20261118_221111/`.
- Thirty final testing scores from
  `experiments/testing-runs/gpt56-library-size-ablation-20261118/results-61.json`.

They remain labeled **Recorded · read-only**. **Replay recorded steps** changes
only the highlighted evidence tabs. The testing archive retains final scores;
missing contracts, source and stage traces are explicitly unavailable. It does
not substitute an invented trace for those missing artifacts. Source comparisons
use only files whose hashes match the frozen trajectory input.

For recording, choose a training case, click **Presentation view**, and show
Auto-Contract → Patch → Experience → Candidate → Run log. Demonstrate configuration
and a real launch separately on a provisioned execution host.

## Offline checks

```sh
python3 -B -m unittest discover -s tools/experience-lab -p 'test_*.py'
node --check tools/experience-lab/web/app.js
# Requires the Playwright dependency installed under vscode-extension/:
CHROME_PATH=/path/to/chrome node tools/experience-lab/test_prepare_browser.cjs

node tools/experience-lab/test_feedback.js
```

Controller tests replace model execution with explicit synthetic fixtures. They
check command construction, preparation/start separation, frozen one-Action
testing, fresh-root enforcement, HTTP action boundaries and read-only archives.
They do not establish model performance or repair benefit.

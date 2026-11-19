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

Open **http://127.0.0.1:8765**. Keep the terminal open. Use `--port 8766` if that
port is occupied; this launcher never replaces another running service.

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
The workbench does not deploy files, configure credentials or install images.

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
5. When the batch says **prepared**, click **Start training/testing**. This
   explicitly authorizes model execution for the selected cases. Each case runs
   `python3 -B -m temporal_contract_analyzer tempoevo run --root ... --execute`.
6. Inspect a case's source/AST evidence, Auto-Contract, verified patch comparison,
   delivered experience, candidate proposal, and stage/execution logs as they
   become available. Run completion and behavioral success are separate states.

Prepare immediately shows its pending state. Invalid fields expand their environment
section, and preparation errors appear beside the button. The Run log shows
preparation events even before the first case exists, followed by preparation output.

The defaults refer to this development checkout's research assets. A clean source
export may lack them; configure your own paths and model profiles. Environment
checks cover Docker availability, Codex presence and image availability, but do
not establish authentication, quota or completion of a real model run.

### Model profiles

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
```

Controller tests replace model execution with explicit synthetic fixtures. They
check command construction, preparation/start separation, frozen one-Action
testing, fresh-root enforcement, HTTP action boundaries and read-only archives.
They do not establish model performance or repair benefit.

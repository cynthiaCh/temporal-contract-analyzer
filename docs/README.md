# Documentation guide

These files explain the current tool. The runner does not load them as executable
configuration or model prompts. For research coordination, explicitly provide
[MASTER_PROMPT.md](../MASTER_PROMPT.md) to the coordinating agent; runtime stage
instructions are assembled in code.

| When you need to… | Read |
|---|---|
| Connect a coding agent, recall guidance or save user corrections | [Personal MCP](PERSONAL_MCP.md) |
| Scan source, inspect reports or expand related definitions | [Analyzer and reports](ANALYZER.md) |
| Understand learning, testing, budgets and feedback boundaries | [Research workflow](WORKFLOW.md) |
| Prepare Docker images and launch a research batch | [Docker execution](DOCKER_TRAINING.md) |
| Find implementation modules, obligation labels or archive rules | [Architecture and terminology](ARCHITECTURE.md) |

Start with the [repository README](../README.md) for installation and basic CLI
use. Experience-bank review/storage lives in
[experience-memory/README.md](../experience-memory/README.md); the experiment
case split is documented in [cases/README.md](../cases/README.md).

## Consolidated topics

Former report-center, source-context, low-noise and state-publication guides are
combined in `ANALYZER.md`. Docker backend details are combined in
`DOCKER_TRAINING.md`; evaluation boundaries in `WORKFLOW.md`; taxonomy and archive
policy in `ARCHITECTURE.md`. Version-by-version development narratives are available
in Git history rather than maintained as current operating instructions.

Actual settings come from configuration and the prepared run's `protocol.json`.
Documentation describes defaults, not a replacement for inspecting a run. Frozen
historical runs retain their original inputs, settings, scores and approvals.

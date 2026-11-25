# Everyday MCP guidance and personal corrections

Use this guide to connect an agent and retain project-specific user corrections.
The MCP server provides lexical recall and storage; the current host agent checks
meaning, applicability and updates. It does not launch a separate model, training
run, project execution for memory operations or Gold. Temporal scans are optional
when relevant; report tools are documented in [ANALYZER.md](ANALYZER.md).

## Workflow and stores

```text
Task/source -> recall general guidance + personal corrections
  -> host agent checks conditions/exclusions -> edit and validate
User correction -> host extracts durable understanding/repair steps
  -> personal top-5 recall -> compare/read history -> add/update/delete/restore/noop
```

The general pack (`temporal_contract_analyzer/data/temporal-experience.json`) is
read-only reviewed temporal guidance. Its current version/count is in the pack;
training traces and case outputs are excluded. Personal corrections can cover any
coding topic and take effect on the next recall without research review. These
stores are separate from the experimental bank; no personal rule is automatically
promoted to general guidance. Current user requirements take precedence; resolve
material ambiguous business semantics instead of guessing.

## Connect an agent

Use Python 3.9+ and the absolute checkout path. Replace `/absolute/path` below.
Parser dependencies are needed only for supported source analysis, as described in
the repository README; memory operations need only Python's standard library.

```sh
codex mcp add tempoevo -- python3 -I -S -B -X utf8 \
  /absolute/path/temporal-contract-analyzer/temporal_contract_analyzer/hub_entry.py \
  reports mcp
codex mcp list
```

For Claude Code, register the same launch command:

```sh
claude mcp add tempoevo -- python3 -I -S -B -X utf8 \
  /absolute/path/temporal-contract-analyzer/temporal_contract_analyzer/hub_entry.py \
  reports mcp
```

Quote paths containing spaces. An absolute Python executable can replace `python3`
when the client environment has a different PATH. Restart/reconnect the agent
session after registration. These commands register the server; they do not
exercise a repair or establish a successful client connection.

The personal directory defaults to
`~/.temporal-contract-analyzer/personal-memory/`. Override it with
`reports mcp --personal-store /absolute/path/to/personal-memory`, or the server's
`TCA_PERSONAL_MEMORY` environment variable. The explicit option takes precedence.
`--store` still selects the separate report archive, not personal memory.
Reading guidance does not create the personal directory; the first correction does.
Configure different agents with the same personal directory to share experience.
Writes use a lock and atomic replacement on a local filesystem (macOS/Linux).
The directory contains user text; do not point it at an experimental memory bank.

## General-pack configuration

Combined recall alternates personal/general candidates; the host agent checks
semantic applicability. This is not the experiment's model-based business selector.
Override the pack with `reports mcp --general-store /absolute/pack.json` or
`TCA_GENERAL_MEMORY` (explicit option wins). An invalid pack visibly fails combined
recall; `source=personal` remains independently usable. Never point personal storage
at a general pack or experimental bank.

Export an updated guidance-only pack offline to a new output path:

```sh
python3 -B -m temporal_contract_analyzer experience-memory export-general \
  --store experience-memory/library --version reviewed-YYYYMMDD \
  --output /absolute/new-temporal-experience.json
```

Export does not call models or change the library. Deployment is an explicit
configuration/package update, not a consequence of personal feedback.

## Three experience tools

Each tool requires `project`: the same existing absolute project root used when
recording. Symlinks are resolved. There is no automatic project-rename migration,
cross-project fallback or global-scope inference.

| Tool | Arguments | Result |
|---|---|---|
| `recall_experience` | `project`, `query`; optional `source` (`all`, `personal`, `general`), `limit` (1–20, default 5), `offset` | Current candidates with source, version, conditions, counts and `next_offset` |
| `read_experience` | `project`, `experience_id`; optional `source` (`personal` default, or `general`) | Personal content/history/deleted status, or full read-only general guidance |
| `update_experience` | `project`, `operation`; fields below depend on operation | `{operation, changed, experience}`; actual operation may be `noop` |

| Operation | Required fields beyond project/operation | Behavior |
|---|---|---|
| `add` | `correction` | New personal rule; omit ID/version |
| `update` | `correction`, `experience_id`, `expected_version` | Local revision under the same ID; preserve prior history |
| `delete` | `experience_id`, `expected_version` | Soft-delete; exclude from recall but retain recoverable content |
| `restore` | `experience_id`, `expected_version` | Restore a deleted personal rule |
| `noop` | None, or both `experience_id` and `expected_version` | No writes/versions; targeted noop checks a current active rule |

Only `add` and `update` accept content: optional `perspective`, `modification`, `guidance`, `context`, `mistake`,
`applicability`, `exclusions` and `related_general_id`. Other operations reject
content rather than silently ignoring it. A targetless noop returns
`experience: null` and does not create the personal directory. A targeted noop
rejects a stale version or deleted rule. `changed` is false for exact duplicate
adds/updates and already-deleted/restored entries; these report `operation: noop`.

## Correction content and update rules

| Field | Content |
|---|---|
| `correction` | New verbatim user feedback; old quotes remain in history |
| `perspective` | Supported problem understanding and distinctions |
| `modification` | Reusable repair and validation steps |
| `applicability` / `exclusions` | Where advice does or does not apply |

Strings are limited to 4096 characters. Facets are optional; save raw feedback
rather than inventing a mechanism or unperformed validation. Omitted fields retain
old values; an explicit empty string clears obsolete content. Reconcile old
`guidance` when replacing it with structured facets. General-pack fields keep their
original meaning and are not relabeled as inferred root causes.

Recall searches lowercase words and Chinese bigrams, not embeddings. Top-5 is a
candidate limit, not a semantic conclusion; broaden queries or paginate when
needed. An empty query can list active personal entries. No match does not prove
absence. Stale expected versions fail: read and reconcile instead of blind retry.
Individual writes are locked/atomic, but multi-entry recall is not a frozen
experimental snapshot. Delete is recoverable; there is no permanent-erasure tool.

## Instructions for the consuming project

MCP does not listen to the entire conversation or force tool calls. For persistent
agent behavior, append the following to the consuming project's AGENTS.md or
CLAUDE.md while preserving its existing rules. Service/tool display names can
vary by client:

```markdown
## TempoEvo

- Before coding, use `tempoevo.recall_experience` with this project's absolute
  root and task query. Check applicability and exclusions against current source;
  use at most three nonredundant entries, or none. Scan temporal behavior when useful.
- Extract durable corrections into `perspective` (problem understanding) and
  `modification` (repair/checking steps). Keep user words in `correction`, with
  scope/exclusions separate. Do not invent causes or claim unperformed validation.
- Before updating personal memory, call `recall_experience` with `source=personal`,
  `limit=5` and a query combining the feedback with task/module context. Use
  `read_experience` for full content and history when needed.
- Compare perspective, objects/APIs, scenarios and scope before adapting modification steps. Use `update_experience` with `add`
  for independent knowledge, `update` for the same rule's correction or extension,
  or `noop` if already covered. Shared vocabulary alone does not justify merging.
- Preserve valid old constraints in cumulative perspective and modification. Update only the affected
  ID and pass its current version. Omitted fields retain old values; an explicit
  empty string clears obsolete content. History keeps original user quotes.
- Use `delete` only for a clearly withdrawn rule; use `restore` at user request.
  Clarify material ambiguous conflicts. Noop does not write or add a version.
- Personal corrections may cover any coding topic and take effect without research
  review. Never write general guidance. Report failed operations honestly.
```

Restricted `--report-id` / `--layer` sessions expose only the assigned report,
without experience tools or everyday memory instructions.

The perspective/modification split, local item updates and compare-before-write
workflow draw on SWE-Exp, ACE and Mem0 respectively; this is not a reproduction of
their model/embedding pipelines. Storage/protocol checks do not establish measured
reductions in mistakes or experimental repair benefit for this everyday path.

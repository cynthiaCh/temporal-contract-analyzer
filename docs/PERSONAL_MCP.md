# Personal experience through local MCP

TempoEvo's existing stdio MCP now serves source analysis and personal corrections.
It uses the current coding agent for reasoning; the server does not call a model,
start a training run, execute project code for memory operations, or update model
weights. No web service, database, Skill or VS Code extension is required.
Personal corrections take effect on the next recall without research approval.
The experiment library and frozen testing protocol remain separate.

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
An empty read does not create the personal directory; the first correction does.
Configure different agents with the same personal directory to share experience.
Writes use a lock and atomic replacement on a local filesystem (macOS/Linux).
The directory contains user text; do not point it at an experimental memory bank.

## Call from normal conversation

Start with:

> Before editing, use tempoevo recall_experience for this project's absolute root
> and the current task. Check whether returned guidance applies to the source.

When correcting an agent:

> Closing the page must not cancel already-submitted saves. Fix this and use
> tempoevo remember_correction to remember my exact correction for this project.

The service's MCP initialization instructions explain this workflow. MCP does not
listen to the full conversation or force calls. For persistent instructions,
append the following to the consuming project's AGENTS.md (Codex) or CLAUDE.md
(Claude Code), preserving existing content:

```markdown
## TempoEvo

- Before coding, call MCP service `tempoevo`, tool `recall_experience`, using
  this project's absolute root and a query describing the task.
- Check returned candidates against current requirements and source.
- When the user explicitly corrects a mistake or requests a remembered rule,
  call `remember_correction`. Preserve the user's original words in `correction`;
  put any model summary separately in `guidance`. Default to this project.
- For a revision, read the existing entry and pass its ID and current version.
  Do not silently merge unrelated rules. New guidance replaces the previous
  guidance for recall, so retain still-applicable constraints in the revision.
- Show, delete or restore entries with `manage_experience` at user request.
- Report tool failures honestly; do not claim a correction is test-verified.
```

## Tools and arguments

All three tools require `project`: the same existing absolute project root on
record and recall. Symlink paths are resolved. There is no cross-project fallback
or global-scope inference. A project rename requires an explicit future migration;
this version does not infer renamed repositories.

| Tool | Arguments | Result |
|---|---|---|
| `recall_experience` | `project`, `query`; optional `limit` (1–20, default 5), `offset` | Active current entries, lexical scores, total and `next_offset` |
| `remember_correction` | `project`, `correction`; optional `guidance` | New active entry, stable ID, version and history |
| `remember_correction` (revision) | Same fields plus `experience_id`, `expected_version` | New revision of that entry; prior revisions retained |
| `manage_experience` | `project`, `experience_id`; optional `action` (`show`, `delete`, `restore`; default `show`) | Full entry and history; mutations require `expected_version` |

Example MCP tool arguments (the host supplies the tools/call envelope):

```json
{"project":"/work/my-app","correction":"Closing the page must not cancel already-submitted saves.","guidance":"Stop UI updates after close; preserve submitted save requests."}
```

Recall from the same root:

```json
{"project":"/work/my-app","query":"closing page save cancellation"}
```

Use an empty query to list all active entries; follow `next_offset` for more.
Search uses lowercase word tokens and Chinese character bigrams, not embeddings
or automatic semantic applicability judgments. Different vocabulary can miss a
relevant entry; use broader queries or list entries when needed. Each input string
is capped at 4096 characters. Recall returns current text only; history is
available through `manage_experience`.

For revision/delete/restore, supply the `expected_version` returned by recall or
show. A stale version fails without overwriting another client's change. Re-read
and reconcile before retrying. Each entry is one JSON file; a process lock protects
writes by cooperating clients. Reads see either the old or new complete file.
A query over several entries is not a frozen experimental snapshot.

Delete is reversible: it excludes the entry from recall and retains its content
on disk. Restore requires the current version and the saved experience ID.
There is no permanent-erasure tool in this version. User corrections are guidance,
not independently verified assertions. Record them immediately; do not invent
feedback or silently extend a project-specific rule to other projects.

Research sessions bound with `--report-id` and `--layer` still expose only their
assigned frozen report, without personal tools or personal workflow instructions.

# TempoEvo: general temporal guidance and personal corrections through MCP

TempoEvo's existing stdio MCP now serves source analysis and personal corrections.
It uses the current coding agent for reasoning; the server does not call a model,
start a training run, execute project code for memory operations, or update model
weights. No web service, database, Skill or VS Code extension is required.
TempoEvo retains its temporal-contract focus. General guidance comes from reviewed
temporal repair experience; personal corrections can cover any project coding
error, API misunderstanding, business rule or workflow. Personal corrections take
effect on the next recall without research approval. The experimental library and
frozen testing protocol remain separate; the new everyday flow does not inherit
experimental repair-benefit claims.

## Everyday flow

```text
Task + current source
  -> recall general temporal guidance + current-project personal corrections
  -> agent checks applicability, exclusions, conflicts and redundant advice
  -> agent uses at most three useful entries (or none), edits and validates
  -> explicit user correction
  -> recall related personal rules, then add / revise locally / skip duplicate
  -> later task or session recalls the current versions
```

The server performs lexical recall and storage; the current coding agent makes
semantic decisions. It does not introduce a separate reflector, curator or model
call. Temporal source scans remain useful for relevant tasks, not mandatory for
all coding work. Current explicit requirements take precedence; a scoped project
correction may specialize general guidance, but does not license inventing backend
semantics. Ask the user when a material business conflict remains unresolved.
Corrections do not modify the read-only general pack.


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

## Read-only general guidance

The package includes `data/temporal-experience.json`, version `reviewed-20261124`,
with 58 current accepted entries and their current accepted Abstracts. Guidance,
applicability, exclusions, preservation and verification text are copied verbatim;
training traces, case outputs, learning scores and evidence attachments are not
included. Existing library approval and replacement rules select current entries;
exporting is not an additional review or a claim of unseen-source generalization.

`recall_experience` reads this pack and the personal store in one call. Candidate
pages alternate personal/general entries so one source cannot fill the first page
by itself. Each item has `source`, `scope`, `version`, `read_only` and lexical
`score`; general items include their full conditions and reviewer attribution.
This is candidate retrieval, not the model-based experimental applicability
selector. The calling agent decides which advice is applicable to current code.

Override the pack using `reports mcp --general-store /absolute/path/pack.json`, or
`TCA_GENERAL_MEMORY`; the explicit option wins. An invalid pack fails combined
recall visibly; `source=personal` remains usable independently. General tool paths
cannot be supplied through remember/manage to overwrite the pack. Keep personal
storage separate from pack files and the experimental library.

Refresh a pack offline from a reviewed categorized library (new output path only):

```sh
python3 -B -m temporal_contract_analyzer experience-memory export-general \
  --store experience-memory/library --version reviewed-YYYYMMDD \
  --output /absolute/path/new-temporal-experience.json
```

The exporter does not call models or write the input library. Deploying a new pack
is an explicit configuration/package update, not a consequence of user feedback.
No experience is automatically promoted from personal to general storage.

## Call from normal conversation

Start with:

> Before editing, use tempoevo recall_experience for this project's absolute root
> and the current task. Check both general and personal candidates against the source.

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
  this project's absolute root and a task query. Consult general temporal guidance
  and personal project corrections; personal experience is not limited to time/order.
- Check full conditions and exclusions against current task/source, remove redundant
  advice and use at most three entries, or none. Use source analysis when relevant.
- Current explicit requirements take precedence. Project corrections specialize
  general advice only within their scope; ask about unresolved business conflicts.
- When the user explicitly corrects a mistake or requests a remembered rule,
  first recall related entries with `source=personal`. Add a genuinely new rule,
  revise the same rule using `remember_correction` with its ID/current version,
  or skip a duplicate. This is direct personal recording, not research review.
- Preserve user words in `correction`. Put model guidance, context, the prior mistake,
  applicability and exclusions in separate fields; leave unknowns empty.
- Revise only the affected entry. Preserve valid prior constraints in the updated
  guidance; omitted optional fields retain previous values. Use an explicit empty
  string to clear obsolete content. Do not rewrite or merge the whole library.
- Use `related_general_id` for a known project-specific exception; never rewrite
  the general pack. Do not infer that a correction is universally applicable.
- Show, delete or restore personal entries with `manage_experience` at user request.
- Report tool failures honestly; do not claim a stored correction is test-verified.
```

## Tools and arguments

All three tools require `project`: the same existing absolute project root on
record and recall. Symlink paths are resolved. There is no cross-project fallback
or global-scope inference. A project rename requires an explicit future migration;
this version does not infer renamed repositories.

| Tool | Arguments | Result |
|---|---|---|
| `recall_experience` | `project`, `query`; optional `source` (`all`, `personal`, `general`; default `all`), `limit` (1–20, default 5), `offset` | General and personal candidates with provenance, counts and `next_offset` |
| `remember_correction` | `project`, `correction`; optional `guidance`, `context`, `mistake`, `applicability`, `exclusions`, `related_general_id` | New active entry, stable ID, version and history |
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

Use an empty query to list active candidates from both sources, or `source=personal`
to list only project corrections; follow `next_offset` for more.
Search uses lowercase word tokens and Chinese character bigrams, not embeddings
or automatic semantic applicability judgments. Different vocabulary can miss a
relevant entry; use broader queries or list entries when needed. Each input string
is capped at 4096 characters. An exact repeat of current personal content is a no-op, without a new ID/version.
Similar but nonidentical text is not automatically merged; the agent must decide
which rule, if any, should be revised. Recall returns current text only; history is
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
assigned frozen report, without either memory source, memory tools or everyday workflow instructions.


## Design references and evaluation scope

- [SWE-Exp, §3](https://arxiv.org/html/2507.23361v2): distinguish reusable
  understanding from modification guidance; adapt experience to current source.
- [ACE, §3](https://arxiv.org/html/2510.04618v3): use itemized local updates instead
  of rewriting the entire accumulated context.
- [Mem0, §2.1](https://arxiv.org/html/2504.19413v1): compare new information with
  related memory before choosing add, update, delete or no-op.

These inform the workflow, not a reproduction of their algorithms. This version
uses lexical retrieval and the host agent, not their embedding/model pipelines.
It does not claim automatic semantic deduplication, autonomous experience
extraction or a measured reduction in repeated mistakes. Offline tests establish
storage, retrieval, source isolation and protocol behavior. Real agent use and
repair effectiveness require separate evaluation; historical frozen test scores
remain evidence for their original protocol only.

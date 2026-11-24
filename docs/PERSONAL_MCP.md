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
  -> agent extracts perspective + modification from durable user corrections
  -> recall_experience: source=personal, limit=5
  -> read_experience if full history is needed
  -> agent selects add / update / delete / restore / noop
  -> update_experience executes the selected personal-memory operation
```

The server performs lexical recall and storage; the host coding agent extracts
information, compares scope and decides operations. It does not introduce another
model call, autonomous conversation listener, reflector or curator. Personal
corrections are not restricted to temporal bugs. Separate durable corrections
from temporary requests and changed requirements. Temporal scans are useful when
relevant, not mandatory for all coding work.

Current explicit requirements take precedence. Project corrections specialize
general guidance only within their scope; ask about unresolved business semantics.
A supplement or scoped exception usually updates a rule rather than deleting it.
Delete only when the user clearly withdraws it. Never modify the general pack.

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

> Before editing, use tempoevo recall_experience for this project's absolute root
> and task. Check general and personal candidates against the current source.

When correcting an agent:

> Status 2 means pending confirmation and needs a yellow badge. Fix this and
> remember the correction for this project's order list.

The MCP initialization instructions describe extraction, top-5 comparison and
operations. MCP does not listen to the full conversation or force calls. For
persistent guidance, append this to the consuming project's AGENTS.md (Codex) or
CLAUDE.md (Claude Code), preserving existing instructions:

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

The dotted names above identify the service and tool, not a client-specific
internal tool-name format. Clients may display names differently.

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

## Two facets of a personal repair experience

Borrowing SWE-Exp's representation, the host agent can separate:

| Field | Content | Example |
|---|---|---|
| `correction` | New verbatim user feedback | Pending orders need a yellow badge. |
| `perspective` | How to understand the problem, supported mechanism and key distinctions | Order status is a project API contract; numeric values cannot be inferred from generic labels. |
| `modification` | Reusable repair and checking steps | Use the existing enum mapping; render pending in yellow; check other statuses and empty-state behavior. |
| `applicability` / `exclusions` | Where this advice does or does not apply | This project's order list, not the separate payment-status field. |

`perspective` and `modification` are optional strings (up to 4096 characters each).
Modification can contain several readable steps. We borrow the two-facet idea,
not SWE-Exp's complete representation or search architecture. A raw correction
can still be saved without a supported explanation; missing facets are unknown,
not invented. Both facets participate in lexical recall and are returned in full
when present. Use perspective while understanding/localizing a problem and
modification while editing and checking; do not reuse a strategy solely because
the patch looks similar.

Updates preserve omitted facets; explicitly pass an empty string to clear an
obsolete explanation or strategy. Delete/restore preserve them and version history
keeps previous text and original feedback. Existing `guidance` remains readable
as free-text context, not automatically reclassified or copied into the facets.
When replacing older guidance with a structured explanation, the agent should
reconcile the text and explicitly clear obsolete guidance rather than leave
contradictory instructions. The reviewed general pack remains unchanged; its
existing applicability, recommendation and preservation fields retain their
original meaning and are not relabeled as inferred root causes.

Examples of tool arguments (the agent client supplies the MCP envelope):

```json
{"project":"/work/my-app","query":"order status pending yellow badge","source":"personal","limit":5}
```

After inspecting a candidate, update it using its actual returned ID/version:

```json
{"project":"/work/my-app","operation":"update","experience_id":"0123456789abcdef0123456789abcdef","expected_version":1,"correction":"Pending orders need a yellow badge.","perspective":"Order status meanings come from this project's API enum, not general naming conventions.","modification":"For the order list, map status 2 to pending confirmation and render it with a yellow badge. Preserve other status mappings and check their display."}
```

Here perspective states the problem understanding, while modification preserves
the old status meaning and adds the new display rule.
The new `correction` contains only the new verbatim user feedback; old quotes stay
unchanged in history. To add an independent rule, use `operation=add` and omit
ID/version. To confirm already-covered feedback without changing storage:

```json
{"project":"/work/my-app","operation":"noop","experience_id":"0123456789abcdef0123456789abcdef","expected_version":2}
```

Top-5 is a candidate limit, not a semantic conclusion. Search uses lowercase words
and Chinese bigrams, not embeddings. Different wording can miss a relevant rule;
broaden the query, paginate, or use an empty query to list active personal entries.
No match does not prove absence. General guidance does not occupy the personal
update candidates. Each input string is limited to 4096 characters.

Writes use a local process lock and atomic replacement. A stale expected version
fails; read again and reconcile instead of blindly retrying. Reads see complete
individual files, but multi-entry recall is not a frozen experimental snapshot.
Existing personal JSON records remain readable; no content migration is needed.
There is no permanent-erasure operation. General-pack updates are separate explicit
exports/package changes, never a side effect of personal corrections.

Restricted `--report-id`/`--layer` sessions expose only the assigned report, with
no experience tools, memory access or everyday workflow instructions.

## Design references and evaluation scope

- [SWE-Exp, §3](https://arxiv.org/html/2507.23361v2): separate perspective (problem understanding)
  and modification (repair strategy); adapt both to current source.
- [ACE, §3](https://arxiv.org/html/2510.04618v3): itemized local updates instead of
  rewriting the whole context.
- [Mem0, §2.1](https://arxiv.org/html/2504.19413v1): extract information from dialogue,
  compare related memory, then choose add/update/delete/noop.

These inform the workflow, not a reproduction of their algorithms. This version
uses lexical retrieval and the host agent, not their embedding/model pipelines.
It does not claim automatic server-side semantic merging or measured reductions
in repeated mistakes. Offline tests establish storage, protocol behavior and
source isolation. Historical frozen scores apply to their original protocol only.

# Assumption ledger — failure learning
<!-- ASK mode: never -->

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| FL-001 | Meaning of evolution | Candidate experience memory and source-inspection recipe selection; no automatic rule/model training or correctness promotion | semantic | default |
| FL-002 | Learning trigger | After evaluation only when reference calibration PASS and a completed job has a scored failed outcome; timeouts, runner errors and unverified jobs are not semantic lessons | semantic | default |
| FL-003 | Feedback trust | Saved feedback is researcher-side evidence, not business truth; classify audit-related failed assertion names as an effect-separation clue; all other failures get a generic source-checking recipe | semantic | default |
| FL-004 | Storage and deduplication | Separate store/lessons, one deterministic lesson per experiment/evaluation; preserve evaluation and candidate files; repeating extraction is idempotent | interface | default |
| FL-005 | Retrieval scope | Same case ID, original candidate-file byte inventory and task text only; file permissions, model and oracle version are not matching keys, so applicability remains a candidate hypothesis; no cross-case or unseen-project transfer claim | semantic | default |
| FL-006 | Exposure | Lessons only enter explicit learned_review jobs; these are feedback-informed development retries, never blinded holdouts; A/D and restricted MCP frozen layers unchanged | semantic | default |
| FL-007 | Delivery content | Agent gets generic candidate review questions plus current snapshot excerpts, not oracle expected values, reference patches or failed assertion/schedule names; provenance IDs remain recorded | semantic | default |
| FL-008 | Context selection | Deterministic source search for recipe-related effect names, prioritize files containing both recording/display families absent from original report; full identified enclosing function or bounded nearby lines, max 6000 code chars; source-search candidates not proven callback dataflow | semantic | default |
| FL-009 | Limits and refresh | At most latest 3 matching lessons per new run; frozen IDs/material are checked at start; learning failure must not alter an otherwise completed evaluation | interface | default |
| FL-010 | Controls | CLI learn/lessons plus browser lesson-generation button, visible lesson cards and opt-in learned_review checkbox; generating/preparing never starts models | interface | default |
| FL-011 | D prerequisite | learned_review adds to the original D report, so a substantive source finding is required even if lexical recipe context exists | semantic | sweep |

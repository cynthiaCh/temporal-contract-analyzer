# Source-reviewed seven-label experience versions

Base commit: `b816f84a1a41778ef97a1c65df47d2c08de7c769`.

Use one shared research memory with multi-label obligation organization. Inspect
the three existing English bundles against their actual original training task,
visible documents and source. Record per-rule AI-assisted label reasoning and
exact source anchors. Create immutable native-taxonomy child candidates while
preserving every rule body, applicability predicate and old version.

No legacy-label lookup/mapping, reference patch, test trajectory or score is a
classification input. No model calls, rescoring, development repair replay,
expert activation, production update or commit. Historical outcome references
remain audit data and do not become effectiveness evidence for a new taxonomy.

The new versions remain candidates. Expert semantic acceptance and a separately
bounded development replay remain explicit later stages, not completed actions.

## Decisions before implementation

| ID | Choice | Type | Source |
|---|---|---|---|
| S-01 | Use the existing canonical seven-label codebook unchanged | semantic | user |
| S-02 | Per-rule annotations are source-reviewed AI judgments, not ground-truth labels or expert approval | semantic | default |
| S-03 | Taxonomy-only child versions copy rule bodies and requires/excludes exactly | interface | default |
| S-04 | Labels are the union of supported per-rule labels; absence means not established here, not mechanism absence | semantic | default |
| S-05 | Retain original translation/effect limitations and outcome references; do not launch a new repair experiment | semantic | default |
| S-06 | Repeated CLI label filters mean all requested labels; filtering does not bypass applicability/admission | interface | default |
| S-07 | A declarative annotation sheet is an offline audit artifact, never a runtime case-ID/class lookup | semantic | user |

# Assumption Ledger

ASK mode: never

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | Where automatic analysis starts | Omit `visible` from `prepare`; retain the existing reviewed-input path | interface | default |
| A-002 | Analysis approval | Pause after extraction; `review-analysis` accepts an explicitly supplied source-bound review before any repair | semantic | default |
| A-003 | Which AST material is delivered | Select finding evidence events, their conditions and supported relations/call links; include coverage and limitations, omit raw tree and provenance hashes; full numbered source remains available | semantic | default |
| A-004 | Incomplete AST coverage | Preserve partial/unavailable coverage and continue source-based analysis; never infer safety from no findings | semantic | default |
| A-005 | Model and budget | Reuse existing runner extraction role: gpt-6-sol/low, 12 requests, 600 seconds, one analysis session | interface | default |
| A-006 | Parser runtime | Use host Node for Docker preparation; native preparation uses its configured Node | interface | default |
| A-007 | Review may correct analysis | Preserve raw output; accept explicitly submitted corrected analysis plus source-bound review; do not invent approval or repair citations silently | semantic | default |
| A-008 | Source text and limits | Retain the current full-source prompt behavior, without silent truncation or a new ranking policy | interface | default |

| A-009 | Snapshot timing while analysis awaits review | Freeze active experience at prepare time, including automatic analysis; review retrieves only from that snapshot | semantic | default |

| A-010 | Structurally parseable but invalid analysis | Keep schema-valid duplicate/missing-evidence analyses reviewable; preserve validation issues and require explicit correction before repairs | semantic | sweep |
| A-011 | Development with unresolved labels | Require at least one evidence-supported label and one known premise before development repairs; evaluation still permits empty labels | semantic | sweep |

No live training/model execution is part of this implementation task.

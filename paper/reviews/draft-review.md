# Fresh-context draft assurance review

Review date: 2026-10-29, Asia/Shanghai. Reviewer: fresh-context Codex subagent, same model family. This is a **provisional same-family review**, not independent external acceptance, a citation-audit certificate, or a semantic correctness certificate.

**Verdict: PASS AS A WORKING DRAFT, with minor revisions. Not ready for submission.** At review close there are **0 unresolved CRITICAL findings and 0 unresolved MAJOR findings** in the manuscript's implementation/evidence claims. The concrete reproduction and interface-scope issues found during review were corrected by the authoring agent and reinspected. The remaining publication blockers are separated below. A completed developer study is not required to deliver this honestly scoped draft.

## Scope and files inspected

I read paper/main.tex, all seven paper/sections/*.tex files, paper/math_commands.tex, paper/figures/architecture.tex, paper/references.bib, paper/EVIDENCE_LEDGER.md, paper/TOOL_ENHANCEMENT_ROADMAP.md, and paper/README.md. I inspected main.pdf, its text/font metadata and all four freshly rendered pages, plus main.log/main.aux/compile.log for layout and compilation evidence.

Evidence inspected: paper/evidence/demo-traces.json, demo-analysis.json, demo-archive.json, the subsequently added demo-archive-guarded.json and demo-comparison.json, python-tests.log, extension-tests.log, and environment.json. Demo implementation inspected: both panel.cjs variants, replay.cjs, capture_demo.cjs, the subsequently added analyze_demo.py and demo/README.md.

Source checks covered boundary_cards.py in full, the relevant extraction/rule/compare paths in core.py, lifecycle.py, archive.py, archive_cli.py, mcp_server.py, web/app.js, VS Code extension.js, selected reentrancy.py/parser paths, and the boundary-card/annotation test in tests/test_report_hub.py. This was a targeted implementation-to-paper review, not a whole-repository code audit.

I independently reran the synthetic replay and independently recomputed both analysis reports and card projections using /usr/bin/python3. The reports and cards exactly matched the saved demo-analysis data. Both variants were parsed and retained the same three rule kinds; only the guarded variant's guard-state card had the conditional guard reference. Direct comparison was compatible and returned one removed and one added guard-state finding, with panel.cjs changed. All implementation digests listed in environment.json matched the current files. I inspected the saved 127-test and 9-test successful logs; I did not rerun those complete suites.

## What the evidence supports

The source-backed contribution is coherent: a bounded, rule-driven source analysis feeds four-question review cards; reviewers distinguish whether a relationship holds from whether its protection is sufficient; archived source supports repeatable inspection across entry points. These are implemented capabilities. The manuscript correctly avoids presenting lexical co-occurrence as object identity, candidate links as complete execution paths, annotations as oracle labels, or transport records as proof of agent understanding.

The synthetic example is accurately labeled and reproducible. It establishes publication versus no publication for the stated close-before-resolution schedule. It does not establish repair correctness for arbitrary schedules, real-project detection effectiveness, or a comprehension benefit. The manuscript keeps those boundaries clear. The epoch check is accurately attributed to the reviewer rather than synthesis by the analyzer.

The roadmap distinguishes proposed identity/protection inference, function-level change filtering, framework semantics, and held-out evaluation from current implementation. These proposals should remain outside present-tense capability claims until implemented and evaluated. No unjustified downgrade of implemented source navigation, archive comparison, annotations, or candidate-call filtering is necessary.

## CRITICAL findings

None found within the requested draft-assurance scope. There is no observed fabrication of user-study outcomes, real-project defect counts, or automatic protection proofs.

## MAJOR findings found and resolved during this review

1. **The advertised two-version demonstration lacked a complete checked-in reproduction path.** Initially, capture_demo.cjs archived only the unguarded version, no script regenerated demo-analysis.json, and independently scanning guarded/unguarded directories would give different archive project identities. The current analyze_demo.py reproduces both scans; capture_demo.cjs now changes the source at the same temporary project path, supplies the parent report ID, and writes both archives and a compatible comparison. I inspected the saved comparison: comparable=true, one changed file, and changed guard evidence with unchanged rule kinds. Resolved for the draft.

2. **The scripted annotation cited a nonexistent requirement document.** The original annotation referenced paper/demo/README.md, which did not exist. The file now exists and explicitly specifies the supplied requirement, single replay schedule, exclusions, and synthetic provenance. Resolved.

3. **Cross-interface wording could imply that MCP delivered reviewer notes.** MCP read_report returns frozen report/layer text, while current reviewer notes are available through workbench/CLI JSON and the workbench copy packet. The manuscript now explicitly explains this distinction, and the demo's final paragraph separates frozen MCP material from workbench annotation history. Resolved.

## MINOR revisions

1. **Make Figure 1's arrows match persistence order.** In paper/figures/architecture.tex, the source archive still appears only after the reviewer, while the caption calls the arrows tool data flow. The implementation persists the scan before archive.read_report derives cards, and annotations are appended afterward. A simple source → analysis → archived scan → cards → reviewer chain with a separate reviewer-notes arrow into the archive would remove the ambiguity. Alternatively, label the existing diagram as a conceptual review workflow rather than literal tool data flow. This does not undermine the implemented archive claim.

2. **Qualify the diagnostics statement.** In sections/2_tool.tex, change “Editor diagnostics are informational” to “Review-hint diagnostics are informational.” extension.js uses Information for hints but Warning for incomplete parsing. This small change makes the statement exact.

3. **Make the screenshot demonstrate the two judgments more directly.** Figure 2 is an actual, readable card, but its annotation controls are collapsed and the UI is Chinese. The caption maps the four fields adequately for a draft. Before submission, consider a second crop or visible annotation panel showing confirmed relation plus insufficient/sufficient protection, with English explanatory callouts outside the actual UI. Do not fabricate an English product interface. This would exhibit the distinctive interaction without needing any new study result.

4. **Separate hard submission requirements from planned evidence in the roadmap.** Its final “submission blockers” list groups author/public-tool requirements, a video, independent evaluation, and novelty auditing together. The video is optional under the current CFP; an independent developer study is a research-strengthening task rather than a stated formal tool-track prerequisite. Keep these distinctions explicit so the roadmap does not accidentally turn future work into an invented mandatory condition.

5. **Name the card that contains the added guard when polishing the demo.** The conditional comparison is present in the guard-state card, while the effect-after-await card itself still has no guard references. The current text says “available syntax evidence,” which is accurate. One short phrase identifying the guard-state card would prevent readers from assuming that protection evidence is automatically joined into every effect card.

## Citations and venue checks

The four references support the narrow contexts in which they are used. Sillito et al. supports developer questions and relationship discovery during evolution; the author PDF does not justify a claim that these particular four temporal questions were empirically validated. The manuscript makes no such claim. [Author PDF](https://www.cs.ubc.ca/~murphy/papers/other/asking-answering-fse06.pdf)

The Slicito institutional abstract supports interactive scope reduction, interprocedural data-flow analysis, and symbolic execution. EventRacer's author PDF supports dynamic event-driven race analysis and race coverage. The draft's distinctions are accurate and do not claim superiority. [Slicito institutional record](https://www.d3s.mff.cuni.cz/publications/husak_combining_2025/), [EventRacer author PDF](https://manu.sridharan.net/files/OOPSLA13EventRacer.pdf)

The DOI landing page for Whyline was inaccessible through the web tool, so I checked the authors' project page and linked paper instead. They support the code-and-execution-derived why/why-not question description. The current Amy J. Ko metadata is consistent with the author's current attribution; no name correction is needed. [Whyline author page](https://www.cs.cmu.edu/~NatProg/whyline-java.html), [2008 author PDF](https://www.cs.cmu.edu/~NatProg/papers/Ko2008JavaWhyline.pdf)

These checks are scoped citation verification, not an exhaustive novelty review. Four well-matched references are an acceptable starting set for this draft; broader related-work coverage can improve submission positioning without inventing new results.

I fetched the current official ICPC 2027 tool-track page directly after the web tool could not access it. It specifies IEEEtran conference 10pt, a maximum of four tool-description pages plus one reference page, and nonanonymous submission. Public source or binaries are required. A 3–5 minute video is encouraged and optional; the earlier “must” wording has been removed from the conclusion. [Official ICPC 2027 Tool Demonstration CFP](https://conf.researchr.org/track/icpc-2027/icpc-2027-tool-demonstration)

## Layout and page feasibility

The reviewed PDF has **three body pages including acknowledgment plus one reference page**. It is within the maximum 4+1 allowance; there is no need to pad the body to exactly four pages. I inspected all four freshly rendered pages. No clipping, overlapping elements, unreadable body text, or broken reference/citation markers were observed. The full-width screenshot is readable, though its collapsed annotation panel limits what it illustrates. Table text wraps adequately.

The LaTeX source uses the required 10pt conference class without compsoc/compsocconf. Early TU/ptm font warnings appear in the log, but the final PDF uses embedded Times-compatible Nimbus Roman fonts; those warnings alone do not establish a formatting violation. No formal publisher PDF preflight is claimed. Recompile and reinspect after further edits, particularly changes to the architecture figure or screenshot.

## Submission blockers and research-readiness limits

**Formal/incomplete artifact items:** replace author/affiliation placeholders and make source or binaries available at a stable public URL. The current document honestly identifies an internal prototype and has no usable public artifact link. These do not block delivery of a draft.

**Practical readiness items:** provide a clear installation path and usage instructions, validate the selected distribution in a clean environment, and ensure the live demonstration can be replayed from the released version. These are appropriate maturity tasks; the current unit and extension-runner tests do not certify installation or editor-host behavior across platforms.

**Evidence limitations:** no independent review-instance evaluation or comprehension study exists. Preserve that disclosure. Such evidence would materially improve competitiveness, but its absence is not a reason to fabricate results, claim a hard CFP study requirement, or withhold this working draft. The video, English-facing demonstration materials, and broader novelty comparison are recommended next deliverables.

**Final assessment:** the manuscript now presents the existing prototype honestly, supports its narrow demonstration claims, and leaves proposed capabilities and efficacy claims in future work. It is a usable draft with a concrete improvement path. This verdict remains provisional and same-family.

# Expert review: paused-shared-work

Status: AI-assisted label recoding, pending real expert acceptance.

Parent: `e399b6e8b146ce9d0fa88dd06338ceac8fff6b00b1e46d28084c339e3371db24`

Candidate: `e611f6789497c4f217c6892eb60f01a51ca02871b3f21003f02fe65fe757f024`

Candidate labels: R, L, I, A. Rule text and applicability are unchanged.

Check both each rule and its proposed labels against the actual source; a valid quotation is not automatic semantic support. No new repair replay has occurred.

## R01

Applies when shared cache state outlives observers, each attempt has its own cancellation resource, actual access to the cancellation capability is recorded lazily, and paused continuations resume asynchronously.

**L / documented_requirement**: Applicability separates shared cache, observer lifetime and attempt-local cancellation resources.

- [README.md:16](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:16) — The component owns observer scope; the cache remains outside individual views.
- [README.md:7](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:7) — accessor. Each actual access records consumption; each fetch owns its controller
- [README.md:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:12) — Multiple observers share one fetch. Unconsumed active work can finish into cache

Review boundary: Resource/record contrast alone does not establish I; asynchronous scheduling alone is not O or B.

## R02

For fresh online-mode work that has not entered execution while offline, after the last observer leaves, prevent that attempt from entering on a reconnect continuation with a still-live cancellation signal. Coordinate settlement, state restoration and resource termination according to existing cancellation semantics.

**R / documented_requirement**: Connectivity/network-mode and focus prerequisites govern initial entry versus paused continuation.

- [README.md:9](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:9) — paused continuation resumes on a Promise turn. First start uses network mode;
- [README.md:10](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:10) — continuation also needs focus. 'always' can run offline; 'offlineFirst' allows
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/task.md:1) — with a live signal after reconnect.

**L / documented_requirement**: The last-observer departure must not leave the target attempt eligible to enter with a live cancellation signal.

- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/task.md:1) — with a live signal after reconnect.
- [original.js:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/original.js:12) — if(q.observers.size===0){const a=q.attempt;
- [README.md:13](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:13) — after its view departs; consumed work is physically abortable. Cancellation

Review boundary: Forbidding a live-signal entry does not require zero entries; an already-aborted signal remains a distinct allowed implementation.

## R03

Do not retire all work merely because it is paused, has not entered execution or temporarily has no observers. Background refresh backed by an existing successful cache, and work that has entered execution without accessing its cancellation capability, may continue and write back to the cache under existing rules.

**L / documented_requirement**: Unobserved/paused work is not uniformly retired: cache-backed and entered-unconsumed background work has a different lifetime.

- [README.md:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:12) — Multiple observers share one fetch. Unconsumed active work can finish into cache
- [README.md:13](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:13) — after its view departs; consumed work is physically abortable. Cancellation
- [README.md:16](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:16) — The component owns observer scope; the cache remains outside individual views.

Review boundary: This is a lifecycle exclusion, not a universal cancel-on-zero-observers policy.

## R04

Keep the shared consumption record and the cancellation resource of an individual attempt under their respective ownership. An attempt-local resource does not justify relocating, resetting or making the shared consumption record attempt-local.

**L / source_fact**: Preserve distinct storage/resource ownership of the shared consumption record and attempt controller.

- [original.js:9](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/original.js:9) — Object.defineProperty(context,'signal',{enumerable:true,get(){q.consumed=true;return a.controller.signal;}})
- [README.md:7](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:7) — accessor. Each actual access records consumption; each fetch owns its controller
- [README.md:16](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:16) — The component owns observer scope; the cache remains outside individual views.

Review boundary: Not I: this rule is a static record/resource ownership contrast, without effect rebinding across a transition.

## R05

Preserve sharing across multiple observers, harmless handling of unknown departures, physical abort and prior-state restoration for consumed work, background completion for entered but unconsumed work, and isolation that prevents late completion of an old attempt from overwriting current data.

**L / documented_requirement**: Preserve cancellation settlement/restoration and background work under their documented lifecycle conditions.

- [README.md:13](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:13) — after its view departs; consumed work is physically abortable. Cancellation
- [README.md:14](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:14) — reverts previous query data/status and settles the originating attempt. Late
- [README.md:16](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:16) — The component owns observer scope; the cache remains outside individual views.

**I / documented_requirement**: Late fulfillment stays attached to its originating attempt and cannot become the new attempt result.

- [README.md:15](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:15) — fulfillment cannot become a new attempt's data. Unknown unsubscribe is inert.
- [original.js:7](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/original.js:7) — active(q,a){return q.attempt===a&&!a.settled;}

**A / documented_requirement**: Multiple observers explicitly share one fetch rather than duplicating the same shared execution.

- [README.md:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:12) — Multiple observers share one fetch. Unconsumed active work can finish into cache

## R06

Separately test zero entry or entry with an already-aborted signal after the target offline departure and reconnect; legitimate cached background continuation and later consumption; and continuation eligibility, asynchronous timing, state restoration, observer reuse and late-completion isolation.

**R / documented_requirement**: Verification separates reconnect/network eligibility and delayed continuation entry.

- [README.md:9](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:9) — paused continuation resumes on a Promise turn. First start uses network mode;
- [README.md:10](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:10) — continuation also needs focus. 'always' can run offline; 'offlineFirst' allows
- [task.md:1](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/task.md:1) — with a live signal after reconnect.

**L / documented_requirement**: Verify cache-backed continuation, consumed cancellation and observer departure independently.

- [README.md:12](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:12) — Multiple observers share one fetch. Unconsumed active work can finish into cache
- [README.md:13](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:13) — after its view departs; consumed work is physically abortable. Cancellation
- [README.md:16](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:16) — The component owns observer scope; the cache remains outside individual views.

**I / documented_requirement**: Late completion isolation must respect the originating versus current attempt.

- [README.md:15](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/README.md:15) — fulfillment cannot become a new attempt's data. Unknown unsubscribe is inert.
- [original.js:7](/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-headroom-reuse-pilot-20261109_141850/training/inputs/original.js:7) — active(q,a){return q.attempt===a&&!a.settled;}

Review boundary: No assertion names, scorer policy file or historical test outcome is a classification input.

## Labels not established here

- O: Connectivity eligibility is R; asynchronous resume alone does not establish an additional ordering/reentry obligation.
- B: No requirement here settles all shared work before an observer-departure return.
- F: Old attempt invalidation is L/I, not a demonstrated within-owner revision-ordering policy.

## Decision

The separate `expert-decision-template.json` has no name or approval. Fill it only after a real review, including labels and applicability, then submit the exact candidate digest through `experience-memory expert-review`. Do not approve on behalf of another person.

No whole-task result, gain, loss or classifier accuracy is claimed for this taxonomy migration. Historical outcomes retain their original conditions.

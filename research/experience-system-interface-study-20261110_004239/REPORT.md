# Experience-system foundations: offline first pass

The prior studies produced useful evidence, but interface repair, experience
generation, routing and repair-effect evaluation changed together too often.
Their successes and failures cannot all be attributed to experience quality.
Preserve those histories and separate the research questions going forward.

This directory inventories actual output boundaries (`OUTPUTS.md`) and sets the
research order (`RESEARCH_ORDER.md`). `build_inventory.py` reads historical JSON
without importing experiment runners, creates exact labeled projections and
checks source hashes. `sources.json` records provenance; `integrity.json` records
offline checks. All new documentation is English; historical excerpts are verbatim.

No model, evaluator, scheduler or production-memory update is performed. The
stopped batch remains stopped. Its completed training results remain available;
its missing test maintenance results are not zero-valued failures.

Immediate next work is an agreed output contract and comparison of experience
representations. Unified experience retrieval follows that agreement. Shared
class-prompt evolution is a later, separately measured intervention. This report
does not claim that a unified RAG has already been built or that a representation,
retriever or learned class prompt has been shown superior.

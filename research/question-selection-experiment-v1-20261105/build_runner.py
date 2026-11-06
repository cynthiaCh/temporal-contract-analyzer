"""One-time derivation of the verified previous runner; no historical writes."""
from pathlib import Path
here=Path(__file__).resolve().parent
p=Path('results/question-bank-rag-pilot-v1-20261105/run.py').read_text()
p=p.replace('from source_retrieval import retrieve,terms','from source_retrieval import retrieve\nfrom retriever import retrieve as retrieve_questions, render, CONFIG, load')
p=p.replace("CASES=['listener-registration-order-vanilla','document-submit-snapshot-vanilla','transfer-progress-composition-v4-vanilla']", "CASES=['listener-registration-order-vanilla','document-submit-snapshot-vanilla','handoff-redirect-reentrancy-vanilla','feature-flag-readiness-vue3']")
p=p.replace("ARMS=['A','R','RQ','RG']", "ARMS=['S','F','R']")
a=p.index('def question_retrieve(');b=p.index('\ndef check_frozen',a)
p=p[:a]+'''def question_retrieve(task,source_packet):
    packet=retrieve_questions(task,source_packet['snippets'],BANK)
    return packet,render(packet['selected_ids'],BANK)
'''+p[b:]
p=p.replace("assert all(c in exposure['affected_cases'] for c in CASES)","# Unknown/shared authored lineage is conservatively exploratory, never independent.\n    save(OUT/'split-policy-snapshot.json',exposure)")
p=p.replace("case_meta[case]=dict(case_manifest", "case_meta[case]=dict(independent_unit_id=cm.get('independent_unit_id'),provenance=cm.get('provenance'),validation=cm.get('validation'),source_classification=('development-source' if case in exposure['affected_cases'] else 'related-author-template / independent lineage unverified'),case_manifest")
p=p.replace('range(4)','range(3)').replace('random.Random(20261105)','random.Random(2026110502)')
p=p.replace("question_retrieve(m['task'],files)","question_retrieve(m['task'],source_packet)")
p=p.replace("                generic=(OUT/'generic-checklist.md').read_text()\n                materials=dict(A='',R=source,RQ=source+'\\n'+qtext,RG=source+'\\n'+generic)","                materials=dict(S=source,F=source+'\\n'+render([q['id'] for q in load(BANK)],BANK),R=source+'\\n'+qtext)")
p=p.replace("read(fp)==question_packet","{k:v for k,v in read(fp).items() if k!='elapsed_seconds'}=={k:v for k,v in question_packet.items() if k!='elapsed_seconds'}")
p=p.replace("question_packet['selected_ids'] if arm=='RQ' else []", "question_packet['selected_ids'] if arm=='R' else [q['id'] for q in load(BANK)] if arm=='F' else []")
p=p.replace("OUT/'generic-checklist.md',", "OUT/'retriever.py',OUT/'offline-validation.json',OUT/'PLAN.md',OUT/'prior-audit.json',OUT/'selection-review.json',")
p=p.replace("    tracked=list", "    save(OUT/'selection-review.json',selection_review(runs))\n    tracked=list")
p=p.replace("    protocol=dict(","    tracked += [Path(r['path'])/'jobs/j-001/prompt.md' for r in runs]+[f for r in runs for f in (Path(r['path'])/'input').rglob('*') if f.is_file()]\n    protocol=dict(random_seed=2026110502,retrieval_config=CONFIG,output_limit='Same Workbench command and inherited local config as prior round; no explicit output token cap in prior script',selection_review_at=archive.now(),")
p=p.replace("max_parallel=4","max_parallel=3").replace("schema_version='question-bank-rag-pilot-1'","schema_version='question-selection-v1'")
p=p.replace("question_selection='Frozen BM25 automatic top2; task + visible candidate text; no outcome-conditioned selection'", "question_selection='Frozen weighted lexical BM25 with score >=5 and >=3 English matches; task + SAME retrieved code snippets only; top2, may abstain'")
p=p.replace("hypothesis='RQ incremental effect over same source RAG R; generic comparator RG controls for receiving review questions.'", "hypothesis='R reduces irrelevant questions and costs relative to F; compare whole behavior and losses against S without presupposing benefit.'")
p=p.replace("primary='Whole-task PASS per case and arm; descriptive paired block outcomes RQ vs R and RQ vs RG; no significance or generalization claim.'", "primary='Whole-task PASS, loss of originally passed checks, unnecessary behavior changes on negative case. Descriptive only, four cases, two repeats per condition.'")
p=p.replace("exposure='All3 cases and same-source variants are development-source; never independent generalization tests. No unseen-source claim.'", "exposure='Exploratory only: 2 direct development cases, 1 related authored extension, 1 shared-template negative; no independently certified generalization case.'")
p=p.replace('ThreadPoolExecutor(max_workers=4)','ThreadPoolExecutor(max_workers=3)')
insert='''
def selection_review(runs):
    # Researcher applicability review of visible task/code BEFORE launches/outcomes.
    judgments={
      'listener-registration-order-vanilla':dict(applicable=['TCQ-001','TCQ-002','TCQ-003'],uncertain=[],evidence='subscription.js connects before addEventListener; decode.then(receive) survives detach; workspace-navigation.js permits synchronous select/hide from publish.'),
      'document-submit-snapshot-vanilla':dict(applicable=['TCQ-003','TCQ-004','TCQ-005'],uncertain=[],evidence='README requires close/open settlement, accepted submit receipt and visit-bound notice; store notifications run inline and may navigate/edit.'),
      'handoff-redirect-reentrancy-vanilla':dict(applicable=['TCQ-003'],uncertain=[],evidence='README permits synchronous navigation during handoff; later-started navigation wins. Synchronous store writes, no deferred work or async result.'),
      'feature-flag-readiness-vue3':dict(applicable=[],uncertain=[],evidence='runTarget waits for loadedFlag; runAdjacent is emergency fail-open. No listener registration, visit retirement, callback reentry, persistent history/display split or deferred writes.')}
    for c,v in judgments.items():
      selected=next(r['question_ids'] for r in runs if r['case']==c and r['arm']=='R')
      v.update(selected=selected,missed=sorted(set(v['applicable'])-set(selected)),irrelevant=sorted(set(selected)-set(v['applicable'])-set(v['uncertain'])))
    return dict(reviewed_at=archive.now(),stage='before any formal call or behavior score; main-agent researcher review, not independent human/blind review',cases=judgments)

'''
p=p.replace('def prepare():',insert+'def prepare():')
(here/'run.py').write_text(p)

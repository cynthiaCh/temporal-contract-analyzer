import json
from pathlib import Path
from retriever import retrieve,render,load,CONFIG
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BANK=ROOT/'research/temporal-contract-question-bank-v1/questions.jsonl'
def stable(r):return {k:v for k,v in r.items() if k!='elapsed_seconds'}
checks=[]
for text in ['', 'Compute the total price of three oranges.', 'Fix premium action readiness for a remote feature flag.']:
 r=retrieve(text,[],BANK);assert not r['selected_ids'];checks.append(dict(query=text,selected=r['selected_ids']))
# Archived developer inputs only, no model outcomes read.
old=ROOT/'results/question-bank-rag-pilot-v1-20261105'
runs=json.loads((old/'runs.json').read_text())
for case in sorted({r['case'] for r in runs}):
 folder=Path(next(r['path'] for r in runs if r['case']==case));sp=json.loads((folder/'source-retrieval.json').read_text())
 r=retrieve(sp['query'],sp['snippets'],BANK)
 assert stable(r)==stable(retrieve(sp['query'],sp['snippets'],BANK)) and len(r['selected_ids'])<=2
 checks.append(dict(development_case=case,ranked=r['ranked'],selected=r['selected_ids']))
for q in load(BANK):assert render([q['id']],BANK).split('\n\n',2)[2].strip() in render([x['id'] for x in load(BANK)],BANK)
assert all(x not in render([q['id'] for q in load(BANK)],BANK) for x in ['evidence_status','provenance.json','common_wrong_repairs'])
(HERE/'offline-validation.json').write_text(json.dumps(dict(status='PASS',config=CONFIG,threshold_rationale='Conservative a-priori floor 5.0 and 3 distinct English support terms to avoid one-word overlap. Checked only on archived development snippets and synthetic unrelated queries; not optimized for recall or behavior. Chinese-only queries intentionally fail English-support gate: limitation.',checks=checks),ensure_ascii=False,indent=2)+'\n')
print('offline PASS')

"""Post-hoc hygiene sensitivity only; never changes a delivered query or prompt."""
from copy import deepcopy
from run import *
from retriever import retrieve as question_lookup
case='handoff-redirect-reentrancy-vanilla';r=next(r for r in read(OUT/'runs.json') if r['case']==case);folder=Path(r['path']);sp=read(folder/'source-retrieval.json');old=read(folder/'question-retrieval.json');snippets=deepcopy(sp['snippets'])
for s in snippets:
 if s['file']=='package.json':
  s['code']=s['code'].replace('handoff-redirect-reentrancy-fixture','')
new=question_lookup(sp['query'],snippets,BANK)
save(OUT/'protocol-deviation.json',dict(recorded_at=archive.now(),affected_case=case,affected_runs=[r['id'] for r in read(OUT/'runs.json') if r['case']==case],requirement='Do not use case names as retrieval evidence',finding='Visible source RAG included package.json name=handoff-redirect-reentrancy-fixture. Its reentrancy token contributed to TCQ-003 lexical score. Preflight checked exact case ID absence but missed this fixture-name variant.',status='protocol deviation; preserve all deployed bytes/results; exclude this case in additional strict-subset summaries',original_record=str(folder/'question-retrieval.json'),original_selected=old['selected_ids'],original_ranked=old['ranked'],masked_package_name_sensitivity=new,selected_ids_unchanged=old['selected_ids']==new['selected_ids'],selection_threshold_and_all_prompts_unchanged=True,formal_retries=0,limitation='Unchanged selection after masking does not retroactively make the deployed query compliant. Post-hoc sensitivity is not a replacement run.'))
print(old['selected_ids'],new['selected_ids'])

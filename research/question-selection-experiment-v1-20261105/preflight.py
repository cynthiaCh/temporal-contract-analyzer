from run import *
from retriever import render,NOTICE
p=check_frozen();runs=read(OUT/'runs.json');assert len(runs)==24
checks=[]
for case in CASES:
 rr=[r for r in runs if r['case']==case];base=None;source=None
 for r in rr:
  folder=Path(r['path']);m=read(folder/'manifest.json');j=m['jobs'][0];prompt=(folder/'jobs/j-001/prompt.md').read_text();sp=read(folder/'source-retrieval.json');qp=read(folder/'question-retrieval.json')
  if source is None:source=(OUT/'packets'/case/'S.md').read_text()
  material=(OUT/'packets'/case/(r['arm']+'.md')).read_text()
  assert material.startswith(source)
  assert prompt.endswith(material+'\n</candidate-assistance>\n')
  original=prompt.split('\n<candidate-assistance>\n')[0]
  if base is None:base=original
  assert base==original and sha(prompt)==r['prompt_sha256']
  assert m['model']==MODEL and m['effort']==EFFORT and m['timeout']==600 and m['mode']=='workspace-write'
  for name,h in r['input_files'].items():assert sha((folder/'input'/name).read_bytes())==h
  assert qp['query']==m['task']+'\n\n'+'\n\n'.join(s['code'] for s in sp['snippets'])
  assert r['question_ids']==([] if r['arm']=='S' else [q['id'] for q in load(BANK)] if r['arm']=='F' else qp['selected_ids'])
  assert (NOTICE in prompt)==(r['arm']!='S')
  cmd=Workbench(OUT/'preflight-reports',node=str(NODE)).command(m,folder/'jobs/j-001/workspace',folder/'jobs/j-001/answer.md')
  assert cmd[cmd.index('-m')+1]==MODEL and 'model_reasoning_effort="low"' in cmd
  checks.append(dict(id=r['id'],case=case,arm=r['arm'],command=cmd,question_ids=r['question_ids']))
save(OUT/'preflight.json',dict(status='PASS',checked_at=archive.now(),checks=checks,source_retriever_sha256=sha((OUT/'source_retrieval.py').read_bytes()),prior_source_retriever_sha256=sha((REPO/'results/question-bank-rag-pilot-v1-20261105/source_retrieval.py').read_bytes())))
print('24 prompts and commands PASS; shared original task/source bytes verified')

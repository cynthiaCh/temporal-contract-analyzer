"""Standalone deterministic lexical retrieval. Only questions.jsonl is read."""
from collections import Counter
import hashlib,json,math,re,time
from pathlib import Path
CONFIG=dict(fields={'title':2,'retrieval.zh_keywords':3,'retrieval.en_keywords':3,'retrieval.description':2,'core_question':2,'preconditions':1,'verification_methods':1},k1=1.5,b=.75,threshold=5.0,minimum_distinct_english_matches=3,top_k=2,tokenizer='camel/snake English words + Chinese bigrams; unique query terms; fixed stopwords',dedup='one result per stable ID; identical core_question collapsed; score descending, ID ascending')
STOP=set('a an the to of and or in on with for is be by from that this it as may can must only current same before after when then return function const let var export import if else null true false new value text id read write task source'.split())
def terms(s):
 s=re.sub(r'([a-z])([A-Z])',r'\1 \2',s).replace('_',' ').lower()
 en=[x for x in re.findall(r'[a-z][a-z0-9]*',s) if x not in STOP]
 zh=[z[i:i+2] for z in re.findall(r'[\u4e00-\u9fff]+',s) for i in range(len(z)-1)]
 return en+zh
def field(q,path):
 v=q
 for k in path.split('.'):v=v[k]
 return v if isinstance(v,str) else '\n'.join(v)
def load(bank):
 qs=[json.loads(s) for s in Path(bank).read_text().splitlines() if s.strip()]
 assert len(qs)==5 and len({q['id'] for q in qs})==5
 return qs
def retrieve(task,snippets,bank):
 start=time.monotonic();qs=load(bank)
 # Code bytes only: no case names, source paths, scores or researcher labels.
 query=task+'\n\n'+'\n\n'.join(s['code'] for s in snippets)
 qt=set(terms(query));docs=[]
 for q in qs:
  c=Counter()
  for f,w in CONFIG['fields'].items():
   for t,n in Counter(terms(field(q,f))).items():c[t]+=n*w
  docs.append((q,c,sum(c.values())))
 df=Counter(t for _,c,_ in docs for t in c);avg=sum(n for _,_,n in docs)/len(docs);ranked=[]
 for q,c,n in docs:
  matched=sorted(qt&c.keys());en=[t for t in matched if re.fullmatch('[a-z][a-z0-9]*',t)]
  contrib={t:math.log(1+(len(docs)-df[t]+.5)/(df[t]+.5))*c[t]*2.5/(c[t]+1.5*(.25+.75*n/avg)) for t in matched}
  score=sum(contrib[t] for t in sorted(contrib))
  eligible=score>=CONFIG['threshold'] and len(en)>=CONFIG['minimum_distinct_english_matches']
  ranked.append(dict(id=q['id'],score=score,matched_terms=matched,english_match_count=len(en),term_contributions=contrib,eligible=eligible,reason='eligible' if eligible else 'below score threshold' if score<CONFIG['threshold'] else 'insufficient distinct English support'))
 ranked.sort(key=lambda x:(-x['score'],x['id']));selected=[];seen=set()
 by={q['id']:q for q in qs}
 for r in ranked:
  if not r['eligible']:continue
  core=by[r['id']]['core_question']
  if core in seen:r['reason']='duplicate core question'
  elif len(selected)>=CONFIG['top_k']:r['reason']='eligible but outside top-k'
  else:selected.append(r['id']);seen.add(core);r['reason']='selected: threshold and lexical support passed, within top-k'
 return dict(query=query,query_sha256=hashlib.sha256(query.encode()).hexdigest(),query_summary=dict(task_characters=len(task),snippet_characters=sum(len(s['code']) for s in snippets),unique_terms=len(qt),terms=sorted(qt)),bank_sha256=hashlib.sha256(Path(bank).read_bytes()).hexdigest(),config=CONFIG,ranked=ranked,selected_ids=selected,return_reason='selected qualifying nonduplicate questions' if selected else 'abstain: no qualifying question',elapsed_seconds=time.monotonic()-start)
NOTICE='以下问题是待核查提示，不代表当前项目存在缺陷，也不构成额外业务要求。仅根据当前任务和候选源码决定是否适用。'
def render(ids,bank):
 qs={q['id']:q for q in load(bank)}
 # Same allowlisted format for F and R. No research status, provenance or repairs.
 fields=['id','title','core_question','preconditions','event_orders','source_evidence_to_seek','verification_methods','non_applicability_and_preserved_behavior']
 return '# Temporal contract review questions\n\n'+NOTICE+'\n\n'+'\n\n'.join(json.dumps({f:qs[i][f] for f in fields},ensure_ascii=False,indent=2) for i in ids)+'\n'

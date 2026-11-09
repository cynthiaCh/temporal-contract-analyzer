"""Fresh training-only ledger and locked applicability from reviewed analysis."""
import json,shutil
from pathlib import Path
from archive import save,sha
from evidence import verify_ledger,rebuild_feedback,assemble_payload
from handoff import VERSION
from toolflow import PREDICATES
A=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())

INSTRUCTIONS='''Generate ONE fresh experience rule revision from this batch's training only. No old experience seed, reference patch, test data, tools, alternatives, retries or extra judge.
Only output rules and unresolved under the supplied typed schema. Python copies version/requires/excludes/applicability from the separately locked source-reviewed training analysis. Do not output or alter these metadata fields. If that scope is unsupported, record an unresolved policy/applicability issue instead of assuming it met.
Use 5-7 concise single-source rules, each body once, all categories applicability/event_relation/verification/preservation/exclusion; Chinese preferred. Bodies max480 characters. Python numbers and joins exact bodies, without policy synthesis or prose edits. Do not emit duplicate full text, model rule IDs or copyable patches.
support/conditions/counterevidence are existing evidence IDs, preserve only constraint IDs; explanation text goes in explanation fields. Every normative support must include relevant documented requirement/source fact/preservation inference, not observations alone. Cover every preservation constraint and mandatory counterexample. A valid ID does not establish entailment. Do not infer policy or root cause from check labels.
Bodies delivered to repair agents must not contain case IDs, paths, grading identifiers, evidence management IDs, specialized field/function names or directly copyable fixes. Express mechanism conditions, event relations, validation actions, preserved behavior and exclusions. No unique implementation is required.
Use the actual tasks/docs/source, both AUTO patches, complete results and traces. Preserve original successes and repaired successes, report regressions and unknowns. Current defective source is not automatically preservation policy. Repair final claims are unverified and cannot override execution/score evidence. Separate source facts, documented requirements, observed effects, source reasoning, hypotheses and unknown causal contributions; no controlled causal intervention has been run.
Use predicate definitions literally; distinguish boundary-return persistence from eventual retained audit, delayed persistent work from a transient discard-on-hide consumer, pending batch ownership from active-view display and synchronous reentrant newer navigation from old continuation. Derive current obligations from supplied source/task, not another task's ownership or cancellation policy. Never add blanket flushing or cancelling across unrelated consumers. If evidence is insufficient, narrow rules or retain an unresolved issue.
No benefit is established by generating a rule. Development revalidation is a process check, not independent testing or stability proof. Subsequent review is execution-agent AI-assisted evidence review, not independent human approval.
Complete frozen training payload below uses lossless repeated-subtree references: substitute each object containing only $same with its identical shared_values entry recursively. These keys are serialization only, not evidence IDs; no source/check/trace/success/regression is removed:
'''

def reference_view(value):
 dictionary={};seen={}
 def encode(x):
  key=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
  if len(key)<320:return x
  if key in seen:return {'$same':seen[key]}
  out={k:encode(v) for k,v in x.items()} if isinstance(x,dict) else [encode(v) for v in x] if isinstance(x,list) else x
  token='D%04d'%(len(dictionary)+1);dictionary[token]=out;seen[key]=token;return {'$same':token}
 root=encode(value)
 def expand(x):
  if isinstance(x,dict) and set(x)=={'$same'}:return expand(dictionary[x['$same']])
  if isinstance(x,dict):return {k:expand(v) for k,v in x.items()}
  if isinstance(x,list):return [expand(v) for v in x]
  return x
 assert expand(root)==value
 return {'serialization':'lossless-repeated-subtree-references-1','shared_values':dictionary,'payload':root}

def build():
 root=A/'training';root.mkdir(exist_ok=False);files={};entries=[]
 def cp(src,name,role):
  dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);files[name]={'role':role,'sha256':sha(dest)}
 cp(A/'materials/D/task.md','inputs/task.md','training_task')
 for f in (A/'materials/D/candidate').rglob('*'):
  if f.is_file() and f.suffix in ['.md','.js']:cp(f,'inputs/source/'+str(f.relative_to(A/'materials/D/candidate')),'training_document' if f.suffix=='.md' else 'training_source')
 cp(A/'materials/D/standards.json','inputs/standards.json','training_standard')
 cp(A/'materials/D/evaluation/recovery-rubric.json','inputs/rubric.json','training_standard')
 cp(A/'derived/D/analysis.json','inputs/analysis.json','training_contract')
 cp(A/'calibration/D/original/stdout.json','inputs/original-score.json','training_score')
 for i,rec in enumerate(read(A/'development/baselines.json'),1):
  arc=A/'runs'/rec['slot']/'archive'
  for src,name,role in [('score/stdout.json','score.json','training_score'),('patch.diff','patch.diff','training_patch'),('raw-answer.txt','delivery.json','training_public_delivery')]:cp(arc/src,f'inputs/auto{i}/'+name,role)
  for f in (arc/'final-candidate').rglob('*.js'):cp(f,f'inputs/auto{i}/final/'+str(f.relative_to(arc/'final-candidate')),'training_source')
 def lines(eid,kind,statement,file,start=1,end=None):
  text=(root/file).read_text().splitlines();end=end or len(text)
  entries.append({'id':eid,'kind':kind,'statement':statement,'author':'execution_agent_source_review_AI_assisted','related':[],
   'anchors':[{'type':'lines','file':file,'start':start,'end':end,'quote':'\n'.join(text[start-1:end])}]})
 lines('R-task','documented_requirement','Introduce latest-only quiet-interval document writes, keep later bursts and other behavior; preview change is outside scope.','inputs/task.md')
 lines('R-doc','documented_requirement','README explicitly requires departed latest text available before close/open returns, later-started reentrant navigation wins, and transient preview retains 40ms/discard-on-hide.','inputs/source/README.md')
 lines('R-badge','documented_requirement','Source comments retire the departed badge at the beginning of close/open; document persistence is a separate responsibility.','inputs/source/src/save-status.js')
 lines('F-editor','source_fact','Current editor writes immediately and has no buffered handoff; it is the maintenance starting point, not policy to retain the reported write frequency.','inputs/source/src/editor.js')
 lines('F-batch','source_fact','Current trailing utility retires the pending batch and timer before work; cancel discards, flush runs pending work now.','inputs/source/src/trailing-task.js')
 lines('F-store','source_fact','Store writes first then synchronously notifies a snapshot, skipping removed subscriptions.','inputs/source/src/draft-store.js')
 lines('F-navigation','source_fact','Workspace onSaved receives navigation synchronously; editor is reused across open/close and output render sinks.','inputs/source/src/workspace.js')
 lines('F-preview','source_fact','Adjacent preview currently uses the same utility with a 40ms delay and discard on hide.','inputs/source/src/search-preview.js')
 analysis=read(A/'derived/D/analysis.json');positive=list(PREDICATES)[:10];app=[]
 for fact in analysis['facts']:
  if fact['predicate'] not in positive or fact['state']!='known':continue
  ids=[]
  for ref in fact['evidence']:
   name='inputs/task.md' if ref['file']=='TASK' else 'inputs/source/'+ref['file'];eid='M-'+fact['predicate']
   lines(eid,'source_fact','Frozen source-bound analysis marks this mechanism known; source interpretation was checked by execution agent: '+PREDICATES[fact['predicate']],name,ref['line'],ref['line']);ids.append(eid)
  app.append({'predicate':fact['predicate'],'status':'known','evidence':ids,'explanation':'Exact known mechanism from the frozen source-reviewed training analysis, not a newly generated applicability claim.'})
 locked={'version':VERSION,'requires':[r['predicate'] for r in app],'excludes':[],'applicability':app}
 assert locked['requires'];save(A/'locked-metadata.json',locked)
 constraints=[{'id':'C-bursts','statement':'Latest-only quiet burst, subsequent bursts and reentrant newly queued batches remain live.','evidence':['R-task','F-batch']},
  {'id':'C-departure','statement':'Commit departed document under its bound key before boundary returns, without duplicate stale timer writes.','evidence':['R-doc','F-batch','F-store']},
  {'id':'C-ownership','statement':'Retire old badge before handoff notifications, preserve live badges, and let newer-started navigation own the result.','evidence':['R-doc','R-badge','F-store','F-navigation']},
  {'id':'C-preview','statement':'Preserve unrelated preview 40ms, discard-on-hide and reuse plus public APIs.','evidence':['R-doc','R-task','F-preview']}]
 ledger={'schema':'evidence-ledger-1','scope':'Only this batch D sources and two AUTO outcomes, no test feedback, reference patch or old experience',
  'files':files,'entries':entries,'constraints':constraints,'mandatory_counterevidence':[],
  'causal_interventions':[],'verified_causes':[],
  'feedback_inputs':{'original':'inputs/original-score.json','repairs':['inputs/auto1/score.json','inputs/auto2/score.json'],'standards':'inputs/standards.json'}}
 fb=rebuild_feedback(root,ledger)
 for i,row in enumerate(fb['runs'],1):
  raw=read(root/f'inputs/auto{i}/score.json')
  for ordinal,relation in enumerate(row['differences']):
   k=relation['effect'];eid=f'O-auto{i}-{ordinal}';pointer='/schedules/'+k if k in raw['schedules'] else '/observed_effects/'+k
   value=raw['schedules'][k] if k in raw['schedules'] else raw['observed_effects'][k]
   entries.append({'id':eid,'kind':'observed_result','statement':'Complete failing relation, actual/expected checks and available trace; not isolated causation.','author':'python_generic_score_extraction','related':[],
    'anchors':[{'type':'json','file':f'inputs/auto{i}/score.json','pointer':pointer,'value':value}]})
   ledger['mandatory_counterevidence'].append(eid)
 entries.append({'id':'U-cause','kind':'unknown','statement':'No independent causal isolation; model final delivery is an unverified claim.','author':'execution_agent','related':[],'anchors':[]})
 save(root/'evidence-ledger.json',ledger);save(root/'feedback.json',fb);verify_ledger(root,ledger)
 payload=assemble_payload(root,ledger,fb)
 for m in payload['materials']:
  if m['artifact'].endswith('.json'):m['content']=json.loads(m['content'])
 payload['mechanism_predicates']=PREDICATES;payload['locked_metadata']=locked
 payload['output_protocol']={'mandatory_counterevidence':ledger['mandatory_counterevidence'],'preservation_constraints':[c['id'] for c in constraints]}
 save(root/'reflection-input.json',payload);view=reference_view(payload);save(root/'model-view.json',view)
 return ledger,INSTRUCTIONS+json.dumps(view,ensure_ascii=False,separators=(',',':'))

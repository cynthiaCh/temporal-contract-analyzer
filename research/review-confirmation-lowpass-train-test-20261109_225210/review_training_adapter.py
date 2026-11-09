"""Named review-editor evaluation adapter, not generic policy inference."""
import ast,json,shutil
from pathlib import Path
from archive import save,sha
from evidence import verify_ledger,rebuild_feedback,assemble_payload
from handoff import VERSION
from toolflow import PREDICATES
A=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
INSTRUCTIONS='''Generate ONE fresh English experience rule revision from this batch's TRAINING material only. No old experience, reference patch, test trajectory, tools, alternatives, retries or extra judge.
Output only rules and unresolved under the typed schema. Python copies version/requires/excludes/applicability from the separately source-reviewed training analysis. Do not output or alter those fields. If that scope is unsupported, report an unresolved policy/applicability issue rather than assuming it met.
Use 5-7 concise rules, each body once and at most 480 characters. Cover applicability, event_relation, verification, preservation and exclusion. Python numbers and concatenates exact bodies; it does not repair policy. No duplicated full text, model-written rule IDs or directly copyable patches.
support/conditions/counterevidence contain existing evidence IDs only; preserve contains constraint IDs only. Put explanation prose in explanation fields. Normative rules require genuinely relevant documented requirements, source facts or preservation inferences, not observations alone. Cover every preservation constraint and mandatory counterevidence. ID existence does not prove entailment.
Delivered bodies must not contain case IDs, grading identifiers, file paths, evidence-management IDs, specialized field/function names or code patches. Express ordinary temporal guidance, not a unique implementation when alternatives preserve the same relations.
Read the full task/docs/original source, both actual AUTO patches and final source, complete expected/actual checks and event traces. Separate original successes, actual repair successes, improvements, regressions, source facts, policy inferences, causal hypotheses and unknowns. Defective starting behavior is not automatically preservation policy. Repair-Agent claims cannot override source or execution. No controlled intervention isolated causes; do not claim verified causes from assertion names or co-occurring changes.
The named evaluator adapter labels preservation inferences instead of pretending all policies are literal documentation. Check actual task/source anchors. Do not create business policy to explain expected results. Narrow unsupported scope or retain an unresolved issue. Unknown cause is not unknown policy; a missing proven stable repair is not itself a policy contradiction.
Use predicates literally. Distinguish accepted durable work, action-entry values and current-view capabilities. Generic resource ownership does not establish ownership of other state. Preserve unrelated consumers' documented boundaries. The question is whether a grounded candidate improves fixed baselines while recording every loss.
Development is not independent testing or stability proof. Review is execution-agent AI-assisted, not independent human approval. Write all generated prose in English.
The complete training payload uses lossless repeated-subtree references: recursively replace each object containing only $same with its identical shared_values item. These keys are not evidence IDs. No source, check, trace, success, regression or unknown is removed. Non-ASCII evidence/test values are losslessly JSON-escaped, not translated or edited:
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
  dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);files[name]={'role':role,'sha256':sha(dest)}
 cp(A/'materials/D/task.md','inputs/task.md','training_task')
 for f in (A/'materials/D/candidate').rglob('*'):
  if f.is_file() and f.suffix in ['.md','.py']:cp(f,'inputs/source/'+str(f.relative_to(A/'materials/D/candidate')),'training_document' if f.suffix=='.md' else 'training_source')
 for src,name,role in [('materials/D/standards.json','inputs/standards.json','training_standard'),('materials/D/evaluation/recovery-rubric.json','inputs/rubric.json','training_standard'),('derived/D/analysis.json','inputs/analysis.json','training_contract'),('calibration/D/original/stdout.json','inputs/original-score.json','training_score')]:cp(A/src,name,role)
 for i,rec in enumerate(read(A/'development/baselines.json'),1):
  arc=A/'runs'/rec['slot']/'archive'
  for src,name,role in [('score/stdout.json','score.json','training_score'),('patch.diff','patch.diff','training_patch'),('raw-answer.txt','delivery.json','training_public_delivery')]:cp(arc/src,'inputs/auto%d/'%i+name,role)
  for f in (arc/'final-candidate').rglob('*.py'):cp(f,'inputs/auto%d/final/'%i+str(f.relative_to(arc/'final-candidate')),'training_source')
 def lines(eid,kind,statement,file,start=1,end=None,related=None):
  text=(root/file).read_text().splitlines();end=end or len(text);assert 1<=start<=end<=len(text)
  entries.append({'id':eid,'kind':kind,'statement':statement,'author':'execution_agent_named_review_evaluation_adapter_AI_assisted','related':related or [],'anchors':[{'type':'lines','file':file,'start':start,'end':end,'quote':'\n'.join(text[start-1:end])}]})
 py='inputs/source/src/workflow.py';tree=ast.parse((root/py).read_text());classes={n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
 def cls(eid,name,statement):n=classes[name];lines(eid,'source_fact',statement,py,n.lineno,n.end_lineno)
 lines('R-task','documented_requirement','Coalesce editor input into latest-only 120ms quiet saves; later bursts remain usable. Preserve supported behavior and synchronous public interfaces; preview is outside scope.','inputs/task.md')
 lines('R-doc','documented_requirement','Documents and durable queue are separate services. Preserve synchronous APIs and injected contracts; reopening creates a fresh visit and restores persisted text. Acquired outlets own visits.','inputs/source/README.md')
 doc=(root/'inputs/source/README.md').read_text().splitlines();outlet=next(i for i,l in enumerate(doc,1) if l.startswith('An outlet acquires'))
 lines('R-outlet','documented_requirement','An outlet captures the visit active when binding is called, cannot infer an earlier action from a receipt, and same-document reopening creates a new identity.','inputs/source/README.md',outlet,outlet)
 cls('F-store','Store','Storage updates document and revision before synchronously invoking still-subscribed listeners; it does not define UI ownership.')
 cls('F-queue','Archive','Queue capture constructs and retains an immutable receipt, then synchronously notifies integrations. Repeated calls append distinct accepted actions.')
 cls('F-batch','Trailing','Pending value and timer are cleared before work; cancel discards pending work. Empty text differs from no pending value.')
 cls('F-capability','Confirmation','Acquisition captures the current native visit. Later display compares its exact owner identity with the current visit.')
 cls('F-commands','Workspace','Edits currently write immediately. Commands snapshot action data and acquire capability before queue delivery. Retirement removes old subscription/current visit. Navigation counters exist but do not guard a newly introduced reentrant flush.')
 cls('F-preview','Preview','Preview uses a 40ms quiet task and discards pending publication when hidden, unlike document persistence boundaries.')
 lines('P-departure','preservation_inference','After buffering, preserving original synchronous command behavior requires accepted text readable under its original key when navigation returns. Retire old-view status before handoff notifications. Derived from preservation, immediate original writes, persistent store and subscription retirement; not a claimed literal README sentence.',py,classes['Workspace'].lineno,classes['Workspace'].end_lineno,['R-task','R-doc','F-store','F-commands'])
 lines('P-action','preservation_inference','Preserve entry-owned snapshots and returned immutable receipts across inline store/queue integrations. Buffering cannot make queue capture observe unpersisted accepted data or retarget an accepted action to reentered state. Durable result and view eligibility are separate.',py,classes['Workspace'].lineno,classes['Workspace'].end_lineno,['R-task','R-doc','F-store','F-queue','F-capability'])
 lines('P-reentry','preservation_inference','New navigation accepted by an inline integration must not be overwritten by an older suspended handoff. Reentrant input keeps its own later batch, consistent with synchronous APIs, callback contracts and clearing old batch state before work. Existing counters are a clue, not proof this guard works.',py,classes['Workspace'].lineno,classes['Workspace'].end_lineno,['R-task','R-doc','F-store','F-commands','F-batch'])
 analysis=read(A/'derived/D/analysis.json');app=[]
 for fact in analysis['facts']:
  if fact['predicate'] not in list(PREDICATES)[:10] or fact['state']!='known':continue
  assert len(fact['evidence'])==1;ref=fact['evidence'][0];file='inputs/task.md' if ref['file']=='TASK' else 'inputs/source/'+ref['file'];eid='M-'+fact['predicate'];lines(eid,'source_fact','Admitted source-bound training analysis identifies: '+PREDICATES[fact['predicate']],file,ref['line'],ref['line']);app.append({'predicate':fact['predicate'],'status':'known','evidence':[eid],'explanation':'Known mechanism from fixed training analysis and visible-source AI review, not test results.'})
 locked={'version':VERSION,'requires':[r['predicate'] for r in app],'excludes':[],'applicability':app};assert locked['requires'];save(A/'locked-metadata.json',locked)
 constraints=[{'id':'C-bursts','statement':'Latest-only 120ms saves, reusable bursts and reentrantly queued next input remain live.','evidence':['R-task','F-batch']},{'id':'C-departure','statement':'Accepted text stays under its bound key before boundary return, without duplicate stale timers or old-view status.','evidence':['P-departure','F-batch','F-store']},{'id':'C-action','statement':'Entry-owned immutable receipts, persistence before capture, retained results after navigation, repeated and empty-text actions.','evidence':['P-action','F-queue','F-commands']},{'id':'C-outlet','statement':'Acquired view capability remains bound to its true visit; no inferred earlier owner or revival on same-key reopening.','evidence':['R-outlet','F-capability','P-action']},{'id':'C-reentry','statement':'Newer inline navigation retains ownership; normal live status and later input remain usable.','evidence':['P-reentry','F-store','F-batch']},{'id':'C-preview','statement':'Unrelated preview retains 40ms, discard-on-hide and reuse; no scope extension.','evidence':['R-task','R-doc','F-preview']},{'id':'C-interfaces','statement':'Preserve synchronous APIs, injected interfaces, teardown, dependency/build configuration and independent resources.','evidence':['R-task','R-doc','F-commands']}]
 ledger={'schema':'evidence-ledger-1','scope':'Only new training source and two new AUTO runs; no reference patch, old experience, historical patch or test feedback.','files':files,'entries':entries,'constraints':constraints,'mandatory_counterevidence':['R-outlet','F-preview'],'causal_interventions':[],'verified_causes':[],'feedback_inputs':{'original':'inputs/original-score.json','repairs':['inputs/auto1/score.json','inputs/auto2/score.json'],'standards':'inputs/standards.json'}}
 fb=rebuild_feedback(root,ledger)
 for i,row in enumerate(fb['runs'],1):
  raw=read(root/('inputs/auto%d/score.json'%i))
  for ordinal,relation in enumerate(row['differences'],1):
   key=relation['effect'];eid='O-auto%d-%02d'%(i,ordinal);pointer='/schedules/'+key if key in raw['schedules'] else '/observed_effects/'+key;value=raw['schedules'][key] if key in raw['schedules'] else raw['observed_effects'][key];entries.append({'id':eid,'kind':'observed_result','statement':'Actual failed relation with complete expected/actual checks and trace, not isolated causation.','author':'python_generic_score_extractor','related':[],'anchors':[{'type':'json','file':'inputs/auto%d/score.json'%i,'pointer':pointer,'value':value}]});ledger['mandatory_counterevidence'].append(eid)
 entries.append({'id':'U-cause','kind':'unknown','statement':'No independently verified causal contribution. Public model claims remain unverified.','author':'execution_agent','related':[],'anchors':[]})
 save(root/'evidence-ledger.json',ledger);save(root/'feedback.json',fb);verify_ledger(root,ledger);payload=assemble_payload(root,ledger,fb)
 for m in payload['materials']:
  if m['artifact'].endswith('.json'):m['content']=json.loads(m['content'])
 payload['mechanism_predicates']=PREDICATES;payload['locked_metadata']=locked;payload['output_protocol']={'mandatory_counterevidence':ledger['mandatory_counterevidence'],'preservation_constraints':[c['id'] for c in constraints]};save(root/'reflection-input.json',payload);view=reference_view(payload);save(root/'model-view.json',view)
 return ledger,INSTRUCTIONS+json.dumps(view,ensure_ascii=True,separators=(',',':'))

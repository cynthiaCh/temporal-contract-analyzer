"""One authorized training-only evolution; explicit stages, no retry or scheduler."""
import copy,json,shutil,subprocess,sys,tempfile,time,unittest
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
sys.path.insert(0,str(A))
import runner
from archive import save,sha,inventory,digest
from evidence import verify_ledger,assemble_payload,rebuild_feedback,object_digest
from feedback import feedback
from handoff import make_schema,validate_candidate,render,numbered_rules,semantic_gate
from toolflow import PREDICATES,maintenance_prompt
from report_common import aggregate
P=A.parent/'transfer-progress-one-pair-pilot-v2a-20261109_092536'
TARGETS=['progress-reopen-during-start','progress-hide-emit-during-start','progress-switch-emit-during-start']
def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def write(p,text):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(text)
def cp(src,rel):
 dst=A/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);return dst
def stop(kind,reason):
 save(A/'stop.json',{'time':time.time(),'kind':kind,'reason':reason,'no_retry':True,'no_more_model_calls':True})
 raise RuntimeError(reason)
def check():
 assert not (A/'stop.json').exists(),'Batch stopped'
 for name in ['initial-freeze.json','experience-freeze.json']:
  if (A/name).exists():runner.verify(read(A/name)['files'])
def add_lines(ledger,eid,kind,statement,file,start,end,related=()):
 lines=(A/'training'/file).read_text().splitlines()
 ledger['entries'].append({'id':eid,'kind':kind,'statement':statement,'author':'execution_agent_source_review_AI_assisted',
  'related':list(related),'anchors':[{'type':'lines','file':file,'start':start,'end':end,'quote':'\n'.join(lines[start-1:end])}]})

def prepare():
 assert not (A/'initial-freeze.json').exists()
 old=read(A/'initial-state.json');runner.verify(old['parent_files'])
 c=read(A/'case.json');original=A/'materials/D/candidate';task=A/'materials/D/task.md'
 assert runner.backend.hashes(original)==c['candidate_files'] and sha(task)==c['task_sha256']
 for name,value in c['oracle_files'].items():assert sha(Path(c['source_case'])/'oracle'/name)==value
 prompt=(A/'development/AUTO-prompt.md').read_text()
 assert prompt==maintenance_prompt(task.read_text(),(A/'derived/D/automatic-contract.md').read_text())
 selected=[]
 for slot in ['session-02','session-03','session-05','session-06']:
  arc=P/'runs'/slot/'archive';rec=read(arc/'receipt.json');cfg=read(arc/'input/config.json')
  assert cfg['model']=='gpt-5.6-terra' and cfg['effort']=='low' and cfg['requests_per_session']==24 and cfg['seconds_per_session']==600
  assert rec['infrastructure_valid'] and rec['scoring_admissible'] and rec['scoring_status']=='COLLECTED' and rec['scored_candidate_unchanged']
  assert runner.backend.hashes(arc/'input/original')==c['candidate_files']
  assert sha(arc/'input/task.md')==c['task_sha256']
  actual=(arc/'input/actual-prompt.md').read_text()
  assert actual==prompt if slot in ['session-02','session-03'] else actual.startswith(prompt+'\n\n')
  command=read(arc/'command.json')
  assert command[command.index('-m')+1]=='gpt-5.6-terra' and 'model_reasoning_effort="low"' in command
  assert rec['native']['started']<=24 and rec['seconds']<=600
  assert read(arc/'score/receipt.json')['oracle_files']==c['oracle_files']
  selected.append({'slot':slot,'role':'AUTO' if slot in ['session-02','session-03'] else 'parent-development',
    'archive':str(arc),'receipt_sha256':sha(arc/'receipt.json'),'original_digest':digest(inventory(arc/'input/original')),
    'prompt_sha256':sha(arc/'input/actual-prompt.md'),'score_sha256':sha(arc/'score/stdout.json'),
    'model':'gpt-5.6-terra','effort':'low','requests_cap':24,'seconds_cap':600})
 save(A/'baseline-selection.json',{'selection':'Reuse both fixed parent AUTO slots, not outcome selection; no new AUTO authorized.',
  'rows':selected,'same_candidate_task_contract_tools_budgets_scorer':True})
 # All evidence remains training-only. Old AUTO counterexamples are exact
 # schedule projections; full old raw scores remain pinned in provenance.
 ledger=copy.deepcopy(read(P/'training/evidence-ledger.json'))
 ledger['scope']='Same training case, parent candidate evolution using its two actual development trials; no test material or reference patch.'
 ledger['files']={}
 def material(src,name,role):
  dest=cp(src,'training/'+name);ledger['files'][name]={'role':role,'sha256':sha(dest)}
 needed={a['file'] for e in ledger['entries'] for a in e['anchors'] if e['kind']!='observed_result'}
 needed|={'inputs/standards.json','inputs/rubric.json','inputs/original-score.json','inputs/contract.md'}
 for name in sorted(needed):material(P/'training'/name,name,read(P/'training/evidence-ledger.json')['files'][name]['role'])
 prior={}
 for i,slot in enumerate(['session-02','session-03'],1):
  score=read(P/'runs'/slot/'archive/score/stdout.json')
  prior['auto'+str(i)]={k:score['schedules'][k] for k in TARGETS}
 save(A/'training/inputs/prior-observations.json',prior)
 ledger['files']['inputs/prior-observations.json']={'role':'training_score','sha256':sha(A/'training/inputs/prior-observations.json')}
 for e in ledger['entries']:
  if e['kind']=='observed_result':
   a=e['anchors'][0];i=1 if e['id'].startswith('O-auto1-') else 2;k=a['pointer'].split('/')[-1]
   a.update(file='inputs/prior-observations.json',pointer='/auto'+str(i)+'/'+k)
   assert a['value']==prior['auto'+str(i)][k]
 for n in ['experience-object.json','experience.md','semantic-review.json','admission.json','comparisons.json']:
  material(P/'development'/n,'inputs/parent/'+n,'training_rejection_review')
 tests=[]
 for i,slot in enumerate(['session-05','session-06'],1):
  arc=P/'runs'/slot/'archive'
  for src,name,role in [('score/stdout.json','score.json','training_score'),('patch.diff','patch.diff','training_patch'),('raw-answer.txt','delivery.json','training_public_delivery')]:
   material(arc/src,f'inputs/dev{i}/'+name,role)
  for f in (arc/'final-candidate').rglob('*.js'):
   material(f,f'inputs/dev{i}/final/'+str(f.relative_to(arc/'final-candidate')),'training_source')
  for k in TARGETS:
   score=read(arc/'score/stdout.json');eid=f'O-dev{i}-'+str(TARGETS.index(k))
   ledger['entries'].append({'id':eid,'kind':'observed_result','statement':'Actual startup-retirement failed check and complete event order; not isolated causation.',
    'author':'python_score_extraction','related':[], 'anchors':[{'type':'json','file':f'inputs/dev{i}/score.json','pointer':'/schedules/'+k,'value':score['schedules'][k]}]})
   ledger['mandatory_counterevidence'].append(eid)
  cmds=[]
  for line in (arc/'tool-outputs.jsonl').read_text().splitlines():
   item=read_json_line(line).get('item',{})
   if item.get('type')=='command_execution' and '/runtime/node' in item.get('command',''):
    cmds.append(item)
  path=f'inputs/dev{i}/actual-self-checks.json';save(A/'training'/path,cmds)
  ledger['files'][path]={'role':'training_source','sha256':sha(A/'training'/path)}
  ledger['entries'].append({'id':f'F-dev{i}-selfchecks','kind':'source_fact','statement':'Actual executed self-check commands/output, separate from final delivery claims. Inspect placement of emissions relative to select/start return.',
   'author':'execution_agent_tool_record_review_AI_assisted','related':['F-navigation','F-cancel'],
   'anchors':[{'type':'json','file':path,'pointer':'','value':cmds}]})
  tests.append({'development':i,'commands':len(cmds)})
 add_lines(ledger,'F-dev1-listener','source_fact','Final first development patch registers before start, but its listener has no entry eligibility check and records before visible callback.',
  'inputs/dev1/final/src/progress.js',2,11,['R-history-view'])
 add_lines(ledger,'F-dev2-visible-only','source_fact','Second development adds attempt identity only inside visible delivery; audit callback remains unconditional. This is source placement, not a claim that the guard is globally unnecessary.',
  'inputs/dev2/final/src/queue.js',8,24,['F-view-owner','R-history-view'])
 # Explain the exact uncovered window, with direct textual/observational support.
 note='''AI-assisted execution-agent reasoning, not an isolated intervention or independent human review.
Source facts: selection assigns the returned cancellation handle only after enqueue returns; progress subscription returns its remover only after source startup returns. The listener decodes and records before the current-view display guard.
Observed startup ordering: the old first frame is displayed; its callback hides, switches or reopens; a second frame is emitted before the old start returns; the retired old subscription audits it; old cancellation is observed later. Consult the complete three schedules in each dev score.
Verification limitation confirmed for development-1: its hide test emits after workspace.select returns; its navigation test switches to a distinct new source, and emits again on the old source only after outer select returns. These checks do not exercise a post-retirement old-source emission while the old startup stack is still active, or nested same-source reopen emission. Passing them does not demonstrate the missing boundary.
The final delivery's broader verification claim cannot override those commands or original scoring. The second development's visible-only guard cannot prevent its unconditional audit from receiving a newly retired event.
This source/trace explanation is supported reasoning. No counterfactual intervention has isolated all causal contributions, no implementation is prescribed, and no new business cancellation policy is granted.
Keep separate: event admission before retirement; asynchronous decode completion/audit of that admitted event after retirement; visibility for the current visit and attempt; eventual physical listener cleanup. Retaining accepted audit is not permission to accept later events. Suppressing every completion after navigation would violate existing passed cases.
'''
 write(A/'training/inputs/window-review.md',note)
 ledger['files']['inputs/window-review.md']={'role':'training_rejection_review','sha256':sha(A/'training/inputs/window-review.md')}
 add_lines(ledger,'I-startup-window','preservation_inference','The documented no-new-retired-admission obligation applies even before the cleanup handle is available; keep already admitted delayed audit separately. Source and trace support a timing explanation, not a uniquely proven implementation.',
  'inputs/window-review.md',1,7,['R-history-view','F-cancel','F-navigation','F-dev1-listener','F-dev2-visible-only'])
 ledger['feedback_inputs']['repairs']=['inputs/dev1/score.json','inputs/dev2/score.json']
 ledger['causal_interventions']=[];ledger['verified_causes']=[]
 save(A/'training/evidence-ledger.json',ledger);verify_ledger(A/'training',ledger)
 fb=rebuild_feedback(A/'training',ledger);save(A/'training/feedback.json',fb)
 # Existing handoff validates full material values, then JSON serialization is
 # mechanically compacted; no feedback/check/trace values are removed.
 payload=assemble_payload(A/'training',ledger,fb)
 changed=[]
 for m in payload['materials']:
  if m['artifact'].endswith('.json'):
   m['content']=json.loads(m['content']);changed.append(m['artifact'])
 payload['mechanism_predicates']=PREDICATES
 payload['output_protocol']={'mandatory_counterevidence':ledger['mandatory_counterevidence'],'preservation_constraints':[r['id'] for r in ledger['constraints']]}
 save(A/'training/reflection-input.json',payload)
 save(A/'reflection.schema.json',make_schema(ledger,PREDICATES))
 instructions='''Evolve ONE parent training experience using its two actual development repairs. No tools, retry, alternative, old external experience, reference patch, test feedback or extra judge.
Use the existing single-source-rules-1 schema, 5-7 rules, each body once, no full experience text or model rule IDs. Python only numbers and joins exact bodies. Chinese preferred.
This is a targeted evolution: retain the parent's valid applicability and preservation boundaries. Focus changes on distinguishing admission from later audit/visibility, and validating the still-active startup stack. Avoid restating the same broad principle without useful timing/verification guidance.
Explain how retirement eligibility remains enforceable even when physical cleanup/remover/cancellation handle has not yet returned; preserve exactly-once audit of events accepted before retirement when decode settles afterwards; require checks that emit after synchronous navigation but BEFORE the outer startup returns, including reuse of the same source. Do not mandate a unique API/implementation or blanket observerless cancellation.
Bodies cannot contain case IDs, scoring/check identifiers, file paths, specialized code field/function names, evidence management IDs or copyable patches. Maintenance receives only bodies; make the useful timing and verification distinction visible there.
support/conditions/counterevidence must use only provided evidence IDs; preserve only constraint IDs; requires/excludes only existing mechanism keys. Every normative support includes relevant documented requirement, source fact or preservation inference, never observations alone. Cover every preservation constraint and mandatory counterexample. Unknown prerequisites do not pass. Explanations belong in explanation fields.
Do not treat final repair-agent claims as executed facts. Distinguish source facts, actual complete outcomes, observed ordering, source-based interpretation, unknown causal contributions, and validated causes. No controlled causal intervention has been run. No successful full repair is available; do not claim one.
The parent content passed an AI-assisted policy review but produced no development improvement. Its text and identity are supplied for evolution, not as a proven effective policy. Read actual patches and commands: checking stale emission only after select/start returns cannot establish the missing in-start retirement boundary. Check source attribution and preserve every passed behavior, including delayed audit, current-visit UI/resource ownership, retries, cancellation, independent workspaces and retained record format. Do not widen adjacent policies or preserve the reported bug.
One candidate only; subsequent review is AI-assisted execution-agent review, not independent human approval.
Complete frozen training payload (JSON content objects are deterministic views of byte-pinned raw materials):
'''
 text=instructions+json.dumps(payload,ensure_ascii=False,separators=(',',':'))
 write(A/'training/reflection-prompt.md',text);write(A/'training/reflection-task.md','One bounded training-only parent experience evolution; no tools.\n')
 (A/'training/model-workspace').mkdir();save(A/'training/model-workspace/payload.json',payload)
 save(A/'serialization-audit.json',{'conversion':'JSON strings parsed to identical full JSON values; compact whitespace only','artifacts':changed,'prompt_bytes':len(text.encode()),'no_dropped_checks_or_traces':True,'prior_AUTO_projection':'Exact three failed schedules retained; all raw parent artifacts separately hash pinned, no historical score rerun.','selfchecks':tests})
 protocol={'parent':str(P),'case':c['case'],'scope':'One training-only parent evolution; no test or next reflection',
  'models':{'reflect':['gpt-5.6-terra','medium',12,600],'repair':['gpt-5.6-terra','low',24,600]},
  'maximum_sessions':3,'maximum_requests':60,'concurrency':1,'no_retry':True,'no_extra_extraction_or_judge':True,
  'schedule':['reflection','development-1','development-2'],'baseline':'Fixed parent AUTO1/AUTO2, 17/20 each; no new AUTO',
  'normal_behavior_failure':'Continue to second scheduled development slot; no full-pass gate',
  'stop':'First infrastructure/isolation/meter/archive anomaly, invalid or unsupported experience. After two runs stop regardless of gains.',
  'if_no_improvement':'Investigate maintenance execution and verification interface; do not add more experience text automatically',
  'production_update':False,'create_commit':False}
 save(A/'protocol.json',protocol);save(A/'actual-schedule.json',[])
 preflight()

def frozen_input_files(root):
 return {str(p):sha(p) for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['actual-schedule.json','stop.json','initial-freeze.json'] and p.suffix!='.log'}
def read_json_line(line):return json.loads(line)
def reference_view(value):
 """Lossless repeated-subtree interning for input serialization, not evidence editing."""
 dictionary={};seen={}
 def encode(node):
  key=json.dumps(node,ensure_ascii=False,sort_keys=True,separators=(',',':'))
  if len(key)<320:return node
  if key in seen:return {'$same':seen[key]}
  result={k:encode(v) for k,v in node.items()} if isinstance(node,dict) else [encode(v) for v in node] if isinstance(node,list) else node
  token='D%04d'%(len(dictionary)+1);dictionary[token]=result;seen[key]=token
  return {'$same':token}
 root=encode(value)
 def expand(node):
  if isinstance(node,dict) and set(node)=={'$same'}:return expand(dictionary[node['$same']])
  if isinstance(node,dict):return {k:expand(v) for k,v in node.items()}
  if isinstance(node,list):return [expand(v) for v in node]
  return node
 assert expand(root)==value
 return {'serialization':'lossless-repeated-subtree-references-1','meaning':'Every object containing only $same substitutes the identical full value in shared_values at that key, recursively. These keys are serialization only, never evidence IDs. Nothing is omitted.','shared_values':dictionary,'payload':root}
def preflight():
 import test_toolflow,test_runtime_v2,test_source_proof,test_locked_scope
 suite=unittest.TestSuite()
 for m in [test_toolflow,test_runtime_v2,test_source_proof,test_locked_scope]:suite.addTests(unittest.TestLoader().loadTestsFromModule(m))
 with (A/'offline-tests.log').open('w') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 assert result.wasSuccessful(),'Offline regression failure'
 c=read(A/'case.json')
 # Real bwrap mounts/tool roles, but never launch the CLI/model during preflight.
 with tempfile.TemporaryDirectory(prefix='transfer-evolve-offline-') as td:
  runtime=Path(td);folder=runtime/'check';folder.mkdir();(folder/'archive').mkdir();shutil.copytree(A/'materials/D/candidate',folder/'workspace')
  socket=runtime/'control';socket.mkdir()
  for phase in ['repair','reflect']:
   cmd=runner.command('offline-'+phase,folder,phase,c,runtime=runtime,socket_dir=socket,copy_auth=False)
   assert cmd[cmd.index('-m')+1]=='gpt-5.6-terra'
   assert '--disable' in cmd
   if phase=='reflect':assert 'shell_tool' in cmd and 'code_mode_host' in cmd
   z=subprocess.run(cmd[:cmd.index('/opt/codex')]+['/bin/sh','-c','set -eu\ncat /workspace/src/progress.js\ntest ! -e /home/sribd\n/runtime/node --version'],capture_output=True,timeout=30)
   assert z.returncode==0 and (A/'materials/D/candidate/src/progress.js').read_bytes() in z.stdout
 # Old response replay, identity checks and no new calibration/model calls.
 ledger=read(A/'training/evidence-ledger.json');validate_candidate(read(P/'development/experience-object.json'),read(P/'training/evidence-ledger.json'),PREDICATES)
 assert len(read(A/'materials/D/standards.json'))==20
 frozen=frozen_input_files(A)
 frozen.update(read(A/'initial-state.json')['parent_files'])
 for f in (Path(c['source_case'])/'oracle').rglob('*'):
  if f.is_file():frozen[str(f)]=sha(f)
 frozen[str(Path.home()/'.codex/config.toml')]=sha(Path.home()/'.codex/config.toml')
 save(A/'initial-freeze.json',{'time':time.time(),'files':frozen,'offline_tests':result.testsRun,'model_calls':0,'calibration':'Parent D same scorer/candidate evidence reused; no calibration rerun'})
 print('OFFLINE PASS',result.testsRun,'prompt bytes', (A/'training/reflection-prompt.md').stat().st_size,flush=True)

def scorer(final,out):
 c=read(A/'case.json');cmd=[c['node'],str(Path(c['source_case'])/'oracle/probe.cjs'),str(final),'ungranted']
 with (out/'stdout.json').open('wb') as o,(out/'stderr.txt').open('wb') as e:z=subprocess.run(cmd,stdout=o,stderr=e,timeout=120)
 s=read(out/'stdout.json');rules=read(A/'materials/D/evaluation/effects.json')['variants']['ungranted'];eff=s['observed_effects']
 assert z.returncode in [0,1] and s['case_id']==c['case']
 assert set(eff)==set(read(A/'calibration/D/original/stdout.json')['observed_effects'])
 missing=[k for k in rules['required'] if eff.get(k) is not True];forbidden=[k for k in rules['forbidden'] if eff.get(k) is True]
 expected='UNDERREACH_AND_OVERREACH' if missing and forbidden else 'UNDERREACH' if missing else 'OVERREACH' if forbidden else 'PASS'
 assert expected==s['verdict'] and missing==s['missing_required_effects'] and forbidden==s['observed_forbidden_effects']
 assert not any(v.get('runtimeError') for v in s['schedules'].values())
 save(out/'receipt.json',{'command':cmd,'exit_code':z.returncode,'oracle_files':c['oracle_files'],'candidate_digest':digest(inventory(final)),'single_scoring_invocation':True})
 return {'verdict':expected,'effects':eff,'missing':missing,'forbidden':forbidden,'score_valid':True}

def execute(name,phase,prompt,candidate,task):
 check();rows=read(A/'actual-schedule.json');expected=['reflection','development-1','development-2']
 assert len(rows)<3 and name==expected[len(rows)]
 slot={'slot':f'session-{len(rows)+1:02d}','name':name,'phase':phase,'condition':'EVOLVE' if phase=='reflect' else 'AUTO_EVOLVED_EXPERIENCE'}
 save(A/'actual-schedule.json',rows+[{**slot,'status':'DISPATCHING','dispatched_at':time.time()}])
 c=read(A/'case.json')
 if phase=='reflect':c.pop('candidate_files');c.pop('task_sha256')
 try:
  rec=runner.session(slot,prompt,case=c,candidate=candidate,task=task,
   config={'seconds_per_session':600,'stdout_bytes':16777216,'frozen_files':read(A/'initial-freeze.json')['files']},
   run_dir=A/'runs'/slot['slot'],score_fn=scorer if phase=='repair' else None,allow_model_execution=True)
 except Exception as exc:
  save(A/'dispatch-error.json',{'slot':slot,'error':repr(exc),'no_retry':True})
  stop('runner',repr(exc))
 save(A/'actual-schedule.json',rows+[rec]);print(json.dumps({'name':name,'status':rec['status'],'requests':rec.get('native',{}).get('started'),'score':rec.get('score_result'),'seconds':rec.get('seconds')},ensure_ascii=False),flush=True)
 arc=A/'runs'/slot['slot']/'archive';meter=read(arc/'meter/ledger.json',{});native=rec.get('native',{})
 if rec.get('archive_failure_requires_stop'):stop('archive','Archival failure; original service outcome kept separately')
 if read(arc/'guard-collector-status.json',{}).get('errors'):stop('meter','Collector errors')
 if meter.get('started')!=native.get('started') or meter.get('completed')!=native.get('completed'):stop('meter','Request accounting drift')
 if sum(r.get('native',{}).get('started',0) for r in read(A/'actual-schedule.json'))>60:stop('meter','Batch cap exceeded')
 if not rec.get('infrastructure_valid') or not rec.get('candidate_complete'):stop('infrastructure_or_output',name+' incomplete or infrastructure failure')
 if phase=='repair' and (rec.get('scoring_status')!='COLLECTED' or not rec.get('scored_candidate_unchanged')):stop('score','No valid unchanged scored candidate')
 check();return rec

def reflect():
 assert len(read(A/'actual-schedule.json'))==0
 rec=execute('reflection','reflect',(A/'training/reflection-prompt.md').read_text(),A/'training/model-workspace',A/'training/reflection-task.md')
 raw=(A/'runs'/rec['slot']/'archive/raw-answer.txt').read_bytes();(A/'development/reflection-raw.txt').write_bytes(raw)
 try:
  candidate=json.loads(raw);save(A/'development/experience-object.json',candidate)
  result=validate_candidate(candidate,read(A/'training/evidence-ledger.json'),PREDICATES)
  text=render(candidate)
  banned=[read(A/'case.json')['case'],'src/','```']+[s['effect'] for s in read(A/'materials/D/standards.json')]
  if any(x in text for x in banned):raise ValueError('Prohibited case/path/scoring/patch in delivered prose')
  write(A/'development/experience.md',text);save(A/'development/structural-review.json',result)
  save(A/'development/rule-evidence.json',{'rules':numbered_rules(candidate),'applicability':candidate['applicability'],'unresolved':candidate['unresolved']})
  parent=read(P/'development/experience-object.json');changes=[]
  for i in range(max(len(parent['rules']),len(candidate['rules']))):
   old=parent['rules'][i] if i<len(parent['rules']) else None;new=candidate['rules'][i] if i<len(candidate['rules']) else None
   changes.append({'ordinal':i+1,'unchanged':old==new,'old':old,'new':new})
  save(A/'development/parent-diff.json',{'parent_object_sha256':object_digest(parent),'candidate_sha256':object_digest(candidate),'rule_changes':changes,'mechanism_fields_unchanged':all(parent[k]==candidate[k] for k in ['requires','excludes','applicability'])})
  save(A/'development/derivation.json',{'operation':'Program-derived exact rule body concatenation and numbering; no prose edits','raw_candidate_sha256':sha(A/'development/experience-object.json'),'object_sha256':object_digest(candidate),'text_sha256':sha(A/'development/experience.md'),'parent':str(P/'development/experience-object.json')})
 except Exception as exc:
  save(A/'development/rejection.json',{'reason':repr(exc),'raw_retained':True});stop('candidate',repr(exc))

def freeze():
 check();assert len(read(A/'actual-schedule.json'))==1 and not (A/'experience-freeze.json').exists()
 candidate=read(A/'development/experience-object.json');ledger=read(A/'training/evidence-ledger.json')
 decision=semantic_gate(candidate,ledger,PREDICATES,read(A/'development/semantic-review.json'))
 save(A/'development/content-review.json',decision)
 if not decision['development_eligible']:stop('candidate','AI-assisted evidence review rejects candidate')
 text=render(candidate);assert text==(A/'development/experience.md').read_text()
 prompt=(A/'development/AUTO-prompt.md').read_text()+'\n\n以下为冻结经验，按当前证据核查适用性：\n'+text
 write(A/'development/revalidation-prompt.md',prompt)
 files={str(p):sha(p) for p in (A/'development').rglob('*') if p.is_file()}
 save(A/'experience-freeze.json',{'time':time.time(),'files':files,'only_intended_difference_from_AUTO':'Appended exact program-rendered experience; original candidate, public prompt, task, automatic Contract, tools/model/effort/budget/scorer unchanged'})
 print('EXPERIENCE FROZEN',sha(A/'development/experience.md'),flush=True)

def develop(n):
 assert (A/'experience-freeze.json').exists() and n in [1,2]
 execute('development-'+str(n),'repair',(A/'development/revalidation-prompt.md').read_text(),A/'materials/D/candidate',A/'materials/D/task.md')

if __name__=='__main__':
 raise SystemExit('Use workflow.py for the new locked-scope batch; this module supplies reused helpers only.')
 try:
  stage=sys.argv[1]
  if stage=='develop':develop(int(sys.argv[2]))
  else:{'prepare':prepare,'reflect':reflect,'freeze':freeze}[stage]()
 except Exception as exc:
  if not (A/'stop.json').exists():save(A/'stop.json',{'time':time.time(),'kind':'stage_exception','reason':repr(exc),'no_retry':True,'no_more_model_calls':True})
  print('STOP',repr(exc),flush=True);sys.exit(1)

"""Frozen U1 skills-only maintenance study. No GEPA, evolution, retries or controller."""
import argparse,hashlib,importlib.util,json,os,random,shutil,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
OLD=ROOT/'research/gepa-official-skill-experiment-v1-20261106';DEV=ROOT/'research/development-feedback-mechanism-v1-20261106'
sys.path[:0]=[str(OLD),str(ROOT)];os.environ['PYTHONDONTWRITEBYTECODE']='1'
spec=importlib.util.spec_from_file_location('trusted_autonomous_bridge',OLD/'runtime.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt);rt.OUT=OUT;rt.rt.OUT=OUT
read=rt.read;save=rt.save;sha=rt.sha;CASE='transfer-progress-composition-v4-vanilla';SEED=2026110607

def frozen():
 p=read(OUT/'protocol.json');assert sha((OUT/'protocol.json').read_bytes())==(OUT/'protocol.sha256').read_text().strip()
 for n,h in p['frozen_files'].items():assert sha(Path(n).read_bytes())==h,n
 return p

def prepare():
 assert not (OUT/'protocol.json').exists()
 mapping=read(DEV/'private-label-mapping.json')['candidates'];orig=next(r for r in read(OLD/'task-results.json') if r['id']=='e-5b07bf1156dc48d0');origdir=Path(orig['path']);om=read(origdir/'manifest.json');meta=read(OLD/'protocol.json')['cases'][CASE]
 mat=OUT/'materials'/CASE;mat.mkdir(parents=True);shutil.copytree(origdir/'input',mat/'input')
 for n in ['common.md','task.md','source.md','questions.md','source-retrieval.json']:
  if (OLD/'materials'/CASE/n).exists():shutil.copyfile(OLD/'materials'/CASE/n,mat/n)
 for n in ['BASE.md','END.md']:shutil.copyfile(OLD/n,OUT/n)
 (OUT/'K.md').write_bytes((DEV/'inputs/U1/parent.md').read_bytes());assert (OUT/'K.md').read_bytes()==(OLD/'K0.md').read_bytes()
 sources={'K':dict(candidate_id='K0',source=str(DEV/'inputs/U1/parent.md'),parent_sha256=sha((OUT/'K.md').read_bytes()),source_execution='e-5b07bf1156dc48d0')}
 for arm,label in [('F0','A'),('F1','B')]:
  cid,m=min(((c,m) for c,m in mapping.items() if m['unit']=='U1' and m['condition']==label),key=lambda x:x[1]['sequence'])
  raw=DEV/'runs'/m['call_id']/'raw-answer.txt';assert sha(raw.read_bytes())==m['raw_sha256'];skill=read(raw)['skill'];assert skill==(DEV/'anonymous-review/candidates'/cid/'skill.md').read_text()
  (OUT/(arm+'.md')).write_text(skill);sources[arm]=dict(candidate_id=cid,source_call=m['call_id'],source_generation_sequence=m['sequence'],source=str(raw),source_raw_sha256=sha(raw.read_bytes()),parent_sha256=sha((OUT/'K.md').read_bytes()),selection='first generation of U1 in this condition, not rating or length')
 for arm,r in sources.items():r.update(skill_sha256=sha((OUT/(arm+'.md')).read_bytes()),characters=len((OUT/(arm+'.md')).read_text()))
 save(OUT/'candidate-sources.json',sources)
 # Exact original task/common/skill envelope; no retrospective evidence/question package.
 prompts={arm:rt.full_prompt(CASE,(OUT/(arm+'.md')).read_text()) for arm in sources}
 assert prompts['K']==(origdir/'jobs/j-001/prompt.md').read_text()
 for arm,text in prompts.items():(OUT/(arm+'.prompt.md')).write_text(text)
 prefix=prompts['K'].split('<temporal-contract-skill>\n')[0]+'<temporal-contract-skill>\n';suffix='\n</temporal-contract-skill>'+prompts['K'].split('\n</temporal-contract-skill>',1)[1]
 (OUT/'common-prefix.md').write_text(prefix);(OUT/'common-suffix.md').write_text(suffix)
 for arm in sources:assert prompts[arm]==prefix+(OUT/(arm+'.md')).read_text()+suffix
 unchanged=OLD/'calibration'/CASE/'unchanged/oracle/stdout.json';dest=OUT/'calibration'/CASE/'unchanged/oracle';dest.mkdir(parents=True);shutil.copyfile(unchanged,dest/'stdout.json')
 save(OUT/'historical-comparators.json',dict(frozen_start_raw=str(unchanged),frozen_start_sha256=sha(unchanged.read_bytes()),historical_parent_execution=orig,not_execution_start='historical parent patch never supplied to any new job'))
 runs=[];w=rt.wb();rng=random.Random(SEED);order=['K','F0','F1'];rng.shuffle(order)
 for rep in [1,2]:
  for arm in order if rep==1 else list(reversed(order)):
   m=w.prepare_case(dict(case_id=CASE,model='gpt-6-sol',effort='low',timeout=600,repeats=1,conditions=['none'],use_local_config=True));folder=w.folder(m['id']);d=folder/'jobs/j-001'
   assert m['task']==om['task'];assert m['input_files']==om['input_files']==meta['input_files']
   assert all(sha((folder/'input'/n).read_bytes())==h for n,h in om['input_files'].items())
   (d/'prompt.md').write_text(prompts[arm]);common=(mat/'common.md').read_text();(d/'report.md').write_text(common)
   m['jobs'][0].update(prompt_sha256=sha(prompts[arm]),report_sha256=sha(common),report_characters=len(common));save(folder/'manifest.json',m)
   runs.append(dict(sequence=len(runs)+1,arm=arm,replicate=rep,id=m['id'],path=str(folder),skill_sha256=sources[arm]['skill_sha256'],prompt_sha256=sha(prompts[arm]),input_files=m['input_files']))
 save(OUT/'runs.json',runs);save(OUT/'schedule.json',dict(seed=SEED,model_sampling_seed=None,order=runs))
 save(OUT/'input-control.json',dict(original_job=orig['id'],original_prompt_K_byte_identical=True,only_skill_block_differs=True,common_prefix_sha256=sha(prefix),common_suffix_sha256=sha(suffix),task_sha256=sha(om['task']),input_files=om['input_files'],ast_delivery=False,source_and_questions='original archived common bytes; no retrieval recomputed',config=dict(model='gpt-6-sol',effort='low',timeout=600,mode='workspace-write',explicit_output_token_cap=None,workflow='original autonomous CLI',native_request_meter='passive except rejecting transport retry; no tool/Stop controller')))
 # Freeze code, exact prompts/skills, archival provenance and current trusted scoring files.
 paths=[f for f in OUT.rglob('*') if f.is_file() and '.runtime' not in f.parts]
 paths += [OLD/'runtime.py',ROOT/'research/staged-react-experiment-v1-20261105/run.py']
 paths += list((ROOT/'temporal_contract_analyzer').glob('*.py'))
 paths += [Path(n) for n in read(OLD/'protocol.json')['frozen_files'] if '/oracle/' in n and Path(n).is_file()]
 paths += [Path(meta['manifest']),DEV/'private-label-mapping.json',DEV/'review.csv',DEV/'review.freeze.json']
 for arm,s in sources.items():paths.append(Path(s['source']))
 p=dict(created_at=rt.archive.now(),cases={CASE:meta},original_job=orig['id'],max_maintenance_sessions=6,max_repeats=2,extra_reflections=0,gepa=False,independent_human_review_complete=False,exposed_development_only=True,seed=SEED,frozen_files={str(f):sha(f.read_bytes()) for f in sorted(set(paths))})
 save(OUT/'protocol.json',p);(OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('FROZEN',[(r['arm'],r['replicate'],r['id']) for r in runs],flush=True)

def preflight():
 p=frozen();w=rt.wb();s=OUT/'offline'
 for n in ['workspace','output','stage','profile']:(s/n).mkdir(parents=True,exist_ok=True)
 cmd=rt.rt.isolation(s/'workspace',s/'output',s/'stage',s/'profile',w.codex)
 check='set -eu\ntest ! -e /home/sribd\ntest ! -e /proc/1/root/home/sribd\ntest ! -e /workspace/../research\ntest -x /opt/codex-code-mode-host\n/opt/codex --version\n/opt/codex-code-mode-host --help\nnode --version\n/runtime/node16 --version\nprintf "const x = 1;" > /workspace/synthetic.js\nnode --check /workspace/synthetic.js\n'
 proc=subprocess.run(cmd+['/bin/bash','-c',check],capture_output=True,text=True,timeout=30);save(OUT/'offline/isolation.json',dict(exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr));assert proc.returncode==0
 # Mechanical leakage checks supplement, never substitute, source-grounded risk review.
 bans=read(OLD/'skill-banned-identifiers.json')+read(OLD/'private-score-identifiers.json');checks=[]
 for arm in ['K','F0','F1']:
  skill=(OUT/(arm+'.md')).read_text();hits=[b for b in bans if b.lower() in skill.lower()];assert not hits,hits
  checks.append(dict(arm=arm,skill_sha256=sha(skill),literal_banned_hits=hits,prompt_characters=len((OUT/(arm+'.prompt.md')).read_text())))
 for r in read(OUT/'runs.json'):
  m=w.read(r['id']);inner=rt.Workbench.command(w,m,Path('/workspace'),Path('/output/answer.md'))
  assert m['mode']=='workspace-write' and m['timeout']==600 and inner[inner.index('-m')+1]=='gpt-6-sol' and 'model_reasoning_effort="low"' in inner
  assert m['input_files']==r['input_files']
 # Synthetic request-meter events, no provider/model calls.
 spec=importlib.util.spec_from_file_location('study_meter',OUT/'request_meter.py');meter=importlib.util.module_from_spec(spec);spec.loader.exec_module(meter)
 root=s/'meter';root.mkdir();save(root/'config.json',dict(max_requests=None,reject_transport_retries=True))
 assert not meter.account(dict(hook_event_name='PreModelRequest'),root,kill=False)
 assert not meter.account(dict(hook_event_name='PostModelRequest',status='completed'),root,kill=False)
 assert not meter.account(dict(hook_event_name='PreModelRequest'),root,kill=False)
 assert not meter.account(dict(hook_event_name='PostModelRequest',status='failed'),root,kill=False)
 assert meter.account(dict(hook_event_name='PreModelRequest'),root,kill=False)
 save(OUT/'preflight.json',dict(status='PASS',at=rt.archive.now(),model_calls=0,workspace_isolation=True,code_mode_host_available=True,skill_checks=checks,risk_review='RISK_REVIEW.md; independent human review NOT completed',same_original_task_and_input=True,only_skill_differs=True,request_meter_synthetic_no_retry_gate=True,calibration='existing unchanged calibration reused offline; original scorer performs fresh passing-reference check after each actual job',no_reference_or_history_mounted=True))
 print('PREFLIGHT_PASS',flush=True)

def execute():
 frozen();assert read(OUT/'preflight.json')['status']=='PASS';assert not (OUT/'invocations.json').exists(),'No resume or reruns'
 w=rt.wb();ledger=[];rows=[];save(OUT/'invocations.json',ledger)
 for r in read(OUT/'runs.json'):
  frozen();assert len(ledger)<6;ledger.append(dict(id=r['id'],sequence=r['sequence'],at=rt.archive.now()));save(OUT/'invocations.json',ledger);row=dict(r);start=time.monotonic()
  try:
   w.start(r['id']);w.thread.join();m=w.read(r['id']);j=m['jobs'][0];d=Path(r['path'])/'jobs/j-001';ep=w.latest_evaluation(r['id']);ev=read(ep) if ep else {};entry=ev.get('jobs',{}).get('j-001',{})
   category='execution-failure' if j['status']!='completed' else 'behavior' if ev.get('calibration_verdict')=='PASS' and entry.get('status') in ['passed','failed'] else 'validation-unverified'
   tr=rt.usage((d/'events.jsonl').read_text());changes=read(d/'changes.json') if (d/'changes.json').exists() else {'files':[]};meter=read(d/'model-meter/ledger.json') if (d/'model-meter/ledger.json').exists() else None
   if 'failed to spawn code-mode host' in (d/'events.jsonl').read_text():category='execution-tool-unavailable'
   row.update(category=category,status=j['status'],evaluation=str(ep) if ep else None,started_at=j.get('started_at'),completed_at=j.get('completed_at'),score=None,usage=tr['totals'],tool_calls=len(tr['tools']),model_requests=meter['started'] if meter else None,model_completed=meter['completed'] if meter else None,denied_retries=meter['denied'] if meter else None,changed_paths=[f['path'] for f in changes['files']])
   if category=='behavior':
    rawpath=Path(r['path'])/entry['result_path'];row.update(raw_score=str(rawpath),score=rt.normalize(CASE,read(rawpath)))
   save(d/'trajectory-index.json',tr);(d/'patch.diff').write_text('\n'.join(f.get('diff','') for f in changes['files']))
  except Exception as e:row.update(category='execution-error',error=repr(e),score=None)
  finally:shutil.rmtree(OUT/'.runtime'/r['id'],ignore_errors=True)
  row['including_score_seconds']=time.monotonic()-start;rows.append(row);save(OUT/'results.json',rows)
  print(json.dumps(dict(event='session_finished',sequence=r['sequence'],id=r['id'],status=row['category'])),flush=True)
 save(OUT/'completion.json',dict(status='COMPLETE',sessions=len(ledger),at=rt.archive.now(),no_retries=True));print('SIX_SESSIONS_FINISHED',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','execute']);globals()[parser.parse_args().action]()

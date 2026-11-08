"""Exactly two cases / 18 unique sessions. Never imports an old dispatcher."""
import importlib.util,json,os,re,shutil,signal,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parent.parent
spec=importlib.util.spec_from_file_location('small_native',O/'native_backend.py');backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend);backend.OUT=O
read=backend.read;save=backend.save;hashes=backend.hashes
def sha(p):return backend.sha(Path(p).read_bytes())
def cases():return read(O/'cohort.json')['cases']
def command(call,folder,phase,cap=None):
 meter=folder/'meter';cap=cap or (12 if phase in ['extract','reflect'] else 24)
 if not (meter/'config.json').exists():save(meter/'config.json',{'global_cap':cap,'calls':{call:{'cap':cap,'mode':'extraction' if phase=='extract' else 'reflection' if phase=='reflect' else 'maintenance'}}})
 cmd=backend.command(call,folder,'reflection' if phase=='reflect' else 'extraction',True,meter)
 if phase in ['repair','reflect']:
  i=cmd.index(str(folder/'workspace'));assert cmd[i-1]=='--ro-bind';cmd[i-1]='--bind'
  cmd[cmd.index('--sandbox')+1]='danger-full-access';cmd[cmd.index('-m')+1]='gpt-5.6-terra'
  cmd=[s.replace('model_reasoning_effort="low"','model_reasoning_effort="medium"') for s in cmd]
 node=cases()[0]['node'];i=cmd.index('--chdir')
 cmd[i:i]=['--ro-bind',node,'/runtime/node','--ro-bind',str(O/'read_policy.py'),'/read_policy.py']
 return cmd
def verify():
 for p,h in read(O/'protocol.json')['files'].items():assert sha(p)==h,p
def source_proof(events,c):
 proofs=[]
 for n,e in enumerate(events,1):
  item=e.get('item',{})
  if e.get('type')!='item.completed' or item.get('type')!='command_execution' or item.get('exit_code')!=0:continue
  output=item.get('aggregated_output','');normalized={re.sub(r'^\s*\d+\s+','',line).strip() for line in output.splitlines()}
  for f in (O/'materials'/c['case']/'candidate').rglob('*'):
   if f.suffix not in ['.js','.py']:continue
   lines={s.strip() for s in f.read_text().splitlines() if len(s.strip())>=20};matched=sorted(lines&normalized)
   if len(matched)>=3:proofs.append({'event_line':n,'source':str(f),'source_sha256':sha(f),'matched_lines':matched,'tool_output_sha256':backend.sha(output)})
 return proofs
def session(slot,prompt):
 verify();case=next(c for c in cases() if c['case']==slot['case']);call=slot['slot'];phase=slot['phase'];d=O/'runs'/call
 d.mkdir(parents=True,exist_ok=False);shutil.copytree(O/'materials'/case['case']/'candidate',d/'workspace');assert hashes(d/'workspace')==case['candidate_files']
 save(d/'frozen-start.json',{'case':case['case'],'files':hashes(d/'workspace'),'recorded_before_launch':True})
 (d/'actual-prompt.md').write_text(prompt);cmd=command(call,d,phase)
 rec=dict(slot,status='LAUNCHED',started_at=time.time(),command=cmd,prompt_sha256=backend.sha(prompt),stop_reason=None)
 save(d/'receipt.json',rec);proc=None
 try:
  with (d/'actual-prompt.md').open('rb') as inp,(d/'events.jsonl').open('wb') as out,(d/'stderr.log').open('wb') as err:
   proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,cwd=d/'workspace',start_new_session=True)
   while proc.poll() is None:
    if time.time()-rec['started_at']>=600:rec['resource_limit']='timeout';os.killpg(proc.pid,signal.SIGKILL);break
    if (d/'events.jsonl').stat().st_size>16777216:rec['resource_limit']='stdout_archive_limit';os.killpg(proc.pid,signal.SIGKILL);break
    try:proc.wait(timeout=1)
    except subprocess.TimeoutExpired:pass
   proc.wait()
  events=[];badlines=[]
  for n,line in enumerate((d/'events.jsonl').read_text().splitlines(),1):
   try:events.append(json.loads(line))
   except ValueError:badlines.append(n)
  meter=read(d/'meter/ledger.json') if (d/'meter/ledger.json').exists() else {};native=meter.get('sessions',{}).get(call,{})
  posts=[r['event'] for r in meter.get('events',[]) if r['event'].get('hook_event_name')=='PostModelRequest']
  usage={k:sum(e.get('token_usage',{}).get(k,0) or 0 for e in posts) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']}
  rawpath=d/'cli-output/answer.json';raw=rawpath.read_text() if rawpath.exists() else '';(d/'raw-answer.txt').write_text(raw)
  try:ans=json.loads(raw);format_ok=isinstance(ans,dict) and set(ans)=={'report'} and isinstance(ans['report'],str) and len(ans['report'])<=6000
  except (ValueError,TypeError):ans={};format_ok=False
  budget_hit=bool(rec.get('resource_limit')) or bool(native.get('blocked_requests') and native.get('started')==(12 if phase in ['extract','reflect'] else 24))
  expected='gpt-6-sol' if phase=='extract' else 'gpt-5.6-terra'
  model_events=[r['event'] for r in meter.get('events',[]) if r['event'].get('hook_event_name') in ['PreModelRequest','PostModelRequest']]
  models_ok=bool(model_events) and all(e.get('model')==expected for e in model_events)
  pending=(native.get('started',0)-native.get('completed',0))
  accounted=bool(native.get('started')) and (pending==0 or budget_hit and pending==1) and len(posts)==native.get('completed')
  service_error=any(e.get('status')!='completed' for e in posts) or any(e.get('type')=='turn.failed' for e in events)
  completed=proc.returncode==0 and sum(e.get('type')=='turn.completed' for e in events)==1
  infra_ok=accounted and models_ok and not native.get('blocked_tools') and not service_error and not badlines and (completed or budget_hit)
  rec.update(exit_code=proc.returncode,seconds=time.time()-rec['started_at'],usage=usage,native=native,usage_incomplete=not accounted or pending!=0 or any(not e.get('token_usage') for e in posts),usage_unknown_request_count=pending+sum(not e.get('token_usage') for e in posts),model_match=models_ok,output_format_valid=format_ok,malformed_event_lines=badlines,tools=sum(e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution' for e in events),source_body_proofs=source_proof(events,case),candidate_files=hashes(d/'workspace'),infrastructure_valid=infra_ok,model_budget_limit=budget_hit)
  rec['status']='VALID' if infra_ok and (completed or budget_hit) else 'INVALID'
  rec['failure_class']='infrastructure' if not infra_ok else 'model_resource_limit' if budget_hit else 'model_delivery_format' if not format_ok else None
  if not infra_ok:rec['stop_reason']='tool_guard_service_configuration_or_accounting_failure'
  if phase=='extract':
   assert hashes(d/'workspace')==case['candidate_files']
   full=ans.get('report','');(d/'contract-full.md').write_text(full)
   h1='1. 可确认的 Contract\n';h2='2. 每条的条件、效果、来源及依据\n'
   if rec['status']=='VALID' and rec['source_body_proofs'] and full.count(h1)==full.count(h2)==1:
    body=full.split(h1,1)[1].split(h2,1)[0];assert body.strip();(d/'contract.md').write_text(body);rec['contract_sha256']=backend.sha(body)
   else:
    rec['status']='INVALID';rec['failure_class']=rec['failure_class'] or 'model_extraction_format_or_read_omission';rec['stop_reason']=rec['stop_reason'] or 'no_valid_frozen_automatic_contract'
  elif phase=='reflect':
   (d/'experience.md').write_text(ans.get('report',''))
  else:
   diff=subprocess.run(['diff','-ruN',str(O/'materials'/case['case']/'candidate'),str(d/'workspace')],capture_output=True,text=True);(d/'patch.diff').write_text(diff.stdout)
   rec['patch_delivered']=bool(diff.stdout)
   result=subprocess.run([case['node'],str(Path(case['source_case'])/'oracle/probe.cjs'),str(d/'workspace'),'ungranted'],capture_output=True,text=True,timeout=90)
   (d/'score.stdout.json').write_text(result.stdout);(d/'score.stderr.txt').write_text(result.stderr)
   try:
    score=json.loads(result.stdout);assert score['case_id']==case['case'];assert set(score['observed_effects'])==set(case['calibration'][0]['effects']);rec['raw_verdict']=score['verdict'];score_ok=result.returncode in [0,1]
   except (ValueError,KeyError,AssertionError):score_ok=False
   rec['scoring_valid']=score_ok;rec['scored_candidate_files']=hashes(d/'workspace');assert rec['scored_candidate_files']==rec['candidate_files']
   if not score_ok:rec.update(status='INVALID',failure_class='scoring_anomaly',stop_reason='score_case_or_effects_or_execution_mismatch')
  save(d/'receipt.json',rec)
 except Exception as exc:
  if proc and proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
  rec.update(status='INVALID',failure_class='infrastructure',stop_reason='runner_exception',exception=repr(exc),seconds=time.time()-rec['started_at'])
  if (d/'meter/ledger.json').exists():
   meter=read(d/'meter/ledger.json');rec['native']=meter.get('sessions',{}).get(call,{})
   posts=[r['event'] for r in meter.get('events',[]) if r['event'].get('hook_event_name')=='PostModelRequest'];rec['usage']={k:sum(e.get('token_usage',{}).get(k,0) or 0 for e in posts) for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']}
  rec['usage_incomplete']=True;save(d/'receipt.json',rec)
 finally:
  profile=Path((O/'runtime-location.txt').read_text().strip())/'.runtime'/call
  if (profile/'config.toml').exists():save(d/'configuration-after.json',{'profile_sha256':sha(profile/'config.toml'),'global_config':backend.global_snapshot()})
  shutil.rmtree(profile,ignore_errors=True)
 return rec

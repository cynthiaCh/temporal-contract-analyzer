"""Six frozen native autonomous maintenance sessions. No retry/replacement."""
import json,hashlib,os,shutil,subprocess,time,signal,sys,importlib.util
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parent.parent;X=R/'research/contract-extraction-cross-case-v1-20261107'
spec=importlib.util.spec_from_file_location('previous_native',X/'run.py');prev=importlib.util.module_from_spec(spec);spec.loader.exec_module(prev);prev.OUT=O
node=R/'results/ad-model-effort-20261104/runtime/node-v16.20.2-linux-x64/bin/node'
def save(p,x):prev.save(p,x)
def sha(p):return prev.sha(Path(p).read_bytes())
def read(p):return prev.read(p)
def command(call,folder,meter=None):
 cmd=prev.command(call,folder,'extraction',True,meter)
 i=cmd.index(str(folder/'workspace'));assert cmd[i-1]=='--ro-bind';cmd[i-1]='--bind'
 i=cmd.index('--sandbox');cmd[i+1]='danger-full-access'
 i=cmd.index('--chdir');cmd[i:i]=['--ro-bind',str(node),'/runtime/node']
 return cmd

def offline():
 p=O/'offline';(p/'workspace').mkdir(parents=True);shutil.copytree(O/'materials/C3/candidate',p/'workspace',dirs_exist_ok=True)
 save(p/'meter/config.json',{'global_cap':1,'calls':{'offline':{'cap':1,'mode':'maintenance'}}})
 cmd=command('offline',p,p/'meter');prefix=cmd[:cmd.index('--')+1]
 script="""from pathlib import Path
import subprocess,json
p=Path('/workspace');q=p/'offline-write';q.write_text('ok');assert q.read_text()=='ok';q.unlink()
assert not Path('/home/sribd').exists() and not Path('/proc/1/root/home/sribd').exists()
assert not Path('/workspace/oracle').exists() and not Path('/workspace/README.hidden').exists()
assert subprocess.check_output(['/runtime/node','--version'],text=True).strip()=='v16.20.2'
print((p/'src/controller.js').read_text())
"""
 t=subprocess.run(prefix+['/usr/bin/python3','-c',script],capture_output=True,text=True,timeout=20);(p/'source-read-write-check.txt').write_text(t.stdout+t.stderr);assert t.returncode==0
 flags=[]
 for i,x in enumerate(cmd):
  if x in ['-c','--enable','--disable']:flags+=cmd[i:i+2]
 t=subprocess.run(prefix+['/opt/codex','features','list']+flags,capture_output=True,text=True,timeout=20);assert t.returncode==0;(p/'effective-features.txt').write_text(t.stdout)
 f={x.split()[0]:x.split()[-1]=='true' for x in t.stdout.splitlines() if x.strip()};assert f['code_mode_host'] and f['shell_tool'] and not any(f[k] for k in ['apps','plugins','multi_agent'])
 t=subprocess.run(prefix+['/opt/codex-code-mode-host','--help'],capture_output=True,text=True,timeout=20);assert t.returncode==0
 fake="import subprocess,json;ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'});subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
 import shlex
 t=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(fake)],capture_output=True,text=True,timeout=20);assert t.returncode!=0 and not (p/'cli-output/over-cap').exists()
 shutil.rmtree(O/'.runtime/offline')
 save(O/'offline-validation.json',{'status':'PASS','model_calls':0,'workspace_write_and_source_read':True,'research_and_scorer_unmounted':True,'runtime':'v16.20.2','backend_host_help':True,'features':f,'request_cap_hard_kill_exit':t.returncode,'command':cmd,'threat_model':'cooperative maintenance model inside filesystem namespace; tools may access system binaries, dedicated profile/output and meter; no host research/source beyond candidate mounted. Native hooks enforce budget; no experimental ReAct.'})

def freeze():
 assert read(O/'admission.json')['C3']['eligible'];assert read(O/'offline-validation.json')['status']=='PASS'
 order=[s for s in read(R/'research/candidate-contract-repair-prep-v1-20261107/schedule.proposed.json')['order'] if s['case']=='C3']
 for s in order:
  s.update(status='FROZEN',actual_prompt=None,actual_output=None);s['prompt']=str(O/'prompts/C3'/(s['condition']+'.md'))
 save(O/'schedule.json',{'seed':2026110710,'order':order,'filter':'C3 eligible; C1 scoring-policy mismatch','maximum_sessions':6})
 save(O/'request-meter/config.json',{'global_cap':49,'calls':{s['call_id']:{'cap':12,'mode':'maintenance'} for s in order}})
 config={'model':'gpt-6-sol','effort':'low','service_tier':'priority','timeout_seconds':600,'per_slot_requests':12,'global_requests':49,'final_report_characters':6000,'sessions':6,'retries':0,'reAct':False,'source_read_backend':['code_mode_host','shell_tool'],'scoring':str(O/'admission.json'),'public_materials':prev.hashes(O/'materials/C3'),'contract_only_group_difference':True,'server_routing_attested':False,'global_config_before':prev.global_snapshot()}
 save(O/'frozen-config.json',config)
 files=[p for sub in ['materials','contracts','prompts','scoring'] for p in (O/sub).rglob('*') if p.is_file()]+[O/n for n in ['runner.py','request_guard.py','research-config.toml','models-cache.snapshot.json','extraction.schema.json','schedule.json','admission.json','frozen-config.json','request-meter/config.json']]
 b=read(O/'source-score-bindings.previous.json')['cases']['C3'];case=Path(b['case_manifest']);files += [case]+[case.parent/'oracle'/n for n in b['oracle_files']]
 save(O/'protocol.json',{'files':{str(p):sha(p) for p in files},'frozen_before_model_calls':True})
 (O/'protocol.sha256').write_text(sha(O/'protocol.json')+'\n')

def run():
 assert not (O/'requests.json').exists()
 for slot in read(O/'schedule.json')['order']:
  assert sha(O/'protocol.json')==(O/'protocol.sha256').read_text().strip()
  for p,h in read(O/'protocol.json')['files'].items():assert sha(p)==h,p
  folder=O/'runs'/slot['call_id'];folder.mkdir(parents=True,exist_ok=False);shutil.copytree(O/'materials/C3/candidate',folder/'workspace')
  prompt=Path(slot['prompt']).read_text();(folder/'actual-prompt.md').write_text(prompt);cmd=command(slot['call_id'],folder)
  rec=dict(slot,model='gpt-6-sol',effort='low',service_tier='priority',started_at=time.time(),command=cmd,prompt_sha256=prev.sha(prompt),status='launched')
  rows=read(O/'requests.json') if (O/'requests.json').exists() else [];rows.append(rec);save(O/'requests.json',rows)
  try:
   with (folder/'actual-prompt.md').open('rb') as inp,(folder/'events.jsonl').open('wb') as out,(folder/'stderr.log').open('wb') as err:
    proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err,cwd=folder/'workspace',start_new_session=True)
    try:proc.wait(timeout=600)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();rec['timed_out']=True
   events=[json.loads(x) for x in (folder/'events.jsonl').read_text().splitlines()];turns=[e for e in events if e.get('type')=='turn.completed'];meter=read(O/'request-meter/ledger.json');native=meter['sessions'].get(slot['call_id'],{})
   rawpath=folder/'cli-output/answer.json';raw=rawpath.read_text() if rawpath.exists() else '';(folder/'raw-answer.txt').write_text(raw)
   errors=[]
   try:
    ans=json.loads(raw);assert set(ans)=={'report'} and isinstance(ans['report'],str) and len(ans['report'])<=6000
   except (ValueError,AssertionError,TypeError):errors.append('invalid_output_format')
   rec.update(exit_code=proc.returncode,seconds=time.time()-rec['started_at'],completed_at=time.time(),native=native,usage={k:sum(t.get('usage',{}).get(k,0) or 0 for t in turns) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']},tools=sum(e.get('type')=='item.completed' and e.get('item',{}).get('type') not in [None,'agent_message','reasoning','error'] for e in events),format_errors=errors)
   rec['status']='completed' if proc.returncode==0 and len(turns)==1 and native.get('started',0)>0 and native.get('started')==native.get('completed') and not native.get('blocked_requests') and not errors else 'execution_failed'
   diff=subprocess.run(['diff','-ruN',str(O/'materials/C3/candidate'),str(folder/'workspace')],capture_output=True,text=True);(folder/'patch.diff').write_text(diff.stdout)
   save(folder/'candidate-hashes.json',prev.hashes(folder/'workspace'))
   # Scoring happens in the research host only after session exit.
   b=read(O/'source-score-bindings.previous.json')['cases']['C3'];score=subprocess.run([str(node),str(Path(b['case_manifest']).parent/'oracle/probe.cjs'),str(folder/'workspace'),'ungranted'],capture_output=True,text=True,timeout=60)
   (folder/'score.stdout.json').write_text(score.stdout);(folder/'score.stderr.txt').write_text(score.stderr);rec['score_exit_code']=score.returncode
   try:rec['verdict']=json.loads(score.stdout)['verdict']
   except ValueError:rec['scoring_anomaly']=True
   save(folder/'receipt.json',rec);rows[-1]=rec;save(O/'requests.json',rows);print(json.dumps({k:rec.get(k) for k in ['call_id','condition','status','verdict','seconds','native']},ensure_ascii=False),flush=True)
   if not native.get('started'):raise RuntimeError('Native meter absent; no further sessions')
  finally:
   profile=O/'.runtime'/slot['call_id']
   if (profile/'config.toml').exists():save(folder/'configuration-after.json',{'profile_config_sha256':sha(profile/'config.toml'),'global_config':prev.global_snapshot(),'service_tier':'priority configured only; server route unattested'})
   shutil.rmtree(profile,ignore_errors=True)
if __name__=='__main__':globals()[sys.argv[1]]()

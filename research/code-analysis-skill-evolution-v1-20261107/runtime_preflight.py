"""Zero-model namespace/guard checks and pre-call protocol freeze."""
import importlib.util,json,shutil,subprocess,shlex
from pathlib import Path
from run import OUT,ROOT,read,save,sha,command
import request_guard as guard

def main():
 assert not (OUT/'requests.json').exists();schedule=read(OUT/'proposed-schedule.json');order=schedule['order'];slots=[]
 for i,row in enumerate(order,1):slots.append(dict(row,call_id='a'+str(i).zfill(2),sequence=i))
 save(OUT/'schedule.json',dict(seed=2026110701,order=slots));calls={s['call_id']:dict(cap=1 if s['phase']=='reflection' else 12,mode='reflection' if s['phase']=='reflection' else 'analysis') for s in slots};save(OUT/'request-meter/config.json',dict(calls=calls,global_cap=97))
 offline=OUT/'offline-runtime';offline.mkdir(exist_ok=True)
 for label,mode,cap in [('analysis','analysis',12),('reflection','reflection',1)]:
  d=offline/label;save(d/'config.json',dict(calls={'test':dict(cap=cap,mode=mode)}))
  for _ in range(cap):
   assert not guard.account({'hook_event_name':'PreModelRequest'},d,'test',False);assert not guard.account({'hook_event_name':'PostModelRequest','status':'completed'},d,'test',False)
  assert guard.account({'hook_event_name':'PreModelRequest'},d,'test',False)
 for label,event,mode in [('retry',{'hook_event_name':'PostModelRequest','status':'failed'},'analysis'),('no-tools',{'hook_event_name':'PreToolUse','tool_name':'exec_command','tool_input':{'cmd':'cat src/example'}},'reflection'),('no-tests',{'hook_event_name':'PreToolUse','tool_name':'exec_command','tool_input':{'cmd':'node script.js'}},'analysis')]:
  d=offline/label;save(d/'config.json',dict(calls={'test':dict(cap=12,mode=mode)}))
  if label=='retry':
   guard.account({'hook_event_name':'PreModelRequest'},d,'test',False);guard.account(event,d,'test',False);assert guard.account({'hook_event_name':'PreModelRequest'},d,'test',False)
  else:assert guard.account(event,d,'test',False)
 # Exact namespace: source read allowed, in-place mutation impossible, research unavailable.
 d=offline/'ns';work=d/'workspace';work.mkdir(parents=True);(work/'source.txt').write_text('frozen source')
 meter=offline/'fake';save(meter/'config.json',dict(calls={'offline':dict(cap=1,mode='analysis')}));cmd=command('offline',d,'analysis',False,meter);prefix=cmd[:cmd.index('--')+1]
 shell='set -eu\ntest ! -e /home/sribd\ntest ! -e /proc/1/root/home/sribd\ntest -f /workspace/source.txt\ncat /workspace/source.txt\nif echo overwrite > /workspace/source.txt; then exit 9; fi\ntest -x /opt/codex-code-mode-host\n/opt/codex --version\n'
 test=subprocess.run(prefix+['/bin/sh','-c',shell],capture_output=True,text=True,timeout=20);assert test.returncode==0,test.stderr
 code="import subprocess,json; ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'}); subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
 killed=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=20);assert killed.returncode!=0 and not (d/'cli-output/over-cap').exists();shutil.rmtree(OUT/'.runtime/offline')
 save(OUT/'runtime-preflight.json',dict(status='PASS',model_calls=0,source_readonly=True,research_not_mounted=True,no_test_commands=True,reflection_no_tools=True,caps_analysis12_reflection1=True,no_transport_retries=True,synchronous_kill_before_excess_request=True,namespace_stdout=test.stdout,namespace_stderr=test.stderr,fake_provider_exit=killed.returncode))
 # Freeze only genuinely immutable inputs, never mutable runtime manifests/ledgers.
 files=[OUT/n for n in ['PLAN.md','run.py','request_guard.py','REPORT_TEMPLATE.md','analysis_skill_K0.md','report.schema.json','reflection.schema.json','schedule.json','source-verification.json','standard-confirmation-update.json','confirmation-status.json','K0.freeze.json','request-meter/config.json']]
 files += [f for f in (OUT/'materials').rglob('*') if f.is_file()]
 standards=ROOT/'research/code-analysis-standard-drafts-v1-20261107';files+=list(standards.glob('*'))
 save(OUT/'protocol.json',dict(status='FROZEN_BEFORE_FORMAL_MODELS',model='gpt-6-sol',effort='low',timeout=600,session_cap=9,analysis_request_cap=12,reflection_request_cap=1,global_request_cap=97,report_character_cap=6000,independent_blind_human_review=False,files={str(f):sha(f.read_bytes()) for f in files if f.is_file()}));(OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('RUNTIME_PREFLIGHT_PASS_ZERO_MODELS')
if __name__=='__main__':main()

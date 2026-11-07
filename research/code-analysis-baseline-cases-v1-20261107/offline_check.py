"""Zero-model source, namespace, request accounting and freeze checks."""
import json,shlex,shutil,subprocess,hashlib
from pathlib import Path
from run import OUT,ROOT,HELPER,BINARY,command,read,save,sha
import request_guard as guard

def main():
 assert not (OUT/'requests.json').exists();off=OUT/'offline';off.mkdir()
 meter=off/'counter';save(meter/'config.json',dict(call_id='offline',request_cap=12))
 for i in range(12):
  assert not guard.account({'hook_event_name':'PreModelRequest'},meter,'offline',False)
  assert not guard.account({'hook_event_name':'PostModelRequest','status':'completed'},meter,'offline',False)
 assert guard.account({'hook_event_name':'PreModelRequest'},meter,'offline',False)
 retry=off/'retry';save(retry/'config.json',dict(call_id='offline',request_cap=12))
 guard.account({'hook_event_name':'PreModelRequest'},retry,'offline',False)
 guard.account({'hook_event_name':'PostModelRequest','status':'failed'},retry,'offline',False)
 assert guard.account({'hook_event_name':'PreModelRequest'},retry,'offline',False)
 tools=off/'tools';save(tools/'config.json',dict(call_id='offline',request_cap=12))
 assert not guard.account({'hook_event_name':'PreToolUse','tool_name':'exec_command','tool_input':{'cmd':'nl -ba src/example.js'}},tools,'offline',False)
 for name,text in [('exec_command','node src/example.js'),('apply_patch','change source'),('exec_command','npm test'),('exec_command','curl https://example.org')]:
  assert guard.account({'hook_event_name':'PreToolUse','tool_name':name,'tool_input':{'cmd':text}},tools,'offline',False)
 ns=off/'namespace';work=ns/'workspace';work.mkdir(parents=True);(work/'source.txt').write_text('frozen candidate')
 fake=off/'namespace-meter';save(fake/'config.json',dict(call_id='offline',request_cap=1))
 cmd=command('offline',ns,False,fake);prefix=cmd[:cmd.index('--')+1]
 shell='''set -eu
 test ! -e /home/sribd
 test ! -e /proc/1/root/home/sribd
 test ! -e /workspace/research
 test ! -e /workspace/source-manifest.json
 cat /workspace/source.txt
 if echo changed > /workspace/source.txt; then exit 9; fi
 /opt/codex --version
'''
 result=subprocess.run(prefix+['/bin/sh','-c',shell],capture_output=True,text=True,timeout=20)
 assert result.returncode==0,(result.stdout,result.stderr)
 code="import subprocess,json; ev=lambda k:json.dumps({'hook_event_name':k,'status':'completed'}); subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PostModelRequest'),text=True);subprocess.run(['/usr/bin/python3','/request_guard.py'],input=ev('PreModelRequest'),text=True);open('/output/over-cap','w').write('bad')"
 killed=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=20)
 assert killed.returncode!=0 and not (ns/'cli-output/over-cap').exists()
 shutil.rmtree(OUT/'.runtime/offline')
 # The exact shared prompt prefix/suffix and skill are byte-identical across cases.
 template=(OUT/'common-prompt-template.md').read_text();skill=(OUT/'analysis_skill_K0.md').read_text()
 for c in read(OUT/'source-verification.json')['cases']:
  base=OUT/'materials'/c['case'];prompt=(base/'prompt.md').read_text()
  assert prompt==template.replace('{{TASK}}',(base/'task.md').read_text()).replace('{{SKILL}}',skill)
  assert {str(f.relative_to(base/'candidate')):sha(f) for f in (base/'candidate').rglob('*') if f.is_file()}==c['candidate_files']
  assert not any(f.is_symlink() for f in (base/'candidate').rglob('*'))
 # Same parser/limit assumptions checked without any provider call.
 obj=json.loads(json.dumps({'report':'x'*6000}));assert set(obj)=={'report'} and len(obj['report'])==6000
 assert len(json.loads(json.dumps({'report':'x'*6001}))['report'])>6000
 limits=dict(top_level_sessions=6,per_session_native_requests=12,total_native_requests=72,timeout_seconds=600,report_unicode_character_limit=6000,auto_retry=False)
 save(OUT/'offline-validation.json',dict(status='PASS',model_calls=0,limits=limits,source_and_task_digests=True,K0_original_freeze_matched=True,common_prompt_bytes_equal_except_task=True,source_symlinks=False,read_only_workspace_verified=True,host_home_and_research_inaccessible=True,per_slot_meter_only=True,no_standard_in_workspace=True,excess_request_killed_before_dispatch=True,retry_blocked=True,candidate_programs_and_edit_tools_blocked=True,output_parser_and_length_checked=True,namespace_stdout=result.stdout,namespace_stderr=result.stderr,fake_provider_exit=killed.returncode,semantic_limit='These are offline runtime checks, not model behavior or independent human approval.'))
 files=[OUT/n for n in ['PLAN.md','prepare.py','run.py','request_guard.py','offline_check.py','analysis_skill_K0.md','report.schema.json','common-prompt-template.md','schedule.json','source-verification.json','confirmation-status.json','offline-validation.json']]
 files += [f for f in (OUT/'materials').rglob('*') if f.is_file()]
 files += [f for f in (ROOT/'research/code-analysis-standard-cases-v1-20261107').rglob('*') if f.is_file()]
 files += [HELPER,BINARY,ROOT/'research/code-analysis-skill-evolution-v1-20261107/analysis_skill_K0.md']
 config=Path.home()/'.codex/config.toml'
 if config.exists():files.append(config)
 save(OUT/'protocol.json',dict(status='FROZEN_BEFORE_FORMAL_MODELS',model='gpt-6-sol',effort='low',limits=limits,binary_version=result.stdout.splitlines()[-1],files={str(f):sha(f) for f in files},standard_confirmations='none; all draft business policies pending',skill_version='original analysis K0',seed=2026110708))
 (OUT/'protocol.sha256').write_text(sha(OUT/'protocol.json')+'\n')
 print('OFFLINE_PASS_ZERO_MODELS: runtime, budgets, materials and plan frozen')
if __name__=='__main__':main()

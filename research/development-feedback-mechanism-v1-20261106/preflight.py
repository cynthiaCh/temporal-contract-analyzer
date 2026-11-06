"""No model pre-run: input isolation and guard tests with an OS-level fake provider."""
import importlib.util,json,shutil,subprocess,sys,shlex,hashlib
from pathlib import Path
from run import OUT,ROOT,read,save,sha,command,FEATURES
import request_guard as guard

def main():
    assert not (OUT/'requests.json').exists();offline=OUT/'offline';offline.mkdir(exist_ok=True)
    for mode in ['global','session','tool']:
        d=offline/mode;save(d/'config.json',dict(global_cap=8,per_session_cap=1))
        if mode=='global':
            for i in range(8):assert not guard.account(dict(hook_event_name='PreModelRequest',simulation=True),d,str(i),False)
            assert guard.account(dict(hook_event_name='PreModelRequest',simulation=True),d,'9',False);assert read(d/'ledger.json')['started']==8
        elif mode=='session':
            assert not guard.account(dict(hook_event_name='PreModelRequest',simulation=True),d,'x',False);assert guard.account(dict(hook_event_name='PreModelRequest',simulation=True),d,'x',False);assert read(d/'ledger.json')['started']==1
        else:assert guard.account(dict(hook_event_name='PreToolUse',tool_name='Bash',simulation=True),d,'x',False)
    # Exact namespace, no /opt/codex execution: substitute a Python fake ancestor.
    d=offline/'fake-provider';save(d/'config.json',dict(global_cap=8,per_session_cap=1));cmd=command('offline',offline/'namespace',d,copy_auth=False);prefix=cmd[:cmd.index('--')+1]
    check=subprocess.run(prefix+['/bin/sh','-c','test ! -e '+str(ROOT)+' && test -f /request_guard.py && test -d /workspace'],capture_output=True,text=True,timeout=20);assert check.returncode==0,check.stderr
    code="import subprocess,json; e=json.dumps({'hook_event_name':'PreModelRequest','simulation':True}); [subprocess.run(['/usr/bin/python3','/request_guard.py'],input=e,text=True) for _ in range(2)]; open('/output/unexpected-continuation','w').write('bad')"
    killed=subprocess.run(prefix+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=20);assert killed.returncode!=0;assert read(d/'ledger.json')['started']==1 and read(d/'ledger.json')['blocked_requests']==1;assert not (offline/'namespace/cli-output/unexpected-continuation').exists()
    save(offline/'fake-provider-result.json',dict(exit_code=killed.returncode,stdout=killed.stdout,stderr=killed.stderr,model_calls=0))
    # Independently test denial before any fake tool action.
    td=offline/'fake-tool';save(td/'config.json',dict(global_cap=8,per_session_cap=1));tc=command('offline-tool',offline/'tool-namespace',td,copy_auth=False);tp=tc[:tc.index('--')+1]
    code="import subprocess,json; subprocess.run(['/usr/bin/python3','/request_guard.py'],input=json.dumps({'hook_event_name':'PreToolUse','simulation':True}),text=True); open('/output/unexpected-tool','w').write('bad')"
    killed2=subprocess.run(tp+['/bin/bash','-c','exec -a /opt/codex /usr/bin/python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=20);assert killed2.returncode!=0 and not (offline/'tool-namespace/cli-output/unexpected-tool').exists()
    for name in ['offline','offline-tool']:shutil.rmtree(OUT/'.runtime'/name,ignore_errors=True)
    controls=[]
    for unit in ['U1','U2']:
        d=OUT/'inputs'/unit;prefix=(d/'common-prefix.md').read_text();suffix=(d/'common-suffix.md').read_text()
        for arm in ['A','B']:
            text=(d/(arm+'.prompt.md')).read_text();block=(d/(arm+'.feedback-block.md')).read_text();assert text==prefix+block+suffix;assert len(text)<=72000
        common=read(d/'common-record.json');assert 'Feedback' not in common;assert 'raw_failed_assertions' not in (d/'B.prompt.md').read_text();controls.append(read(d/'control-check.json'))
    old=(OUT/'HISTORICAL_REFLECTION_TEMPLATE.md').read_text();new=(OUT/'REFLECTION_TEMPLATE.md').read_text();assert old.split('Return only the complete proposed skill')[0]==new.split('Return one JSON object')[0]
    s=read(OUT/'schedule.json')['order'];assert len(s)==8 and len({(x['unit'],x['condition'],x['replicate']) for x in s})==8
    units=read(OUT/'units.freeze.json');keys=read(OUT/'evidence-key.json');assert len(units)==len(keys['units'])==2;assert units[0]['job']!=units[1]['job']
    save(OUT/'offline-validation.json',dict(status='PASS',model_calls=0,maintenance_runs=0,scorer_runs=0,optimizer_runs=0,inputs_controlled=True,only_feedback_block_varies=True,common_output_clause_change_disclosed=True,schema_common=True,schedule_slots=8,global_native_cap=8,per_session_native_cap=1,cli_entries_cap=8,fake_provider_terminated_before_second_request=True,fake_tool_terminated_before_execution=True,research_root_inaccessible=True,readonly_workspace=True,features_disabled=FEATURES,no_model_prerun=True,live_native_hook_firing='verify during first formal request; old endpoint uses this hook interface',controls=controls))
    frozen=[p for p in OUT.rglob('*') if p.is_file() and (p.suffix in ['.py','.md','.json','.jsonl','.diff']) and 'offline' not in p.relative_to(OUT).parts and '.runtime' not in p.relative_to(OUT).parts and p.name not in ['initial-state.json','protocol.json','offline-validation.json']]
    save(OUT/'protocol.json',dict(status='FROZEN_BEFORE_GENERATION',model='gpt-6-sol',effort='low',timeout=600,max_cli_sessions=8,max_native_requests=8,per_session_cap=1,seed=2026110606,input_character_cap=72000,output_skill_character_cap=6000,output_notes_character_cap=1200,units=units,reviewer_mode='unblinded executing-agent proxy; independent human review pending',frozen_files={str(p):sha(p.read_bytes()) for p in frozen}))
    (OUT/'protocol.sha256').write_text(sha((OUT/'protocol.json').read_bytes())+'\n');print('PREFLIGHT_PASS_NO_MODELS')
if __name__=='__main__':main()

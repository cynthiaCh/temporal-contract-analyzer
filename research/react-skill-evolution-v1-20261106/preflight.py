"""No-model offline checks of sources, isolation, hooks discovery and controller logic."""
import importlib.util,json,os,selectors,shutil,subprocess,threading,time
from pathlib import Path
from run import OUT,REPO,DEV,HOLD,wb,rt,NODE,read,save,sha,frozen,runtime,invoke,Workbench,capture,file_modes,write_files,candidate_check


def main():
    p=frozen();w=wb();root=OUT/'offline';root.mkdir();syn=root/'synthetic';workspace=syn/'workspace';stage=syn/'stage';control=syn/'control'
    for f in [workspace/'src',stage,control]:f.mkdir(parents=True)
    (workspace/'src/sample.js').write_text('export const value = 1;\n// original\n')
    spec=importlib.util.spec_from_file_location('synthetic_controller',OUT/'controller.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    initial=module.hashes(workspace);save(control/'config.json',dict(active=True,initial_files=initial))
    events=[]
    def hook(kind,tool='',command='',code=0,output='actual synthetic output'):
        e=dict(hook_event_name=kind,session_id='synthetic-same-session',turn_id='synthetic-same-turn',tool_name=tool,tool_input=dict(command=command),tool_response=dict(exit_code=code,stdout=output))
        response=module.handle(e,control,workspace,stage);events.append(dict(event=e,response=response));return response
    response=hook('PostToolUse','Bash','cat src/sample.js',output=(workspace/'src/sample.js').read_text());assert 'additionalContext' in response['hookSpecificOutput'];assert read(control/'state.json')['state']=='inspect'
    assert hook('PreToolUse','apply_patch','*** Update File: /workspace/src/sample.js')['hookSpecificOutput']['permissionDecision']=='deny'
    checkpoint=dict(state='inspect',action_basis='visible task and source',evidence=['src/sample.js:1'],applicability='applicable',event_orders=['ordinary completion','completion after ownership changes'],observations='source read',unresolved=[],next_action='repair')
    save(stage/'checkpoint.json',checkpoint);hook('PostToolUse','Bash','write checkpoint',output='checkpoint written');assert read(control/'state.json')['state']=='repair_validate'
    (workspace/'src/sample.js').write_text('export const value = 2;\n// changed\n');hook('PostToolUse','apply_patch','update src/sample.js')
    checkpoint.update(state='repair_validate',maintenance_status='completed',reason='visible requirement repaired');save(stage/'checkpoint.json',checkpoint)
    assert hook('Stop')['decision']=='block'
    actual=subprocess.run(['node','--check',str(workspace/'src/sample.js')],capture_output=True,text=True)
    # Node check of module may need stdin; this is a no-dependency synthetic syntax check.
    if actual.returncode:actual=subprocess.run(['node','--input-type=module','--check'],input=(workspace/'src/sample.js').read_text(),capture_output=True,text=True)
    assert actual.returncode==0
    hook('PostToolUse','Bash','node --check src/sample.js',code=actual.returncode,output=actual.stdout+actual.stderr)
    assert hook('Stop').get('decision')!='block';assert read(control/'state.json')['completion_check']['mechanical_pass']
    # New synthetic state: no diff is allowed with cited no-change/incomplete explanation.
    (control/'state.json').unlink();save(control/'config.json',dict(active=True,initial_files=module.hashes(workspace)))
    hook('PostToolUse','Bash','cat src/sample.js',output=(workspace/'src/sample.js').read_text());checkpoint.update(maintenance_status='no_change',reason='source already meets synthetic requirement');save(stage/'checkpoint.json',checkpoint);assert hook('Stop').get('decision')!='block'
    checkpoint.pop('maintenance_status');save(stage/'checkpoint.json',checkpoint);assert hook('Stop')['decision']=='block'
    checkpoint.update(maintenance_status='incomplete',reason='visible evidence insufficient');save(stage/'checkpoint.json',checkpoint);assert hook('Stop').get('decision')!='block'
    hook('PostToolUse','Bash','node failing-check.js',code=1,output='AssertionError');assert events[-1]['response']['hookSpecificOutput']['additionalContext']
    checkpoint.update(state='collect',unresolved=['missing dependency guarantee']);save(stage/'checkpoint.json',checkpoint);hook('PostToolUse','Bash','cat src/sample.js',output='source');assert read(control/'state.json')['state']=='collect'
    # Passive condition records actual outputs without injecting or denying/continuing.
    (control/'state.json').unlink();save(control/'config.json',dict(active=False,initial_files=module.hashes(workspace)));assert hook('PostToolUse','Bash','cat src/sample.js',output='source')=={};assert hook('Stop')=={}
    save(root/'synthetic-tests.json',dict(status='PASS',synthetic_only=True,same_session_and_turn=True,events=events,checks=['source observation and inspect transition','pre-edit evidence denial','inspection to repair transition','patch snapshot','stop continuation without verification','actual synthetic syntax validation','completion with patch and validation','evidence-backed no-change allowed','question-only outcome continued','explicit incomplete allowed','actual nonzero output feedback','return to collect','passive control no feedback']))
    # Real runtime configuration/isolated shell, but no inference turn.
    sample=root/'runtime';work=sample/'workspace';work.mkdir(parents=True);(work/'sample.js').write_text('const value = 1;\n');save(sample/'dummy.json',{})
    manifest=dict(id='offline-hooks',mode='workspace-write',local_codex=True,model_override='gpt-6-sol',effort='low',react_control=True)
    cmd=w.command(manifest,work,sample/'answer.md');prefix=cmd[:cmd.index('--')+1]
    shell='''set -eu
test ! -e /home/sribd
test ! -e /proc/1/root/home/sribd
test ! -e /workspace/../materials
test -x /opt/codex-code-mode-host
/opt/codex --version
/opt/codex-code-mode-host --help
/usr/bin/python3 -c "import json; from pathlib import Path; compile(Path('/controller.py').read_text(),'/controller.py','exec')"
node --check /workspace/sample.js
/runtime/node16 --version
printf '{"hook_event_name":"SessionStart","session_id":"offline-cli-shape"}' | /usr/bin/python3 /controller.py
'''
    proc=subprocess.run(prefix+['/bin/bash','-c',shell],capture_output=True,text=True,timeout=30);save(root/'isolation.json',dict(exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr));assert proc.returncode==0,proc.stderr
    rpc=subprocess.Popen(prefix+['/opt/codex','app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(root/'appserver.stderr').open('w'),text=True,bufsize=1)
    messages=[]
    def send(obj):rpc.stdin.write(json.dumps(obj)+'\n');rpc.stdin.flush()
    def until(identifier):
        end=time.monotonic()+30
        while time.monotonic()<end:
            ready,_,_=__import__('select').select([rpc.stdout],[],[],1)
            if not ready:continue
            line=rpc.stdout.readline()
            if not line:raise RuntimeError('appserver ended')
            obj=json.loads(line);messages.append(obj)
            if obj.get('id')==identifier:
                assert 'error' not in obj,obj
                return obj
        raise TimeoutError('offline hooks discovery')
    try:
        send(dict(id=1,method='initialize',params=dict(clientInfo=dict(name='react-skill-offline',version='1'),capabilities=dict(experimentalApi=True))));until(1);send(dict(method='initialized',params={}))
        send(dict(id=2,method='hooks/list',params=dict(cwds=['/workspace'])));response=until(2)
        text=json.dumps(response);assert '/controller.py' in text and 'postToolUse' in text and 'stop' in text
    finally:
        rpc.terminate();rpc.wait(timeout=10);shutil.rmtree(OUT/'.runtime/offline-hooks',ignore_errors=True)
    save(root/'hooks-discovery.json',dict(no_model_turn_sent=True,messages=messages));cal=[]
    for case,meta in p['cases'].items():
        cp=Path(meta['manifest']);cm=read(cp);engine=runtime(cm,'legacy-js',str(NODE))
        for label in ['unchanged','reference']:
            files,_=capture(cp.parent/'base');modes=file_modes(cp.parent/'base',files)
            if label=='reference':
                ref=cp.parent/cm['references']['bounded'];overlay,_=capture(ref);files.update(overlay);modes.update(file_modes(ref,overlay))
            dest=OUT/'calibration'/case/label/'candidate';write_files(dest,files,modes)
            raw=invoke([engine['path'],str(cp.parent/cm['oracle']['probe']),str(dest),'ungranted'],dest.parent/'oracle',threading.Event(),Workbench.terminate,case)
            assert raw['verdict']==('PASS' if label=='reference' else 'UNDERREACH')
            cal.append(dict(case=case,label=label,verdict=raw['verdict'],runtime=engine))
    assert candidate_check(dict(skill=(OUT/'K0.md').read_text(),parent='K0',changes=[dict(failure_evidence='synthetic',step_changed='S1',observable_action_change='synthetic',preserved_behavior_risk='synthetic')]))['valid']
    assert not candidate_check(dict(skill='S1 src/answer.js S2 S3 S4 S5 S6',parent='K0',changes=[]))['valid']
    for c in DEV+HOLD:
        folder=OUT/'materials'/c;a=(folder/'A-K0.prompt.md').read_text();b=(folder/'B-K0.prompt.md').read_text();assert a+( '\n<external-control>\n'+(OUT/'CONTROL.md').read_text()+'\n</external-control>\n')==b
        assert sha((folder/'common.md').read_bytes())==p['cases'][c]['common_sha256']
    save(OUT/'preflight.json',dict(status='PASS',at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),no_model_calls=True,calibration=cal,source_and_split_frozen=True,skill_parent_delivery_archived=True,common_byte_equality=True,synthetic_controller_checks=13,real_cli_hooks_discovered=True,real_cli_hook_execution_without_inference='controller run inside exact namespace; native hook firing first checked during formal execution and not falsely pre-certified',hidden_scoring_isolation=True,heldout_not_in_optimizer=True))
    print('PREFLIGHT_PASS',flush=True)
if __name__=='__main__':main()

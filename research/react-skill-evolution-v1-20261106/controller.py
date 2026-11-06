"""Synchronous, bounded observation/completion controller. No model/scorer access."""
import fcntl, hashlib, json, os, re, sys, time
from pathlib import Path


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and '.git' not in p.parts}


def tool_result(event):
    value=event.get('tool_response');text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
    codes=[]
    def visit(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k in ('exit_code','exitCode','process_exit_code') and isinstance(x,int):codes.append(x)
                else:visit(x)
        elif isinstance(v,list):
            for x in v:visit(x)
    visit(value)
    codes += [int(n) for n in re.findall(r'(?:Process exited with code|exit code|Exit code|exit_code["\s:]*)\s*[:=]?\s*(-?\d+)',text)]
    return text,codes[-1] if codes else None


def checkpoint(root,workspace,seen):
    file=root/'checkpoint.json'
    try:
        raw=file.read_text();obj=json.loads(raw)
        assert len(raw)<=2400 and isinstance(obj,dict)
    except (OSError,ValueError,AssertionError):return {},False,[]
    citations=[]
    for value in obj.get('evidence',[]):
        if not isinstance(value,str):continue
        m=re.fullmatch(r'(?:/workspace/)?([^:]+):(\d+)(?:-\d+)?',value.strip())
        if not m:continue
        path=workspace/m[1]
        try:
            if path.is_file() and workspace.resolve() in path.resolve().parents and 1<=int(m[2])<=len(path.read_text().splitlines()) and m[1] in seen:citations.append(value)
        except (OSError,UnicodeError):pass
    applicable=obj.get('applicability')
    orders=obj.get('event_orders',[])
    valid=bool(citations) and bool(obj.get('action_basis')) and ((applicable=='applicable' and isinstance(orders,list) and len(orders)>=2) or (applicable=='not_applicable' and bool(obj.get('reason'))))
    return obj,valid,citations


def handle(event,root=Path('/control'),workspace=Path('/workspace'),stage=Path('/stage')):
    config=json.loads((root/'config.json').read_text());active=config['active'];state_path=root/'state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else dict(state='collect',steps=0,source_observations=0,seen_paths=[],validations=[],snapshot=config['initial_files'],last_change_step=0,injections=0,edit_blocks=0,stop_blocks=0,backtracks=0)
    kind=event.get('hook_event_name');reply={};start=time.monotonic();before=state['state'];text='';code=None;changed=[];decision='observe';reason=''
    tool=event.get('tool_name','');command=event.get('tool_input',{});command=command.get('command','') if isinstance(command,dict) else str(command)
    if kind=='PostToolUse':
        state['steps']+=1;text,code=tool_result(event);snapshot=hashes(workspace)
        changed=[p for p in set(snapshot)|set(state['snapshot']) if snapshot.get(p)!=state['snapshot'].get(p)]
        if changed:state['last_change_step']=state['steps']
        state['snapshot']=snapshot
        # Read observations are linked to actual output, not a self-authored stage claim.
        if code in (0,None) and text and re.search(r'\b(cat|sed|rg|head|tail|nl|read_text|readFile)\b',command):
            found=[p for p in snapshot if p in command or p in text or (('src/*.js' in command or 'src/*' in command) and p.startswith('src/'))]
            if found:
                state['source_observations']+=1;state['seen_paths']=sorted(set(state['seen_paths'])|set(found))
        if re.search(r'\b(node|npm|pytest|unittest|test|assert)\b|--check',command) and (code is not None or 'passed' in text.lower() or 'AssertionError' in text):
            state['validations'].append(dict(step=state['steps'],tool_use_id=event.get('tool_use_id'),command=command,exit_code=code,after_last_change=state['steps']>state['last_change_step']))
    obj,inspected,citations=checkpoint(stage,workspace,state['seen_paths'])
    if active:
        if kind=='PostToolUse':
            feedback=[]
            if obj.get('state')=='collect' and obj.get('unresolved') and before!='collect' and state['backtracks']<2:
                state['state']='collect';state['backtracks']+=1;feedback.append('A recorded unresolved evidence gap requests collect. Resolve the decision-relevant definition/caller before relying on it.')
            elif state['state']=='collect' and state['source_observations']:
                state['state']='inspect';feedback.append('Actual source output is now available. Inspect the applicable skill relations and concrete event orders; cite observed source, keep unknowns explicit, then continue the original maintenance task.')
            if inspected and state['source_observations'] and obj.get('state') in ('inspect','repair_validate'):
                state['state']='repair_validate'
                if before!='repair_validate':feedback.append('A cited inspection checkpoint exists. Its semantics are not certified. Continue the original maintenance repair and verify the supported behavior; a discussion alone is not the requested deliverable.')
            if code not in (0,None):feedback.append('The last actual tool output has nonzero exit code '+str(code)+'. Distinguish an environment/command issue, a failed behavioral check and an unsupported expectation before changing code or claiming validation.')
            if changed:feedback.append('Observed workspace file changes: '+', '.join(changed[:6])+'. Run relevant visible verification after this change and preserve original task/adjacent behavior.')
            if feedback and state['injections']<8:
                reason=' '.join(feedback);reply={'hookSpecificOutput':{'hookEventName':kind,'additionalContext':'External control ['+state['state']+']: '+reason}};state['injections']+=1;decision='continue-with-observation'
        elif kind=='PreToolUse':
            candidate_write=(tool in ('apply_patch','Edit','Write') and '/stage/' not in command) or (tool=='Bash' and re.search(r'(?:\b(?:cat|tee)\b[^\n]*>\s*(?:/workspace/)?(?:src/|[A-Za-z_])|\bwrite_text\s*\(|\bwriteFile|\bapply_patch\b|sed\s+-i)',command) and not ('/stage/checkpoint.json' in command and not re.search(r'/workspace/|src/',command)))
            if candidate_write and not inspected and state['edit_blocks']<2:
                state['edit_blocks']+=1;decision='deny-edit-for-evidence';reason='Before a candidate edit, use actual source output and write /stage/checkpoint.json with cited evidence, applicability and two relevant event orders (or an evidence-backed non-applicability reason). Then perform the original maintenance task. No particular patch is required.'
                reply={'hookSpecificOutput':{'hookEventName':kind,'permissionDecision':'deny','permissionDecisionReason':reason}}
        elif kind=='Stop':
            snapshot=hashes(workspace);changed=[p for p in set(snapshot)|set(config['initial_files']) if snapshot.get(p)!=config['initial_files'].get(p)]
            status=obj.get('maintenance_status');explanation=bool(obj.get('reason')) and bool(citations)
            actual_validation=any(v['step']>state['last_change_step'] for v in state['validations'])
            if changed:
                maintenance=(status in ('completed','incomplete') and explanation and actual_validation)
            else:maintenance=(status in ('no_change','incomplete') and explanation and state['source_observations']>0)
            state['completion_check']=dict(changed_paths=changed,declared_status=status,actual_validation_after_change=actual_validation,cited_reason=explanation,mechanical_pass=bool(maintenance),semantic_correctness='not established by controller')
            if not maintenance and state['stop_blocks']<2:
                state['stop_blocks']+=1;decision='continue-same-session';reason='The original maintenance task has not yet been accounted for by actual artifacts. '+('Workspace changes exist but a cited completion record or post-change visible validation is missing. ' if changed else 'No candidate patch was observed; a contract-only answer is not task completion. ')+ 'Continue this SAME task: implement and verify a justified repair, or record an evidence-backed no_change/incomplete outcome and its reason in /stage/checkpoint.json. Do not force a diff or invent requirements.'
                reply={'decision':'block','reason':reason}
            else:decision='allow-stop' if maintenance else 'allow-stop-with-unresolved-limit'
    elif kind=='Stop':
        snapshot=hashes(workspace);state['completion_check']=dict(changed_paths=[p for p in set(snapshot)|set(config['initial_files']) if snapshot.get(p)!=config['initial_files'].get(p)],passive=True)
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    entry=dict(at=time.time(),session_id=event.get('session_id'),turn_id=event.get('turn_id'),event=event,controller_state_before=before,controller_state_after=state['state'],decision=decision,reason=reason,exit_code=code,changed_paths=changed,citations=citations,active=active,response=reply,controller_seconds=time.monotonic()-start)
    with (root/'hook-events.jsonl').open('a') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    return reply


def main():
    event=json.load(sys.stdin);root=Path(os.environ.get('TCA_CONTROL_ROOT','/control'));workspace=Path(os.environ.get('TCA_CONTROL_WORKSPACE','/workspace'));stage=Path(os.environ.get('TCA_CONTROL_STAGE','/stage'))
    with (root/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);response=handle(event,root,workspace,stage)
    print(json.dumps(response,ensure_ascii=False))
if __name__=='__main__':main()

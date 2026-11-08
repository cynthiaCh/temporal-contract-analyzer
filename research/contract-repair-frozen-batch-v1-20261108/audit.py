"""Read-only historical investigation; writes only this new research directory."""
import hashlib, json, subprocess
from pathlib import Path

O = Path(__file__).resolve().parent
R = O.parent.parent
U = R / 'research/u2-contract-repair-diagnostic-v1-20261108'
B = R.parent / 'temporal-contract-bench-git'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name, obj):
    p = O / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True)

def main():
    save('initial-state.json', {
        'analyzer': {k: git(R, *v) for k,v in {'head':['rev-parse','HEAD'], 'status':['status','--porcelain=v1'], 'diff':['diff'], 'staged':['diff','--cached']}.items()},
        'bench': {k: git(B, *v) for k,v in {'head':['rev-parse','HEAD'], 'status':['status','--porcelain=v1'], 'diff':['diff'], 'staged':['diff','--cached']}.items()},
        'global_config_sha256':sha(Path.home()/'.codex/config.toml'),
        'AGENTS': [{'path':str(p/'AGENTS.md'), 'exists':(p/'AGENTS.md').exists()} for p in [R,*R.parents,B,O,O.parent]],
        'note':'Analyzer initially clean before this new directory; untracked entries here are this task. Bench pre-existing modifications preserved.'})
    inventory=[]
    for p in sorted(U.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or '.runtime' in p.parts: continue
        row={'path':str(p.relative_to(R)), 'bytes':p.stat().st_size, 'sha256':sha(p)}
        try:
            text=p.read_text(); row['lines']=len(text.splitlines())
            if p.suffix=='.json':
                j=json.loads(text); row['json_type']=type(j).__name__
                row['keys_or_count']=list(j) if isinstance(j,dict) else len(j)
            elif p.suffix=='.jsonl':
                events=[json.loads(l) for l in text.splitlines() if l.strip()]
                row['events']=len(events)
                row['event_types']=sorted({str(e.get('type',e.get('event',{}).get('hook_event_name'))) for e in events})
            row['read_status']='fully_read'
        except (UnicodeError, ValueError) as e: row['read_status']=type(e).__name__
        inventory.append(row)
    save('evidence/historical-inventory.json', inventory)
    protected={str(p):sha(p) for root in [U,R/'research/contract-extraction-cross-case-v1-20261107',R/'research/contract-extraction-evolution-u2-v2-20261107'] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.runtime' not in p.parts}
    save('protected-files.json',protected)
    proofs={}
    for slot in ['u01','u02','u03','u04','u05','u06']:
        d=U/'runs'/slot
        events=[json.loads(l) for l in (d/'events.jsonl').read_text().splitlines()]
        tools=[{'event_line':n,'item':e['item']} for n,e in enumerate(events,1) if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
        messages=[{'event_line':n,'text':e['item'].get('text')} for n,e in enumerate(events,1) if e.get('item',{}).get('type')=='agent_message']
        proofs[slot]={'receipt':json.loads((d/'receipt.json').read_text()),'score':json.loads((d/'score.stdout.json').read_text()),'tool_outputs':tools,'agent_statements':messages,'patch_sha256':sha(d/'patch.diff'),'actual_prompt_sha256':sha(d/'actual-prompt.md')}
    save('evidence/historical-run-review.json',proofs)
    # Verify every file in the pre-execution protocol, including original oracle.
    protocol=json.loads((U/'protocol.json').read_text())
    save('evidence/historical-freeze-check.json',{'protocol_sha256_matches':sha(U/'protocol.json')==(U/'protocol.sha256').read_text().strip(),'files':{p:{'expected':h,'actual':sha(p),'matches':sha(p)==h} for p,h in protocol['files'].items()}})
    commits={}
    for rev in ['9d02bd7','cda6ef5']:
        changes=git(R,'diff-tree','--no-commit-id','--name-status','-r',rev)
        commits[rev]={'metadata':git(R,'show','-s','--format=fuller',rev),'changes':changes,
            'runner_and_input_paths':[l for l in changes.splitlines() if any(x in l for x in ['runner.py','request_guard.py','run.py','research-config.toml','materials/','prompts/','contracts/','models-cache'])]}
    actual_files=[U/'runner.py',U/'request_guard.py',U/'research-config.toml',R/'research/contract-extraction-cross-case-v1-20261107/run.py']
    save('evidence/head-investigation.json',{'commits':commits,'actual_execution_files':{str(p):{'current':sha(p),'protocol_expected':protocol['files'].get(str(p)),'same_as_current_HEAD':subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(R))],cwd=R)==p.read_bytes()} for p in actual_files},'prepare_change':git(R,'diff','9d02bd7','cda6ef5','--',str((U/'prepare.py').relative_to(R))),'origin':'Git author metadata is available; process/intent of external commit not established. No rollback performed.'})
    score=proofs['u02']['score'];save('evidence/five-failures.json',{'missing':score['missing_required_effects'],'observations':{k:score['schedules'][k] for k in ['downloadClosePending','downloadCloseReady','downloadReopen']},'agent_tools':proofs['u02']['tool_outputs']})
    print('historical files fully read:',len(inventory),'protocol mismatches:',[p for p,h in protocol['files'].items() if sha(p)!=h])

if __name__=='__main__':main()

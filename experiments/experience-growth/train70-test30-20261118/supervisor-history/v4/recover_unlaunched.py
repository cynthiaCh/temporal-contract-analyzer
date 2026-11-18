"""Recover controller-stop stages only when absence of dispatch is proven."""
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
from pathlib import Path
from temporal_contract_analyzer import archive
from temporal_contract_analyzer.tempoevo_v4 import Trajectory

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def read(path):return json.loads(Path(path).read_text())
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
STOP_ERROR="EvidenceError('Run dispatch stopped; inspect last event before resuming')"


def unlaunched_evaluation(stage,root):
    if stage.get('kind') not in ('visible','gold') or stage.get('status')!='invalid' or stage.get('requests')!=0:return False
    directory=Path(root)/'stages'/stage['key'];raw=directory/'raw-result.json'
    if not raw.exists():return False
    value=read(raw)
    return (value.get('valid') is False and value.get('failure_type')=='infrastructure_error' and value.get('error')==STOP_ERROR
        and {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}=={'input.json','raw-result.json','result.json'})


def controller_stopped(state,root):
    return state.get('status')=='execution_invalid' and (state.get('error')==STOP_ERROR
        or bool(state.get('stages')) and unlaunched_evaluation(state['stages'][-1],root))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id',required=True)
    parser.add_argument('--jobs',nargs='+',required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    root=(HERE/'runs'/args.run_id).resolve();assert root.parent==HERE/'runs'
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=read(root/'manifest.json')
        for relative,sha in manifest['bindings'].items():assert digest(REPO/relative)==sha,relative
        budget=read(root/'balance.json');assert budget['pending_stage_count']==0
        events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines() if line]
        for job in args.jobs:
            folder=(root/'jobs'/job).resolve();assert folder.parent==root/'jobs'
            trajectory=Trajectory(folder/'trajectory');trajectory.verify();state=trajectory.state()
            assert controller_stopped(state,trajectory.root)
            assert not (folder/'completion.json').exists()
            pending=[s for s in state['stages'] if s['status']=='started' or unlaunched_evaluation(s,trajectory.root)];assert pending
            retained=[s for s in state['stages'] if s not in pending]
            for stage in retained:
                assert stage['status']=='complete'
                assert digest(trajectory.root/'stages'/stage['key']/'result.json')==stage['result_sha256']
            items=[]
            for stage in pending:
                directory=(trajectory.root/'stages'/stage['key']).resolve();assert directory.parent==trajectory.root/'stages'
                prefix=directory.relative_to(root).as_posix()+'/'
                assert not any(s['stage_id'].startswith(prefix) for s in budget['stages'])
                assert not any(e.get('stage','').startswith(prefix) and e['event']=='stage_intent' for e in events)
                assert not any(e.get('stage')==prefix.rstrip('/') and e['event']=='evaluation_finished' for e in events)
                assert not list(directory.rglob('native-request.json')) and not list(directory.rglob('metered-result.json'))
                assert not list(directory.rglob('ledger.json'))
                items.append(dict(stage=stage['key'],stage_row=stage,files={p.relative_to(directory).as_posix():digest(p) for p in directory.rglob('*') if p.is_file()}))
            receipt=dict(at=datetime.now(timezone.utc).isoformat(),run_id=args.run_id,job=job,reason='Controller stop before stage admission; no model dispatch or budget consumption',
                before_state_sha256=digest(trajectory.root/'state.json'),preserved_completed_stages=[dict(key=s['key'],result_sha256=s['result_sha256'],requests=s.get('requests'),seconds=s.get('seconds')) for s in retained],
                unlaunched=items,model_calls=0,protocol_unchanged=True)
            if args.apply:
                recovery=folder/'recovery'/('controller-stop-before-dispatch-'+receipt['before_state_sha256'][:16]);recovery.mkdir(parents=True,exist_ok=False)
                (recovery/'state-before.json').write_bytes((trajectory.root/'state.json').read_bytes())
                for item in items:
                    (trajectory.root/'stages'/item['stage']).rename(recovery/item['stage'])
                state['stages']=retained;state['status']='prepared'
                for key in ('error','stop_reason'):state.pop(key,None)
                trajectory.save('state.json',state)
                receipt['after_state_sha256']=digest(trajectory.root/'state.json')
                archive.atomic_json(recovery/'receipt.json',receipt)
                event=dict(at=receipt['at'],run_id=args.run_id,event='unlaunched_stage_reconciled',job=job,
                    receipt_sha256=digest(recovery/'receipt.json'),model_calls=0,completed_results_preserved=True)
                for path in (root/'events.jsonl',HERE/'EVENTS.jsonl'):
                    with path.open('a',encoding='utf8') as stream:stream.write(json.dumps(event)+'\n')
            print(json.dumps(dict(job=job,applied=args.apply,preserved_completed=[r['key'] for r in retained],unlaunched=[r['stage'] for r in items],model_calls=0)))


if __name__=='__main__':main()

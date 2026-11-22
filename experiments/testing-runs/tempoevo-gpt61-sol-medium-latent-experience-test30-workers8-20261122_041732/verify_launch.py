"""Observe real CLI flags and successful model hooks without making requests."""
import datetime,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent/'temporal-contract-analyzer'
rows=json.loads((ROOT/'batch/progress.json').read_text());deadline=time.monotonic()+150
while True:
    requests=[];responses=[];commands=[];started=[]
    for row in rows:
        t=Path(row['root'])/'trajectory';s=json.loads((t/'state.json').read_text())
        assert s['contract'] is None and all(x['kind'] in ('action','gold') for x in s['stages'])
        if s['stages']:started.append(row['case_id'])
        for f in t.glob('stages/action-1/executions/*/native-stage/native/archive/meter/events.jsonl'):
            for line in f.read_text().splitlines():
                if not line:continue
                try:item=json.loads(line)
                except ValueError:continue
                e=item['event'];kind=e.get('hook_event_name')
                if kind=='PreModelRequest' and not item['denied']:
                    assert e['model']=='gpt-6.1-sol'
                    requests.append(dict(case_id=row['case_id'],model=e['model'],denied=False))
                if kind=='PostModelRequest' and e.get('status')=='completed':responses.append(dict(case_id=row['case_id'],status='completed'))
        for f in t.glob('stages/action-1/executions/*/native-stage/native/archive/command.json'):
            cmd=json.loads(f.read_text());assert cmd[cmd.index('-m')+1]=='gpt-6.1-sol'
            assert 'model_reasoning_effort="medium"' in cmd
            commands.append(dict(case_id=row['case_id'],model='gpt-6.1-sol',medium_flag=True))
    if len(started)>=8 and len({r['case_id'] for r in requests})>=8 and responses:
        report=dict(ready=True,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workers=8,started_cases=len(started),actual_request_cases=len({r['case_id'] for r in requests}),real_model_requests=requests,completed_responses=responses,verified_commands=commands,condition='latent_experience',contract_stage=False,experience_updates=False)
        break
    if time.monotonic()>deadline:
        report=dict(ready=False,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='Launch observation timed out; inspect running queue before any relaunch.',started_cases=len(started),actual_request_cases=len({r['case_id'] for r in requests}),completed_responses=len(responses));break
    time.sleep(2)
(ROOT/'launch-verification.json').write_text(json.dumps(report,indent=2)+'\n')
target=REPO/'experiments/testing-runs'/ROOT.name;shutil.copyfile(ROOT/'launch-verification.json',target/'launch-verification.json')
print(json.dumps({k:v for k,v in report.items() if k not in ('real_model_requests','verified_commands','completed_responses')}),flush=True)
sys.exit(0 if report['ready'] else 1)

"""One fresh replay for the sole execution-invalid case; retain all59 scores."""
import copy,datetime,hashlib,json,runpy,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
m=runpy.run_path(str(ROOT/'manage.py'));read=m['read'];write=m['write'];now=m['now']
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
plan=read(ROOT/'plan.json');arm=plan['arms'][0];parent=Path(arm['root'])
assert not plan.get('recoveries'),'Do not duplicate recovery'
row=next(r for r in read(parent/'batch/progress.json') if r['case_id']=='draft-autosave-handoff-order-example-react')
state=read(Path(row['root'])/'trajectory/state.json');assert state['status']=='execution_invalid' and not state.get('gold_result')
assert state['stages'][-1]['failure_type']=='infrastructure_error'
ident='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'-memory20-retry1'
target=REPO/'.tempoevo/runs'/ident;target.mkdir()
old=read(parent/'lab.json');cmd=old['prepare_command'][:]
for flag,value in [('--root',str(target/'batch')),('--start-rank','30'),('--limit','1')]:cmd[cmd.index(flag)+1]=value
config=copy.deepcopy(old['config']);config.update(start=30,count=1,workers=1)
meta=dict(id=ident,title='DeepSeek memory20 · execution-invalid recovery1',status='preparing',created_at=now(),config=config,model=old['model'],prepare_command=cmd,ablation=old['ablation'],recovery_of=arm['id'])
write(target/'lab.json',meta)
with (target/'prepare.log').open('w') as log:result=subprocess.run(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0
rows=read(target/'batch/progress.json');assert len(rows)==1 and rows[0]['case_id']==row['case_id']
t=Path(rows[0]['root'])/'trajectory';p=Trajectory(t).verify();before=read(Path(row['root'])/'trajectory/protocol.json')
for key in ('task','original_inventory','public_case_record','binary','model_settings','backend','limits','total_request_cap','max_attempts','mode','learning_policy','retrieval_profile','memory_snapshot'):
 assert p[key]==before[key],key
write(target/'paired-input-validation.json',dict(valid=True,cases=1,model_calls=0,original_invalid_case=row['case_id'],retained_scored_cases=59,parent=arm['id'],memory_size=20,same_task_source_model_budget_snapshot=True))
meta.update(status='prepared',prepared_cases=1);write(target/'lab.json',meta)
plan['recoveries']=[dict(size=20,id=ident,root=str(target),case_id=row['case_id'],reason='Qoder mandatory tool gate missing; original stage attributed infrastructure_error. Original receipt retained; no valid behavioral score replayed.')];write(ROOT/'plan.json',plan)
print(m['api']('/api/start',dict(id=ident)),flush=True)

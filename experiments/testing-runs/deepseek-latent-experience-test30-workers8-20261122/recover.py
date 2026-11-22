"""Record the verified candidate crash as failure; replay only the tool-gate error."""
import copy,datetime,json,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.core import sha
read=lambda p:json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
plan=read(ROOT/'plan.json');assert not plan.get('recoveries'),'No duplicate replay'
parent=Path(plan['root']);rows=read(parent/'batch/progress.json')
crash=next(r for r in rows if r['case_id']=='draft-autosave-handoff-order-example-react');t=Path(crash['root'])/'trajectory'
raw=t/'stages/final-gold/raw-result.json';gold=read(raw);assert gold['valid'] is False and gold['runtime_diagnostics']
diff=t/'attempts/1/diff.json';assert 'this.env.onSaved(saved)' in read(diff)['from_original']
assert all('Workspace.jsx:90' in x['runtime_error'] for x in gold['runtime_diagnostics'])
write(ROOT/'metric-overrides.json',{crash['case_id']:dict(passed=0,source_run=plan['id'],reason='candidate_runtime_crash_counted_as_failure_per_user_policy',raw_gold_sha256=sha(raw.read_bytes()),diff_sha256=sha(diff.read_bytes()),evidence='Candidate added this.env.onSaved(saved) after store.write, causing a second callback without navigation. Three retained schedules fail at that call with undefined navigation.close/open. Raw grader status remains unchanged.')})
row=next(r for r in rows if r['case_id']=='transfer-progress-maintenance-v2-jquery');old=Path(row['root'])/'trajectory';state=read(old/'state.json');assert state['status']=='execution_invalid' and 'mandatory tool gate' in state['error'] and not state.get('gold_result')
ident='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'-latent-experience-retry1';target=REPO/'.tempoevo/runs'/ident;target.mkdir();previous=read(parent/'lab.json');cmd=previous['prepare_command'][:]
for flag,value in [('--root',str(target/'batch')),('--start-rank',str(row['rank'])),('--limit','1')]:cmd[cmd.index(flag)+1]=value
config=copy.deepcopy(previous['config']);config.update(start=row['rank'],count=1,workers=1)
meta=dict(id=ident,title='Latent+experience · sole tool-gate recovery',status='preparing',config=config,model=previous['model'],created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),prepare_command=cmd,recovery_of=plan['id']);write(target/'lab.json',meta)
with (target/'prepare.log').open('w') as log:r=subprocess.run(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
fresh=read(target/'batch/progress.json');assert len(fresh)==1 and fresh[0]['case_id']==row['case_id'];p=Trajectory(Path(fresh[0]['root'])/'trajectory').verify();before=read(old/'protocol.json')
for key in ('task','original_inventory','public_case_record','binary','model_settings','backend','limits','total_request_cap','max_attempts','mode','condition','learning_policy','retrieval_profile','memory_snapshot','frozen_selection','frozen_experience_delivery'):
 assert p[key]==before[key],key
write(ROOT/'recovery-input-validation.json',dict(valid=True,cases=1,model_calls=0,case_id=row['case_id'],unchanged_original_scores=28,crash_counted_failed=1,same_input_source_experience_model_budget=True))
meta.update(status='prepared',prepared_cases=1);write(target/'lab.json',meta);plan['recoveries']=[dict(id=ident,root=str(target),case_id=row['case_id'],reason='Original mandatory-tool-gate infrastructure error; no valid score replayed')];write(ROOT/'plan.json',plan)
o=urllib.request.build_opener(urllib.request.ProxyHandler({}));base='http://127.0.0.1:8765';token=json.load(o.open(base+'/api/bootstrap'))['token'];request=urllib.request.Request(base+'/api/start',data=json.dumps(dict(id=ident)).encode(),headers={'Content-Type':'application/json','Origin':base,'X-TempoEvo-Token':token});print(json.load(o.open(request,timeout=120)),flush=True)

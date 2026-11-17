SOURCE='/home/sribd/Downloads/wangshu/tempoevo-gpt6-medium-low20-workers8-20261117_112828'
CASE='workspace-draft-projection-latent-vanilla-port-vue3'
from pathlib import Path
import json,shutil,hashlib,sys
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer');sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.candidate_files import capture,inventory
from temporal_contract_analyzer import experience_approval as approval
from temporal_contract_analyzer._session_runtime.read_policy import allowed
PARENT=Path(SOURCE);cid=CASE
old=PARENT/'batch'/cid/'trajectory';p=json.loads((old/'protocol.json').read_text());s=json.loads((old/'state.json').read_text());b=json.loads((old/'binding.json').read_text())
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(old/'protocol.json')==b['protocol'] and sha(old/'memory-snapshot.json')==b['bank']
assert inventory(capture(old/'original')[0])==p['original_inventory']
assert s['status']=='execution_invalid' and not s['attempts'] and s.get('gold_result') is None
assert [(z['kind'],z['status'],z['requests']) for z in s['stages']]==[('selection','complete',1),('contract','invalid',2)]
assert all(sha(path)==h for path,h in b['evaluators'].items())
assert allowed("if [ -f 'docs/host-api.md' ]; then cat 'docs/host-api.md'; fi")
shutil.copytree(PARENT/'experience-library',ROOT/'experience-library');shutil.copy2(PARENT/'memory-snapshot.json',ROOT/'memory-snapshot.json');shutil.copy2(PARENT/'model-profiles.json',ROOT/'model-profiles.json')
bank=approval.validate_snapshot(ROOT/'experience-library',json.loads((ROOT/'memory-snapshot.json').read_text()));assert len(bank['entries'])==73
cfg=json.loads((old.parent/'config.json').read_text());cfg.update(candidate=str(old/'original'),store=str(ROOT/'experience-library'),model_config=str(ROOT/'model-profiles.json'),memory_snapshot=bank)
base=ROOT/'batch'/cid;base.mkdir(parents=True);t=base/'trajectory';loop=Trajectory(t);loop.prepare(cfg)
new=loop.verify()
for key in ['task','task_id','model','mode','condition','max_attempts','limits','memory_snapshot_sha256']:assert new[key]==p[key],key
for name in ['delivery.json','online-snapshot.json','routing-analysis.json']:
 if (old/name).exists():shutil.copy2(old/name,t/name)
for stage in s['stages']:
 original=stage['key'];key='historical-contract-error' if stage['status']=='invalid' else original
 if stage['status']=='complete':assert sha(old/'stages'/original/'result.json')==stage['result_sha256']
 target=t/'stages'/key;target.mkdir(parents=True)
 for name in ['result.json','input.json','prompt-context.json']:
  if (old/'stages'/original/name).exists():shutil.copy2(old/'stages'/original/name,target/name)
 stage['key']=key
s.update(status='prepared',error=None,finalized=False,stop_reason=None)
loop.save('state.json',s);loop.verify();limit=loop._remaining_limit(new,'contract','contract');assert limit['requests']==10
loop.report();loop.save('recovery-lineage.json',dict(original_root=str(old),original_protocol_sha256=sha(old/'protocol.json'),original_state_sha256=sha(old/'state.json'),new_model_calls=0,prior_actions=0,prior_gold_calls=0,selection_reused=True,remaining_contract_requests=10,action_limit=24))
(ROOT/'batch/progress.json').write_text(json.dumps([dict(case_id=cid,rank=1,root=str(base),status='prepared')],indent=2)+'\n')
(ROOT/'plan.json').write_text(json.dumps(dict(test_cases=1,approved_entries=73,memory_snapshot_sha256=bank['sha256'],workers=1,parent_run=str(PARENT),affected_case=cid),indent=2)+'\n')
(ROOT/'preflight.json').write_text(json.dumps(dict(valid=True,model_calls=0,new_gold_calls=0,bindings=1,original_controls_unchanged=True,selection_reused=True,remaining_contract_requests=10,new_actions_allowed=1,old_result_retained=True),indent=2)+'\n')
print(json.dumps(dict(valid=True,prepared=1,model_calls=0,remaining_contract_requests=10)))

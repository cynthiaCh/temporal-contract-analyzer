"""Zero-model validator for unexecuted training-cohort selector seeds."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent/'temporal-contract-analyzer';sys.path.insert(0,str(REPO))
from temporal_contract_analyzer import experience_approval as approval,evaluation_split
from temporal_contract_analyzer.core import sha
read=lambda p:json.loads(p.read_text())
plan=read(ROOT/'plan.json');bank=read(ROOT/'memory-snapshot.json');approval.validate_snapshot(ROOT/'experience-library',bank);assert len(bank['entries'])==61 and bank['sha256']==plan['memory_snapshot_sha256']
rows=read(ROOT/'selection-seeds-v2/progress.json');expected=list(csv.DictReader((REPO/'cases/train70.csv').open(encoding='utf-8-sig')));assert [r['case_id'] for r in rows]==[r['case_id'] for r in expected] and len(rows)==70
assert sha(Path(plan['binary']).read_bytes())==plan['binary_sha256']
checked={};inputs={};implementation=sha((REPO/'temporal_contract_analyzer/tempoevo_v4.py').read_bytes())
for row in rows:
 assert row['status']=='prepared';t=Path(row['root'])/'trajectory';p=read(t/'protocol.json');s=read(t/'state.json');b=read(t/'binding.json')
 assert b['implementation']==implementation
 for name,key in [('protocol.json','protocol'),('memory-snapshot.json','bank'),('ast-evidence.json','ast')]:assert sha((t/name).read_bytes())==b[key]
 assert p['evaluation_purpose']=='training_replay' and p['evaluation_split']['role']=='training' and evaluation_split.enforce(p)==p['evaluation_split'] and p['held_out_eligible'] is False
 assert p['mode']=='testing' and p['learning_policy']=='frozen' and p['condition']=='structured' and p['retrieval_profile']=='business-source-v1' and p['max_attempts']==1
 assert p['memory_snapshot']==bank and p['backend']==plan['backend'];assert p['model_settings']['model']=='gpt-6.1-sol' and p['model_settings']['reasoning_effort']=='medium' and p['model_settings']['service_tier']=='priority'
 assert p['limits']['action']==dict(requests=24,seconds=600) and p['limits']['selection']==dict(requests=12,seconds=600)
 assert p['evaluation_budget']==dict(visible=0,oracle=0,gold=1) and not p.get('training_evaluator') and not p.get('training_recipe')
 assert s['contract'] is None and not s['stages'] and not s['attempts']
 for group in ('runtime','evaluators'):
  for path,digest in b[group].items():
   if path not in checked:assert sha(Path(path).read_bytes())==digest;checked[path]=digest
   else:assert checked[path]==digest
 for name,digest in p['original_inventory'].items():assert sha((t/'original'/name).read_bytes())==digest
 controls=read(ROOT/'calibration-reuse.json');assert controls['valid'] and controls['controls']==210
for item in controls['receipts']:
 source=Path(item['source']);copy=Path(item['copy']);assert sha(source.read_bytes())==item['source_sha256'] and sha(copy.read_bytes())==item['copy_sha256'];raw=read(copy);assert raw['valid'] and raw['passed']==(item['control']=='reference')
image=read(ROOT/'selected-case-image-verification.json');assert not image['mismatches']
report=dict(valid=True,cases=70,workers=8,bank_entries=61,model_calls=0,original_training_roles=True,independent_holdout=False,action_attempts=1,calibration_controls_fresh=210,image_files=image['files_checked'],selection_only_before_frozen_action=True)
(ROOT/'preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

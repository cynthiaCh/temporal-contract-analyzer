"""Verify frozen inputs and zero-model preflight; safe before launch only."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent/'temporal-contract-analyzer';sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
from temporal_contract_analyzer.core import sha,canonical
from temporal_contract_analyzer import business_retrieval as retrieval

def read(p):return json.loads(p.read_text())
plan=read(ROOT/'plan.json');rows=read(ROOT/'batch/progress.json');parents={p['case_id']:p for p in read(ROOT/'parent-results.json')}
expected=list(csv.DictReader((REPO/'cases/test30.csv').open(encoding='utf-8-sig')))
assert len(rows)==30 and [r['case_id'] for r in rows]==[r['case_id'] for r in expected]
assert sha(Path(plan['binary']).read_bytes())==plan['binary_sha256']=='c3dea068c8794f1764051c1fd182ff0524352bbddf2f2638e72386b9b7b74368'
assert read(ROOT/'calibration.json')['controls']==90 and read(ROOT/'calibration.json')['valid']
image=read(ROOT/'selected-case-image-verification.json');assert not image['mismatches']
checks=[]
for row in rows:
    assert row['status']=='prepared'
    cid=row['case_id'];t=Path(row['root'])/'trajectory';p=Trajectory(t).verify()
    parent=Path(parents[cid]['result_source'])/'batch'/cid/'trajectory';old=read(parent/'protocol.json');delivery=read(parent/'delivery.json')
    for key in ('task','original_inventory','model','model_settings','binary','backend','limits','max_attempts','mode','learning_policy','retrieval_profile','memory_snapshot','protected_paths','feedback_fields','public_case_record'):
        assert p[key]==old[key],(cid,key)
    assert p['condition']=='latent_experience' and p['total_request_cap']==24
    assert p['evaluation_split']['role']=='testing'
    assert p['gold_evaluator']['image']==old['gold_evaluator']['image'] and p['gold_evaluator']['command']==old['gold_evaluator']['command']
    assert not p.get('training_evaluator') and not p.get('visible_evaluator')
    assert p['frozen_experience_delivery']==delivery
    state=read(t/'state.json');assert not state['stages'] and not state['attempts'] and state['contract'] is None
    checks.append(dict(case_id=cid,protocol_sha256=sha((t/'protocol.json').read_bytes()),exact_delivery=True,nonempty=bool(delivery['experience_text'])))
report=dict(valid=True,cases=30,workers=8,bank_entries=61,memory_snapshot_sha256=plan['memory_snapshot_sha256'],calibration_controls=90,image_files=image['files_checked'],model_calls=0,nonempty_experience_cases=sum(r['nonempty'] for r in checks),checks=checks)
(ROOT/'preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'}),flush=True)

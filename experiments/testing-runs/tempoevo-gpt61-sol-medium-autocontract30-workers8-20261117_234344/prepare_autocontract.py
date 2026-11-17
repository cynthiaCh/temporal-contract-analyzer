"""Zero-model preparation; reuse exact validated controls, not solver outputs."""
import json,hashlib,subprocess,csv,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
parent=Path(json.loads((ROOT/'plan.json').read_text())['parent_with_experience_run'])
control_parent=Path(json.loads((ROOT/'plan.json').read_text())['control_parent'])
args=json.loads((ROOT/'prepare-selected.json').read_text())
def option(name):return args[args.index(name)+1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert (ROOT/'testing_30_cases.csv').read_bytes()==(parent/'testing_30_cases.csv').read_bytes()
assert (ROOT/'model-profiles.json').read_bytes()==(parent/'model-profiles.json').read_bytes()
cal=json.loads((control_parent/'calibration.json').read_text());assert cal['valid'] is True and cal['cases']==30 and cal['controls']==90
rows=list(csv.DictReader((ROOT/'testing_30_cases.csv').open(encoding='utf-8-sig')));assert len(rows)==30
assert {r['case_id'] for r in rows}=={r['case_id'] for r in cal['results']}
oldspec=json.loads((control_parent/'env-spec.json').read_text())
assert oldspec['solver_image']==option('--solver-image') and oldspec['grader_image']==option('--grader-image')
assert oldspec['files']['tools/tempoevo-docker/gold.py']==sha(REPO/'tools/tempoevo-docker/gold.py')
for record in cal['results']:
    assert len(record['controls'])==3
    for control in record['controls']:
        raw=json.loads((control_parent/'calibration'/record['case_id']/'checks'/control['control']/'result.json').read_text())
        assert raw['valid'] is True and raw['passed']==(control['control']=='reference')
bench=Path(option('--swe-tempoc-root'));roster={r['case_id']:r for r in json.loads((bench/'benchmark/swe-tempoc.json').read_text())['cases']}
files={}
for row in rows:
    for p in (bench/roster[row['case_id']]['manifest']).parent.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:files[p.relative_to(bench).as_posix()]=sha(p)
code="import sys,json,hashlib;from pathlib import Path;f=json.load(sys.stdin);bad=[k for k,v in f.items() if not (Path('/opt/swe-tempoc')/k).is_file() or hashlib.sha256((Path('/opt/swe-tempoc')/k).read_bytes()).hexdigest()!=v];print(json.dumps(dict(files_checked=len(f),mismatches=bad)))"
r=subprocess.run(['docker','run','--rm','-i','--pull=never','--network','none','--read-only','--entrypoint','python3',option('--grader-image'),'-B','-c',code],input=json.dumps(files),capture_output=True,text=True,check=True)
check=json.loads(r.stdout);assert not check['mismatches'];assert check==json.loads((control_parent/'selected-case-image-verification.json').read_text())
(ROOT/'selected-case-image-verification.json').write_text(json.dumps(check,indent=2)+'\n')
(ROOT/'calibration-reuse.json').write_text(json.dumps(dict(valid=True,parent=str(parent),source= str(control_parent/'calibration.json'),sha256=sha(control_parent/'calibration.json'),cases=30,controls_reused=90,new_gold_calls=0,model_calls=0),indent=2)+'\n')
with (ROOT/'prepare-selected.log').open('w') as log:r=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,r.returncode
progress=json.loads((ROOT/'batch/progress.json').read_text());assert len(progress)==30 and all(r['status']=='prepared' for r in progress)
sys.path.insert(0,str(REPO))
from temporal_contract_analyzer.tempoevo_v4 import Trajectory
bindings=[]
for row in progress:
    current=Path(row['root'])/'trajectory';p=Trajectory(current).verify();old=json.loads((parent/'batch'/row['case_id']/'trajectory/protocol.json').read_text())
    assert (current.parent/'case.json').read_bytes()==(parent/'batch'/row['case_id']/'case.json').read_bytes()
    assert json.loads((current/'binding.json').read_text())['runtime']==json.loads((parent/'batch'/row['case_id']/'trajectory/binding.json').read_text())['runtime']
    assert p['task']==old['task'] and p['original_inventory']==old['original_inventory'] and p['public_case_record']==old['public_case_record']
    assert p['model_settings']==old['model_settings'] and p['backend']==old['backend'] and p['limits']==old['limits']
    assert p['condition']=='contract' and p['memory_snapshot']['entries']==[] and p['total_request_cap']==36
    assert p['max_attempts']==1 and p['contract_review_policy'] is None and p['mode']=='testing'
    assert p['gold_evaluator']['image']==old['gold_evaluator']['image'] and p['gold_evaluator']['command']==old['gold_evaluator']['command']
    bindings.append(dict(case_id=row['case_id'],protocol_sha256=sha(current/'protocol.json'),binding_sha256=sha(current/'binding.json')))
(ROOT/'paired-input-validation.json').write_text(json.dumps(dict(valid=True,cases=30,bindings=bindings,parent_with_experience=str(parent),model_calls=0,source_case_image_and_action_budgets_identical=True),indent=2)+'\n')
print(json.dumps(dict(valid=True,prepared=30,controls_reused=90,new_gold_calls=0,model_calls=0)))

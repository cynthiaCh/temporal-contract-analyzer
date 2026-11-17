"""Authorized queue supervisor; archive results, never retry/learn from tests."""
import json,shutil,subprocess,sys,csv
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
ARCHIVE=REPO/'experiments/testing-runs'/ROOT.name
args=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(ROOT),'--workers','8','--adaptive-workers','--execute']
with (ROOT/'testing.log').open('a') as log:
    result=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
(ROOT/'run-exit.json').write_text(json.dumps(dict(exit_code=result.returncode,finished_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
ARCHIVE.mkdir(parents=True,exist_ok=True)
for name in ('completion.json','testing-progress.json','queue-events.jsonl','run-exit.json'):
    if (ROOT/name).exists():shutil.copyfile(ROOT/name,ARCHIVE/name)
if (ROOT/'completion.json').exists():
    completion=json.loads((ROOT/'completion.json').read_text());plan=json.loads((ROOT/'plan.json').read_text());plan['status']='finished';plan['passed']=completion['passed'];plan['failed']=completion['failed'];plan['unscored']=completion['unscored']
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');shutil.copyfile(ROOT/'plan.json',ARCHIVE/'plan.json')
    parent=Path(plan['parent_with_experience_run'])
    old=json.loads((parent/'completion.json').read_text())
    previous={r['case_id']:r for r in old['cases']}
    paired=[dict(case_id=r['case_id'],auto_contract_passed=r.get('gold_passed'),with_experience_passed=previous[r['case_id']].get('gold_passed'),auto_status=r['status'],with_experience_status=previous[r['case_id']]['status']) for r in completion['cases']]
    shared=[r for r in paired if r['auto_contract_passed'] is not None and r['with_experience_passed'] is not None]
    comparison=dict(scope='Same-case historical pipeline comparison; memory arm also had a12-request selection stage; no claim that preparation budgets are equal.',selected_cases=len(paired),shared_valid_cases=len(shared),auto_contract_passed_on_shared=sum(r['auto_contract_passed'] is True for r in shared),with_experience_passed_on_shared=sum(r['with_experience_passed'] is True for r in shared),cases=paired)
    (ROOT/'paired-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    shutil.copyfile(ROOT/'paired-comparison.json',ARCHIVE/'paired-comparison.json')
    subprocess.run(['git','add','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','--only','-m','Archive GPT5.6 medium Auto-Contract-only30 test results','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO)
sys.exit(result.returncode)

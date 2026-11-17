"""Authorized queue supervisor; archive results, never retry/learn from tests."""
import json,shutil,subprocess,sys
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
    completion=json.loads((ROOT/'completion.json').read_text());completion.update(headline_pass_rate=completion['passed']/completion['expected_cases'],failed_including_execution_errors=completion['expected_cases']-completion['passed'],execution_errors_count_as_failure=True);(ROOT/'completion.json').write_text(json.dumps(completion,indent=2)+'\n');shutil.copyfile(ROOT/'completion.json',ARCHIVE/'completion.json');plan=json.loads((ROOT/'plan.json').read_text());plan['status']='finished';plan['passed']=completion['passed'];plan['failed']=completion['failed'];plan['unscored']=completion['unscored']
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');shutil.copyfile(ROOT/'plan.json',ARCHIVE/'plan.json')
    parent=Path(plan['parent_with_experience_run']);previous=json.loads((parent/'completion.json').read_text());old={r['case_id']:r for r in previous['cases']}
    paired=[dict(case_id=r['case_id'],gpt61_passed=r.get('gold_passed') is True,gpt56_passed=old[r['case_id']].get('gold_passed') is True,gpt61_status=r['status'],gpt56_status=old[r['case_id']]['status']) for r in completion['cases']]
    comparison=dict(scope='Identical-case model transfer under same full-experience pipeline; all selected cases retained, execution errors count as failures.',cases_count=len(paired),gpt61_passed=sum(r['gpt61_passed'] for r in paired),gpt56_passed=sum(r['gpt56_passed'] for r in paired),cases=paired)
    (ROOT/'model-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n');shutil.copyfile(ROOT/'model-comparison.json',ARCHIVE/'model-comparison.json')
    subprocess.run(['git','add','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','--only','-m','Archive GPT6.1 medium same30 full-experience test results','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO)
sys.exit(result.returncode)

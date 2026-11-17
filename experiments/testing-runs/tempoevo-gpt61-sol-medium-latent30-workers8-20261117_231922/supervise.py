"""Authorized fresh Latent queue; valid-score denominator, no test learning/replays."""
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
if (ROOT/'completion.json').exists():
    c=json.loads((ROOT/'completion.json').read_text());valid=c['passed']+c['failed']
    c.update(headline_pass_rate=c['passed']/valid if valid else None,headline_denominator=valid,execution_errors_count_as_failure=False)
    (ROOT/'completion.json').write_text(json.dumps(c,indent=2)+'\n')
    plan=json.loads((ROOT/'plan.json').read_text());plan.update(status='finished',passed=c['passed'],failed=c['failed'],unscored=c['unscored'])
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    previous=json.loads((Path(plan['parent_with_experience_run'])/'completion.json').read_text());old={r['case_id']:r for r in previous['cases']}
    pairs=[dict(case_id=r['case_id'],latent_passed=r.get('gold_passed'),latent_status=r['status'],with_experience_passed=old[r['case_id']].get('gold_passed'),with_experience_status=old[r['case_id']]['status']) for r in c['cases']]
    shared=[r for r in pairs if type(r['latent_passed']) is bool and type(r['with_experience_passed']) is bool]
    comparison=dict(scope='Fresh GPT6.1 medium Latent vs same-model full-experience single-Action on identical30 originals; execution errors excluded, one final Gold per completed Action.',latent_passed=c['passed'],latent_valid=valid,latent_unscored=c['unscored'],with_experience_passed=previous['passed'],with_experience_valid=previous['passed']+previous['failed'],shared_valid_count=len(shared),shared_latent_passed=sum(r['latent_passed'] for r in shared),shared_with_experience_passed=sum(r['with_experience_passed'] for r in shared),cases=pairs)
    (ROOT/'latent-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
for name in ('completion.json','testing-progress.json','queue-events.jsonl','run-exit.json','plan.json','latent-comparison.json'):
    if (ROOT/name).exists():shutil.copyfile(ROOT/name,ARCHIVE/name)
subprocess.run(['git','add','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO,check=True)
subprocess.run(['git','commit','--only','-m','Archive fresh GPT6.1 medium Latent30 test results','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO)
sys.exit(result.returncode)

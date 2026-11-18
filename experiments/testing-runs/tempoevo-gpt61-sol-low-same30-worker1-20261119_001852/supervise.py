"""Serial low-effort fixed30 test; retain raw scores and frozen memory."""
import json,subprocess,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
TARGET=REPO/'experiments/testing-runs'/ROOT.name
cmd=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(ROOT),'--workers','1','--execute']
with (ROOT/'testing.log').open('a') as log:rc=subprocess.run(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
(ROOT/'run-exit.json').write_text(json.dumps(dict(exit_code=rc,finished_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
TARGET.mkdir(parents=True,exist_ok=True)
if (ROOT/'completion.json').exists():
    c=json.loads((ROOT/'completion.json').read_text());valid=c['passed']+c['failed'];c.update(headline_pass_rate=c['passed']/valid if valid else None,headline_denominator=valid,execution_errors_count_as_failure=False)
    (ROOT/'completion.json').write_text(json.dumps(c,indent=2)+'\n')
    plan=json.loads((ROOT/'plan.json').read_text());plan.update(status='finished',passed=c['passed'],failed=c['failed'],unscored=c['unscored']);(ROOT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    previous=json.loads((Path(plan['parent_with_experience_run'])/'completion.json').read_text());old={r['case_id']:r for r in previous['cases']};assert len(old)==30 and set(old)=={r['case_id'] for r in c['cases']}
    pairs=[dict(case_id=r['case_id'],low_passed=r.get('gold_passed'),low_status=r['status'],medium_passed=old[r['case_id']].get('gold_passed'),medium_status=old[r['case_id']]['status']) for r in c['cases']]
    common=[r for r in pairs if type(r['low_passed']) is bool and type(r['medium_passed']) is bool]
    comparison=dict(scope='Same fixed30/full61bank/model/CLI/images/Action budgets; low new serial run vs historical medium8worker run; current read-only policy fix and explicit split reservation are recorded infrastructure differences.',low_passed=c['passed'],low_valid=valid,low_unscored=c['unscored'],medium_passed=previous['passed'],medium_valid=previous['passed']+previous['failed'],shared_valid=len(common),shared_low_passed=sum(r['low_passed'] for r in common),shared_medium_passed=sum(r['medium_passed'] for r in common),cases=pairs)
    (ROOT/'effort-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    rate=f"{100*c['passed']/valid:.1f}% ({c['passed']}/{valid})" if valid else 'No valid scores'
    text=f"# GPT-6.1-sol low: fixed30 testing\n\n| Model / effort | Passed | Failed | Unscored | Valid pass rate |\n|---|---:|---:|---:|---|\n| GPT-6.1-sol low | {c['passed']} | {c['failed']} | {c['unscored']} | {rate} |\n| GPT-6.1-sol medium (historical) | {previous['passed']} | {previous['failed']} | {previous['unscored']} | {100*previous['passed']/(previous['passed']+previous['failed']):.1f}% ({previous['passed']}/{previous['passed']+previous['failed']}) |\n\nFull61 frozen approved entries, no learning, one Action24requests/600sec, independent final Gold. Low run1worker; previousmedium8workers. Same Codex0.167 binary c3dea068 pinned. Current readonly-command fix/default registry differ from historicalmedium; this is not claimed to isolate reasoning effort as the sole environment difference. Execution-invalid runs excluded from valid denominator.\n"
    (ROOT/'RESULT.md').write_text(text)
for n in ['plan.json','completion.json','testing-progress.json','queue-events.jsonl','run-exit.json','effort-comparison.json','RESULT.md']:
    if (ROOT/n).exists():shutil.copyfile(ROOT/n,TARGET/n)
subprocess.run(['git','add','--',str(TARGET.relative_to(REPO))],cwd=REPO,check=True)
subprocess.run(['git','commit','--quiet','--only','-m','Archive GPT6.1 low fixed30 serial test results','--',str(TARGET.relative_to(REPO))],cwd=REPO)
sys.exit(rc)

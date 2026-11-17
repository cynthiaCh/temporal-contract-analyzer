"""Run only the previously pre-Action invalid case, then append a separate20-case summary."""
from pathlib import Path
import json,subprocess,sys,shutil,datetime
ROOT=Path(__file__).resolve().parent;REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
assert json.loads((ROOT/'agent-follows-doc.json').read_text())['valid']
plan=json.loads((ROOT/'plan.json').read_text());parent=Path(plan['parent_run']);cid=plan['affected_case']
cmd=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(ROOT),'--workers','1','--execute']
with (ROOT/'testing.log').open('a') as f:code=subprocess.run(cmd,cwd=REPO,stdout=f,stderr=subprocess.STDOUT).returncode
child=json.loads((ROOT/'completion.json').read_text());original=json.loads((parent/'completion.json').read_text());replacement=child['cases'][0]
assert replacement['case_id']==cid
cases=[dict(replacement,recovery_root=str(ROOT)) if r['case_id']==cid else r for r in original['cases']];assert len(cases)==len({r['case_id'] for r in cases})==20
old=next(r for r in original['cases'] if r['case_id']==cid)
summary=dict(expected_cases=20,recorded_cases=20,passed=sum(r['gold_passed'] is True for r in cases),failed=sum(r['gold_passed'] is False for r in cases),execution_invalid=sum(r['status']=='execution_invalid' for r in cases),unscored=sum(r['gold_passed'] is None for r in cases),cases=cases,model='gpt-6-sol',reasoning_effort='medium',frozen_approved_entries=73,original_run=str(parent),original_counts=dict(passed=original['passed'],failed=original['failed'],execution_invalid=original['execution_invalid']),single_case_recovery=str(ROOT),original_results_unchanged=True,read_guard_version_changed_for_one_pre_action_case=True,original_peak_workers=8,recovery_workers=1,known_model_requests=original['model_requests']+replacement['requests']-old['requests'],usage_incomplete=original['usage_incomplete'] or child['usage_incomplete'],finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),recovery_exit_code=code)
for p in [ROOT/'postfix-completion.json',parent/'postfix-completion.json']:p.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
target=REPO/'experiments/testing-runs'/parent.name;shutil.copy2(ROOT/'postfix-completion.json',target/'postfix-completion.json')
subprocess.run(['git','add',str(target/'postfix-completion.json'),str(REPO/'experiments/testing-runs'/ROOT.name)],cwd=REPO,check=True)
subprocess.run(['git','commit','--only',str(target/'postfix-completion.json'),str(REPO/'experiments/testing-runs'/ROOT.name),'-m','Record one-case read-guard recovery and append separate20-case aggregate'],cwd=REPO,check=True)
print(json.dumps({k:v for k,v in summary.items() if k!='cases'}),flush=True)

"""Authorized20-entry test queue, usage accounting and three-point curve export."""
import json,subprocess,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
ARCHIVE=REPO/'experiments/testing-runs'/ROOT.name
args=[sys.executable,'-B',str(REPO/'tools/tempoevo-docker/run_testing.py'),'--root',str(ROOT),'--workers','8','--adaptive-workers','--execute']
with (ROOT/'testing.log').open('a') as log:rc=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
(ROOT/'run-exit.json').write_text(json.dumps(dict(exit_code=rc,finished_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
ARCHIVE.mkdir(parents=True,exist_ok=True)
if (ROOT/'completion.json').exists():
    c=json.loads((ROOT/'completion.json').read_text());valid=c['passed']+c['failed'];c.update(headline_pass_rate=c['passed']/valid if valid else None,headline_denominator=valid,execution_errors_count_as_failure=False)
    (ROOT/'completion.json').write_text(json.dumps(c,indent=2)+'\n')
    allowed={e['bundle']['sha256'] for e in json.loads((ROOT/'memory-snapshot.json').read_text())['entries']};usage=[]
    for row in json.loads((ROOT/'batch/progress.json').read_text()):
        t=Path(row['root'])/'trajectory';p=t/'delivery.json';d=json.loads(p.read_text()) if p.exists() else {};codes=d.get('selected_sha256s',[]);assert set(codes)<=allowed
        for f in (t/'retrieval').glob('*-recall.json'):
            recalled=json.loads(f.read_text());assert recalled['bank_count']==20 and {x['sha256'] for x in recalled['candidates']}<=allowed
        action_path=t/'stages/action-1/input.json'
        action=json.loads(action_path.read_text()) if action_path.exists() else {}
        usage.append(dict(case_id=row['case_id'],bank_entries=20,selected_count=len(codes),selected_sha256s=codes,reason=d.get('reason'),delivery_available=p.exists(),action_input_available=action_path.exists(),action_received_experience=bool(action.get('experience')) if action_path.exists() else None))
    (ROOT/'experience-usage.json').write_text(json.dumps(dict(cases=usage,bank_entries=20,cases_with_selected_experience=sum(x['selected_count']>0 for x in usage),cases_with_delivery_record=sum(x['delivery_available'] for x in usage),cases_with_action_input=sum(x['action_input_available'] for x in usage),cases_action_received_experience=sum(x['action_received_experience'] is True for x in usage),hidden_entry_exposure=0),indent=2)+'\n')
    with (ROOT/'curve-build.log').open('w') as log:curve_rc=subprocess.run([sys.executable,'-B',str(ROOT/'summarize_curve.py')],cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
    (ROOT/'curve-exit.json').write_text(json.dumps(dict(exit_code=curve_rc),indent=2)+'\n')
for n in ['completion.json','testing-progress.json','queue-events.jsonl','run-exit.json','experience-usage.json','curve.json','curve.csv','CURVE_REPORT.md','library-size-curve.png','library-size-curve.svg','library-size-curve.pdf','curve-exit.json','curve-build.log']:
    if (ROOT/n).exists():shutil.copyfile(ROOT/n,ARCHIVE/n)
subprocess.run(['git','add','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO,check=True)
subprocess.run(['git','commit','--quiet','--only','-m','Archive20-entry fixed30 ablation and0/20/61 comparison curve','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO,check=True)
sys.exit(rc)

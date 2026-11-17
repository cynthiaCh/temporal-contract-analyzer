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
    completion=json.loads((ROOT/'completion.json').read_text());plan=json.loads((ROOT/'plan.json').read_text());plan['status']='finished';plan['passed']=completion['passed'];plan['failed']=completion['failed'];plan['unscored']=completion['unscored']
    (ROOT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');shutil.copyfile(ROOT/'plan.json',ARCHIVE/'plan.json')
    subprocess.run(['git','add','--',str(ARCHIVE.relative_to(REPO))],cwd=REPO,check=True)
    subprocess.run(['git','commit','-m','Archive GPT6 medium same-cluster hard10 test results'],cwd=REPO)
sys.exit(result.returncode)

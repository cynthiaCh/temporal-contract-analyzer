from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parent
REPO=Path('/home/sribd/Downloads/wangshu/temporal-contract-analyzer')
cmd=[sys.executable,'-B',str(ROOT/'retry5.py'),'--execute']
with (ROOT/'retry.log').open('a') as log:rc=subprocess.run(cmd,cwd=REPO,stdout=log,stderr=subprocess.STDOUT).returncode
(ROOT/'run-exit.json').write_text(json.dumps(dict(exit_code=rc,finished_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
target=REPO/'experiments/training-replays'/ROOT.name
shutil.copyfile(ROOT/'run-exit.json',target/'run-exit.json')
subprocess.run(['git','add','--',str(target.relative_to(REPO))],cwd=REPO,check=True)
subprocess.run(['git','commit','--quiet','--only','-m','Record5 execution-error rerun process exit','--',str(target.relative_to(REPO))],cwd=REPO)
sys.exit(rc)

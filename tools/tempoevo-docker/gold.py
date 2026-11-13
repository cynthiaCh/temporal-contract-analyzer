"""Unchanged benchmark probe; host adapter controls train/test feedback projection."""
import json,subprocess,sys
from pathlib import Path
c=json.loads(Path('/checks/case.json').read_text());case=Path('/opt/swe-tempoc')/Path(c['manifest']).parent
p=subprocess.run(['/opt/swe-tempoc/.swe-tempoc/toolchains/node-v16.20.2/bin/node',str(case/'oracle/probe.cjs'),sys.argv[-1],'ungranted'],capture_output=True,text=True,timeout=150)
sys.stderr.write(p.stderr);score=json.loads(p.stdout)
invalid=p.returncode not in (0,1) or ((p.returncode==0)!=(score.get('verdict')=='PASS')) or bool(score.get('runtime_errors')) or any(isinstance(x,dict) and x.get('runtimeError') for x in score.get('schedules',{}).values())
print(json.dumps(dict(valid=not invalid,passed=score['verdict']=='PASS',verdict=score['verdict'],full_score=score,error='Grader runtime error; retained trusted logs' if invalid else None)))

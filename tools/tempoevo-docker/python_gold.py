"""Invoke and classify unchanged Python-pilot benchmark probes on the trusted side."""
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,'/opt/swe-tempoc')
from swe_tempoc import classify
cfg=json.loads(Path('/checks/case.json').read_text());manifest=Path('/opt/swe-tempoc')/cfg['manifest'];m=json.loads(manifest.read_text())
case=manifest.parent
p=subprocess.run([sys.executable,'-B',str(case/m['oracle']['probe']),sys.argv[-1]],capture_output=True,text=True,timeout=150)
sys.stderr.write(p.stderr)
expected=[s['id'] for s in json.loads((case/m['oracle']['schedules']).read_text())['schedules']]
summary,report=classify(p.stdout,p.returncode,m['id'],expected)
valid=summary.get('valid_scored') is True
print(json.dumps(dict(valid=valid,passed=valid and report['verdict']=='PASS',verdict=report['verdict'] if valid else None,full_score=report,error=summary.get('error'))))

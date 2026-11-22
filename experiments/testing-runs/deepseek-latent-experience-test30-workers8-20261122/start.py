"""Start only the fully validated fresh run through the local controller."""
import json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
plan=json.loads((ROOT/'plan.json').read_text());run=Path(plan['root']);meta=json.loads((run/'lab.json').read_text())
assert meta['status']=='prepared' and meta['config']['workers']==8
check=json.loads((ROOT/'paired-input-validation.json').read_text());assert check['valid'] is True and check['cases']==30 and check['model_calls']==0
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));base='http://127.0.0.1:8765'
assert not any(r['status'] in ('preparing','running','stopping') for r in json.load(opener.open(base+'/api/runs')))
token=json.load(opener.open(base+'/api/bootstrap'))['token']
req=urllib.request.Request(base+'/api/start',data=json.dumps(dict(id=plan['id'])).encode(),headers={'Content-Type':'application/json','Origin':base,'X-TempoEvo-Token':token})
print(json.load(opener.open(req,timeout=120)),flush=True)

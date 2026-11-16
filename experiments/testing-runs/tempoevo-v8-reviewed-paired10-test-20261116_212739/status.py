"""Read-only paired test status; no model calls."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
result=dict(root=str(ROOT),arms=[])
for arm in ['A-seed16','B-seed16-plus2']:
 path=ROOT/arm/'progress.json';rows=[]
 for item in json.loads(path.read_text()) if path.exists() else []:
  t=Path(item['root'])/'trajectory';s=json.loads((t/'state.json').read_text());g=s.get('gold_result') or {};rows.append(dict(rank=item['rank'],case_id=item['case_id'],status=s['status'],actions=len(s['attempts']),gold_passed=g.get('passed') if s['status']=='scored' else None,error=s.get('error'),active=[x['key'] for x in s['stages'] if x['status']=='started']))
 result['arms'].append(dict(arm=arm,passed=sum(x['gold_passed'] is True for x in rows),scored=sum(x['status']=='scored' for x in rows),execution_invalid=sum(x['status']=='execution_invalid' for x in rows),cases=rows))
print(json.dumps(result,ensure_ascii=False,indent=2))

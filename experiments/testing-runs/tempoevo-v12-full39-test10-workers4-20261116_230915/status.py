"""Read-only status of the full-approved-memory single testing group."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
rows=[]
p=ROOT/'batch/progress.json'
for item in json.loads(p.read_text()) if p.exists() else []:
 t=Path(item['root'])/'trajectory';s=json.loads((t/'state.json').read_text());g=s.get('gold_result') or {}
 rows.append(dict(rank=item['rank'],case_id=item['case_id'],status=s['status'],actions=len(s['attempts']),gold_passed=g.get('passed') if s['status']=='scored' else None,error=s.get('error'),preparation_warnings=len(s.get('preparation_warnings',[])),active=[x['key'] for x in s['stages'] if x['status']=='started']))
print(json.dumps(dict(root=str(ROOT),condition='single_group_full_approved_memory',approved_entries=39,workers=4,passed=sum(x['gold_passed'] is True for x in rows),scored=sum(x['status']=='scored' for x in rows),execution_invalid=sum(x['status']=='execution_invalid' for x in rows),cases=rows),ensure_ascii=False,indent=2))

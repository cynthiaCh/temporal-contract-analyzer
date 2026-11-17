from pathlib import Path
import json,collections
r=Path(__file__).resolve().parent;p=json.loads((r/'plan.json').read_text());rows=[]
for item in json.loads((r/'batch/progress.json').read_text()) if (r/'batch/progress.json').exists() else []:
 s=json.loads((Path(item['root'])/'trajectory/state.json').read_text());rows.append(dict(case_id=item['case_id'],status=s['status'],passed=(s.get('gold_result') or {}).get('passed'),active=[z['key'] for z in s['stages'] if z['status']=='started'],error=s.get('error')))
print(json.dumps(dict(root=str(r),model=p['model'],effort=p['reasoning_effort'],initial_workers=p['workers'],passed=sum(z['passed'] is True for z in rows),scored=sum(z['status']=='scored' for z in rows),invalid=sum(z['status']=='execution_invalid' for z in rows),cases=rows),ensure_ascii=False,indent=2))

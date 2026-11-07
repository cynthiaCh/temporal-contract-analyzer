from pathlib import Path
import json
O=Path(__file__).resolve().parent;rows=json.loads((O/'requests.json').read_text());out=[]
for r in rows:
 if r['status']=='launched':continue
 p=O/'runs'/r['call_id'];code=(p/'workspace/src/controller.js').read_text();raw=json.loads((p/'raw-answer.txt').read_text())
 out.append({'slot':r['call_id'],'condition':r['condition'],'repeat':r['repeat'],'controller_source':code,'delivered_report':raw['report'],'no_visit_returns_promise': 'async submit' in code or 'if(!visit)returnPromise.resolve(null)' in code.replace(' ',''), 'submit_is_async_function': 'async submit' in code,'patch':str(p/'patch.diff'),'evidence_policy':'Observe actual source and delivered self-check claims; only original oracle assertions determine scored outcome. No-visit, synchronous service timing, propagation and host exceptions are descriptive unknowns.'})
(O/'patch-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print([(r['slot'],r['no_visit_returns_promise']) for r in out])

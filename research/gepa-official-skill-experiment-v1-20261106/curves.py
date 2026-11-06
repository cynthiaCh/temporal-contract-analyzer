import csv,json
from runtime import *
def main():
 xs=read(OUT/'candidate-lineage.json');curve=[]
 for x in xs:
  q=x['paired_sample_tradeoffs'];curve.append(dict(iteration=x['iteration'],parent_train_mean=sum(i['parent_whole'] for i in q)/len(q) if q else None,child_train_mean=sum(i['child_whole'] for i in q)/len(q) if q else None,accepted=x.get('official_decision')=='on_candidate_accepted',lost_previously_passed_checks=sum(len(i['previously_passed_check_losses']) for i in q)))
 with (OUT/'train-curve.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(curve[0]));w.writeheader();w.writerows(curve)
 vals=[]
 for line in (OUT/'official-events.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e['event']=='on_valset_evaluated':vals.append(e['data'])
 save(OUT/'val-curve.json',vals)
 paths=[]
 for key,color in [('parent_train_mean','#2563eb'),('child_train_mean','#dc2626')]:
  pts=' '.join(f'{80+i*95},{230-160*x[key]}' for i,x in enumerate(curve) if x[key] is not None);paths.append(f'<polyline points="{pts}" stroke="{color}" stroke-width="3" fill="none"/>')
 text='<svg xmlns="http://www.w3.org/2000/svg" width="650" height="330" viewBox="0 0 650 330"><rect width="650" height="330" fill="white"/><g font-family="sans-serif" font-size="14"><text x="40" y="28">Train whole-task pass mean (two cases per paired batch)</text><path d="M60 55V240H565" fill="none" stroke="black"/><text x="25" y="75">1.0</text><text x="25" y="155">0.5</text><text x="25" y="235">0.0</text>'+''.join(paths)+''.join(f'<text x="{76+i*95}" y="260">{x["iteration"]}</text>' for i,x in enumerate(curve))+'<text x="70" y="295" fill="#2563eb">parent K0</text><text x="200" y="295" fill="#dc2626">proposed child</text><text x="410" y="295">GEPA iteration</text></g></svg>'
 (OUT/'train-curve.svg').write_text(text)
 # Never interpolate unmeasured candidate validation scores.
 (OUT/'val-curve.md').write_text('# Actual full-validation measurements\n\nOnly events in val-curve.json are measurements; rejected proposals have no validation value.\n\n'+ '\n'.join(json.dumps(v,ensure_ascii=False) for v in vals))
if __name__=='__main__':main()

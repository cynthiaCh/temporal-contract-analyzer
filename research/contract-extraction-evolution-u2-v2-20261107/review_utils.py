"""Research-side evidence ledger; not an LLM judge or maintenance scorer."""
import csv,json
from pathlib import Path
from run import OUT,ROOT,read,save,sha
RULES=list(csv.DictReader((OUT/'evaluation-v1.csv').open(encoding='utf-8-sig')))
def citation(call,q):
 p=OUT/'runs'/call/'contract.md';lines=p.read_text().splitlines();matches=[i for i,x in enumerate(lines,1) if q in x];assert matches,(call,q)
 return str(p.relative_to(ROOT))+':'+str(matches[0])
def make(call,oid,coverage,quote,reason,unknown='合理保留未知',direction='正确（已表达部分）',source='准确（所引部分；缺失另计覆盖）',addition='无'):
 assert read(OUT/'runs'/call/'validity.json')['status']=='PASS'
 rule=next(x for x in RULES if x['item_id']==oid)
 return {'call_id':call,'phase':'K0' if call.startswith('k0') else 'K1','item_id':oid,'coverage':coverage,'semantic_direction':direction,'source_accuracy':source,'unsupported_additions':addition,'unknown_handling':unknown,'model_quote':quote,'model_reference':citation(call,quote),'standard_and_source':rule['source'],'judgment_rule':rule['judgment_rule'],'reason':reason,'review_mode':'AI executing-agent evaluation; not independent human review','quality_total':None}
def timer(call,tid,coverage,quote,reason):
 return {'call_id':call,'item_id':'O4','subitem':tid,'coverage':coverage,'model_quote':quote,'model_reference':citation(call,quote),'reason':reason,'normative_must_cancel_required':False,'review_mode':'AI executing-agent evaluation; not independent human review'}
def write_csv(name,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def append_reviews(rows,timers):
 path=OUT/'review-data.json';previous=read(path) if path.exists() else {'items':[],'timer':[]}
 ids={(x['call_id'],x['item_id']) for x in previous['items']};assert not any((x['call_id'],x['item_id']) in ids for x in rows)
 previous['items']+=rows;previous['timer']+=timers;save(path,previous)
 write_csv('item-review.csv',previous['items']);write_csv('timer-boundary-review.csv',previous['timer'])
 if all(x['phase']=='K0' for x in previous['items']):write_csv('baseline-review.csv',previous['items'])

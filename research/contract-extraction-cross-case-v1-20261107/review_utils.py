"""Post-batch descriptive source-fidelity audit; pending norms never graded."""
import csv,json
from pathlib import Path
from run import OUT,ROOT,read,save

def evidence(call,quote):
 p=OUT/'runs'/call/'contract.md';hits=[n for n,line in enumerate(p.read_text().splitlines(),1) if quote in line];assert hits,(call,quote)
 return str(p.relative_to(ROOT))+':'+str(hits[0])
def item(call,i,coverage,quote,reason,source_accuracy='准确（所引部分）',direction='正确（所述部分）',added='未发现',unknown='合理保留未知'):
 assert read(OUT/'execution-complete.json')['status']=='COMPLETE'
 rules=list(csv.DictReader((OUT/'evaluation.csv').open(encoding='utf-8-sig')));rule=next(x for x in rules if x['item_id']==i);slot=next(x for x in read(OUT/'schedule.json')['order'] if x['call_id']==call)
 return {'call_id':call,'case':slot['case'],'condition':slot['phase'],'repeat':slot['repeat'],'pair_id':slot['pair_id'],'item_id':i,'kind':rule['kind'],'descriptive_source_coverage':coverage,'event_direction':direction,'source_accuracy':source_accuracy,'unsupported_additions':added,'unknown_handling':unknown,'model_quote':quote,'model_reference':evidence(call,quote),'standard_items':rule['standard_items'],'source_reference':str(OUT/'materials'/slot['case']/'candidate')+'/'+rule['candidate_source'] if not rule['candidate_source'].startswith('task.md') else str(OUT/'materials'/slot['case'])+'/'+rule['candidate_source'],'pending_normative_assessment':'NOT_SCORED_PENDING_CONFIRMATION','confirmed_contract_increment':'NOT_ASSESSABLE','reason':reason,'reviewer':'AI executing agent knows condition; not independent blind review'}
def write(name,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

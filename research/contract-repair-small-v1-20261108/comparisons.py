"""Paired original-effect and cost comparisons, without composite check scores."""
import csv,json
from pathlib import Path
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
 actual=read(O/'actual-schedule.json');metrics=read(O/'metric-spec.json');rows=[]
 for case in read(O/'cohort.json')['cases']:
  cid=case['case'];m=metrics[cid]
  for repeat in [1,2]:
   records={r['condition']:r for r in actual if r['phase']=='repair' and r['case']==cid and r['repeat']==repeat}
   for before,after in [('N','H'),('H','M'),('M','E')]:
    a=records.get(before);b=records.get(after)
    row={'case':cid,'repeat':repeat,'before':before,'after':after,'valid_pair':False,'before_overall_pass':None,'after_overall_pass':None,'required_gains':None,'required_losses':None,'new_forbidden':None,'removed_forbidden':None,'extra_requests':None,'extra_input_tokens':None,'extra_output_tokens':None,'extra_seconds':None}
    if a and b and all(r['status']=='VALID' and r.get('scoring_valid') for r in [a,b]):
     sa=read(O/'runs'/a['slot']/'score.stdout.json');sb=read(O/'runs'/b['slot']/'score.stdout.json');ea=sa['observed_effects'];eb=sb['observed_effects']
     row.update(valid_pair=True,before_overall_pass=sa['verdict']=='PASS',after_overall_pass=sb['verdict']=='PASS',required_gains=[k for k in m['required'] if ea.get(k) is False and eb.get(k) is True],required_losses=[k for k in m['required'] if ea.get(k) is True and eb.get(k) is False],new_forbidden=[k for k in m['forbidden'] if ea.get(k) is False and eb.get(k) is True],removed_forbidden=[k for k in m['forbidden'] if ea.get(k) is True and eb.get(k) is False],extra_requests=b['native']['started']-a['native']['started'],extra_input_tokens=b['usage']['input_tokens']-a['usage']['input_tokens'],extra_output_tokens=b['usage']['output_tokens']-a['usage']['output_tokens'],extra_seconds=b['seconds']-a['seconds'])
    rows.append(row)
 (O/'paired-comparisons.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 with (O/'paired-comparisons.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in r.items()} for r in rows)
 char=[]
 for case in read(O/'cohort.json')['cases']:
  p=O/'prompts'/case['case'];m=p/'M.md';e=p/'E.md'
  if m.exists() and e.exists():char.append({'case':case['case'],'M_characters':len(m.read_text()),'E_characters':len(e.read_text()),'E_increment_characters':len(e.read_text())-len(m.read_text()),'same_frozen_automatic_contract':True})
 (O/'enhancement-input-cost.json').write_text(json.dumps({'prompt_characters':char,'standalone_experience_generation_calls_this_batch':0,'cost_accounting':'Actual shared extraction counted once in total, not repeated per repair/condition. Character increment is not a token or monetary estimate.'},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

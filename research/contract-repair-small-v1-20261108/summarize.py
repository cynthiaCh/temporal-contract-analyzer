"""Collect all 18 predeclared slots; never dispatches or retries a model."""
import csv,hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parent.parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 slots=read(O/'schedule.json')['slots'];assert len(slots)==18
 actual=read(O/'actual-schedule.json') if (O/'actual-schedule.json').exists() else [];index={r['slot']:r for r in actual}
 cases=read(O/'cohort.json')['cases'];metrics=read(O/'metric-spec.json')
 reviews=read(O/'patch-review.json') if (O/'patch-review.json').exists() else {}
 rows=[];extractions=[];cost_rows=[]
 for slot in slots:
  rec=index.get(slot['slot']);status=rec['status'] if rec else 'NOT_STARTED';d=O/'runs'/slot['slot']
  row={'slot':slot['slot'],'case':slot['case'],'phase':slot['phase'],'condition':slot['condition'],'repeat':slot['repeat'],'status':status,'failure_class':rec.get('failure_class') if rec else None,'infrastructure_valid':rec.get('infrastructure_valid') if rec else None,'overall_pass':None,'target_pass':None,'raw_verdict':rec.get('raw_verdict') if rec else None,'lost_required':None,'new_forbidden':None,'paired_no_contract_lost_required':None,'patch_delivered':rec.get('patch_delivered') if rec else None,'source_body_read':bool(rec.get('source_body_proofs')) if rec else None,'extra_unsupported_conventions':reviews.get(slot['slot'],{}).get('unsupported_conventions'),'scope_review_status':reviews.get(slot['slot'],{}).get('status','PENDING' if rec and slot['phase']=='repair' else 'NOT_APPLICABLE'),'seconds':rec.get('seconds') if rec else None,'requests':rec.get('native',{}).get('started') if rec else None,'tools':rec.get('tools') if rec else None,'hook_tool_attempts':rec.get('native',{}).get('tool_attempts') if rec else None,'input_tokens':None,'cached_input_tokens':None,'cache_write_input_tokens':None,'output_tokens':None,'reasoning_output_tokens':None,'usage_incomplete':rec.get('usage_incomplete') if rec else None,'not_started_reason':None if rec else ('stopped_before_slot' if (O/'stop.json').exists() else 'not_yet_started')}
  if rec:
   row.update(rec.get('usage',{}));cost_rows.append(rec)
  row['business_files_changed']=reviews.get(slot['slot'],{}).get('business_files_changed')
  row['auxiliary_artifacts']=reviews.get(slot['slot'],{}).get('auxiliary_artifacts')
  if rec and slot['phase']=='repair' and rec.get('status')=='VALID' and rec.get('scoring_valid'):
   score=read(d/'score.stdout.json');effects=score['observed_effects'];m=metrics[slot['case']]
   row['overall_pass']=score['verdict']=='PASS';row['target_pass']=all(effects.get(k) is True for k in m['target_effects'])
   row['lost_required']=[k for k in m['required'] if m['baseline_effects'].get(k) is True and effects.get(k) is not True]
   row['new_forbidden']=[k for k in m['forbidden'] if m['baseline_effects'].get(k) is False and effects.get(k) is True]
   nslot=next(s for s in slots if s['phase']=='repair' and s['case']==slot['case'] and s['repeat']==slot['repeat'] and s['condition']=='N');nrec=index.get(nslot['slot'])
   if nrec and nrec.get('status')=='VALID' and nrec.get('scoring_valid'):
    ne=read(O/'runs'/nslot['slot']/'score.stdout.json')['observed_effects'];row['paired_no_contract_lost_required']=[k for k in m['required'] if ne.get(k) is True and effects.get(k) is not True]
  (extractions if slot['phase']=='extract' else rows).append(row)
 def csvout(name,data):
  with (O/name).open('w',newline='') as f:
   writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in data)
 csvout('case-results.csv',rows);csvout('extraction-results.csv',extractions)
 labels={'N':'无契约','H':'人工整理契约','M':'自动契约','E':'E1-v1经验增强'}
 groups={}
 for c in cases:
  groups[c['case']]={}
  for g in labels:
   subset=[r for r in rows if r['case']==c['case'] and r['condition']==g];valid=[r for r in subset if r['status']=='VALID' and r['overall_pass'] is not None]
   groups[c['case']][g]={'name':labels[g],'planned':2,'launched':sum(r['status']!='NOT_STARTED' for r in subset),'valid':len(valid),'invalid':sum(r['status'] not in ['NOT_STARTED','VALID','LAUNCHING'] for r in subset),'not_started':sum(r['status']=='NOT_STARTED' for r in subset),'overall_passes':sum(bool(r['overall_pass']) for r in valid),'target_passes':sum(bool(r['target_pass']) for r in valid),'overall_denominator':len(valid),'overall_rate':sum(bool(r['overall_pass']) for r in valid)/len(valid) if valid else None,'baseline_loss_slots':[r['slot'] for r in valid if r['lost_required'] or r['new_forbidden']],'paired_N_loss_slots':[r['slot'] for r in valid if r['paired_no_contract_lost_required']],'pending_patch_reviews':[r['slot'] for r in valid if r['scope_review_status']=='PENDING']}
 tokenkeys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
 costs={}
 for name,predicate in [('extraction',lambda r:r['phase']=='extract'),('maintenance',lambda r:r['phase']=='repair'),('enhanced_subset',lambda r:r.get('condition')=='E'),('total',lambda r:True)]:
  records=[r for r in cost_rows if predicate(r)];costs[name]={'sessions':len(records),'requests':sum(r.get('native',{}).get('started',0) for r in records),'tools':sum(r.get('tools',0) for r in records),'hook_tool_attempts':sum(r.get('native',{}).get('tool_attempts',0) for r in records),'seconds':sum(r.get('seconds',0) for r in records),**{k:sum(r.get('usage',{}).get(k,0) or 0 for r in records) for k in tokenkeys},'usage_lower_bound':any(r.get('usage_incomplete',True) for r in records)}
 costs['notes']=['Cache tokens are included in input; reasoning tokens in output. Enhanced is a maintenance subset, never add twice.','Native CLI experiment accounting only; main-chat preparation/analysis tokens and human time unavailable. No verified monetary fees.','Old batch costs below are separate, never included in new total. All offline synthetic requests are excluded.']
 costs['old_batch_separate']=read(O/'supersession.json')['previous_costs_separate'];costs['currency_cost']=None;save('costs.json',costs)
 summary={'status':'COMPLETE' if (O/'completion.json').exists() else 'STOPPED' if (O/'stop.json').exists() else 'RUNNING','planned':{'cases':2,'extraction':2,'maintenance':16,'top_level':18,'request_reservation':408},'actual':{'extraction_started':sum(r['status']!='NOT_STARTED' for r in extractions),'extraction_valid':sum(r['status']=='VALID' for r in extractions),'maintenance_started':sum(r['status']!='NOT_STARTED' for r in rows),'maintenance_valid':sum(r['status']=='VALID' for r in rows),'maintenance_invalid':sum(r['status'] not in ['NOT_STARTED','VALID','LAUNCHING'] for r in rows),'unstarted':sum(r['status']=='NOT_STARTED' for r in rows+extractions)},'groups_by_case':groups,'costs':costs,'stop':read(O/'stop.json') if (O/'stop.json').exists() else None,'case1_gate':read(O/'case1-execution-gate.json') if (O/'case1-execution-gate.json').exists() else None,'E1_confirmation':'approved prior exact E1-v1; repair-only','production_updates':False,'third_case_or_old_resume':False,'interpretation':'Two exposed authored cases, exploratory, not causal/stability/independent-generalization proof.'}
 save('summary.json',summary);save('slot-status.json',{'slots':[{k:r[k] for k in ['slot','case','phase','condition','repeat','status','failure_class','not_started_reason']} for r in extractions+rows]})
 # Produce bounded human-review bundles, not semantic keyword verdicts.
 for c in cases:
  parts=[]
  for r in rows:
   if r['case']!=c['case'] or r['status'] in ['NOT_STARTED','LAUNCHING']:continue
   d=O/'runs'/r['slot'];parts += ['\n# '+r['slot']+' '+labels[r['condition']],'ROW '+json.dumps(r,ensure_ascii=False),'PATCH\n'+((d/'patch.diff').read_text() if (d/'patch.diff').exists() else 'MISSING'),'DELIVERY\n'+((d/'raw-answer.txt').read_text() if (d/'raw-answer.txt').exists() else 'MISSING')]
  (O/('review-'+c['case']+'.txt')).write_text('\n'.join(parts))
 print(json.dumps({'status':summary['status'],'actual':summary['actual'],'cost_requests':costs['total']['requests']},ensure_ascii=False))
if __name__=='__main__':main()

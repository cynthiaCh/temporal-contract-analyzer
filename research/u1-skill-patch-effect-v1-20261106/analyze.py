"""Offline comparisons only; refuses to analyze an incomplete six-slot experiment."""
import csv,hashlib,json,subprocess
from datetime import datetime
from collections import Counter
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
read=lambda p:json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def delta(base,child):
 return dict(gained=[k for k,v in child.items() if v is True and base.get(k) is False],lost=[k for k,v in base.items() if v is True and child.get(k) is False],not_emitted=[k for k,v in base.items() if v is True and k not in child])
def raw_assertions(raw):return {s+'/'+a['id']:a.get('passed') is True for s,v in raw.get('schedules',{}).items() for a in v.get('assertions',[])}
def main():
 completion=read(OUT/'completion.json');rows=read(OUT/'results.json');assert completion['sessions']==len(rows)==len(read(OUT/'invocations.json'))==6
 comp=read(OUT/'historical-comparators.json');base=read(Path(comp['frozen_start_raw']));history=comp['historical_parent_execution']['score'];hist_assertions=history['assertions']
 # Frozen-start required/forbidden check semantics match the unchanged trusted normalizer.
 base_checks={k:v for k,v in history['checks'].items()}
 for k in base_checks:
  kind,name=k.split(':',1);base_checks[k]=base['observed_effects'][name] is (kind=='required')
 base_assertions=raw_assertions(base);output=[];costs=[];command_index={};native_count=0
 for row in rows:
  d=Path(row['path'])/'jobs/j-001';tr=read(d/'trajectory-index.json') if (d/'trajectory-index.json').exists() else dict(commands=[],tools=[],errors=[])
  command_index[row['id']]=tr['commands'];meter=read(d/'model-meter/ledger.json') if (d/'model-meter/ledger.json').exists() else None
  posts=[x['event'] for x in meter['events'] if x['event'].get('hook_event_name')=='PostModelRequest'] if meter else []
  pres=[x['event'] for x in meter['events'] if x['event'].get('hook_event_name')=='PreModelRequest' and not x.get('denied')] if meter else []
  keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens'];usage={k:sum(e.get('token_usage',{}).get(k,0) or 0 for e in posts) for k in keys}
  native_count+=len(pres)
  reconciliation={k:dict(cli=row.get('usage',{}).get(k),native=usage[k],equal=row.get('usage',{}).get(k)==usage[k]) for k in ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens']}
  cli_seconds=(datetime.fromisoformat(row['completed_at'].replace('Z','+00:00'))-datetime.fromisoformat(row['started_at'].replace('Z','+00:00'))).total_seconds() if row.get('started_at') and row.get('completed_at') else None
  costs.append(dict(cli_seconds=cli_seconds,id=row['id'],arm=row['arm'],replicate=row['replicate'],cli_sessions=1,native_started=len(pres) if meter else None,native_completed=len(posts) if meter else None,denied_retry_attempts=meter.get('denied') if meter else None,tool_calls=len(tr['tools']),shell_commands=len(tr['commands']),nonzero_shell=sum(c['exit_code'] not in [None,0] for c in tr['commands']),including_score_seconds=row['including_score_seconds'],**usage,usage_reconciliation=reconciliation))
  score=row.get('score');o=dict(id=row['id'],arm=row['arm'],replicate=row['replicate'],category=row['category'],score=score,comparisons=None,delivered_source_diff=any(n.startswith('src/') for n in row.get('changed_paths',[])),changed_paths=row.get('changed_paths',[]),target_pass=None)
  if score:
   paired=next(r['score'] for r in rows if r['arm']=='K' and r['replicate']==row['replicate'])
   o['target_pass']=score['checks'].get('required:start-switch-admission');o['comparisons']={}
   target=read(Path(row['raw_score'])).get('schedules',{}).get('start-switch-admission',{})
   o['target_history_assertion']=next((a for a in target.get('assertions',[]) if a.get('id')=='start-switch.audit'),None)
   for label,checks,assertions in [('frozen_start',base_checks,base_assertions),('historical_parent_9of10',history['checks'],hist_assertions)]+([('paired_K',paired['checks'],paired['assertions'])] if paired else []):
    o['comparisons'][label]=dict(checks=delta(checks,score['checks']),assertions=delta(assertions,score['assertions']))
  output.append(o)
 def total(rs):return {k:sum(r[k] for r in rs) for k in ['cli_sessions','native_started','native_completed','denied_retry_attempts','tool_calls','shell_commands','nonzero_shell','including_score_seconds','cli_seconds']+keys if all(r[k] is not None for r in rs)}
 summary=dict(scope='one exposed U1 development case; not independent generalization',independent_human_review_complete=False,hypothesis='F1 may help, not assumed',sessions=6,reflection_requests=0,gepa_searches=0,model='gpt-6-sol',effort='low',candidates=read(OUT/'candidate-sources.json'),results=output,costs=dict(total=total(costs),by_arm={arm:total([r for r in costs if r['arm']==arm]) for arm in ['K','F0','F1']},sessions=costs,monetary_cost=None,monetary_cost_reason='No billed charge returned; usage only'),execution_failures=[r['id'] for r in rows if r['category'].startswith('execution')],validation_anomalies=[r['id'] for r in rows if r['category']=='validation-unverified'],whole_pass_by_arm={arm:sum(bool(r['score'] and r['score']['whole_pass']) for r in rows if r['arm']==arm) for arm in ['K','F0','F1']},target_pass_by_arm={arm:sum(r['target_pass'] is True for r in output if r['arm']==arm) for arm in ['K','F0','F1']},no_statistical_inference=True)
 summary.update(runner_interruptions=1,operational_correction='runtime-correction.json; no job rerun',mechanism_review='mechanism-review.csv',conclusion='No observed target repair benefit for F1 over K or F0; all target/whole passes 0/2, and F1 repeat 2 loses ordinary ordered display while preserving retry.',target_history_pass_by_arm={arm:sum((r.get('target_history_assertion') or {}).get('passed') is True for r in output if r['arm']==arm) for arm in ['K','F0','F1']})
 save(OUT/'summary.json',summary);save(OUT/'command-index.json',command_index)
 fields=['id','arm','replicate','category','whole_pass','target_pass','target_history_pass','required_passed','required_total','delivered_source_diff','frozen_start_check_lost','historical_parent_check_lost','paired_K_gained','paired_K_lost','paired_K_assertion_lost','paired_K_assertion_not_emitted']
 with (OUT/'behavior.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in output:
   s=r['score'] or {};c=r['comparisons'] or {};pair=c.get('paired_K',{})
   w.writerow(dict(id=r['id'],arm=r['arm'],replicate=r['replicate'],category=r['category'],whole_pass=s.get('whole_pass'),target_pass=r['target_pass'],target_history_pass=(r.get('target_history_assertion') or {}).get('passed'),required_passed=s.get('required_passed'),required_total=s.get('required_total'),delivered_source_diff=r['delivered_source_diff'],frozen_start_check_lost=json.dumps(c.get('frozen_start',{}).get('checks',{}).get('lost')),historical_parent_check_lost=json.dumps(c.get('historical_parent_9of10',{}).get('checks',{}).get('lost')),paired_K_gained=json.dumps(pair.get('checks',{}).get('gained')),paired_K_lost=json.dumps(pair.get('checks',{}).get('lost')),paired_K_assertion_lost=json.dumps(pair.get('assertions',{}).get('lost')),paired_K_assertion_not_emitted=json.dumps(pair.get('assertions',{}).get('not_emitted'))))
 with (OUT/'costs.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=[k for k in costs[0] if k!='usage_reconciliation']);w.writeheader();w.writerows({k:v for k,v in r.items() if k!='usage_reconciliation'} for r in costs)
 print(json.dumps(dict(whole=summary['whole_pass_by_arm'],target=summary['target_pass_by_arm'],costs=summary['costs']['total']),indent=2))
if __name__=='__main__':main()

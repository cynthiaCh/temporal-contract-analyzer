"""Offline aggregation, never invokes models or scores."""
from pathlib import Path
import json,hashlib,csv
A=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
rows=read(A/'actual-schedule.json') if (A/'actual-schedule.json').exists() else []
C=read(A/'cohort.json');original=read(C['calibration'][0]['raw']);rules=read(A/'materials/evaluation/effects.json')['variants']['ungranted']
flat=lambda s:{sid+'/'+a['id']:a['passed'] for sid,x in s.get('schedules',{}).items() for a in x.get('checks',x.get('assertions',[]))}
orig_assert=flat(original);vectors=[]
for row in rows:
 if row['phase']!='repair':continue
 d=A/'runs'/row['slot']/'archive';s=read(d/'score/stdout.json') if (d/'score/stdout.json').exists() else {};assertions=flat(s);effects=s.get('observed_effects',{});files=read(d/'file-changes.json') if (d/'file-changes.json').exists() else {}
 vectors.append({'slot':row['slot'],'condition':row['condition'],'repeat':row['repeat'],'infrastructure_valid':row['infrastructure_valid'],'model_failure_class':row.get('failure_class'),'archive_status':row['archive_status']['status'],'scoring_valid':row.get('scoring_status')=='COLLECTED' and row.get('scored_candidate_unchanged',False),'overall_pass':row['infrastructure_valid'] and row.get('scoring_status')=='COLLECTED' and row.get('scored_candidate_unchanged',False) and s.get('verdict')=='PASS','verdict':s.get('verdict'),'effects':effects,'assertions':assertions,'required_gains_vs_original':[k for k in rules['required'] if not original['observed_effects'].get(k) and effects.get(k)],'required_losses_vs_original':[k for k in rules['required'] if original['observed_effects'].get(k) and not effects.get(k)],'common_assertion_losses_vs_original':[k for k,v in orig_assert.items() if v and k in assertions and not assertions[k]],'original_passed_assertions_absent':[k for k,v in orig_assert.items() if v and k not in assertions],'absent_assertion_rule':'Conditional trace assertions are recorded as absent, not automatically a policy loss; evaluate applicability against visible source before acceptance.','forbidden':s.get('observed_forbidden_effects',[]),'file_changes':files})
save('behavior-vectors.json',vectors)
def cost(rs):
 us=[];tool_events=0;permissions=0;shell=0
 for row in rs:
  d=A/'runs'/row['slot']/'archive';u=read(d/'usage.json') if (d/'usage.json').exists() else {};us.append(u)
  ledger=read(d/'meter/ledger.json') if (d/'meter/ledger.json').exists() else {}
  tool_events+=sum(x['event'].get('hook_event_name')=='PreToolUse' for x in ledger.get('events',[]));permissions+=sum(x['event'].get('hook_event_name')=='PermissionRequest' for x in ledger.get('events',[]))
  for line in (d/'events.jsonl').read_text().splitlines() if (d/'events.jsonl').exists() else []:
   try:e=json.loads(line)
   except ValueError:continue
   shell+=e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution'
 keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'];subtotal={k:sum((u.get('observed_usage_subtotal') or {}).get(k,0) for u in us) for k in keys};incomplete=[row['slot'] for row,u in zip(rs,us) if u.get('usage_incomplete',True)]
 return {'sessions':len(rs),'requests_started':sum(x.get('native',{}).get('started',0) for x in rs),'requests_completed':sum(x.get('native',{}).get('completed',0) for x in rs),'blocked_dispatches_not_sent':sum(x.get('native',{}).get('blocked_requests',0) for x in rs),'tools_pre_use':tool_events,'permission_events':permissions,'shell_commands_completed':shell,'session_seconds':sum(x['seconds'] for x in rs),'observed_usage_subtotal':subtotal,'total_usage':None if incomplete else subtotal,'unknown_usage_sessions':incomplete}
formal=[v for v in vectors if v['slot'].startswith('final-')];groups={g:{'pass':sum(v['overall_pass'] for v in formal if v['condition']==g),'valid':sum(v['infrastructure_valid'] and v['scoring_valid'] for v in formal if v['condition']==g),'invalid':sum(not(v['infrastructure_valid'] and v['scoring_valid']) for v in formal if v['condition']==g),'started':sum(v['condition']==g for v in formal),'reserved':3} for g in ['AUTO','AUTO_EXP']}
stages={'M1':{'model_requests':0,'model_sessions':0,'calibration_runs':len(C['calibration']),'calibration_seconds':sum(x['seconds'] for x in C['calibration']),'other_local_preparation_seconds':None},'M2_extraction':cost([x for x in rows if x['phase']=='extract']),'M2_AUTO_development':cost([x for x in rows if x['slot'].startswith('base-')]),'M3_reflection':cost([x for x in rows if x['phase']=='reflect']),'M3_revalidation':cost([x for x in rows if x['slot'].startswith('reval-')]),'M4_formal':cost([x for x in rows if x['slot'].startswith('final-')])}
done={x['slot'] for x in rows}
summary={'case':C['case'],'scope':'same-case experience development and frozen fresh-session evaluation; no transfer or independent generalization','stop':read(A/'stop.json') if (A/'stop.json').exists() else {'reason':'formal completed' if len(formal)==6 else 'in progress'},'formal':groups,'development_not_in_formal_denominator':True,'experience_generated':(A/'NEW_EXPERIENCE.md').exists(),'acceptance':read(A/'acceptance.json') if (A/'acceptance.json').exists() else None,'total_cost':cost(rows),'stages':stages,'planned_max_sessions':12,'planned_max_requests':264,'unstarted':[s for s in read(A/'schedule.json')['slots'] if s['slot'] not in done],'main_chat_preparation_usage':None,'currency_cost':None,'usage_boundary':'Model session hooks only; main chat and local orchestration unavailable/not imputed zero; cached/reasoning are subsets; no verified currency estimate.'}
save('summary.json',summary)
with (A/'case-results.csv').open('w') as f:
 fields=['slot','condition','repeat','model_failure_class','verdict','overall_pass','infrastructure_valid','scoring_valid'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:v[k] for k in fields} for v in vectors)
print(json.dumps({'stop':summary['stop']['reason'],'formal':groups,'total_cost':summary['total_cost']},ensure_ascii=False))

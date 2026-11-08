"""Offline evidence aggregation; no model calls and no re-scoring."""
from pathlib import Path
import json,hashlib,csv,subprocess,time
A=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
rows=read(A/'actual-schedule.json') if (A/'actual-schedule.json').exists() else []
keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens']
def cost(xs):
 return {'sessions':len(xs),'requests_started':sum(x.get('native',{}).get('started',0) for x in xs),'requests_completed':sum(x.get('native',{}).get('completed',0) for x in xs),'blocked_dispatches':sum(x.get('native',{}).get('blocked_requests',0) for x in xs),'tool_hook_attempts':sum(x.get('native',{}).get('tool_attempts',0) for x in xs),'shell_commands_completed':sum(x.get('tools',0) for x in xs),'session_seconds':sum(x.get('seconds',0) for x in xs),'observed_usage_subtotal':{k:sum(x.get('usage',{}).get(k,0) for x in xs) for k in keys},'total_usage':None if any(x.get('usage_incomplete',True) for x in xs) else {k:sum(x.get('usage',{}).get(k,0) for x in xs) for k in keys},'usage_unknown_sessions':[x['slot'] for x in xs if x.get('usage_incomplete',True)]}
cohort=read(A/'cohort.json')['cases'];vectors=[]
for r in rows:
 if r['phase']!='repair':continue
 p=A/'runs'/r['slot'];score=read(p/'score.stdout.json') if (p/'score.stdout.json').exists() else {};c=next(x for x in cohort if x['case']==r['case']);base=read(Path(c['calibration'][0]['raw']));effects=score.get('observed_effects',{});rules=read(A/'materials'/r['case']/'evaluation/effects.json')['variants']['ungranted'];required=rules['required']
 flat=lambda d:{sid+'/'+a['id']:a['passed'] for sid,s in d.get('schedules',{}).items() for a in s.get('assertions',[])}
 aa,bb=flat(score),flat(base)
 original={str(f.relative_to(p/'workspace')):sha(f) for f in (p/'workspace').rglob('*') if f.is_file()}
 rec={'slot':r['slot'],'case':r['case'],'condition':r['condition'],'status':r['status'],'failure_class':r.get('failure_class'),'infrastructure_valid':r.get('infrastructure_valid'),'scoring_valid':r.get('scoring_valid'),'raw_verdict':score.get('verdict'),'overall_pass':r.get('infrastructure_valid') and r.get('scoring_valid') and score.get('verdict')=='PASS','effects':effects,'assertions':aa,'required_gained_vs_original':[k for k in required if effects.get(k) and not base['observed_effects'].get(k)],'required_lost_vs_original':[k for k in required if base['observed_effects'].get(k) and not effects.get(k)],'assertions_lost_vs_original':[k for k,v in bb.items() if v and not aa.get(k)],'observed_forbidden_effects':score.get('observed_forbidden_effects',[]),'changed_original_files':[k for k,h in c['candidate_files'].items() if original.get(k)!=h],'added_files':[k for k in original if k not in c['candidate_files']]}
 vectors.append(rec)
save('behavior-vectors.json',vectors)
formal=[x for x in vectors if x['slot'].startswith('py-final-')]
groups={g:{'pass':sum(x['overall_pass'] for x in formal if x['condition']==g),'valid':sum(x['infrastructure_valid'] and x['scoring_valid'] for x in formal if x['condition']==g),'invalid':sum(not(x['infrastructure_valid'] and x['scoring_valid']) for x in formal if x['condition']==g),'started':sum(x['condition']==g for x in formal),'planned':3} for g in ['AUTO','AUTO_EXP']}
stages={
 'M1':{'model_sessions':0,'model_requests':0,'calibration_seconds':sum(s['seconds'] for c in cohort for s in c['calibration']),'calibrations':sum(len(c['calibration']) for c in cohort)},
 'M2_extraction':cost([x for x in rows if x['phase']=='extract']),
 'M2_python_screen':cost([x for x in rows if x['slot'].startswith('py-screen-')]),
 'M2_JS_baseline':cost([x for x in rows if x['slot'].startswith('js-base-')]),
 'M3_reflection':cost([x for x in rows if x['phase']=='reflect']),
 'M3_JS_revalidation':cost([x for x in rows if x['slot'].startswith('js-exp-')]),
 'M4_formal':cost([x for x in rows if x['slot'].startswith('py-final-')])}
stop=read(A/'stop.json') if (A/'stop.json').exists() else {'reason':'completed frozen formal validation' if len(formal)==6 else 'in progress'}
summary={'scope':'same-source exposed cross-language development transfer; Python includes extra startup cue; Reflection text only, not weight training or official GEPA','formal_validation':groups,'screen_not_in_formal_denominator':True,'stopping':stop,'total_cost':cost(rows),'stages':stages,'training_experience_generated':(A/'NEW_EXPERIENCE.md').exists(),'acceptance':read(A/'acceptance.json') if (A/'acceptance.json').exists() else None,'all_attempts_retained':True,'currency_cost':None,'main_chat_usage':None,'usage_boundary':'main chat preparation/analysis excluded as unavailable; cached input and reasoning output are subsets; no verified pricing','unstarted_slots':[s for s in read(A/'schedule.json')['slots'] if s['slot'] not in {r['slot'] for r in rows}]}
save('summary.json',summary)
accounting=[]
for x in rows:
 d=A/'runs'/x['slot'];ledger=read(d/'meter/ledger.json');events=[e['event'] for e in ledger['events']];pre=[e for e in events if e['hook_event_name']=='PreModelRequest'];post=[e for e in events if e['hook_event_name']=='PostModelRequest'];expected='gpt-6-sol' if x['phase']=='extract' else 'gpt-5.6-terra';cap=12 if x['phase'] in ['extract','reflect'] else 24
 assert ledger['sessions'][x['slot']]==x['native']
 assert sha(d/'actual-prompt.md')==x['prompt_sha256']
 assert read(d/'frozen-start.json')['files']==next(c['candidate_files'] for c in cohort if c['case']==x['case'])
 assert all(e.get('model')==expected for e in pre+post)
 assert x['native']['started']<=cap
 if x['phase']=='repair':
  core=(A/'prompts'/x['case']/'AUTO.md').read_text();expected_prompt=core+('\n\n'+(A/'NEW_EXPERIENCE.md').read_text() if x['condition']=='AUTO_EXP' else '')
  assert (d/'actual-prompt.md').read_text()==expected_prompt
 accounting.append({'slot':x['slot'],'requests_including_failed_cancelled':x['native']['started'],'post_hooks':len(post),'failed_posts':sum(e.get('status')!='completed' for e in post),'pending_or_cancelled_without_post':x['native']['started']-x['native']['completed'],'pre_tool_use':sum(e['hook_event_name']=='PreToolUse' for e in events),'permission_requests':sum(e['hook_event_name']=='PermissionRequest' for e in events),'prompt_and_start_and_hook_model_verified':True})
save('request-accounting-validation.json',{'rows':accounting,'prompt_equivalence':True,'failed_cancelled_not_excluded':True})
checks={p:sha(Path(p))==h for p,h in read(A/'protocol.json')['files'].items()};protect={p:sha(Path(p))==h for p,h in read(A/'protected-files.json').items()};config=read(A/'frozen-config.json');global_path=Path.home()/'.codex/config.toml';global_ok=sha(global_path)==config['global_config']['sha256']
usage_ok=all(x.get('native',{}).get('started',0)<= (12 if x['phase'] in ['extract','reflect'] else 24) for x in rows)
assert all(checks.values()) and all(protect.values()) and global_ok and usage_ok
save('integrity-validation.json',{'status':'PASS','frozen_files':len(checks),'protected_files':len(protect),'all_hashes_unchanged':True,'global_config_unchanged':global_ok,'per_session_caps':usage_ok,'total_requests_cap':summary['total_cost']['requests_started']<=324,'sessions_cap':len(rows)<=15,'concurrency':1,'no_auth_archived':not any(p.name=='auth.json' for p in A.rglob('*')),'formal_groups_only_input_difference':'exact appended frozen experience; verified per session if present'})
with (A/'case-results.csv').open('w') as f:
 fields=['slot','case','condition','status','failure_class','raw_verdict','overall_pass','changed_original_files','required_lost_vs_original','assertions_lost_vs_original'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in vectors)
print(json.dumps({'formal':groups,'stopping':stop['reason'],'cost':summary['total_cost']},ensure_ascii=False))

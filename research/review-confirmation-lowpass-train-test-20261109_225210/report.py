"""Derived reporting only: all planned slots, results, losses and known/unknown cost."""
import json,subprocess
from pathlib import Path
from archive import save,sha
from feedback import feedback
from report_common import aggregate
from study import A,ORDER,read,runner,cases

def main():
 records=read(A/'actual-schedule.json',[]);cc=cases();rows=[];costrows=[]
 for name in ORDER:
  rec=next((r for r in records if r['name']==name),None);alias=rec.get('alias') if rec else 'D' if name in ORDER[:6] else name.split('-')[0];phase=rec['phase'] if rec else 'extract' if name.endswith('analysis') else 'reflect' if name=='reflection' else 'repair';arc=A/'runs'/rec['slot']/'archive' if rec else None
  valid=bool(rec and phase=='repair' and rec.get('scoring_admissible') and rec.get('scoring_status')=='COLLECTED' and rec.get('scored_candidate_unchanged') and rec.get('score_result',{}).get('score_valid'))
  score=read(arc/'score/stdout.json') if valid else None;fb=feedback(read(A/'calibration'/alias/'original/stdout.json'),[score],read(A/'materials'/alias/'standards.json'))['runs'][0] if score else None
  row={'name':name,'alias':alias,'phase':phase,'started':rec is not None,'status':rec.get('status') if rec else 'NOT_STARTED','archive':str(arc) if arc else None,'valid_score':valid,'whole_task_pass':score['verdict']=='PASS' if score else None,'verdict':score['verdict'] if score else None,'satisfied_relations':len(fb['actual_successes']) if fb else None,'total_relations':len(read(A/'materials'/alias/'standards.json',[])),'behavior_vector':score['observed_effects'] if score else None,'original_successes_lost':[v['effect'] for v in fb['regressions']] if fb else None,'improvements_over_original':[v['effect'] for v in fb['improvements']] if fb else None,'feedback':fb,'usage':read(arc/'usage.json') if arc else None,'seconds':rec.get('seconds') if rec else None,'failure_class':rec.get('failure_class') if rec else None,'scoring_status':rec.get('scoring_status') if rec else None};rows.append(row)
  if rec:costrows.append({'phase':phase,'name':name,'usage':row['usage'],'seconds':row['seconds']})
 def summary_for(selected):
  planned=len(selected);started=sum(r['started'] for r in selected);valid=sum(r['valid_score'] for r in selected);passed=sum(r['whole_task_pass'] is True for r in selected)
  return {'planned':planned,'started':started,'valid':valid,'invalid':started-valid,'unstarted':planned-started,'whole_task_passes':passed,'denominator':valid,'pass_rate':passed/valid if valid else None,'display':str(passed)+'/'+str(valid) if valid else 'N/A (no valid score)'}
 train_auto=summary_for([r for r in rows if r['name'].startswith('D-AUTO')]);dev=summary_for([r for r in rows if r['name'].startswith('D-development')]);testing={};comparisons=[]
 for alias in ['T1','T2']:
  route=read(A/'testing'/alias/'route.json');selected=[r for r in rows if r['alias']==alias and r['phase']=='repair'];testing[alias]={'case':cc[alias]['case'],'route':route,'classification':read(A/'derived'/alias/'analysis.json'),'semantic_review':read(A/'derived'/alias/'semantic-review.json'),'prompt_difference':read(A/'testing'/alias/'prompt-difference.json'),'A':summary_for([r for r in selected if '-A' in r['name']]),'B':summary_for([r for r in selected if '-B' in r['name']])}
  for b in selected:
   if '-B' not in b['name'] or not b['valid_score']:continue
   for a in selected:
    if '-A' not in a['name'] or not a['valid_score']:continue
    fb=feedback(read(Path(a['archive'])/'score/stdout.json'),[read(Path(b['archive'])/'score/stdout.json')],read(A/'materials'/alias/'standards.json'))['runs'][0];comparisons.append({'case_alias':alias,'B':b['name'],'A':a['name'],'improvements':[x['effect'] for x in fb['improvements']],'regressions':[x['effect'] for x in fb['regressions']],'unknown':fb['unknown'],'experience_attribution_permitted':bool((route or {}).get('selected'))})
 testrows=[r for r in rows if r['alias']!='D' and r['phase']=='repair'];overall={arm:summary_for([r for r in testrows if '-'+arm in r['name']]) for arm in ['A','B']};subsets={}
 for kind in ['hit','fallback','unrouted']:
  aliases=[a for a,d in testing.items() if ('hit' if (d['route'] or {}).get('selected') else 'fallback' if d['route'] else 'unrouted')==kind];subsets[kind]={'aliases':aliases,**{arm:summary_for([r for r in testrows if r['alias'] in aliases and '-'+arm in r['name']]) for arm in ['A','B']}}
 costs={'preanalysis':aggregate([r for r in costrows if r['phase']=='extract']),'reflection':aggregate([r for r in costrows if r['phase']=='reflect']),'training_AUTO':aggregate([r for r in costrows if r['name'].startswith('D-AUTO')]),'development':aggregate([r for r in costrows if r['name'].startswith('D-development')]),'test_A':aggregate([r for r in costrows if r['name'].startswith(('T1-A','T2-A'))]),'test_B':aggregate([r for r in costrows if r['name'].startswith(('T1-B','T2-B'))]),'new_total':aggregate(costrows),'historical_selection_cost_recharged':False,'engineering_usage':None,'engineering_money':None,'offline_calibration_seconds':read(A/'calibration-summary.json',{}).get('seconds')}
 status='stopped' if (A/'stop.json').exists() else 'completed' if len(records)==16 else 'incomplete'
 s={'status':status,'stop':read(A/'stop.json'),'scope':'One fresh low-pass training case and two same-cluster, same-source exposed tests; outcome-informed selection and synthetic variants, not independent new-source generalization.','selection':read(A/'selection.json'),'protocol':read(A/'protocol.json'),'sessions':{'planned':16,'started':len(records),'unstarted':16-len(records)},'training_AUTO':train_auto,'development':dev,'candidate_structural_review':read(A/'development/structural-review.json'),'candidate_content_review':read(A/'development/content-review.json'),'candidate_semantic_review':read(A/'development/semantic-review.json'),'admission':read(A/'development/admission.json'),'no_experience_reason':read(A/'development/no-experience.json'),'frozen_library':read(A/'frozen-library.json'),'tests':testing,'overall_test':overall,'subsets':subsets,'all_slots':rows,'all_valid_test_B_vs_A':comparisons,'development_comparisons':read(A/'development/comparisons.json'),'costs':costs,'test_feedback_used_for_learning':False,'old_experience_seed':False,'training_excluded_from_test_denominators':True,'extra_judge_or_extraction_calls':0,'production_update':False,'git_commit_created':False,'no_next_round':True,'stop_review':read(A/'stop-review.json')}
 save(A/'summary.json',s);save(A/'costs.json',costs);save(A/'behavior-vectors.json',{r['name']:r['behavior_vector'] for r in rows if r['phase']=='repair'});save(A/'test-comparisons.json',comparisons)
 lines=['Fixed low-pass training with two same-cluster tests', '', 'Task 1: sources, implementation and offline checks', '',f"Status: {status}. Started {len(records)}/16 sessions. Stop: {json.dumps(s['stop'],ensure_ascii=False)}.", '', 'D: review-confirmation-binding-python3; T1: review-confirmation-binding-react; T2: review-confirmation-binding-jquery. All are explicit arms of document-review-binding and share source unit debounced-submit-flush. Historical pooled rates and sparse Terra/low provided-Contract failures informed selection; these are not exact current English automatic-Contract baseline evidence. Cases were fixed before new model calls; no substitution follows outcomes.', '', 'All owned model prompts, predicate definitions, labels and generated experience bodies use English. Exact Unicode evidence values are losslessly JSON-escaped, never translated or dropped. Existing source-span binding, null-safe runner-owned archival, accounting, feedback and single-body rules protocol were reused. JSX is included in source reading/normalization; preinstalled public dependencies are read-only. No installation, old scheduler, reference patch or prior experience seed is used.', '', 'Offline original/bounded/expanded/noop/mutant calibration, source isolation and actual dependency reads are archived. Policy audit distinguishes literal task/docs/source facts from AI-assisted preservation inferences. Reference PASS does not establish policy; valid evidence IDs do not prove entailment. AI-assisted review is not independent human approval.', '', 'Task 2: development, freeze and tests', '', '|Stage / case / condition|Planned|Started|Valid|Invalid|Unstarted|Whole-task / valid|','|---|---:|---:|---:|---:|---:|---:|']
 for label,d in [('D AUTO',train_auto),('D new-experience development',dev)]+[(a+' '+arm,d[arm]) for a,d in testing.items() for arm in ['A','B']]:lines.append('|'+label+'|'+str(d['planned'])+'|'+str(d['started'])+'|'+str(d['valid'])+'|'+str(d['invalid'])+'|'+str(d['unstarted'])+'|'+d['display']+'|')
 lines+=['', 'Training/development rows:', '', '|Slot|Relations satisfied|Verdict|Lost original successes|','|---|---:|---|---|']
 for r in rows:
  if r['alias']=='D' and r['phase']=='repair':lines.append('|'+r['name']+'|'+(str(r['satisfied_relations'])+'/'+str(r['total_relations']) if r['valid_score'] else 'unscored')+'|'+str(r['verdict'])+'|'+str(r['original_successes_lost'])+'|')
 lines+=['', 'Candidate admission:', '```json',json.dumps({'structure':s['candidate_structural_review'],'content':s['candidate_content_review'],'admission':s['admission'],'no_experience':s['no_experience_reason']},ensure_ascii=False,indent=2),'```', '', 'No both-PASS gate is applied. A grounded target/overall relation improvement can qualify with all regressions retained; development is not evidence of stable gain. Unsupported content or no observed development improvement stops before testing.']
 for alias,d in testing.items():
  lines+=['',alias+': '+d['case'],'','Route / premise checks:','```json',json.dumps(d['route'],ensure_ascii=False,indent=2),'```', 'Prompt difference: '+json.dumps(d['prompt_difference'],ensure_ascii=False),'', '|Behavior relation (original expectation)|A1|A2|B1|B2|','|---|---|---|---|---|']
  rr={r['name'].split('-')[1]:r for r in testrows if r['alias']==alias}
  for rel in read(A/'materials'/alias/'standards.json',[]):
   cells=[]
   for armrep in ['A1','A2','B1','B2']:
    v=(rr[armrep]['behavior_vector'] or {}).get(rel['effect']);cells.append('unknown / unscored' if type(v) is not bool else 'PASS' if v==rel['expected'] else 'FAIL')
   lines.append('|'+rel['effect']+' ('+str(rel['expected'])+')|'+'|'.join(cells)+'|')
  lines+=['', 'Per-slot final source/diffs, raw checks with actual/expected values and traces, public deliveries and costs remain in each archive. Baseline preservation and gains/losses are in summary.json. If route falls back, A/B identical inputs and random result differences are not experience evidence.']
 lines+=['', 'Task 3: complete gains/losses, costs and limitations', '', 'Overall tests and hit/fallback subsets:', '```json',json.dumps({'overall':overall,'subsets':subsets,'B_vs_A':comparisons},ensure_ascii=False,indent=2),'```', '', 'Costs (all started slots retained, unknown usage never filled with zero):','```json',json.dumps(costs,ensure_ascii=False,indent=2),'```', '', 'The scoring rules are original for each case. Only completed source-read format-valid final candidates are admitted. Candidate-caused syntax/runtime/protocol failures retain original behavioral verdicts; infrastructure or incomplete output remains separately invalid/unscored. No score/model rerun or hidden retry is performed.', '', 'The frozen library, Contracts and routes are not changed from test outcomes. Whole-task gains, target relations and all original-success losses must be read together. Two repeats are descriptive, not statistical significance, stable benefit or independent generalization. Historical selection has already exposed outcomes, and the three cases share one source unit. No production experience update, global configuration edit or Git commit. Stop at this batch.']
 if (A/'EXECUTION_REVIEW.md').exists():lines+=['',(A/'EXECUTION_REVIEW.md').read_text()]
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 (A/'COMMIT_MESSAGE.txt').write_text('research: train on low-pass review binding and test same-cluster variants\n\nFreeze an English-only Python training case and React/jQuery test cohort.\nReuse source-span extraction, evidence handoff, single-body rule output and conservative routing.\nPreserve all original scores, regressions, partial failures and request accounting.\nKeep training/test feedback separate and production experience unchanged.\n')
 errors=[];checks=[]
 for name in ['initial-freeze.json','analysis-freeze-D.json','reflection-freeze.json','experience-freeze.json','library-freeze.json','test-freeze.json']:
  if (A/name).exists():
   try:runner.verify(read(A/name)['files']);checks.append(name)
   except Exception as e:errors.append(repr(e))
 initial=read(A/'initial-state.json')
 for cmd,key in [(['git','rev-parse','HEAD'],'HEAD'),(['git','diff'],'diff'),(['git','diff','--cached'],'cached_diff')]:
  value=subprocess.check_output(cmd,text=True);value=value.strip() if key=='HEAD' else value
  if value!=initial[key]:errors.append('Git state changed: '+key)
 archives=[]
 for rec in records:
  root=A/'runs'/rec['slot']/'archive';manifest=root/'ARTIFACTS.sha256';count=0
  if not manifest.exists():errors.append('Archive manifest missing: '+rec['slot']);continue
  for line in manifest.read_text().splitlines():
   h,name=line.split('  ',1)
   if sha(root/name)!=h:errors.append('Archive mismatch: '+str(root/name))
   count+=1
  archives.append({'slot':rec['slot'],'files_verified':count})
 save(A/'integrity.json',{'errors':errors,'freeze_manifests_verified':checks,'archives':archives,'HEAD_existing_work_and_protected_sources_preserved':not errors,'report_is_derived_not_actor_input':True,'report_code_sha256':sha(A/'report.py'),'freeze_guard_violation_retained':read(A/'stop-review.json'),'archive_integrity_separate_from_configuration_guard':True})
 save(A/'completion.json',{'status':status,'sessions_started':len(records),'valid_test_scores':sum(r['valid_score'] for r in testrows),'no_more_model_calls':True})
 files={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256'};(A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
 print(json.dumps({'status':status,'sessions':s['sessions'],'training':train_auto,'development':dev,'tests':{k:{a:v[a] for a in ['A','B']} for k,v in testing.items()},'costs':costs['new_total'],'integrity_errors':errors},ensure_ascii=False))
 if errors and not (A/'stop.json').exists():raise RuntimeError(errors)

if __name__=='__main__':main()

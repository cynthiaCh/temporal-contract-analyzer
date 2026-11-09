"""Report all fixed slots, including conditional stages never started."""
import json,subprocess
from pathlib import Path
from archive import save,sha
from feedback import feedback
from report_common import aggregate
import pilot
A=Path(__file__).resolve().parent
def read(p,d=None):return json.loads(Path(p).read_text()) if Path(p).exists() else d

def main():
 actual=read(A/'actual-schedule.json',[])
 plan=[('D-analysis','extract','D'),('AUTO-1','repair','D'),('AUTO-2','repair','D'),('reflection','reflect','D'),('development-1','repair','D'),('development-2','repair','D'),('T-analysis','extract','T'),('test-B1','repair','T'),('test-A1','repair','T'),('test-A2','repair','T'),('test-B2','repair','T')]
 rows=[]
 for name,phase,alias in plan:
  rec=next((x for x in actual if x['name']==name),None);arc=A/'runs'/rec['slot']/'archive' if rec else None
  valid=bool(rec and rec.get('scoring_status')=='COLLECTED' and rec.get('score_result',{}).get('score_valid') and rec.get('scored_candidate_unchanged'))
  score=read(arc/'score/stdout.json') if valid else None;standards=read(A/'materials'/alias/'standards.json')
  fb=feedback(read(A/'calibration'/alias/'original/stdout.json'),[score],standards)['runs'][0] if score else None
  rows.append({'name':name,'phase':phase,'alias':alias,'started':rec is not None,'reused':bool(rec and rec.get('reused')), 'valid_behavior_score':valid,
   'valid_preanalysis':rec.get('preanalysis_valid') if rec else None,'status':rec.get('status') if rec else 'NOT_STARTED',
   'verdict':score['verdict'] if score else None,'whole_task_pass':score['verdict']=='PASS' if score else None,
   'satisfied':len(fb['actual_successes']) if fb else None,'total':len(standards),'behavior_vector':score['observed_effects'] if score else None,
   'gains_over_original':[x['effect'] for x in fb['improvements']] if fb else None,'original_successes_lost':[x['effect'] for x in fb['regressions']] if fb else None,
   'full_feedback':fb,'usage':read(arc/'usage.json') if rec else None,'seconds':rec.get('seconds') if rec else None,'archive':str(arc) if arc else None})
  if name=='D-analysis' and rec is None:
   rows[-1].update(reused=True,status='REUSED_SOURCE_BOUND_AUTOMATIC_ANALYSIS',valid_preanalysis=True,source_provenance='derived/D/provenance.json',new_session_started=False)
 def group(subset):
  started=[r for r in subset if r['started']];valid=[r for r in subset if r['valid_behavior_score']];passed=sum(r['whole_task_pass'] for r in valid)
  return {'planned':len(subset),'started':len(started),'valid':len(valid),'invalid':len(started)-len(valid),'unstarted':len(subset)-len(started),
   'whole_task_passes':passed,'denominator':len(valid),'rate':passed/len(valid) if valid else None,'costs':aggregate(started)}
 groups={'training_AUTO':group([r for r in rows if r['name'].startswith('AUTO-')]),'development':group([r for r in rows if r['name'].startswith('development-')]),
  'test_A':group([r for r in rows if r['name'].startswith('test-A')]),'test_B':group([r for r in rows if r['name'].startswith('test-B')])}
 costrows=[r for r in rows if r['started'] and not r['reused']]
 costs={'preanalysis':aggregate([r for r in costrows if r['phase']=='extract']),'reflection':aggregate([r for r in costrows if r['phase']=='reflect']),
  'maintenance':aggregate([r for r in costrows if r['phase']=='repair']),'new_total':aggregate(costrows),
  'calibration':{'model_calls':0,'reused_current_version_scores':22,'new_scoring_calls':0},'reused_AUTO_reference_only':aggregate([r for r in rows if r['reused'] and r['phase']=='repair']),
  'reused_training_analysis':{'new_requests_this_batch':0,'historical_usage':None,'source_provenance':'derived/D/provenance.json','not_recharged':True},'engineering':{'tokens':None,'money':None}}
 summary={'scope':'One fixed authored same-source JS/Python training/test pair, not independent generalization',
  'status':'stopped' if (A/'stop.json').exists() else 'completed' if (A/'completion.json').exists() else 'incomplete','stop':read(A/'stop.json'),
  'cases':read(A/'cases.json'),'selection':read(A/'selection.json'),'maximum_new_sessions':8,'started_sessions':len(costrows),'unstarted_sessions':8-len(costrows),'reused_baseline_sessions':2,'training_analysis_reused':True,
  'groups':groups,'slots':rows,'training_analysis_provenance':read(A/'derived/D/provenance.json'),'test_semantic_rejection':read(A/'test-semantic-rejection.json'),'test_maintenance_effectiveness':None if read(A/'test-semantic-rejection.json') else 'see actual test scores','candidate_review':read(A/'development/content-review.json'),'candidate_admission':read(A/'development/admission.json'),
  'no_experience_reason':read(A/'development/no-experience.json'),'development_comparisons':read(A/'development/comparisons.json'),
  'route':read(A/'testing/route.json'),'costs':costs,'old_experience_seed':False,'test_feedback_used_for_learning':False,
  'no_case_replacement_or_next_round':True,'production_update':False}
 save(A/'summary.json',summary);save(A/'costs.json',costs);save(A/'behavior-vectors.json',{r['name']:r['behavior_vector'] for r in rows})
 lines=['Fixed new training/test pair:','',
  '- Train: query-paused-initial-fetch-10266-vanilla; two exact-condition historical AUTO baselines are reused (not fresh calls).' ,
  '- Test: query-paused-initial-fetch-10266-python3',
  '- Cluster and source unit: query-paused-initial-fetch-10266.',
  '- Both variants and histories are extensively exposed. Same-source synthetic language variants, not unseen or independently sampled.',
  '',f"Status: {summary['status']}; stop: {json.dumps(summary['stop'],ensure_ascii=False)}",'',
  'The pair was chosen and announced before model calls, based on direct lineage and explicit candidate-visible policy. Two genuine matching-model/low AUTO failures (27/29 each) were source-verified and reused. The historically overrestrictive Python Contract was excluded and will not be reused. No guarantee of difficulty for the newly analyzed test input is claimed. The pair was not replaced based on outcomes.',
  '', '|Stage|Planned|Started|Valid|Invalid|Unstarted|Whole-task pass / valid|','|---|---|---|---|---|---|---|']
 for name,g in groups.items():lines.append(f"|{name}|{g['planned']}|{g['started']}|{g['valid']}|{g['invalid']}|{g['unstarted']}|"+(f"{g['whole_task_passes']}/{g['valid']}" if g['valid'] else 'not calculable')+'|')
 lines+=['','|Slot|Started|Satisfied relations|Verdict|Lost original successes|','|---|---|---|---|---|']
 for r in rows:lines.append('|'+r['name']+'|'+('reused analysis' if r['name']=='D-analysis' and r['reused'] else str(r['started']))+'|'+(str(r['satisfied'])+'/'+str(r['total']) if r['valid_behavior_score'] else 'unscored')+'|'+str(r['verdict'])+'|'+str(r['original_successes_lost'])+'|')
 for alias in ['D','T']:
  subset=[r for r in rows if r['alias']==alias and r['valid_behavior_score']]
  if not subset:continue
  lines+=['',f'Complete original behavior vector ({alias}):','','|Relation|'+'|'.join(r['name'] for r in subset)+'|','|---|'+'|'.join('---' for r in subset)+'|']
  for rel in read(A/'materials'/alias/'standards.json'):
   lines.append('|'+rel['effect']+'|'+'|'.join('PASS' if r['behavior_vector'].get(rel['effect'])==rel['expected'] else 'FAIL' for r in subset)+'|')
 lines+=['','No experience reason: '+json.dumps(summary['no_experience_reason'],ensure_ascii=False),'Test semantic rejection: '+json.dumps(summary['test_semantic_rejection'],ensure_ascii=False),
  'Candidate eligibility: '+json.dumps(summary['candidate_admission'],ensure_ascii=False),
  'Test routing: '+json.dumps(summary['route'],ensure_ascii=False),'',
  'No valid score means unknown effectiveness, not a behavioral failure. Training/development results are excluded from all test denominators. If both AUTO baselines pass, the predeclared rule generates no experience and stops before test; this is not a failed test or proof of universal ineffectiveness.',
  '', 'Costs (unknown engineering usage/money remain null):','```json',json.dumps(costs,ensure_ascii=False,indent=2),'```','',
  'Offline preparation: source/task/Contract/full AUTO prompt/model/effort/tools/budget/scorer match for both reused baselines; 22 associated current-version calibrations reused, no rescoring. 36 checks cover source isolation, archival, metering, citations and routing. The initial and derived ledger freeze scopes were separated before the first fresh call; original ledger is pinned separately and augmented ledger is protected by reflection-freeze. Raw evidence and score policy were not changed; pre-call record remains in precall-ledger-phase-check/.',
  'Models: extract gpt-6-sol/low (12 requests), repair gpt-5.6-terra/low (24), reflect gpt-5.6-terra/medium (12); all 600s, serial, no provider retry. Maximum 8 NEW sessions/168 requests; the correct training analysis and two baselines are reused and not charged again. No old scheduler, external judge, prior experience seed, reference patch to learner, case swap, test learning or production update.',
  'The reused training analysis retains its original model provenance and prior offline admission; it is not a new extraction. Reused baseline costs are reference-only; fresh-call totals exclude them. The separate report-only hash gate interception before maintenance was corrected by restoring report.py to its original frozen bytes; the new reporter is report_query.py. All true experimental inputs/guard hashes stayed unchanged, no maintenance session had started at that interception, and the original stop record is retained in pre-maintenance-report-check/. All raw responses/events, actual prompts, Python-generated diffs, final candidates, original scores and usage are under runs/*/archive. Frozen manifests and source/derivation metadata remain separate. Semantic reviews are AI-assisted execution-agent reviews, not independent human approvals.',
  'The two fresh development scores were 28/29 and 29/29 versus reused 27/29 baselines. Both cached target relationships improved; the first run lost accepted-resume-then-offline, while the second lost no baseline success. This is a same-case development observation, not a stable-effect or independent test claim. The experience remains frozen and content-supported; no A/B behavior result exists because test Contract semantic admission failed.',
  'Next necessary repair is generic preservation of qualifiers when converting a reported defect into a normative Contract (forbidden action WITH a condition must not become forbidden action generally). Keep this selected pair and frozen experience; do not restart reflection or select another case to hide the extraction fault. A corrected extraction/test stage requires a separate declared authorization; this batch performs no extra extraction or test.',
  'Finished/stopped at the declared stage. No commit or automatic next batch.']
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 (A/'COMMIT_MESSAGE.txt').write_text('research: stage a fixed autosave parent-port experience pilot\n\nSelect a source-verified hard query pair from valid AUTO/low failures.\nReuse two matching 27/29 baselines and source-bound Contract without charging them again.\nReuse bounded extraction, isolated maintenance and Python-owned archival.\nPreserve every outcome, unknown usage and unstarted conditional stage without case replacement.\n')
 initial=read(A/'initial-state.json');errors=[];checked=[]
 for name in ['initial-freeze.json','reflection-freeze.json','library-freeze.json','test-freeze.json']:
  if (A/name).exists():
   try:pilot.runner.verify(read(A/name)['files']);checked.append(name)
   except Exception as exc:errors.append(repr(exc))
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==initial['HEAD']
 assert subprocess.check_output(['git','diff'],text=True)==initial['diff'] and subprocess.check_output(['git','diff','--cached'],text=True)==initial['cached_diff']
 manifests=[]
 for rec in actual:
  arc=A/'runs'/rec['slot']/'archive';n=0
  for line in (arc/'ARTIFACTS.sha256').read_text().splitlines():
   h,name=line.split('  ',1)
   if sha(arc/name)!=h:errors.append(str(arc/name))
   n+=1
  manifests.append({'slot':rec['slot'],'files_checked':n})
 save(A/'integrity.json',{'frozen_manifests_verified':checked,'archive_manifests':manifests,'errors':errors,'historical_sources_HEAD_index_unchanged':not errors})
 save(A/'provenance.json',{'historical_helper_inputs':'initial-state.json','selected_cases':'selection.json','original_candidate_task_and_source_manifests':'materials/D and materials/T',
  'calibration':'22 matched-version calibration records reused, zero new scores; baseline failure evidence is actual model repair, not original-code calibration',
  'new_implementation':['prepare_batch.py','query_handoff.py','report.py'],'controller_changes':'Fresh rules-only output and deterministic metadata from source-reviewed D mechanisms; existing bounded runner and route reused.'})
 hashes={str(f.relative_to(A)):sha(f) for f in A.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(hashes.items())))
 print(json.dumps({'status':summary['status'],'stop':summary['stop'],'groups':groups,'costs':costs['new_total'],'files':len(hashes)},ensure_ascii=False))
 if errors:raise RuntimeError(errors)

if __name__=='__main__':main()

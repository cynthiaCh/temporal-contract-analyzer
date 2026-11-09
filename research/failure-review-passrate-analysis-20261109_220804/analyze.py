"""Rank historical cases from complete receipts, with explicit validity and copies."""
import collections,csv,hashlib,json,re,subprocess,statistics
from fractions import Fraction
from pathlib import Path
A=Path(__file__).resolve().parent
REAL_MODELS={'gpt-6.1-sol','gpt-5.6-terra','gpt-6-sol','deepseek-v4-pro','gpt-5.6-sol','qwen3-coder:30b'}
VERDICTS={'PASS','UNDERREACH','OVERREACH','UNDERREACH_AND_OVERREACH'}
BAD=re.compile('ERROR|TIMEOUT|CONTAMINAT|INTERRUPT|UNSUPPORTED|INVALID|RUNNING|PENDING|EXCLUDED|PAUSED|STOPPED|CANCELLED',re.I)

def read(name):return json.loads((A/name).read_text())
def save(name,x):(A/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def write_csv(name,rows):
 if not rows:return
 with (A/name).open('w',newline='',encoding='utf-8-sig') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
  for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
def execution_identity(r):
 return r.get('started_at_utc') or r.get('started_at') or (r.get('run_id') if r.get('run_id') not in [None,'','agent','run'] else None)
def duplicate_key(r):return r['receipt_sha256'] if execution_identity(r) else 'PATH:'+r['path']
def bind_score(r,scores):
 d=str(Path(r['path']).parent)
 return next(((p,scores[p]) for p in [d+'/score/score.json',d+'/score.json'] if p in scores),(None,None))
def bind_outer(r,outers):
 d=Path(r['path']).parent
 return outers.get(str(d.parent/'result.json'),{}) if d.name=='agent' else {}

def evaluate(r,score_pairs,outer_records):
 reasons=[];notes=[]
 if r.get('model') not in REAL_MODELS:reasons.append('non_model_stub_or_control')
 if r.get('status') not in ['SCORED','COMPLETED']:reasons.append('non_scored_final_status:'+str(r.get('status')))
 if r.get('valid_scored') is False:reasons.append('explicit_valid_scored_false')
 if r.get('verdict') not in VERDICTS:reasons.append('missing_or_unknown_final_verdict')
 if r.get('contamination_findings'):reasons.append('contamination_findings')
 if any(r.get(k) is False for k in ['candidate_complete','infrastructure_valid','scoring_admissible']):reasons.append('explicit_incomplete_or_invalid')
 for outer in outer_records:
  if BAD.search(str(outer.get('status') or '')):reasons.append('outer_validity_status:'+str(outer['status']))
  if outer.get('valid_scored') is False:reasons.append('outer_valid_scored_false')
 scores=[s for _,s in score_pairs if s is not None]
 if not scores:reasons.append('no_associated_score_receipt')
 for s in scores:
  if s['verdict']!=r.get('verdict'):reasons.append('run_score_verdict_disagreement')
  if s.get('case_id') and s['case_id']!=r['case_id']:reasons.append('run_score_case_disagreement')
  if r.get('variant') and s.get('variant') and s['variant']!=r['variant']:reasons.append('run_score_variant_disagreement')
  if s.get('runtime_error_schedules'):
   if r.get('verdict')=='PASS':reasons.append('PASS_with_recorded_runtime_errors')
   else:notes.append('runtime_error_in_completed_behavioral_failure')
 if len({s['receipt_sha256'] for s in scores})>1:notes.append('multiple_score_receipt_versions_same_execution')
 return not reasons,sorted(set(reasons)),notes

def aggregate(records,keys):
 grouped=collections.defaultdict(list)
 for r in records:grouped[tuple(r.get(k) for k in keys)].append(r)
 out=[]
 for key,rs in grouped.items():
  valid=[r for r in rs if r['valid_score']];p=sum(r['verdict']=='PASS' for r in valid);n=len(valid)
  vals={'records_or_execution_groups':len(rs),'raw_receipts':sum(r['raw_copies'] for r in rs),'archive_copies_folded':sum(r['raw_copies']-1 for r in rs),'valid_scores':n,'passes':p,'behavioral_failures':n-p,'excluded_or_unverified':len(rs)-n,'pass_rate':p/n if n else None,'pass_rate_percent':100*p/n if n else None,'model_count':len({r['model'] for r in valid}),'condition_count':len({r['condition'] for r in valid}),'recorded_effort_count':len({r['effort'] for r in valid}),'input_or_manifest_hash_count':len({r['version_hash'] for r in valid if r['version_hash']}),'unknown_version_scores':sum(not r['version_hash'] for r in valid),'possible_config_mixture':len({(r['model'],r['effort'],r['condition'],r['variant'],r['workflow_profile'],r['timeout_seconds']) for r in valid})>1,'source_units':sorted({r['source_unit'] for r in rs if r['source_unit']}),'models':sorted({r['model'] for r in valid}),'conditions':sorted({r['condition'] for r in valid})}
  out.append({**dict(zip(keys,key)),**vals})
 return out

def rank(rows):
 valid=[r for r in rows if r['valid_scores']];fractions=sorted({Fraction(r['passes'],r['valid_scores']) for r in valid})
 for r in rows:
  f=Fraction(r['passes'],r['valid_scores']) if r['valid_scores'] else None
  r['rank_hardest']=fractions.index(f)+1 if f is not None else None;r['rank_easiest']=len(fractions)-fractions.index(f) if f is not None else None
 return sorted(rows,key=lambda r:(r['pass_rate'] is None,r['pass_rate'] if r['pass_rate'] is not None else 2,-r['valid_scores'],r['case_id']))

def main():
 runs=read('run-receipts.json');scores=read('score-projections.json');outers=read('outer-projections.json')
 buckets=collections.defaultdict(list)
 for r in runs:buckets[duplicate_key(r)].append(r)
 groups=[];raw=[];copy_groups=[]
 for key,rs in sorted(buckets.items()):
  rs=sorted(rs,key=lambda x:x['path']);r=rs[0];pairs=[bind_score(x,scores) for x in rs];outs=[bind_outer(x,outers) for x in rs]
  valid,reasons,notes=evaluate(r,pairs,outs)
  base={'execution_group':key,'case_id':r['case_id'],'source_unit':r.get('source_unit') or r.get('independent_unit_id') or '', 'model':r.get('model') or str(r.get('system_identity')),'effort':r.get('reasoning_effort') or r.get('effort') or '(not recorded)','condition':r.get('condition') or '(not recorded)','variant':r.get('variant') or '(not recorded)','workflow_profile':r.get('workflow_profile') or '(not recorded)','timeout_seconds':r.get('timeout_seconds'),'version_hash':r.get('source_manifest_sha256') or r.get('case_manifest_sha256') or r.get('input_tree_sha256') or r.get('base_tree_sha256'),'runner_sha256':r.get('runner_sha256'),'started_at_utc':r.get('started_at_utc'),'verdict':r.get('verdict'),'valid_score':valid,'exclusion_reasons':reasons,'notes':notes,'runtime_error_schedules':sorted({v for _,ss in pairs if ss for v in ss.get('runtime_error_schedules',[])}),'raw_copies':len(rs),'score_receipts_available':sum(s is not None for _,s in pairs),'all_receipt_paths':[x['path'] for x in rs],'all_score_paths':[p for p,s in pairs if s is not None],'final_status':r.get('status')}
  groups.append(base)
  if len(rs)>1:copy_groups.append({'execution_group':key,'case_id':r['case_id'],'copies':len(rs),'identity_evidence':execution_identity(r),'full_receipt_content_identical':True,'available_score_versions':len({s['receipt_sha256'] for _,s in pairs if s}),'valid_group':valid,'paths':base['all_receipt_paths']})
  for x,(sp,s),outer in zip(rs,pairs,outs):
   v,why,note=evaluate(x,[(sp,s)],[outer]);raw.append({**base,'execution_group':x['path'],'raw_copies':1,'valid_score':v,'exclusion_reasons':why,'notes':note,'all_receipt_paths':[x['path']],'all_score_paths':[sp] if sp else []})
 real=[r for r in groups if r['model'] in REAL_MODELS];rawreal=[r for r in raw if r['model'] in REAL_MODELS]
 case_rows=rank(aggregate(real,['case_id']));raw_cases=rank(aggregate(rawreal,['case_id']))
 rowsbycase={r['case_id']:r for r in case_rows}
 for r in raw_cases:
  new=rowsbycase[r['case_id']];r['folded_pass_rate_percent']=new['pass_rate_percent'];r['raw_minus_folded_percentage_points']=(r['pass_rate_percent']-new['pass_rate_percent']) if r['pass_rate'] is not None and new['pass_rate'] is not None else None
 stratum_keys=['case_id','model','effort','condition','variant','workflow_profile','timeout_seconds']
 strata=aggregate(real,stratum_keys)
 for group_keys,filename in [(['model','effort','condition'],'model_effort_condition.csv'),(['case_id','model','effort','condition','variant','workflow_profile','timeout_seconds','version_hash'],'case_model_condition_version.csv')]:write_csv(filename,aggregate(real,group_keys))
 write_csv('case_ranking.csv',case_rows);write_csv('case_ranking_raw_receipts.csv',raw_cases);write_csv('case_model_condition.csv',strata)
 write_csv('execution_groups.csv',groups);write_csv('duplicate_groups.csv',copy_groups)
 excluded=[r for r in groups if not r['valid_score']];write_csv('excluded_records.csv',excluded)
 # Explicitly separate exploratory condition differences from causal effects.
 cells=collections.defaultdict(dict)
 for r in aggregate(real,['case_id','model','effort','variant','workflow_profile','timeout_seconds','version_hash']+['condition']):
  key=tuple(r[k] for k in ['case_id','model','effort','variant','workflow_profile','timeout_seconds','version_hash']);cells[key][r['condition']]=r
 deltas=[]
 for key,cs in cells.items():
  base=cs.get('latent-maintenance')
  if not base or not base['valid_scores']:continue
  for condition,r in cs.items():
   if condition=='latent-maintenance' or not r['valid_scores']:continue
   delta=r['pass_rate']-base['pass_rate'];deltas.append({**dict(zip(['case_id','model','effort','variant','workflow_profile','timeout_seconds','version_hash'],key)),'baseline_condition':'latent-maintenance','condition':condition,'baseline_passes':base['passes'],'baseline_valid':base['valid_scores'],'passes':r['passes'],'valid':r['valid_scores'],'difference_percentage_points':100*delta,'relative_change':delta/base['pass_rate'] if base['pass_rate'] else None,'causal_claim':False,'version_binding_recorded':key[-1] is not None})
 write_csv('condition_deltas_descriptive.csv',deltas)
 eligible=[r for r in case_rows if r['valid_scores']>=10];unknown=[r for r in case_rows if not r['valid_scores']]
 def overall(rs):
  v=[r for r in rs if r['valid_score']];p=sum(r['verdict']=='PASS' for r in v)
  return {'records_or_groups':len(rs),'valid_scores':len(v),'passes':p,'behavioral_failures':len(v)-p,'excluded_or_unverified':len(rs)-len(v),'pass_rate':p/len(v) if v else None}
 summary={'scope':'Archived outcomes as recorded, not rescored or semantically re-certified. Pooled rates are descriptive and mix models/configurations; primary unit collapses only identical full run receipts with a recorded execution identity.','source_archive':'/home/sribd/Downloads/wangshu/failure-review-export-20261029.zip','inventory':read('inventory-audit.json')['stats'],'export_summary':read('export-summary.json'),'model_run_receipts_including_stubs':len(runs),'non_model_stub_receipts':sum(r['model'] not in REAL_MODELS for r in raw),'case_count':len(case_rows),'cases_with_valid_scores':len(case_rows)-len(unknown),'cases_without_valid_scores':[r['case_id'] for r in unknown],'raw_real_model_receipts':overall(rawreal),'primary_copy_folded':overall(real),'runtime_exclusion_sensitivity':overall([r for r in real if not r['runtime_error_schedules']]),'valid_groups_with_candidate_runtime_errors':sum(r['valid_score'] and bool(r['runtime_error_schedules']) for r in real),'exact_duplicate_groups':len(copy_groups),'copies_folded':sum(r['copies']-1 for r in copy_groups),'copies_of_real_models_folded':sum(r['raw_copies']-1 for r in real),'pass_receipts_marked_contaminated':sum(r.get('verdict')=='PASS' and r.get('status')=='CONTAMINATED' for r in runs),'exclusion_reason_counts_not_disjoint':dict(collections.Counter(reason for r in excluded if r['model'] in REAL_MODELS for reason in r['exclusion_reasons'])),'case_rate_distribution':{'zero_percent':sum(r['valid_scores']>0 and r['passes']==0 for r in case_rows),'hundred_percent':sum(r['valid_scores']>0 and r['passes']==r['valid_scores'] for r in case_rows),'between_zero_and_hundred':sum(0<r['passes']<r['valid_scores'] for r in case_rows),'valid_less_than_10':sum(0<r['valid_scores']<10 for r in case_rows)},'models':sorted(REAL_MODELS),'hardest_at_least_10_valid':eligible[:15],'easiest_at_least_10_valid':sorted(eligible,key=lambda r:(-r['pass_rate'],-r['valid_scores'],r['case_id']))[:15],'prior_research_cases':[r for r in case_rows if r['case_id'] in ['query-paused-initial-fetch-10266-vanilla','query-paused-initial-fetch-10266-python3','transfer-progress-maintenance-v2-vanilla','transfer-progress-maintenance-v2-python3','cached-feed-lifecycle-repair-python3','document-submit-snapshot-vanilla','document-submit-snapshot-python3-eval-v2','draft-autosave-handoff-order-example-vanilla','cached-detail-activation-vanilla']],'limits':['Exact receipt deduplication is conservative; modified/recovered copies may remain. No claim of independent attempts or sampled difficulty.','No valid score means pass rate unavailable, never zero percent. Exceptions remain outside behavioral-failure denominator.','Missing associated score receipts are excluded unless another identical full execution receipt copy contains matching score evidence. All copy paths remain listed.','No standalone score, calibration/control or posthoc rescore is added as a new model attempt.','Case IDs are kept separate; framework/language variants from a common source are not independent sources.','Version hashes are incomplete; pooled case rates may mix source/evaluator versions and prompting protocols.','No statistical significance or confidence-interval claims are made for heterogeneous correlated archived receipts.'],'model_calls':0,'new_scoring_calls':0}
 rates=[r['pass_rate'] for r in case_rows if r['pass_rate'] is not None]
 summary['case_balanced_mean_pass_rate']=statistics.mean(rates)
 summary['median_case_pass_rate']=statistics.median(rates)
 summary['cases_with_multiple_recorded_manifest_or_input_hashes']=sum(r['input_or_manifest_hash_count']>1 for r in case_rows)
 summary['valid_scores_missing_version_hash']=sum(r['unknown_version_scores'] for r in case_rows)
 save('summary.json',summary);save('case-ranking.json',case_rows);save('execution-groups.json',groups)
 print(json.dumps({k:summary[k] for k in ['case_count','cases_with_valid_scores','raw_real_model_receipts','primary_copy_folded','copies_folded','case_rate_distribution','exclusion_reason_counts_not_disjoint']},ensure_ascii=False))
 for title,key in [('HARDEST','hardest_at_least_10_valid'),('EASIEST','easiest_at_least_10_valid'),('PRIOR','prior_research_cases')]:
  print(title,[(r['case_id'],r['passes'],r['valid_scores']) for r in summary[key]])

if __name__=='__main__':main()

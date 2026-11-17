"""Reproducible exact-ID historical and current rates, no new model/scorer calls."""
import csv,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[3];RUN=REPO.parent/OUT.parent.name
HISTORY=REPO.parent/'tempoevo-swe-tempoc-history-20261116';MODELS=('gpt-6.1-sol','gpt-6-sol')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name,v):(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def writecsv(name,rs):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def main():
 selected=list(csv.DictReader((RUN/'selected_100_cases.csv').open(encoding='utf-8-sig')));assert len(selected)==len({r['case_id'] for r in selected})==100
 current=read(RUN/'completion.json');reuse=read(RUN/'reuse.json')['reused'];new=current['new20'];retained=read(Path(current['retained10']['root'])/'completion.json')
 train={r['case_id']:dict(r,root=r['root']) for r in reuse}
 train.update({r['case_id']:r for r in current['new_training_cases']})
 tests={r['case_id']:r for r in new['cases']+retained['cases']}
 history={(r['case_id'],r['model']):r for r in csv.DictReader((HISTORY/'swe242-per-case-model.csv').open(encoding='utf-8-sig')) if r['model'] in MODELS and r['effort']=='medium'}
 ids={r['case_id'] for r in selected};matched=[];counts=Counter();receipt_matches=0;receipt_failures=[];receipt_cache={}
 condition_map={'latent-maintenance':'latent','contract-provided-maintenance':'contract'}
 for line in (HISTORY/'deduplicated-trials.jsonl').open():
  r=json.loads(line)
  if r['case_id'] not in ids or r['model'] not in MODELS or r['effort']!='medium' or r['condition'] not in condition_map:continue
  matched.append(r);condition=condition_map[r['condition']];category=r['category'];counts[r['case_id'],r['model'],condition,category]+=1
  matches=[]
  for path,digest in r['receipt_file_sha256'].items():
   if path not in receipt_cache:
    p=Path(path);receipt_cache[path]=sha(p) if p.exists() else None
   matches.append(receipt_cache[path]==digest)
  if any(matches):receipt_matches+=1
  else:receipt_failures.append(dict(case_id=r['case_id'],model=r['model'],condition=condition,execution_sha256=r['execution_sha256']))
 for cid in ids:
  for model in MODELS:
   r=history.get((cid,model));assert r is not None
   for cond in ('latent','contract'):
    passed=counts[cid,model,cond,'pass'];failed=counts[cid,model,cond,'behavioral_failure']
    assert passed==int(r[cond+'_passes']) and passed+failed==int(r[cond+'_valid']),(cid,model,cond)
    excluded=sum(v for (c,m,k,cat),v in counts.items() if c==cid and m==model and k==cond and cat not in ('pass','behavioral_failure'))
    assert excluded==int(r[cond+'_excluded'])
 percase=[]
 for row in selected:
  cid=row['case_id'];base=dict(case_id=cid,core_case=row['core_case'],split=row['split'],cohort=row['cohort'])
  if row['split']=='training':
   t=Path(train[cid]['root']);state=read(t/'state.json');accepted=state.get('training_accepted') is True
   base.update(current_passed=accepted,current_attempts=len(state['attempts']),first_action_passed=state['attempts'][0]['acceptance_passed'] is True,repair_extraction_unavailable=state['status']=='execution_invalid' and accepted,score_root=str(t),reused_initial26=cid in {r['case_id'] for r in reuse})
  else:
   result=tests[cid];base.update(current_passed=result['gold_passed'],current_attempts=result['actions'],first_action_passed=result['gold_passed'],repair_extraction_unavailable=False,score_root=current['retained10']['root'] if row['cohort']=='retained_regression10' else str(RUN/(RUN.name+'-new20')),reused_initial26=False)
  for model,short in zip(MODELS,('gpt61','gpt6')):
   hist=history[cid,model]
   for cond in ('latent','contract'):
    for metric in ('passes','valid','excluded'):base[short+'_'+cond+'_'+metric]=int(hist[cond+'_'+metric])
    n=int(hist[cond+'_valid']);base[short+'_'+cond+'_rate']=int(hist[cond+'_passes'])/n if n else None
  percase.append(base)
 groups={'all100':percase,'training70':[r for r in percase if r['split']=='training'],'new_test20':[r for r in percase if r['cohort']=='new_test20'],'retained_test10':[r for r in percase if r['cohort']=='retained_regression10'],'test30':[r for r in percase if r['split']=='testing']}
 def historical(rs,short,cond):
  valid=[r for r in rs if r[short+'_'+cond+'_valid']>0];k=sum(r[short+'_'+cond+'_passes'] for r in valid);n=sum(r[short+'_'+cond+'_valid'] for r in valid)
  return dict(passes=k,valid_trials=n,excluded_trials=sum(r[short+'_'+cond+'_excluded'] for r in rs),covered_cases=len(valid),total_cases=len(rs),macro_case_rate=sum(r[short+'_'+cond+'_rate'] for r in valid)/len(valid) if valid else None,pooled_trial_rate=k/n if n else None,missing_valid_case_ids=[r['case_id'] for r in rs if r[short+'_'+cond+'_valid']==0])
 summary={};flat=[]
 for group,rs in groups.items():
  h={model:{cond:historical(rs,short,cond) for cond in ('latent','contract')} for model,short in zip(MODELS,('gpt61','gpt6'))}
  summary[group]=dict(cases=len(rs),historical=h)
  if group!='all100':summary[group]['current']=dict(passed=sum(r['current_passed'] for r in rs),cases=len(rs),rate=sum(r['current_passed'] for r in rs)/len(rs),first_action_passed=sum(r['first_action_passed'] for r in rs),first_action_rate=sum(r['first_action_passed'] for r in rs)/len(rs),maximum_actions=3 if group=='training70' else 1)
  for model in MODELS:
   for cond in ('latent','contract'):flat.append(dict(group=group,model=model,condition=cond,**{k:v for k,v in h[model][cond].items() if k!='missing_valid_case_ids'}))
 assert summary['training70']['current']['passed']==65 and summary['training70']['current']['first_action_passed']==61
 assert summary['new_test20']['current']['passed']==19 and summary['test30']['current']['passed']==27
 writecsv('per-case.csv',percase);writecsv('historical-rates.csv',flat);dump('summary.json',summary)
 cores=[]
 for core in sorted({r['core_case'] for r in percase}):
  rs=[r for r in percase if r['core_case']==core];row=dict(core_case=core,cases=len(rs))
  for group,key in [('training70','training'),('new_test20','new_test'),('retained_test10','retained_test')]:
   subset=[r for r in groups[group] if r['core_case']==core];row[key+'_passed']=sum(r['current_passed'] for r in subset);row[key+'_cases']=len(subset)
  for short in ('gpt61','gpt6'):
   for cond in ('latent','contract'):
    h=historical(rs,short,cond);row[short+'_'+cond+'_macro']=h['macro_case_rate'];row[short+'_'+cond+'_covered']=h['covered_cases']
  cores.append(row)
 writecsv('per-core.csv',cores)
 audit=dict(selected100_unique=True,training70_unique=len(train)==70,test30_unique=len(tests)==30,train_test_disjoint=not set(train)&set(tests),matched_historical_trials=len(matched),matched_original_receipt_digests=receipt_matches,receipt_paths_checked=len(receipt_cache),missing_or_changed_receipts=receipt_failures,summary_reconciled_with_raw_trials=True,model_calls=0,scorer_executions=0,source_files={str(p):sha(p) for p in [RUN/'selected_100_cases.csv',RUN/'completion.json',RUN/'reuse.json',RUN/'final-memory-snapshot.json',Path(current['retained10']['root'])/'completion.json',HISTORY/'swe242-per-case-model.csv',HISTORY/'deduplicated-trials.jsonl',Path(__file__)]},current_model='gpt-6.1-sol / medium',history_input_version_equivalence='not recertified; derived RxJS current public projection differs from historical full repository',contract_baseline='provided benchmark Contract, not current automatically generated Contract',current_test_bank=dict(new20=73,retained10=39),initial_training_bank='historical39 plus training-only provisional;26 accepted older records reused with different historical seeds/checks',historical_invalid_or_unscored_records='excluded, never counted as behavioral failures',new20_gpt61_latent_baseline='20/20 cases,93/93 valid historical trials passed; no evidence of experience gain from current19/20 alone')
 dump('audit.json',audit)
 (OUT/'matched-historical-trials.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in matched))
 lines=['# 固定100例：历史基线与当前训练/测试通过率','', '100个精确case ID：70训练＋20新测试＋10保留测试。训练复用26条历史成功记录；测试复用旧10例8/10成绩。初始39条历史经验并非只来源于这70例；新20冻结73条，旧10冻结39条。','', '历史按case等权宏平均，先分别计算每case的有效试次通过率再平均；缺失case不补0。pooled_trial_rate及完整通过数/有效次数见historical-rates.csv。历史跨批次统计，不是同配置统一复跑；给定Contract不能当作Auto-Contract消融。','', '|集合|gpt6.1 latent（覆盖）|gpt6.1 给定Contract（覆盖）|gpt6 latent|gpt6 给定Contract|','|---|---:|---:|---:|---:|']
 names={'all100':'全部100','training70':'训练70','new_test20':'新测试20','retained_test10':'保留测试10','test30':'测试合计30'}
 for g in groups:
  h=summary[g]['historical'];values=[]
  for model in MODELS:
   for cond in ('latent','contract'):
    a=h[model][cond];values.append(f"{a['macro_case_rate']:.1%}（{a['covered_cases']}/{a['total_cases']}）" if model==MODELS[0] else f"{a['macro_case_rate']:.1%}")
  lines.append('|'+names[g]+'|'+'|'.join(values)+'|')
 lines+=['', '|当前集合|首个Action通过|最终通过|','|---|---:|---:|']
 for g in ['training70','new_test20','retained_test10','test30']:
  a=summary[g]['current'];lines.append(f"|{names[g]}|{a['first_action_passed']}/{a['cases']}（{a['first_action_rate']:.1%}）|{a['passed']}/{a['cases']}（{a['rate']:.1%}）|")
 lines+=['', '**重要：新20例的当前模型历史latent为93/93有效试次通过，覆盖全部20例；当前19/20不能证明经验提升。此划分的新测试侧明显比训练侧容易。综合两模型选题、测试暴露排除和旧10保留约束不等于对当前模型难度均衡的测试集。**','', '训练最多3个Action、测试仅1个Action，二者分别报告，不混成单一性能指标。测试30合计包含不同时间、不同经验快照的两组。工具/评分无效不算行为失败；当前20例均正常完成评分。','', f"原始历史试次核对：{len(matched)}条，{receipt_matches}条至少有1份原始回执SHA匹配，{len(receipt_failures)}条缺失/变动。没有新模型调用或评分。",'', '## 逐core结果','', '|core|例数|训练|新测试|保留测试|','|---|---:|---:|---:|---:|']
 for a in cores:
  fmt=lambda k:f"{a[k+'_passed']}/{a[k+'_cases']}" if a[k+'_cases'] else '—'
  lines.append(f"|{a['core_case']}|{a['cases']}|{fmt('training')}|{fmt('new_test')}|{fmt('retained_test')}|")
 (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(dict(current={g:v.get('current') for g,v in summary.items() if 'current' in v},historical_trial_audit={k:audit[k] for k in ['matched_historical_trials','matched_original_receipt_digests','receipt_paths_checked','missing_or_changed_receipts']}),ensure_ascii=False,indent=2))
if __name__=='__main__':main()

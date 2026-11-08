import hashlib,json,random,shutil,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parent.parent;OLD=R/'research/contract-repair-frozen-batch-v1-20261108'
IDS=['transfer-progress-composition-v4-vanilla','audit-commit-attribution-vanilla']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not (O/'cohort.json').exists()
 previous=json.loads((OLD/'cohort.json').read_text())['cases'];cases=[]
 for cid in IDS:
  c=next(c for c in previous if c['case']==cid);d=O/'materials'/cid
  assert not list(Path(c['source_case']).rglob('AGENTS.md'))
  shutil.copytree(OLD/'materials'/cid,d)
  assert not (d/'M.frozen.md').exists()
  assert all(sha(d/'candidate'/f)==h for f,h in c['candidate_files'].items())
  assert all(sha(Path(c['source_case'])/'base'/f)==h for f,h in c['candidate_files'].items())
  assert sha(Path(c['source_case'])/'case.json')==c['case_manifest_sha256']
  assert all(sha(Path(c['source_case'])/'oracle'/f)==h for f,h in c['oracle_files'].items())
  c['calibration_reused_from']=str(OLD/'cohort.json');c['calibration_reused_exact_bytes']=True
  c['reason_this_batch']='Historical credible behavioral failures in failure-mechanism-diagnosis; event admission/decode/reentrant ownership' if cid==IDS[0] else 'Different independent_unit_id and mechanism: Promise entry snapshot/audit attribution; existing reliable calibrated scoring; easier preservation control'
  c['selection_not_by_current_results']=True;cases.append(c)
 save(O/'cohort.json',{'cases':cases,'source_relations':'transfer-retry-abort-handoff and audit-commit-attribution are distinct authored source units, not renamed variants; both historically research-exposed. Neither derived E1, whose source is old U2. Not independent generalization.','new_case_search_after_freeze':False})
 metric=json.loads((OLD/'metric-spec.json').read_text());save(O/'metric-spec.json',{k:metric[k] for k in IDS})
 scope=json.loads((OLD/'source-scope.json').read_text());save(O/'source-scope.json',[c for c in scope if c['case'] in IDS])
 exposure=json.loads((OLD/'exposure-index.json').read_text());save(O/'exposure.json',{'scope':exposure['interpretation'],'cases':{k:exposure['matches'][k] for k in IDS},'historical_failure_evidence':['research/failure-mechanism-diagnosis-v1-20261106/REPORT.md','research/react-skill-evolution-v1-20261106/REPORT.md'],'E1_source':'U2 only; exact approved v1 reused'})
 common='\n\n完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。\n'
 warning='以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。\n'
 skill=(O/'contract_extraction_K1.md').read_text();experience=(O/'EXPERIENCE.md').read_text()
 for c in cases:
  cid=c['case'];d=O/'materials'/cid;p=O/'prompts'/cid;p.mkdir(parents=True)
  task=(d/'task.md').read_text()
  extract=task+'\n\n只读取 /workspace 的候选源码和文档，不修改或执行候选程序，不访问历史、评分、人工Contract或网络。只读shell支持pwd/ls/rg/cat/nl/sed -n/head/tail/wc，以及用echo/printf标记文件名的普通for文件读取循环；只读路径限 /workspace。\n\n'+skill+'\n\n最终返回JSON，唯一字段report，最多6000个Unicode字符。严格使用四个栏目标题：\n1. 可确认的 Contract\n2. 每条的条件、效果、来源及依据\n3. 不能确认的候选要求\n4. 建议验证范围\n'
  (p/'extraction.md').write_text(extract);(p/'N.md').write_text(task+common)
  (p/'H.md').write_text(task+'\n\n'+warning+(d/'H.md').read_text()+common)
  m=task+'\n\n'+warning+'{{FROZEN_AUTOMATIC_CONTRACT}}'+common
  (p/'M.template.md').write_text(m);(p/'E.template.md').write_text(m+'\n<experience>\n'+experience+'\n</experience>\n')
 save(O/'prompt-equivalence.json',{'labels':{'N':'无契约','H':'人工整理契约参考','M':'自动契约','E':'E1-v1经验增强'},'common':common,'warning':warning,'experience_stage':'repair only','M_and_E_use_same_frozen_Contract':True,'extractor_skill_unchanged':True,'H_status':'Reuse source-grounded manually curated AI-assisted reference from prior batch; not independently human-authored or reviewed. No human standard changed.'})
 rng=random.Random(2026110802);slots=[]
 for i,cid in enumerate(IDS,1):
  slots.append({'slot':'s%02d-x'%i,'case':cid,'phase':'extract','condition':'extraction','repeat':None})
  for repeat in [1,2]:
   groups=['N','H','M','E'];rng.shuffle(groups)
   for g in groups:slots.append({'slot':'s%d-r%d-%s'%(i,repeat,g),'case':cid,'phase':'repair','condition':g,'repeat':repeat})
 save(O/'schedule.json',{'seed':2026110802,'seed_role':'order only, not model sampling','slots':slots,'maximum_top_level_sessions':18,'maintenance':16,'extraction':2,'concurrency':1,'second_case_requires_first_case_execution_validity_gate':True})
 save(O/'budget.json',{'cases':2,'maintenance_sessions':16,'extraction_sessions':2,'total_sessions':18,'repair_requests_per_session':24,'extraction_requests_per_session':12,'total_requests_reserved':408,'seconds_per_session':600,'total_session_seconds_reserved':10800,'final_report_characters_per_session':6000,'stdout_archive_bytes_per_session':16777216,'stdout_limit_scope':'CLI JSON event stdout; preserves partial output if exceeded','token_output_hard_cap':'No verified native all-reasoning token cap; final-report schema/validation cap is 6000 Unicode characters. Do not claim a token cap.','automatic_retries':0,'extra_model_prerun':0,'GEPA':0,'reflection':0,'skill_rewrite':0,'currency_cost':None,'estimate_basis':'Prior U2 gpt-5.6-terra/medium valid repairs 120-172s, 9-12 requests; complex transfer may use more. Full reserved limits, not historical averages, bound all 18 slots.'})
 print('Prepared exactly two cases, 2 extracts + 16 maintenance; old dispatchers excluded.')
if __name__=='__main__':main()

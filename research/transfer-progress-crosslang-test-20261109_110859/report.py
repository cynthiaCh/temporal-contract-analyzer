"""Read-only reporting of every fixed test slot, including invalid/unstarted."""
import ast,json,subprocess
from pathlib import Path
from archive import save,sha
from feedback import feedback
from report_common import aggregate
from pilot_test import A,P,D,ORDER,read,runner
TARGETS=['progress-reopen-during-start','progress-hide-emit-during-start','progress-switch-emit-during-start']

def report():
 actual=read(A/'actual-schedule.json',[]);standards=read(A/'materials/T/standards.json');original=read(A/'calibration/T/original/stdout.json')
 rows=[];cost_rows=[]
 for index,name in enumerate(ORDER):
  rec=next((x for x in actual if x['name']==name),None);arc=A/'runs'/('session-%02d'%(index+1))/'archive'
  if rec:cost_rows.append({'phase':rec['phase'],'arm':name[0] if name!='T-analysis' else None,'usage':read(arc/'usage.json'),'seconds':rec.get('seconds')})
  if index==0:continue
  valid=bool(rec and rec.get('scoring_admissible') and rec.get('scoring_status')=='COLLECTED' and rec.get('scored_candidate_unchanged') and rec.get('score_result',{}).get('score_valid'))
  score=read(arc/'score/stdout.json') if valid else None
  fb=feedback(original,[score],standards)['runs'][0] if score else None
  rows.append({'name':name,'arm':name[0],'repeat':int(name[1]),'started':bool(rec),'valid_scoring':valid,
   'archive':str(arc) if rec else None,'whole_task_pass':score['verdict']=='PASS' if valid else None,
   'verdict':score['verdict'] if valid else None,'satisfied_relations':len(fb['actual_successes']) if fb else None,
   'total_relations':len(standards),'behavior_vector':score['observed_effects'] if valid else None,
   'target_behaviors':{k:score['observed_effects'].get(k) if valid else None for k in TARGETS},
   'improvements_over_original':[x['effect'] for x in fb['improvements']] if fb else None,
   'original_successes_lost':[x['effect'] for x in fb['regressions']] if fb else None,
   'full_feedback':fb,'usage':read(arc/'usage.json') if rec else None,'seconds':rec.get('seconds') if rec else None,
   'failure_class':rec.get('failure_class') if rec else None,'scoring_status':rec.get('scoring_status') if rec else None})
 def arm_summary(arm):
  subset=[r for r in rows if r['arm']==arm];valid=sum(r['valid_scoring'] for r in subset);started=sum(r['started'] for r in subset)
  passed=sum(r['whole_task_pass'] is True for r in subset)
  return {'planned':2,'started':started,'valid':valid,'invalid':started-valid,'unstarted':2-started,'whole_task_passes':passed,'denominator':valid,
   'pass_rate':passed/valid if valid else None,'costs':aggregate([r for r in cost_rows if r['arm']==arm])}
 arms={x:arm_summary(x) for x in ['A','B']}
 costs={'preanalysis':aggregate([r for r in cost_rows if r['phase']=='extract']),
  'AUTO':arms['A']['costs'],'ROUTED':arms['B']['costs'],'new_total':aggregate(cost_rows),
  'training_development_reference_only_not_in_test_cost':read(D/'costs.json')['new_total'],
  'engineering':{'tokens':None,'money':None},'money':None}
 comparisons=[]
 for b in rows:
  if b['arm']!='B' or not b['valid_scoring']:continue
  for a in rows:
   if a['arm']!='A' or not a['valid_scoring']:continue
   fb=feedback(read(Path(a['archive'])/'score/stdout.json'),[read(Path(b['archive'])/'score/stdout.json')],standards)['runs'][0]
   comparisons.append({'B':b['name'],'A':a['name'],'improvements':[x['effect'] for x in fb['improvements']],
    'regressions':[x['effect'] for x in fb['regressions']],'retained_successes':[x['effect'] for x in fb['retained_original_successes']],
    'unknown':fb['unknown']})
 route=read(A/'testing/route.json');prompt=read(A/'testing/prompt-difference.json')
 subset='hit' if route and route.get('selected') else 'fallback' if route else 'unrouted'
 summary={'scope':'One exposed same-source cross-language exploratory test case, two repetitions per condition; not independent generalization or statistical stability',
  'case':read(A/'case.json')['case'],'status':'stopped' if (A/'stop.json').exists() else 'completed' if len(actual)==5 else 'incomplete',
  'stop':read(A/'stop.json'),'actual_schedule':[r['name'] for r in actual],'planned_order':ORDER,
  'sessions':{'planned':5,'started':len(actual),'unstarted':5-len(actual)},'arms':arms,'runs':rows,
  'classification':read(A/'derived/T/analysis.json'),'AI_assisted_semantic_review':read(A/'derived/T/semantic-review.json'),
  'route':route,'prompt_difference':prompt,'subsets':{'selected_subset':subset,'hit':arms if subset=='hit' else None,'fallback':arms if subset=='fallback' else None},
  'all_valid_B_vs_A_descriptive_comparisons':comparisons,'costs':costs,
  'production_update':False,'reflection_calls':0,'extra_judge_calls':0,'new_calibration_calls':0,'historical_score_reruns':0,
  'training_not_in_test_denominator':True,'no_next_batch':True}
 if len(actual)==5 and all(r['valid_scoring'] for r in rows):
  same_vectors=all(r['behavior_vector']==rows[0]['behavior_vector'] for r in rows)
  summary['conclusion']={'actual_experience_delivered':subset=='hit','all_vectors_identical':same_vectors,
   'observed_incremental_behavior_gain':any(c['improvements'] for c in comparisons),
   'observed_behavior_regression':any(c['regressions'] for c in comparisons),
   'interpretation':'Both AUTO repetitions already pass all original checks; no additional pass evidence for experience on this case. This neither proves equivalence nor universal ineffectiveness.',
   'cost_differences_are_descriptive_only':True}
  save(A/'execution-audit.json',{'source_review':'AI-assisted execution-agent inspection, no new test or scorer call',
   'observed_changes':'All four attach the listener before startup, check current admission before decode and retain audit for already admitted delayed completion. A1 adds attempt-aborted admission gating; B2 additionally guards visible completion. Full patches and binary cache files are preserved.',
   'B1_A2_source_AST_equal_ignoring_comments_and_locations':ast.dump(ast.parse((A/'runs/session-02/archive/final-candidate/src/workflow.py').read_text()))==ast.dump(ast.parse((A/'runs/session-04/archive/final-candidate/src/workflow.py').read_text())),
   'all_evaluated_vectors_equal':same_vectors,'no_claim_of_unevaluated_implementation_equivalence':True,
   'validation_bytecode':'All four final snapshots include validation-generated src/__pycache__/workflow.cpython-38.pyc; retained in final candidates and hash manifests, never inherited by later slots.',
   'new_tests_or_scoring_invocations':0})
 save(A/'summary.json',summary);save(A/'costs.json',costs);save(A/'comparisons.json',comparisons)
 save(A/'behavior-vectors.json',{r['name']:r['behavior_vector'] for r in rows})
 save(A/'completion.json',{'status':summary['status'],'started':len(actual),'valid_test_scores':sum(r['valid_scoring'] for r in rows),'no_more_model_calls':True})
 lines=[f"状态：{summary['status']}。固定测试例 {summary['case']}；维护启动 {sum(r['started'] for r in rows)}/4，有效评分 {sum(r['valid_scoring'] for r in rows)}。",'',
  f"完整沿用 Python 案例的 {len(standards)} 项原关系评分，不把训练例的20项删减或套用到此例。",'',
  '经验为 locked-applicability 开发批次的规则正文，原文未改，登记类别来自原训练预分析。测试预分析没有收到该类别、开发轨迹、经验、历史成绩或评分材料。',
  f"实际测试分类：{(summary['classification'] or {}).get('primary_class')}；路由：{json.dumps(route,ensure_ascii=False)}。",'',
  '类别、源码证据和每项前提判断见 derived/T/analysis.json、semantic-review.json 与 testing/route.json；核查为执行 Agent 的 AI 辅助核查，不是独立人工批准。',
  f"A/B提示相同：{(prompt or {}).get('identical')}。若回退，重复运行差异不能归因为经验，亦不证明经验效果等价。",'',
  '|条件|计划|启动|有效|无效|未启动|整题通过/有效|','|---|---|---|---|---|---|---|']
 for name,v in arms.items():lines.append(f"|{name}|2|{v['started']}|{v['valid']}|{v['invalid']}|{v['unstarted']}|"+(f"{v['whole_task_passes']}/{v['valid']}" if v['valid'] else '通过率不可计算')+'|')
 lines+=['','|槽位|满足关系|整题|相对原始候选新增通过|丢失原通过|','|---|---|---|---|---|']
 for r in rows:lines.append('|'+r['name']+'|'+(str(r['satisfied_relations'])+'/'+str(len(standards)) if r['valid_scoring'] else '未评分')+'|'+str(r['whole_task_pass'])+'|'+str(r['improvements_over_original'])+'|'+str(r['original_successes_lost'])+'|')
 lines+=['','|完整行为向量（按原期望判断）|B1|A1|A2|B2|','|---|---|---|---|---|']
 for rel in standards:
  key=rel['effect'];cells=[]
  for r in rows:
   v=(r['behavior_vector'] or {}).get(key);cells.append('未知' if type(v) is not bool else '通过' if v==rel['expected'] else '失败')
  lines.append('|'+key+'|'+'|'.join(cells)+'|')
 lines+=['','全部有效B与A的逐项描述性比较：','```json',json.dumps(comparisons,ensure_ascii=False,indent=2),'```',
  '',f'本案例属于 {subset} 子集；全体结果与该子集相同，另一个子集没有案例，不补零效果。',
  '', '成本（开发费用仅列参考，未计入本轮新增）：','```json',json.dumps(costs,ensure_ascii=False,indent=2),'```',
  '', '原始候选和每槽独立工作区、真实提示、模型原始输出、工具/请求事件、最终源码、Python生成补丁、原评分和计量均归档。完整反馈在 summary.json，每次完整原始检查及事件轨迹在 archive/score/stdout.json。',
  '预分析摘要和运行器在首次调用前冻结；Contract、分类及路由结果、两组完整提示在首次维护前冻结。没有测试后反思、额外候选、重试、补跑或评分规则改变。',
  '两次重复只作描述。该案例已经暴露且与训练来自同一来源单元；开发通过不并入测试分母，本轮不能证明独立泛化、统计显著或稳定效果。',
  '未创建提交、修改历史或更新生产经验库。本批结束即停止。']
 if summary.get('conclusion'):
  lines+=['','四次完整行为向量相同，均整题通过；原三项启动内部关系在两组中全部通过，未观察到新增通过或行为退步。由于 AUTO 两次已全部修对，本轮不提供经验的额外行为收益证据，也不证明两组等价或经验普遍无效。',
   f"成本描述：A {arms['A']['costs']['requests_started']}请求/{arms['A']['costs']['known_usage_subtotal']['total_tokens']} tokens；B {arms['B']['costs']['requests_started']}请求/{arms['B']['costs']['known_usage_subtotal']['total_tokens']} tokens。两次重复及固定顺序不足以把这次成本差异解释为稳定节省。",'实际源码及验证字节码差异见 execution-audit.json；评分向量相同不等于所有未覆盖行为或实现完全相同。']
 if summary['stop']:lines+=['','具体停止：'+json.dumps(summary['stop'],ensure_ascii=False)]
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 (A/'COMMIT_MESSAGE.txt').write_text('research: evaluate frozen progress experience on the Python sibling\n\nFreeze the exact evidence-supported rule body and conservative routing inputs.\nAnalyze the current Python candidate once, then run fixed B1/A1/A2/B2 slots.\nPreserve all vectors, patches, usage, failures and unstarted slots with unchanged scoring.\nKeep source exposure and same-unit transfer limits explicit; do not update production experience.\n')
 initial=read(A/'initial-state.json');assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==initial['HEAD']
 assert subprocess.check_output(['git','diff'],text=True)==initial['diff'] and subprocess.check_output(['git','diff','--cached'],text=True)==initial['cached_diff']
 checked=[];errors=[]
 for n in ['initial-freeze.json','test-freeze.json']:
  if (A/n).exists():
   try:runner.verify(read(A/n)['files']);checked.append(n)
   except Exception as e:errors.append(repr(e))
 archives=[]
 for rec in actual:
  root=A/'runs'/rec['slot']/'archive';n=0
  for line in (root/'ARTIFACTS.sha256').read_text().splitlines():
   h,name=line.split('  ',1)
   if sha(root/name)!=h:errors.append('Archive mismatch: '+str(root/name))
   n+=1
  archives.append({'slot':rec['slot'],'files_checked':n})
 save(A/'integrity.json',{'frozen_manifests_verified':checked,'archive_manifests':archives,'errors':errors,'historical_inputs_and_HEAD_unchanged':not errors})
 save(A/'provenance.json',{'training_experience_source':str(D),'test_material_source':str(P/'materials/T'),'historical_sources_pinned':'initial-state.json',
  'calibration':'11 exact-version receipts reused; no rerun','source_ids':'Raw model span IDs, deterministic references; no claim rewriting',
  'registry_conversion':'Exact experience text/requires/excludes plus existing training class; metadata excluded from route arguments',
  'new_code':['pilot_test.py','report.py'],
  'helper_origins':{name:{'source_sha256':h,'current_sha256':sha(A/name),'byte_identical':sha(A/name)==h}
                    for name,h in read(A/'initial-state.json')['helper_sources'].items()},
  'test_fixture_adaptations':'Only test_citations.py/test_source_proof.py point at pinned historical fixtures and the current controller; runtime helpers are unchanged.'})
 hashes={str(f.relative_to(A)):sha(f) for f in A.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(hashes.items())))
 print(json.dumps({'status':summary['status'],'arms':arms,'scores':{r['name']:r['satisfied_relations'] for r in rows},'route':subset,'costs':costs['new_total'],'files':len(hashes)},ensure_ascii=False))
 if errors:raise RuntimeError(errors)

if __name__=='__main__':report()

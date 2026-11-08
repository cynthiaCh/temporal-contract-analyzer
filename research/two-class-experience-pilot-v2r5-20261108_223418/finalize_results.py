"""Reconcile reused preparation, all test slots and old stopped costs; no model calls."""
import json,hashlib,time
from pathlib import Path
from usage import summarize_ledger
A=Path(__file__).resolve().parent
V2=A.parent/'two-class-experience-pilot-v2-20261108_205648'
R1=A.parent/'two-class-experience-pilot-v2r1-20261108_215007'
R3=A.parent/'two-class-experience-pilot-v2r3-20261108_221141'
R4=A.parent/'two-class-experience-pilot-v2r4-20261108_221657'

def read(p,default=None):return json.loads(p.read_text()) if p.exists() else default
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def aggregate_cost(records):
 ledgers=[read(folder/'meter/ledger.json',{}) for folder in records]
 missing=sum(not isinstance(x.get('started'),int) for x in ledgers)
 combined={'started':sum(x.get('started') or 0 for x in ledgers),'completed':sum(x.get('completed') or 0 for x in ledgers),'events':[e for x in ledgers for e in (x.get('events') or [])]}
 result=summarize_ledger(combined);result.update(sessions=len(records),request_count_unknown_sessions=missing,monetary_cost=None)
 if missing:result['total_usage']=None;result['usage_incomplete']=True;result['requests_started']=None
 return result

def main():
 assert (A/'completion.json').exists() or (A/'stop.json').exists(),'only finalize a terminal run'
 import report_v2
 report_v2.main()
 summary=read(A/'summary.json')
 prep=[(V2,'D1-preanalysis-v2','extract','historical invalid nested JSON'),(R1,'D1-preanalysis-v2r1','extract','historical safe-read false positive'),(R3,'D1-preanalysis-v2r3','extract','correct automatic object reused after source-based scope-limit review'),
       (R4,'D1-AUTO-v2r4-1','repair','new controlled AUTO baseline'),(R4,'D1-AUTO-v2r4-2','repair','new controlled AUTO baseline'),(R4,'D1-reflection-v2r4','reflect','one unedited candidate rejected on source policy'),(R4,'T1-preanalysis-v2r4','extract','correct automatic object reused after source-based distinction review')]
 current=read(A/'actual-schedule.json',[])
 all_records=[(d/'runs'/s/'archive',phase) for d,s,phase,note in prep]+[(A/'runs'/r['slot']/'archive',r['phase']) for r in current]
 summary['v2_family_cost']=aggregate_cost([p for p,phase in all_records])
 summary['v2_family_cost_by_role']={name:aggregate_cost([p for p,phase in all_records if phase==code]) for name,code in [('extraction','extract'),('reflection','reflect'),('maintenance','repair')]}
 summary['preparation_provenance']=[{'source':str(d/'runs'/s/'archive'),'slot':s,'phase':phase,'handling':note,'raw_receipt_status':read(d/'runs'/s/'archive/receipt.json',{}).get('status'),'usage':read(d/'runs'/s/'archive/usage.json')} for d,s,phase,note in prep]
 summary['D1_development_reused']={'public_Contract_sha256':sha(A/'derived/D1/automatic-contract.md'),'baseline_source':str(R4),'baseline_slots':['D1-AUTO-v2r4-1','D1-AUTO-v2r4-2'],'new_baselines_on_corrected_Contract':True,
  'baseline_scores':[read(R4/'runs'/f'D1-AUTO-v2r4-{n}'/'archive/score/stdout.json') for n in [1,2]],
  'reflection_source':str(R4/'runs/D1-reflection-v2r4/archive'),'candidate':read(A/'development/experience-candidate.json'),'candidate_policy_review':read(A/'development/candidate-semantic-review.json'),'admission':read(A/'development/admission.json'),
  'development_revalidations_started':0,'revalidation_skip_reason':'Confirmed unsupported business policy, candidate excluded rather than used in paid validation. No second reflection or manual correction.'}
 summary['semantics_resolution']={'original_v1_direction_error':'confirmed from Repair-task context; must-not was an interpretation, not original verbatim wording','original_v1_reflection_attribution_error':'confirmed by actual no-live-at-entry false/expected true and call trace; unique generation cause unknown',
  'correct_outputs_reused':['D1 R3','T1 R4','D2 v1','T2 v1'],'automatic_text_edited':False,'model_notes_edited':False,
  'model_self_labels_are_not_oracle':True,'source_review':{alias:read(A/'derived'/alias/'semantic-review.json') for alias in ['D1','D2','T1','T2']},
  'library_empty_reason':'T4 sole candidate has confirmed unsupported policy; T3 not searched after prior two AUTO passes. Empty library is a valid result.'}
 summary['historical_v1_cost_not_charged_twice']=read(A.parent/'two-class-experience-pilot-20261108_200017/summary.json',{}).get('costs')
 summary['no_experience_effect_estimate']=True
 summary['empty_library_prompts_identical_all_cases']=all(t['prompt_correspondence']['identical'] for t in summary['tests'].values())
 summary['actual_test_counts']={arm:{k:summary['aggregate']['all'][arm][k] for k in ['planned','started','valid_scored','invalid_or_unscored_started','unstarted','whole_task_passes']} for arm in ['A','B']}
 anomalies=[]
 for row in current:
  if not row.get('infrastructure_valid'):
   root=A/'runs'/row['slot']/'archive'
   anomalies.append({'slot':row['slot'],'source':str(root),'original_service_errors':read(root/'service-errors.json'),'archive_status':row.get('archive_status'),'candidate_complete':row.get('candidate_complete'),'scoring_status':row.get('scoring_status'),'usage':read(root/'usage.json'),'partial_answer_present':(root/'partial-answer.txt').exists(),'partial_candidate_preserved':(root/'final-candidate').exists(),'patch_preserved':(root/'patch.diff').exists(),'behavior_verdict':None})
 summary['runtime_anomalies']=anomalies
 target_keys={'T1':['offline-detach-false','offline-detach-true','offline-detach-always','offline-nonconsuming-detach','detach-after-resume-queued','cached-paused-background','cached-later-consumption'],'T2':['quiet-burst','second-burst','reentrant-switch-on-flush','reentrant-close-on-flush']}
 summary['task_relation_observations']={alias:{row['slot']:{k:(row['effects'].get(k) if row['effects'] is not None else None) for k in keys} for row in summary['tests'][alias]['runs']} for alias,keys in target_keys.items()}
 summary['task_relation_observations_note']='Existing evaluator relations displayed to explain original task and preservation losses; not a newly defined success metric and not used for selection/routing.'
 save(A/'summary.json',summary)
 save(A/'exception-records.json',anomalies)
 # Human-readable focused report, with all individual vectors preserved.
 lines=['# 原定两案例A/B工具试验：最终结果','', '**状态：'+summary['status']+'**。最终测试修订只运行固定8个维护槽位；准备模型输出和全部停止记录保留并单独计费。','',
 '本批已启动6/8槽，5个有效原评分全部UNDERREACH，1个服务断流无效未评分，2个未启动。有效评分A=2、B=3；对应整题通过A=0/2、B=0/3。空经验库使A/B逐字相同，没有经验效果估计。归档在实际null用量断流下正常完成。', '', '## Task 1：实现、修复与语义审计','',
 '复用Python归档、隔离和host-owned请求计量，修复null用量、内嵌JSON字符串上限、角色schema绑定及安全只读重定向。原始服务/错误/部分输出与归档状态分开保存；仅完整候选准入评分。49项离线检查、四例namespace/JS/Python正文读取、两种历史失败回放及16条真实读取请求验证通过。原评分器/原候选/依赖/生产经验库/全局配置未改，没有提交。',
 '原D1/T1方向错误确认：Repair后的错误现象被改成保留义务；原文没有字面must-not，旧报告的该措辞属于解释。原反思声称第一次补丁已修复离线退出，与实际检查/调用记录相反。为何模型作此错误归因仍未知。反馈接口漏读checks而只读assertions、把原始成功与保留成功混义，均已修复；不能说原布尔向量本身错误。',
 'D1新自动对象明确区分共享消费记录与单次取消资源；T1新对象方向、归属和引用可核对。其自评栏中的“冲突/未知”有些是资源-记录区别、当前缺陷-预期行为区别或未穷尽路径声明，并非互斥业务政策。模型原文和自评列表全部保留；由当前可见任务/源码的执行Agent否决记录判定是否存在核心冲突，不把自评栏名当真值，也不手工改写自动材料。真实核心未知仍必须拒绝。',
 '四例均为既有暴露：D1/T1共享query-paused-initial-fetch-10266，D2/T2共享debounced-submit-flush；T2既往求解和事后评分v2保持披露。44份校准按原始base/task/oracle摘要精确匹配复用；Node18.17与JS manifest Node16差异披露，Python3.8.10匹配。没有连接模型预跑，没有第三例。','',
 '## Task 2：开发、拒绝入库与冻结测试','',
 'D1以修正后公共Contract从原始候选独立运行两次新AUTO，均27/29行为通过，整题UNDERREACH。两次均保留缓存暂停后台/后续消费失败；反馈含每次75条实际检查、7条失败检查、完整原有成功/改善/退步，没有从断言名称推断唯一原因。v1错误Contract下的基线不混入受控比较。',
 '唯一一次新反思生成的候选未人工润色，但明确要求消费记录归属单次执行、并泛化结算所有已接纳未开始工作，与当前共享记录/缓存保留政策冲突。因此按“无确认无据业务政策”的准入条件拒绝，在付费回验前剔除，未生成第二候选或借用旧E2。两次开发回验上限未消耗；这不是恢复“两次全对”门槛。候选原文/原始输出/完整拒绝依据在development/。',
 'D2/T3在原开发中两次AUTO已通过，本次不开展额外T3经验搜索，正确Contract保持逐字复用。经验库为空，源修订在T1预分析前已锁定；空库仍执行固定8槽。所有测试Contract、源审查、路由、预算和调度在首个测试维护前再次冻结。测试不学习。', '',
 '| 测试例 | 实际机制主类 | 路由 | A整题/有效评分 | B整题/有效评分 |', '|---|---|---|---|---|']
 for alias,t in summary['tests'].items():
  counts={arm:[sum(r['verdict']=='PASS' for r in t['runs'] if r['arm']==arm and r['valid_score']),sum(r['valid_score'] for r in t['runs'] if r['arm']==arm)] for arm in ['A','B']}
  lines.append(f"|{alias}|{t['analysis']['primary_class']}|{t['route']['reason']}|{counts['A'][0]}/{counts['A'][1]}|{counts['B'][0]}/{counts['B'][1]}|")
 lines+=['','A/B对每个案例提示字节相同，因为没有可投放经验。所有结果均保留；相同提示的随机差异不能归因于经验，也不能证明经验效果等价。当前模型都是gpt-5.6-terra/low、24请求/600s、相同工具、并发1，从同一原始候选独立开始。种子2026110804只固定块内顺序，不控制采样。','']
 for alias,t in summary['tests'].items():
  lines+=['### '+alias+' 证据与完整结果','','分类源证据：'+json.dumps(t['analysis']['evidence'],ensure_ascii=False),'路由：'+json.dumps(t['route'],ensure_ascii=False),
   '前提状态：'+json.dumps(t['analysis']['facts'],ensure_ascii=False),'提示对应：'+json.dumps(t['prompt_correspondence'],ensure_ascii=False),'',
   '| slot | 有效 | 整题 | 请求 | 秒 | 相对原始退步 |','|---|---|---|---|---|---|']
  for r in t['runs']:lines.append(f"|{r['slot']}|{r['valid_score']}|{r['verdict']}|{(r['cost'] or {}).get('requests_started')}|{(r['cost'] or {}).get('session_seconds_known_subtotal')}|{r['regressions_vs_original']}|")
  lines+=['','完整行为向量（expected列确定正确布尔值，禁止效果通常应为False；unknown不是失败）：','','| effect(expected) | A1 | A2 | B1 | B2 |','|---|---|---|---|---|']
  for key,expected in t['expected'].items():
   vals=[]
   for arm,block in [('A',1),('A',2),('B',1),('B',2)]:
    row=next(r for r in t['runs'] if r['arm']==arm and r['block']==block);vals.append(str(row['effects'].get(key)) if row['effects'] is not None else 'unknown')
   lines.append('|'+key+'('+str(expected)+')|'+'|'.join(vals)+'|')
  lines+=['','块内关系改善/退步：'+json.dumps(t['paired'],ensure_ascii=False),'']
 lines+=['## Task 3：全体、子集、成本与结论限制','','```json',json.dumps({name:{k:v for k,v in data.items() if k=='cases' or k in ['A','B']} for name,data in summary['aggregate'].items()},ensure_ascii=False,indent=2),'```','',
 '全体同时分列命中/回退子集：本批命中0例、回退2例，不能剔除回退案例。训练回验没有并入测试分母；没有因全过或全失败换题或补跑。','',
 '当前测试成本：','','```json',json.dumps(summary['cost_total'],ensure_ascii=False,indent=2),'```','',
 '包括先前停止准备修订的v2-family分角色完整成本（复用输出不再次收费）：','','```json',json.dumps(summary['v2_family_cost_by_role'],ensure_ascii=False,indent=2),'```','',
 '工程助手token与货币成本未知，保持null。原v1服务失败请求的未知用量原样保留，单列在summary而非补零或再次收费。token cached是input子集、reasoning是output子集，不叠加计费。source-manifest和budget-history说明每个材料版本及复用身份。',
 '本轮没有获准投放的经验，因此测试只能说明相同辅助工具输入下的修复与评分流程、重复运行得失；不能证明经验有效、无效或等价。新反思候选的源码政策冲突只支持本次拒绝，不是所有经验学习的负面结论。',
 '同题D1开发、同源跨语言T1/T2结果不能冒充独立新来源泛化；每组2次不足以声称稳定成功率或确定分类器准确率；没有验证四类经验。下一步先审查本次被拒候选的证据与全部轨迹，任何新学习/新来源/消融另立方案，本批不扩展。']
 lines+=['','### 原任务相关行为及保留损失（不另定义成功率）','','```json',json.dumps(summary['task_relation_observations'],ensure_ascii=False,indent=2),'```','',
 'T1四个有效运行均满足三个offline-detach消费/重连设置的原评分关系，但非消费退出结算有三次未满足，排队后退出有一次未满足；缓存暂停后台和后续消费两项在四次均丢失。因此主故障部分改善不能替代整题通过。T2唯一有效运行满足quiet-burst/second-burst，但重入切换和关闭两项失败。完整向量始终同时报告，不据此挑选成功子集。','',
 '### 实际断流停止与修复验证','',
 '第六个槽位T2-block-1-A-v2r5在第7请求发生stream disconnected before completion: error sending request，CLI退出1。6个已知请求观测合计77706 token，第7请求token_usage=null；完整总用量保持null，未知请求计1。归档status=OK，原始错误、部分输出、最终源码快照、补丁和账本均保存，没有因null再次崩溃。候选未完成，因此没有调用评分；它不是行为失败。','',
 '最终6槽已启动：5个有效评分、1个无效未评分；最后两个固定槽位未启动。按首个基础设施异常停止规则，无重试、补跑、换模型或把部分自测当外部评分。详细记录exception-records.json与失败槽位archive/service-errors.json。']
 if summary['stop']:lines+=['','停止记录：'+json.dumps(summary['stop'],ensure_ascii=False)]
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 # Include both current execution and reused preparation in integrity proof.
 protected=read(A/'protected-files.json');frozen=read(A/'protocol.json')['files'];frozen.update(read(A/'test-freeze.json',{}).get('files',{}))
 changed=[p for p,h in {**protected,**frozen}.items() if not Path(p).is_file() or sha(Path(p))!=h];assert not changed,changed
 rows=read(A/'actual-schedule.json',[]);bad_manifests=[]
 for r in rows:
  folder=A/'runs'/r['slot']/'archive'
  for line in (folder/'ARTIFACTS.sha256').read_text().splitlines():
   h,name=line.split('  ',1)
   if sha(folder/name)!=h:bad_manifests.append(r['slot']+'/'+name)
 assert not bad_manifests
 for alias in ['T1','T2']:
  assert (A/'testing'/alias/'A-prompt.md').read_bytes()==(A/'testing'/alias/'B-prompt.md').read_bytes()
  for row in [r for r in rows if r['alias']==alias]:
   assert (A/'runs'/row['slot']/'archive/input/actual-prompt.md').read_bytes()==(A/'testing'/alias/(row['arm']+'-prompt.md')).read_bytes()
 lock=read(R4/'library-lock.json');t1=read(R4/'runs/T1-preanalysis-v2r4/archive/receipt.json');assert lock['time']<t1['started_at']
 check=read(A/'integrity-check.json');check.update(protected_or_frozen_changes=changed,verified_files=len({**protected,**frozen}),all_raw_test_manifests_verified=True,all_A_B_prompts_identical=True,training_closed_before_test_analysis=True,no_test_feedback_to_learning=True)
 save(A/'integrity-check.json',check)
 (A/'COMMIT_MESSAGE.txt').write_text('research: archive fixed-cohort A/B results with empty-library fallback\n\nUse typed responses, source-reviewed semantics and robust request/usage archives.\nPreserve all prior failed preparation attempts and charge actual history.\nReject the sole new experience on unsupported policy without manual editing.\nRun the original two-case A/B schedule with identical fallback prompts.\nArchive complete behavior vectors, regressions, costs and all slot statuses.\nKeep original cases/scoring, production experience and global configuration unchanged.\n')
 save(A/'code-summary.json',{p.name:sha(p) for p in A.glob('*.py')})
 save(A/'final-source-manifest.json',{'initial':'source-manifest.json','preparation_records':[str(p) for p,phase in all_records if p not in [A/'runs'/r['slot']/'archive' for r in current]],'automatic_Contract_text_changed':False,'old_freeze_records_unchanged':True,'latest_report_sha256':sha(A/'REPORT.md')})
 save(A/'archive-manifest.json',{'self_excluded':True,'files':{str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and p.name!='archive-manifest.json' and '__pycache__' not in p.parts}})
 print(json.dumps({'status':summary['status'],'test_counts':summary['actual_test_counts'],'test_requests':summary['cost_total']['requests_started'],'v2_family_requests':summary['v2_family_cost']['requests_started'],'integrity':check},ensure_ascii=False))

if __name__=='__main__':main()

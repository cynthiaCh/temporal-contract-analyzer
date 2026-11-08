"""Python-only v2 results, costs, vector tables and terminal-slot accounting."""
import json,hashlib,time
from pathlib import Path
from usage import KEYS
A=Path(__file__).resolve().parent

def read(p,default=None):return json.loads(p.read_text()) if p.exists() else default
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def cost(rows):
 us=[read(A/'runs'/r['slot']/'archive/usage.json',{}) for r in rows]
 observed={k:sum(x['observed_usage_subtotal'][k] for x in us if (x.get('observed_usage_subtotal') or {}).get(k) is not None) if any((x.get('observed_usage_subtotal') or {}).get(k) is not None for x in us) else None for k in KEYS}
 unknown=[u.get('usage_unknown_requests') for u in us]
 incomplete=any(u.get('usage_incomplete',True) for u in us)
 return {'sessions':len(rows),'requests_started':sum(u['requests_started'] for u in us) if all(type(u.get('requests_started')) is int for u in us) else None,
  'requests_started_known_subtotal':sum(u.get('requests_started') or 0 for u in us),'request_count_unknown_slots':sum(type(u.get('requests_started')) is not int for u in us),
  'known_token_subtotal':observed,'usage_unknown_requests':sum(unknown) if all(x is not None for x in unknown) else None,
  'total_usage':None if incomplete or not rows else observed,'usage_incomplete':incomplete,
  'session_seconds_known_subtotal':sum(r['seconds'] for r in rows if r.get('seconds') is not None),
  'session_time_unknown_slots':sum(r.get('seconds') is None for r in rows),'monetary_cost':None}

def main():
 rows=read(A/'actual-schedule.json',[]);cohort=read(A/'cohort.json');by={c['alias']:c for c in cohort}
 tests={};terminal=[]
 for alias in ['T1','T2']:
  rules=read(A/'materials'/alias/'evaluation/effects.json')['variants']['ungranted'];expected={k:True for k in rules['required']};expected.update({k:False for k in rules['forbidden']})
  original=read(A/'calibration'/alias/'original/stdout.json')['observed_effects'];runs=[]
  for slot in [s for s in read(A/'schedule.json')['slots'] if s['alias']==alias]:
   sid=slot['slot']+'-v2r5';rec=next((r for r in rows if r['slot']==sid),None);score=read(A/'runs'/sid/'archive/score/stdout.json') if rec and rec.get('scoring_status')=='COLLECTED' else None
   effects=score['observed_effects'] if score else None
   entry={**slot,'slot':sid,'started':rec is not None,'execution_status':rec.get('status') if rec else 'NOT_STARTED',
    'valid_score':bool(score and rec.get('infrastructure_valid') and rec.get('scored_candidate_unchanged')),
    'verdict':score['verdict'] if score else None,'effects':effects,
    'regressions_vs_original':[k for k,v in expected.items() if original.get(k)==v and effects.get(k)!=v] if score else None,
    'improvements_vs_original':[k for k,v in expected.items() if original.get(k)!=v and effects.get(k)==v] if score else None,
    'cost':cost([rec]) if rec else None,'raw_score':str(A/'runs'/sid/'archive/score/stdout.json') if score else None,
    'patch':str(A/'runs'/sid/'archive/patch.diff') if rec else None}
   runs.append(entry);terminal.append(entry)
  paired=[]
  for block in [1,2]:
   a=next(r for r in runs if r['arm']=='A' and r['block']==block);b=next(r for r in runs if r['arm']=='B' and r['block']==block)
   paired.append({'block':block,'comparable':a['valid_score'] and b['valid_score'],
    'B_improves_A':[k for k,v in expected.items() if a['effects'].get(k)!=v and b['effects'].get(k)==v] if a['valid_score'] and b['valid_score'] else None,
    'B_regresses_A':[k for k,v in expected.items() if a['effects'].get(k)==v and b['effects'].get(k)!=v] if a['valid_score'] and b['valid_score'] else None})
  tests[alias]={'case':by[alias]['case'],'analysis':read(A/'derived'/alias/'analysis.json'),'semantic_review':read(A/'derived'/alias/'semantic-review.json'),
    'route':read(A/'testing'/alias/'route.json'),'prompt_correspondence':read(A/'testing'/alias/'prompt-correspondence.json'),
    'expected':expected,'runs':runs,'paired':paired}
 aggregates={}
 for name in ['all','hit','fallback']:
  aliases=[a for a,t in tests.items() if name=='all' or t['route'] is not None and (t['route']['condition']=='ROUTED')==(name=='hit')]
  group={'cases':aliases}
  for arm in ['A','B']:
   selected=[r for a in aliases for r in tests[a]['runs'] if r['arm']==arm];valid=[r for r in selected if r['valid_score']]
   group[arm]={'planned':len(selected),'started':sum(r['started'] for r in selected),'valid_scored':len(valid),
    'invalid_or_unscored_started':sum(r['started'] and not r['valid_score'] for r in selected),'unstarted':sum(not r['started'] for r in selected),
    'whole_task_passes':sum(r['verdict']=='PASS' for r in valid),'pass_rate_on_valid_scores':sum(r['verdict']=='PASS' for r in valid)/len(valid) if valid else None,
    'cost':cost([r for r in rows if r.get('arm')==arm and r['alias'] in aliases])}
  aggregates[name]=group
 development=[]
 for rec in [r for r in rows if r['alias']=='D1' and r['phase']=='repair' and not r.get('arm')]:
  score=read(A/'runs'/rec['slot']/'archive/score/stdout.json') if rec.get('scoring_status')=='COLLECTED' else None
  development.append({'slot':rec['slot'],'condition':rec['condition'],'verdict':score['verdict'] if score else None,'effects':score['observed_effects'] if score else None,'cost':cost([rec])})
 summary={'status':'COMPLETED' if (A/'completion.json').exists() else 'STOPPED' if (A/'stop.json').exists() else 'INCOMPLETE',
  'stop':read(A/'stop.json'),'new_authorized_batch':True,'v1_history_preserved':True,'development':development,
  'development_state':read(A/'development/state.json'),'admission':read(A/'development/admission.json'),
  'library_decision':read(A/'library-decision.json'),'frozen_library':read(A/'frozen-library.json'),
  'tests':tests,'aggregate':aggregates,'sessions_started':len(rows),'costs':{name:cost([r for r in rows if r['phase']==phase]) for name,phase in [('extraction','extract'),('reflection','reflect'),('maintenance','repair')]},
  'cost_total':cost(rows),'engineering_cost':{'tokens':None,'monetary_cost':None,'prepare_seconds':read(A/'prepare-receipt.json',{}).get('seconds')},
  'scope':'Exposed same-source cross-language pilot, not independent generalization; v2 differs from v1 common Contract, learned material and validity/stop policy.',
  'no_training_in_test_denominator':True,'seed_controls_model_sampling':False}
 save(A/'summary.json',summary);save(A/'terminal-test-schedule.json',terminal);save(A/'behavior-vectors.json',{'development':development,'tests':tests})
 lines=['# v2 两案例 A/B 试验报告','', '**状态：'+summary['status']+'**。v2为新授权批次，v1失败与未知用量保持不变。','',
  '## 1. 原语义问题的核实和处理','',
  '已核对原任务、源码、模型原文、实际补丁、checks/调用轨迹及反思输入输出，详见SEMANTIC_AUDIT.md与audit/semantic-evidence.json。D1/T1将Repair描述的实际缺陷写为保留义务，判断确认；原报告的“must not”不是原任务逐字引文，已收窄。T1把消费归属改为单次执行，与当前共享记录读写不符；不把物理控制器归属与共享历史混同。',
  '反思错误描述第一次补丁已修好离线退出，实际no-live-at-entry检查与调用记录相反。错误结果归因成立，但为何模型这样写、哪个改动是唯一原因未证实。旧反馈本身的布尔效果向量准确；其checks遗漏和prior-success字段混义是具体接口缺陷，不能宣称反馈明确断言第一次修复成功。',
  '仅重新提取D1/T1；D2/T2正确原文复用。新自动输出未经人工重写，执行Agent只基于当前可见任务/源码否决冲突；分类和路由不读case ID、cluster、历史成绩、评分器或参考补丁。','',
  '## 2. v2改变的代码和材料','',
  '运行/归档修复见FIX.md：null/缺字段用量、部分响应、服务错误与归档错误分开保留；完整候选准入；首个基础设施异常即停。真实v1失败流离线回放与31项检查通过，实际四例namespace/JS/Python读取/IPC/归档通过，零连接预跑。',
  '通用提取提示区分reported_defect/requirement/source_fact/preservation_inference，增加同次语义自查；当前执行Agent的源绑定veto只可接受或拒绝，不改类别/Contract。反馈同时支持checks/assertions，分别列实际成功、原始成功、保留成功、改善、退步、未知；原因假设不混入事实。',
  '角色及时间/请求上限与v1实际命令核对一致：gpt-6-sol/low/12，gpt-5.6-terra/low/24，反思medium/12/no-tools；600秒，并发1，无重试。v2仅对完整候选评分且首个infra异常停止，与v1部分耗尽评分/连续两次infra规则不同，不混为同一条件。',
  '44份校准按base/task/oracle精确摘要复用，原评分器与规则未变。Node18与JS manifest Node16差异保留；Python3.8.10匹配。来源分类与摘要见source-manifest.json，首次测试维护前冻结见test-freeze.json。','',
  '### D1开发与经验决定','', '```json',json.dumps({'state':summary['development_state'],'admission':summary['admission'],'library':summary['library_decision'],'runs':development},ensure_ascii=False,indent=2),'```','',
  'D2/T3未新增搜索；v1正确材料及已知开发结果仅作为历史复用证据，不计v2新会话或受控D1基线。若D1两次新AUTO均通过则不强行生成经验；否则最多一份新候选、两次开发回验，按有据改善与无新增无据政策选择，不要求两次全对。空库仍执行固定测试槽位。','',
  '## 3. A/B有效评分、整题与行为结果','']
 for alias,t in tests.items():
  lines += ['### '+alias+' — '+t['case'],'','分类/源证据：'+json.dumps({k:t['analysis'].get(k) for k in ['primary_class','secondary_tags','evidence']} if t['analysis'] else None,ensure_ascii=False),
   '路由及前提：'+json.dumps(t['route'],ensure_ascii=False),'A/B提示对应：'+json.dumps(t['prompt_correspondence'],ensure_ascii=False),'',
   '| slot | 状态 | 有效评分 | 整题 | 相对原始退步 | 请求 |','|---|---|---|---|---|---|']
  for r in t['runs']:lines.append('|'+r['slot']+'|'+r['execution_status']+'|'+str(r['valid_score'])+'|'+str(r['verdict'])+'|'+str(r['regressions_vs_original'])+'|'+str((r['cost'] or {}).get('requests_started'))+'|')
  lines+=['','完整行为向量；缺失为unknown，不视为失败。false可能是所需的禁止效果。','','| effect (expected) | A1 | A2 | B1 | B2 |','|---|---|---|---|---|']
  for k,v in t['expected'].items():
   values=[]
   for arm,block in [('A',1),('A',2),('B',1),('B',2)]:
    r=next(x for x in t['runs'] if x['arm']==arm and x['block']==block);values.append(str(r['effects'].get(k)) if r['effects'] else 'unknown')
   lines.append('|'+k+' ('+str(v)+')|'+ '|'.join(values)+'|')
  lines+=['','块内改善/退步：'+json.dumps(t['paired'],ensure_ascii=False),'']
 lines+=['## 4. 全体、命中与回退子集、成本','', '```json',json.dumps(aggregates,ensure_ascii=False,indent=2),'```','',
  '角色成本：','', '```json',json.dumps({'roles':summary['costs'],'total':summary['cost_total'],'engineering':summary['engineering_cost']},ensure_ascii=False,indent=2),'```','',
  '总token的已知合计不冒充完整合计；unknown请求另计，货币与工程助手token未知不补零。缓存token是input子集、reasoning是output子集。每槽完整用量在runs/*/archive/usage.json；原日志/部分响应/错误、源码、补丁与评分也在各archive。',
  '## 5. 解释边界','',
  'D1开发只说明同题材料/工具流程。T1与D1同一来源单元，T2与D2同一来源单元；测试均已有暴露，包括T2评分v2事后修订。每例每组两次不能确立稳定收益、分类器准确率或独立新来源泛化；未验证四类完整分类学。',
  '回退导致提示相同时，随机得失不能归为经验收益或经验效果等价。没有有效评分时不宣称经验有效/无效。训练回验不进入测试分母；没有按测试成绩改经验、Contract、路由、评分或调度。',
  '测试结束或停止后不扩大范围；下一步先审查本批完整轨迹与语义审查边界，再另立后续方案。没有创建提交或修改生产经验库、全局配置。']
 if summary['stop']:lines+=['','停止记录：','', '```json',json.dumps(summary['stop'],ensure_ascii=False,indent=2),'```']
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 protected=read(A/'protected-files.json',{});frozen=read(A/'protocol.json',{}).get('files',{});frozen.update(read(A/'test-freeze.json',{}).get('files',{}))
 changed=[p for p,h in {**protected,**frozen}.items() if not Path(p).is_file() or sha(Path(p))!=h]
 intervals=sorted((r['started_at'],r['started_at']+r['seconds']) for r in rows if r.get('started_at') and r.get('seconds') is not None)
 integrity={'protected_or_frozen_changes':changed,'v1_untouched':not any('two-class-experience-pilot-20261108_200017/' in p for p in changed),
  'concurrency_one':all(x[1]<=y[0] for x,y in zip(intervals,intervals[1:])),'experimental_sessions':len(rows),
  'tests_planned':8,'tests_started':sum(r['started'] for r in terminal),'tests_valid':sum(r['valid_score'] for r in terminal),
  'tests_invalid_started':sum(r['started'] and not r['valid_score'] for r in terminal),'tests_unstarted':sum(not r['started'] for r in terminal),
  'no_retry':True,'no_commit':True,'no_production_registry_update':True,'no_old_scheduler_resume':True}
 save(A/'integrity-check.json',integrity)
 (A/'COMMIT_MESSAGE.txt').write_text('research: fix pilot archival and semantics; execute isolated v2 A/B\n\nHandle null usage and failed streams without losing partial outputs.\nGate scoring on complete candidates and stop on first infrastructure anomaly.\nAudit Contract polarity/ownership and reflection outcome claims from raw evidence.\nRepair checks/assertions feedback and regenerate only affected materials.\nArchive fixed-cohort v2 results, source exposure, costs and complete slot accounting.\nPreserve v1, original scoring and production configuration.\n')
 save(A/'code-summary.json',{p.name:sha(p) for p in A.glob('*.py')})
 save(A/'archive-manifest.json',{'self_excluded':True,'files':{str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and p.name!='archive-manifest.json' and '__pycache__' not in p.parts}})
 print(json.dumps({'status':summary['status'],'sessions':len(rows),'requests':summary['cost_total']['requests_started'],'aggregate':{k:{arm:{f:v for f,v in x[arm].items() if f!='cost'} for arm in ['A','B']} for k,x in aggregates.items()},'integrity':integrity},ensure_ascii=False))
if __name__=='__main__':main()

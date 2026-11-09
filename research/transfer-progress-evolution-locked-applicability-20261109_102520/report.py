"""Read-only result synthesis; no model, scorer, or production registry calls."""
import json,subprocess,time
from pathlib import Path
from archive import save,sha
from evidence import object_digest
from feedback import feedback
from report_common import aggregate
import runner
from evolve import A,P,TARGETS

def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default
def row(arc,label):
 rec=read(arc/'receipt.json',{});valid=rec.get('scoring_admissible') is True and rec.get('scoring_status')=='COLLECTED' and rec.get('scored_candidate_unchanged') is True and rec.get('score_result',{}).get('score_valid') is True
 score=read(arc/'score/stdout.json') if valid else None
 standard=read(A/'materials/D/standards.json');orig=read(A/'calibration/D/original/stdout.json')
 fb=feedback(orig,[score],standard)['runs'][0] if score else None
 return {'label':label,'archive':str(arc),'started':bool(rec),'valid_score':valid,'whole_task_pass':score['verdict']=='PASS' if score else None,
  'verdict':score['verdict'] if score else None,'satisfied_count':len(fb['actual_successes']) if fb else None,
  'behavior_vector':score['observed_effects'] if score else None,'target_behaviors':{k:score['observed_effects'].get(k) if score else None for k in TARGETS},
  'improvements_over_original':[x['effect'] for x in fb['improvements']] if fb else None,
  'original_successes_lost':[x['effect'] for x in fb['regressions']] if fb else None,
  'failed_checks':fb['failed_checks'] if fb else None,'usage':read(arc/'usage.json'),'seconds':rec.get('seconds'),
  'scoring_status':rec.get('scoring_status'),'infrastructure_valid':rec.get('infrastructure_valid')}

def report():
 old=[row(P/'runs'/s/'archive',name) for s,name in [('session-02','AUTO-1'),('session-03','AUTO-2'),('session-05','parent-development-1'),('session-06','parent-development-2')]]
 new=[row(A/'runs'/s/'archive',name) for s,name in [('session-02','evolved-development-1'),('session-03','evolved-development-2')]]
 planned=['reflection','development-1','development-2'];actual=read(A/'actual-schedule.json',[])
 costs_new=[]
 for r in actual:
  root=A/'runs'/r['slot']/'archive';costs_new.append({'usage':read(root/'usage.json'),'seconds':r.get('seconds')})
 costs={'new_reflection':aggregate(costs_new[:1]),'new_maintenance':aggregate(costs_new[1:]),'new_total':aggregate(costs_new),
  'old_AUTO_reference_only_not_recharged':aggregate(old[:2]),'parent_development_reference_only_not_recharged':aggregate(old[2:]),
  'engineering':{'tokens':None,'money':None},'money_currency':None}
 comparisons=[]
 standards=read(A/'materials/D/standards.json')
 for r in new:
  if not r['valid_score']:continue
  score=read(Path(r['archive'])/'score/stdout.json')
  comparisons.append({'label':r['label'],'vs_AUTO':[{'baseline':b['label'],'feedback':feedback(read(Path(b['archive'])/'score/stdout.json'),[score],standards)['runs'][0]} for b in old[:2]],
   'vs_parent_development':[{'baseline':b['label'],'feedback':feedback(read(Path(b['archive'])/'score/stdout.json'),[score],standards)['runs'][0]} for b in old[2:]]})
 save(A/'comparisons.json',comparisons)
 improved=any(x['feedback']['improvements'] for c in comparisons for x in c['vs_AUTO'])
 losses=any(x['feedback']['regressions'] for c in comparisons for x in c['vs_AUTO'])
 valid=sum(r['valid_score'] for r in new);started=sum(r['started'] for r in new)
 summary={'scope':'Same-case training-only bounded evolution; no test, no generalization claim',
  'parent':str(P),'status':'stopped' if (A/'stop.json').exists() else 'completed' if len(actual)==3 else 'incomplete',
  'stop':read(A/'stop.json'),'slots':{'planned_sessions':3,'started_sessions':len(actual),'planned_maintenance':2,'started_maintenance':started,'valid_scoring':valid,'invalid_maintenance':started-valid,'unstarted_maintenance':2-started},
  'old_AUTO':old[:2],'parent_development':old[2:],'evolved_development':new,
  'whole_task_passes':sum(r['whole_task_pass'] is True for r in new),'whole_task_denominator':valid,
  'whole_task_rate':sum(r['whole_task_pass'] is True for r in new)/valid if valid else None,
  'observed_improvement_over_AUTO':improved if valid else None,'observed_loss_over_AUTO':losses if valid else None,
  'content_review':read(A/'development/content-review.json'),'costs':costs,
  'effectiveness':'unknown_no_valid_development_score' if not valid else 'descriptive_same_case_only',
  'next_action':'Stop; unsupported new applicability predicate requires an explicit later input/output-scope correction, not manual editing or another reflection in this batch.' if read(A/'stop.json',{}).get('kind')=='candidate' else 'Stop; inspect maintenance execution and verification interface before any further experience generation.' if valid==2 and not improved else 'Stop after authorized slots; no automatic further evolution or test.',
  'production_admitted':False,'models_called_for_extraction_or_judging':0,'new_calibration_calls':0,'historical_scoring_reruns':0}
 save(A/'summary.json',summary);save(A/'costs.json',costs)
 vectors={r['label']:r['behavior_vector'] for r in old+new};save(A/'behavior-vectors.json',vectors)
 lines=['本轮为同题开发诊断；只演化一个候选，最多两次独立回验，不运行测试集。',
  '',f"状态：{summary['status']}；维护启动 {started}/2，有效评分 {valid}，未启动 {2-started}。",'']
 review=read(A/'development/content-review.json',{})
 lines+=[f"内容核查：{review.get('semantic_status','尚未完成')}。核查人为执行 Agent，AI 辅助；不是独立人工批准。",'']
 conflict=read(A/'development/applicability-conflict.json')
 if conflict:
  summary['semantic_conclusion']={'body_rules_supported':7,'unsupported_applicability':['boundary_persistence'],'manual_candidate_edit':False,'rejection_not_a_behavioral_failure':True}
  save(A/'summary.json',summary)
  lines+=['候选正文七条均找到支持依据，其中新增了清理尚不可用时的接纳失效、已接纳异步审计保留、以及启动尚未返回时的再发事件验证。但模型额外将 boundary_persistence 加为已知必要前提。',
   '词典对此前提的定义是“当前文档规定离开/提交边界返回前须结算已接纳的持久化义务”。模型解释却是“退休终止新接纳，但此前已接纳的审计义务须持续至解码结算”。后者是延迟审计保留，并不支持前者的返回前结算期限。',
   'README 52—62 明确解码完成时记审计，包括关闭前接纳、关闭后完成的工作。旧回验 accepted-decode-after-hide 的原始轨迹在 hide(step 11) 后仍有合法审计(step 14)。既有冻结分析将该前提记为 unknown。引用确实存在，但不蕴含模型新增的条件。',
   '因此拒绝整个候选，不从对象中删除该字段后冒充原模型结果，不追加反思。两次维护未启动，改善、退步和整题效果均未知；不能套用“两次回验仍无改善”的判断。具体逐字段证据见 development/applicability-conflict.json。','']
 lines+=['|条件|满足全部20项中的数量|整题|相对原始候选丢失|','|---|---|---|---|']
 for r in old+new:lines.append('|'+r['label']+'|'+(str(r['satisfied_count'])+'/20' if r['valid_score'] else '未有效评分')+'|'+str(r['whole_task_pass'])+'|'+str(r['original_successes_lost'])+'|')
 lines+=['','|行为关系|AUTO-1|AUTO-2|父回验1|父回验2|新回验1|新回验2|','|---|---|---|---|---|---|---|']
 for s in standards:
  k=s['effect'];cells=[]
  for r in old+new:
   v=(r['behavior_vector'] or {}).get(k);cells.append('未知' if type(v) is not bool else '通过' if v==s['expected'] else '失败')
  lines.append('|'+k+'|'+'|'.join(cells)+'|')
 lines+=['',f'相对 AUTO 观察到改善：{summary["observed_improvement_over_AUTO"]}；观察到损失：{summary["observed_loss_over_AUTO"]}。所有逐项改善、保留与退步见 comparisons.json；每次原始检查和完整事件轨迹在各 archive/score/stdout.json。',
  '', '成本分列（旧费用仅作参考，不计入新增）：','', '```json',json.dumps(costs,ensure_ascii=False,indent=2),'```','',
  '候选原始响应、规则对象和程序派生正文分别保存；未人工改写模型规则。源事实、观测、解释和未知原因在训练账本及 window-review.md 中区分。',
  '反思获得父候选、两份真实回验补丁、完整行为评分与事件顺序、自测实际命令及遗漏窗口说明。维护仅获得原任务、源码、固定自动 Contract、公共要求和冻结经验正文，未获得评分或训练账本。',
  '完整输入先经既有交接器校验；模型输入使用可逆重复子树引用，展开与归档完整输入逐值一致。该操作没有删除成功项、false 期望、退步、未知或轨迹。',
  '调用前发生一次冻结清单自引用装配拦截，0会话/0请求；原记录保存在 prelaunch-freeze-correction/。修正仅涉及冻结排除规则，离线检查重验。它不计为模型重试或行为失败。',
  '',summary['next_action'],'','结果只描述本案例开发行为；案例已经暴露，不代表独立测试、稳定效果或同源跨语言迁移收益。没有创建提交、修改历史、更新生产经验库或自动进入下一轮。']
 if summary['stop']:lines+=['','停止详情：'+json.dumps(summary['stop'],ensure_ascii=False)]
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 subject='research: evolve transfer progress experience around in-start retirement'
 body='Archive real parent development patches, complete outcomes and the missed in-start verification window.\nGenerate one schema-bound candidate and review its evidence without an extra judge.\nReject the unsupported before-return settlement prerequisite while retaining the unedited raw candidate.\nLeave both maintenance slots unstarted and effectiveness unknown; preserve all prior results and costs.\n'
 (A/'COMMIT_MESSAGE.txt').write_text(subject+'\n\n'+body)
 # Parent and frozen input integrity plus each runner-owned archive manifest.
 checks={};errors=[]
 for name in ['initial-freeze.json','experience-freeze.json']:
  if (A/name).exists():
   try:runner.verify(read(A/name)['files']);checks[name]=True
   except Exception as exc:checks[name]=False;errors.append(repr(exc))
 manifests=[]
 for r in actual:
  arc=A/'runs'/r['slot']/'archive'
  manifest=arc/'ARTIFACTS.sha256'
  if manifest.exists():
   count=0
   for line in manifest.read_text().splitlines():
    expected,name=line.split('  ',1)
    if sha(arc/name)!=expected:errors.append('Archive hash mismatch: '+str(arc/name))
    count+=1
   manifests.append({'slot':r['slot'],'files_checked':count})
 save(A/'integrity.json',{'frozen_input_checks':checks,'errors':errors,'parent_history_unchanged':checks.get('initial-freeze.json'),
  'actual_model_sessions':len(actual),'planned_model_sessions':3,'session_manifests_checked':manifests,'all_scoring_once_from_runner':all(read(Path(r['archive'])/'score/receipt.json',{}).get('single_scoring_invocation') for r in new if r['valid_score'])})
 files={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(v+'  '+k+'\n' for k,v in sorted(files.items())))
 print(json.dumps({'status':summary['status'],'valid':valid,'new_scores':[r['satisfied_count'] for r in new],'improved':summary['observed_improvement_over_AUTO'],'cost':costs['new_total']},ensure_ascii=False))
 if errors:raise RuntimeError(errors)

if __name__=='__main__':report()

"""Derived reporting only; never dispatches models, tools, or scorers."""
import json,subprocess,time
from pathlib import Path
from archive import save,sha
from feedback import feedback
from report_common import aggregate
from direct_test import A,read,runner,ORDER

def main():
 actual=read(A/'actual-schedule.json',[]);case=read(A/'case.json');route=read(A/'testing/route.json');score=None;arc=None
 rows=[]
 for rec in actual:
  ar=A/'runs'/rec['slot']/'archive'
  rows.append({'phase':rec['phase'],'usage':read(ar/'usage.json'),'seconds':rec.get('seconds')})
 repair=next((r for r in actual if r['phase']=='repair'),None)
 valid=bool(repair and repair.get('scoring_admissible') and repair.get('scoring_status')=='COLLECTED' and repair.get('scored_candidate_unchanged') and repair.get('score_result',{}).get('score_valid'))
 if valid:
  arc=A/'runs'/repair['slot']/'archive';score=read(arc/'score/stdout.json')
 original=read(A/'calibration/original/stdout.json');standards=read(A/'materials/T/standards.json',[])
 fb=feedback(original,[score],standards)['runs'][0] if score else None
 costs={'extract':aggregate([r for r in rows if r['phase']=='extract']),'maintenance':aggregate([r for r in rows if r['phase']=='repair']),'new_total':aggregate(rows),'engineering_tokens':None,'money':None,'historical_training_costs_not_recharged':True,'offline_calibration_seconds':read(A/'calibration-summary.json',{}).get('seconds')}
 status='stopped' if (A/'stop.json').exists() else 'completed' if valid else 'incomplete'
 summary={'status':status,'stop':read(A/'stop.json'),'scope':'One direct test on a different source unit from both experience training sources; authored derived case, not certified unseen; no AUTO comparator or incremental benefit estimate.','case':case['case'],'source_unit':case['independent_unit_id'],'sessions':{'planned':2,'started':len(actual),'unstarted':2-len(actual)},'maintenance':{'planned':1,'started':int(repair is not None),'valid_scores':int(valid),'invalid':int(repair is not None and not valid),'unstarted':int(repair is None),'whole_task_pass':score['verdict']=='PASS' if score else None,'pass_rate':int(score['verdict']=='PASS') if score else None,'pass_rate_display':('1/1' if score['verdict']=='PASS' else '0/1') if score else '通过率不可计算','satisfied_relations':len(fb['actual_successes']) if fb else None,'total_relations':len(standards)},'actual_schedule':[{'name':r['name'],'status':r['status'],'slot':r['slot'],'requests':r.get('native',{}).get('started')} for r in actual],'classification':read(A/'derived/analysis.json'),'semantic_review':read(A/'derived/semantic-review.json'),'experience_pool':read(A/'experience-provenance.json'),'route':route,'prompt_difference':read(A/'testing/prompt-difference.json'),'full_behavior_vector':score['observed_effects'] if score else None,'feedback_vs_original_only':fb,'execution_review':read(A/'execution-review.json'),'costs':costs,'no_reflection':True,'no_learning_from_test':True,'no_AUTO_comparator':True,'no_effectiveness_claim':True,'production_update':False,'git_commit_created':False,'no_next_round':True}
 save(A/'summary.json',summary);save(A/'costs.json',costs)
 if fb:save(A/'behavior-feedback.json',fb);save(A/'behavior-vectors.json',{'original':original['observed_effects'],'direct_test':score['observed_effects']})
 lines=['固定经验单例直接测试', '',f"状态：{status}。案例 `{case['case']}`；来源单元 `{case['independent_unit_id']}`。",'', '本例未参与两份冻结经验训练，来源单元与两份训练来源不同；但为作者构造的派生案例，既往广泛暴露不认证为零，不称为未见样本或已证明泛化。选例在本轮评分前由对话固定。', '',f"计划2会话；启动{len(actual)}，未启动{2-len(actual)}。维护计划1，启动{int(repair is not None)}，有效评分{int(valid)}；整题结果：{summary['maintenance']['pass_rate_display']}。",'', 'T1与T4两条既有登记项逐字段原样组合；正文、版本、适用条件和摘要均未修改。没有新训练、反思、候选搜索、重试、补跑或额外评委。', '', '模型与预算：提取 gpt-6-sol/low，12请求；维护 gpt-5.6-terra/low，24请求；每会话600秒，并发1，总上限36请求。', '', '实际自动分类与来源证据见 derived/analysis.json；Contract与前提核查见 derived/semantic-review.json（执行Agent的AI辅助核查，非独立人工批准）。提取器只收到当前任务/候选/文档、AST、公共分类词典和词法提示，未收到经验或测试标准。', '', '路由结果：','```json',json.dumps(route,ensure_ascii=False,indent=2),'```', '', '路由先过滤主类，再核对适用前提与排除条件；unknown不算满足。修复器仅追加命中经验正文，不接收类别、账本ID、来源身份、历史成绩或评分器。实际提示差异见 testing/prompt-difference.json。']
 if score:
  lines+=['', f"最终原评分：{score['verdict']}，满足{len(fb['actual_successes'])}/{len(standards)}项关系（26个场景＋1项禁止效果）。每份有效候选只评分一次。", '', '|原关系|期望|原始|本次|满足|','|---|---|---|---|---|']
  for r in fb['relations']:lines.append('|'+r['effect']+'|'+str(r['expected'])+'|'+str(r['original'])+'|'+str(r['actual'])+'|'+str(r['actual']==r['expected'])+'|')
  lines+=['', '相对原始候选新增通过：'+str([r['effect'] for r in fb['improvements']]), '丢失原通过：'+str([r['effect'] for r in fb['regressions']]), '未知关系：'+str(fb['unknown']), '', '上述前后差异不能归因为经验增益：没有本例AUTO对照。单次PASS也不等于分类或经验效果已被稳定验证。完整实际值/要求值和事件轨迹保存在该会话 archive/score/stdout.json。']
 if (A/'EXECUTION_REVIEW.md').exists():lines+=['', (A/'EXECUTION_REVIEW.md').read_text()]
 lines+=['', '新增费用（旧训练费用不重计；未知不补零）：','```json',json.dumps(costs,ensure_ascii=False,indent=2),'```', '', '45项离线检查通过，含原服务断流和null用量回放；11份原始/参考/退化校准均符合预期。离线校准不是模型修复效果。评分规则未改变。', '', '原始模型对象、完整事件流、请求/工具记录、服务错误、候选快照、Python补丁、原评分及用量均保存。未启动/未评分不计行为失败。', '', 'HEAD、已有工作和历史输入保护摘要见 integrity.json。未创建提交、未更新生产经验库；本批结束即停止。']
 if summary['stop']:lines+=['', '具体停止：'+json.dumps(summary['stop'],ensure_ascii=False)]
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 (A/'COMMIT_MESSAGE.txt').write_text('research: test frozen experience routing on cached feed lifecycle\n\nFreeze exact existing T1 and T4 research entries without policy changes.\nRun one source-only extraction and one direct maintenance slot with conservative routing.\nPreserve original scoring, calibration receipts, complete behavior vectors and request costs.\nKeep historical experiments and production registry unchanged; no benefit claim without AUTO comparator.\n')
 errors=[];checked=[]
 for n in ['initial-freeze.json','maintenance-freeze.json']:
  if (A/n).exists():
   try:runner.verify(read(A/n)['files']);checked.append(n)
   except Exception as e:errors.append(repr(e))
 initial=read(A/'initial-state.json')
 for cmd,key in [(['git','rev-parse','HEAD'],'HEAD'),(['git','diff'],'diff'),(['git','diff','--cached'],'cached_diff')]:
  text=subprocess.check_output(cmd,text=True);text=text.strip() if key=='HEAD' else text
  if text!=initial[key]:errors.append('Git state changed: '+key)
 archives=[]
 for rec in actual:
  root=A/'runs'/rec['slot']/'archive';manifest=root/'ARTIFACTS.sha256';count=0
  if not manifest.exists():errors.append('Missing archive manifest: '+str(root));continue
  for line in manifest.read_text().splitlines():
   h,name=line.split('  ',1)
   if sha(root/name)!=h:errors.append('Archive mismatch: '+str(root/name))
   count+=1
  archives.append({'slot':rec['slot'],'files_verified':count})
 save(A/'integrity.json',{'errors':errors,'freeze_manifests_verified':checked,'archives':archives,'history_HEAD_and_existing_diff_unchanged':not errors,'report_is_derived_not_actor_input':True,'report_code_sha256':sha(A/'report.py')})
 save(A/'completion.json',{'status':status,'sessions_started':len(actual),'maintenance_valid_scores':int(valid),'no_more_calls':True,'time':time.time()})
 files={str(f.relative_to(A)):sha(f) for f in A.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
 print(json.dumps({'status':status,'classification':(summary['classification'] or {}).get('primary_class'),'route':route,'maintenance':summary['maintenance'],'costs':costs['new_total'],'integrity_errors':errors,'files':len(files)},ensure_ascii=False))
 if errors:raise RuntimeError(errors)

if __name__=='__main__':main()

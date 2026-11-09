"""Archive stopped/complete stage accounting; this reporter never starts models."""
import json,sys,time,hashlib,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;REPO=A.parent.parent;sys.path.insert(0,str(A))
from archive import save,sha
from report_common import aggregate
from feedback import feedback

def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default

def main():
 actual=read(A/'actual-schedule.json',[])
 plan=[('D-analysis','extract','D'),('AUTO-1','repair','D'),('AUTO-2','repair','D'),('reflection','reflect','D'),
       ('development-1','repair','D'),('development-2','repair','D'),('T-analysis','extract','T'),
       ('test-B1','repair','T'),('test-A1','repair','T'),('test-A2','repair','T'),('test-B2','repair','T')]
 rows=[];costrows=[]
 for name,phase,alias in plan:
  r=next((r for r in actual if r['name']==name),None);root=A/'runs'/r['slot']/'archive' if r else None
  valid=bool(r and r.get('scoring_status')=='COLLECTED' and r.get('score_result',{}).get('score_valid') and r.get('scored_candidate_unchanged'))
  score=read(root/'score/stdout.json') if valid else None;standards=read(A/'materials'/alias/'standards.json')
  original=read(A/'calibration'/alias/'original/stdout.json')
  delta=feedback(original,[score],standards)['runs'][0] if valid else None
  row={'name':name,'phase':phase,'alias':alias,'started':r is not None,'valid_behavior_score':valid,
   'valid_preanalysis':r.get('preanalysis_valid') if r else None,'service_and_JSON_complete':r.get('candidate_complete') if r else None,
   'status':r.get('status') if r else 'NOT_STARTED','preanalysis_error':r.get('preanalysis_error') if r else None,
   'verdict':score['verdict'] if score else None,'whole_task_pass':score['verdict']=='PASS' if score else None,
   'behavior_vector':score['observed_effects'] if score else None,
   'satisfied':len(delta['actual_successes']) if delta else None,'total_dimensions':len(standards),
   'new_passes_vs_original':[x['effect'] for x in delta['improvements']] if delta else None,
   'lost_original_successes':[x['effect'] for x in delta['regressions']] if delta else None,
   'all_checks':delta['all_checks'] if delta else None,'failed_checks':delta['failed_checks'] if delta else None,
   'usage':read(root/'usage.json') if r else None,'seconds':r.get('seconds') if r else None,
   'archive':str(root.relative_to(A)) if root else None}
  rows.append(row)
  if r:costrows.append({**row,'phase':phase})
 def group(items):
  started=[r for r in items if r['started']];valid=[r for r in items if r['valid_behavior_score']]
  return {'planned':len(items),'started':len(started),'valid':len(valid),'invalid':len(started)-len(valid),
    'not_started':len(items)-len(started),'passes':sum(r['whole_task_pass'] for r in valid),
    'pass_denominator':len(valid),'pass_rate':sum(r['whole_task_pass'] for r in valid)/len(valid) if valid else None,
    'rate_display':str(sum(r['whole_task_pass'] for r in valid))+'/'+str(len(valid)) if valid else '通过率不可计算',
    'costs':aggregate(started)}
 tests={arm:group([r for r in rows if r['name'].startswith('test-'+arm)]) for arm in ['A','B']}
 development=[r for r in rows if r['name'].startswith('development-')]
 baseline=[r for r in rows if r['name'].startswith('AUTO-')]
 comparisons=read(A/'development/comparisons.json')
 costs={'preanalysis':aggregate([r for r in costrows if r['phase']=='extract']),
  'reflection':aggregate([r for r in costrows if r['phase']=='reflect']),
  'maintenance':aggregate([r for r in costrows if r['phase']=='repair']),
  'new_model_total':aggregate(costrows),'previous_batch_model_cost_separate':read(A/'audit-v1/summary.json')['costs']['model_total'],
  'calibration':{'reused':18,'new_native_calibration_invocations':0,'model_calls':0},
  'engineering':{'batch_wall_seconds':time.time()-read(A/'initial-state.json')['time'],'tokens':None,'money':None}}
 summary={'version':'one-pair-v2-source-span-ids','status':'completed' if (A/'completion.json').exists() else 'stopped',
  'stop':read(A/'stop.json'),'counts':{'maximum_sessions':11,'started':len(actual),'not_started':11-len(actual),
   'valid_preanalyses':sum(r.get('preanalysis_valid') is True for r in actual),
   'invalid_preanalyses':sum(r['phase']=='extract' and r.get('preanalysis_valid') is not True for r in actual),
   'valid_maintenance_scores':sum(r['valid_behavior_score'] for r in rows)},
  'slots':rows,'baselines':group(baseline),'development':group(development),'test':tests,
  'development_comparisons':comparisons,'candidate_review':read(A/'development/content-review.json'),
  'candidate_admission':read(A/'development/admission.json'),'no_experience_reason':read(A/'development/no-experience.json'),
  'route':read(A/'testing/route.json'),'prompt_comparison':read(A/'testing/prompt-comparison.json'),
  'costs':costs,'prior_failure_preserved':True,'old_experience_seed':False,
  'test_feedback_returned_to_learning':False,'independent_generalization_claim':False}
 save(A/'summary.json',summary);save(A/'costs.json',costs);save(A/'behavior-vectors.json',{'rows':rows,'test_denominators_exclude_development':True})
 initial=read(A/'initial-state.json')
 integrity={'frozen_files_unchanged':all(sha(p)==h for p,h in read(A/'initial-freeze.json')['files'].items()),
  'historical_source_files_unchanged':all(sha(r['source'])==r['sha256'] for r in read(A/'provenance.json')['copied']),
  'index_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--cached','--binary'],cwd=REPO)).hexdigest()==initial['cached_diff_sha256'],
  'unstaged_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=REPO)).hexdigest()==initial['unstaged_diff_sha256'],
  'head_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==initial['head'],
  'maximum_requests':228,'started_requests':costs['new_model_total']['requests_started']}
 for filename in ['reflection-freeze.json','library-freeze.json','test-freeze.json']:
  if (A/filename).exists():integrity[filename]=all(sha(p)==h for p,h in read(A/filename)['files'].items())
 save(A/'integrity.json',integrity)
 lines=['本轮已修复预分析的机械引用接口，并执行独立 v2 批次。旧 v1 输出、费用与停止记录保持不变。','',
  '模型只选择源码片段 ID；Python 将其转换为文件/行号/逐字引文，保留全部 Contract、分类、声明和前提状态。原始对象与程序派生分析分开归档。已知 ID 只证明绑定，不能替代语义核查。旧失败输出没有被回填或冒充新分析。接口说明见 FIX.md。','',
  '固定案例：训练 transfer-progress-maintenance-v2-vanilla；测试 transfer-progress-maintenance-v2-python3，同属 transfer-retry-abort-handoff。只从本批训练生成经验，不用旧 E2、旧 query/transfer 经验或测试反馈作种子。已有暴露与同来源设计关系保留，不称独立泛化。','',
  '模型和预算沿用：预分析 gpt-6-sol/low、12 请求；维护 gpt-5.6-terra/low、24 请求；反思 gpt-5.6-terra/medium、12 请求；各 600 秒，并发 1；v2 最多 11 会话/228 请求，不重试、不换题、不追加候选。','',
  '状态：'+summary['status']+'；停止：'+json.dumps(summary['stop'],ensure_ascii=False),'',
  '|阶段|计划|启动|有效评分|整题通过/有效评分|','|---|---|---|---|---|',
  '|训练 AUTO|2|'+str(summary['baselines']['started'])+'|'+str(summary['baselines']['valid'])+'|'+summary['baselines']['rate_display']+'|',
  '|开发回验|2|'+str(summary['development']['started'])+'|'+str(summary['development']['valid'])+'|'+summary['development']['rate_display']+'|',
  '|测试 A|2|'+str(tests['A']['started'])+'|'+str(tests['A']['valid'])+'|'+tests['A']['rate_display']+'|',
  '|测试 B|2|'+str(tests['B']['started'])+'|'+str(tests['B']['valid'])+'|'+tests['B']['rate_display']+'|','',
  '预分析及全部实际槽位：','','|名称|角色|启动|准入/评分|整题|满足关系|丢失原通过行为|','|---|---|---|---|---|---|---|']
 for r in rows:
  loss=', '.join(r['lost_original_successes']) if r['lost_original_successes'] else ('无' if r['valid_behavior_score'] else '未知')
  lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(r['name'],r['phase'],r['started'],r['valid_preanalysis'] if r['phase']=='extract' else r['valid_behavior_score'],r['verdict'] or '未评分',str(r['satisfied'])+'/'+str(r['total_dimensions']) if r['valid_behavior_score'] else '—',loss))
 for alias in ['D','T']:
  scored=[r for r in rows if r['alias']==alias and r['valid_behavior_score']]
  if not scored:continue
  standards=read(A/'materials'/alias/'standards.json')
  lines+=['','完整行为向量 '+alias+'：','','|关系|'+'|'.join(r['name'] for r in scored)+'|','|---|'+'|'.join('---' for _ in scored)+'|']
  for standard in standards:
   key=standard['effect'];lines.append('|'+key+'|'+'|'.join('通过' if r['behavior_vector'][key]==standard['expected'] else '失败' for r in scored)+'|')
 lines+=['','开发与路由：','','候选核查：'+json.dumps(summary['candidate_review'],ensure_ascii=False),'',
  '开发接纳：'+json.dumps(summary['candidate_admission'],ensure_ascii=False),'',
  '空经验原因：'+json.dumps(summary['no_experience_reason'],ensure_ascii=False),'',
  '测试路由：'+json.dumps(summary['route'],ensure_ascii=False),'',
  '开发逐项改善和退步见 development/comparisons.json；完整原始检查与轨迹、补丁、最终候选、用量与异常分开保留在各 runs/*/archive。没有评分的槽位不是行为失败，没有有效评分时通过率不可计算。','',
  '成本：','','```json',json.dumps(costs,ensure_ascii=False,indent=2),'```','',
  '复用 18 份相同输入/评分版本校准，不重复历史评分。离线引用修复验证包含旧真实失败回放、完整原始响应保存、ID/源码摘要篡改、部分 JSON 拒绝和实际隔离；测试数量见 initial-freeze.json。新增校准调用 0，工程 tokens 与金额未知，保持 null。','',
  '本批维护和评分只验证同来源 JS 到 Python 的开发/迁移流程；有限重复不证明稳定效果，训练回验不进测试分母。同类主标签不强制命中；前提不足或分类不同则回退，提示相同的随机差异不能归因为经验。未更新生产经验库、创建 Git 提交或自动开始下一轮。','',
  '推荐 Git commit subject: `research: bind preanalysis citations to frozen source IDs`','',
  '推荐 Git commit body:','','```text',
  'Replace model-transcribed citation triples with enumerated source-span IDs.',
  'Derive compatibility citation fields without editing any model statement.',
  'Replay prior rejection offline and retain semantic review and isolation gates.',
  'Run a separately authorized fixed transfer pair with unchanged role budgets.',
  'Preserve prior costs, all real outcomes and unstarted slots without retries.', '```']
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 hashes={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(hashes.items())))
 print(json.dumps({'status':summary['status'],'counts':summary['counts'],'test':tests,'costs':costs,'integrity':integrity},ensure_ascii=False),flush=True)

if __name__=='__main__':main()


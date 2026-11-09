"""Archive stopped/complete stage accounting; this reporter never starts models."""
import json,sys,time,hashlib,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;REPO=A.parent.parent;sys.path.insert(0,str(A))
from archive import save,sha
from report_common import aggregate

def read(p,default=None):return json.loads(Path(p).read_text()) if Path(p).exists() else default

def main():
 actual=read(A/'actual-schedule.json',[])
 planned=[('D-analysis','extract','D'),('AUTO-1','repair','D'),('AUTO-2','repair','D'),
          ('reflection','reflect','D'),('development-1','repair','D'),('development-2','repair','D'),
          ('T-analysis','extract','T'),('test-B1','repair','T'),('test-A1','repair','T'),('test-A2','repair','T'),('test-B2','repair','T')]
 slots=[];costrows=[]
 for name,phase,alias in planned:
  rec=next((r for r in actual if r['name']==name),None)
  root=A/'runs'/rec['slot']/'archive' if rec else None
  valid_analysis=bool(rec and rec.get('preanalysis_valid')) if phase=='extract' else None
  valid_score=bool(rec and rec.get('scoring_status')=='COLLECTED' and rec.get('score_result',{}).get('score_valid')) if phase=='repair' else None
  row={'name':name,'phase':phase,'alias':alias,'started':rec is not None,
       'service_and_JSON_complete':rec.get('candidate_complete') if rec else None,
       'valid_analysis':valid_analysis,'valid_behavior_score':valid_score,
       'status':'NOT_STARTED' if rec is None else 'ADMISSION_REJECTED' if phase=='extract' and not valid_analysis else rec['status'],
       'failure':rec.get('preanalysis_error') or rec.get('failure_class') if rec else None,
       'behavior_outcome':rec.get('score_result') if valid_score else None,
       'archive':str(root.relative_to(A)) if root else None}
  slots.append(row)
  if rec:costrows.append({'phase':phase,'usage':read(root/'usage.json'),'seconds':rec.get('seconds')})
 costs={'preanalysis':aggregate([r for r in costrows if r['phase']=='extract']),
        'reflection':aggregate([r for r in costrows if r['phase']=='reflect']),
        'maintenance':aggregate([r for r in costrows if r['phase']=='repair']),
        'model_total':aggregate(costrows),
        'offline_calibration':{'native_invocations':len(read(A/'calibration-summary.json')),
                              'seconds':sum(read(f)['seconds'] for f in (A/'calibration').glob('*/*/receipt.json')),'model_calls':0},
        'engineering':{'batch_wall_seconds':time.time()-read(A/'initial-state.json')['time'],'tokens':None,'money':None}}
 case_summary=[{'case':c['case'],'role':c['role'],'unit':c['independent_unit_id'],
                'effect_dimensions':len(read(A/'materials'/c['alias']/'standards.json')),
                'candidate_sha256':c['candidate_files'],'oracle_sha256':c['oracle_files'],
                'exposure':c['exposure']} for c in read(A/'cases.json')]
 summary={'status':'complete' if (A/'completion.json').exists() else 'stopped','stop':read(A/'stop.json'),
  'cases':case_summary,'maximum_sessions':11,'maximum_requests':228,
  'counts':{'planned_sessions':11,'started_sessions':len(actual),'not_started':11-len(actual),
            'valid_preanalyses':sum(bool(r['valid_analysis']) for r in slots),
            'invalid_preanalyses':sum(r['started'] and r['phase']=='extract' and not r['valid_analysis'] for r in slots),
            'maintenance_sessions_started':sum(r['started'] and r['phase']=='repair' for r in slots),
            'valid_behavior_scores':sum(bool(r['valid_behavior_score']) for r in slots)},
  'slots':slots,'costs':costs,'experience_generated':(A/'development/experience-object.json').exists(),
  'test_pass_rate':None,'test_pass_rate_display':'通过率不可计算',
  'new_experience_effect':'unknown, no valid maintenance score',
  'source_evidence_audit':read(A/'source-evidence-audit.json'),
  'proposed_primary_class':read(A/'preanalysis-object.json',{}).get('primary_class'),
  'admitted_primary_class':None if not (A/'derived/D/semantic-review.json').exists() else read(A/'derived/D/analysis.json')['primary_class'],
  'no_old_experience_seed':True,'no_behavior_failure_imputed_to_unstarted_slots':True}
 save(A/'summary.json',summary);save(A/'costs.json',costs)
 save(A/'behavior-vectors.json',{'training_models':[],'development_models':[],'test_models':[],
     'reason':'No maintenance session started; offline calibrations excluded from experimental denominators.'})
 initial=read(A/'initial-state.json');integrity={
  'frozen_files_unchanged':all(sha(p)==h for p,h in read(A/'initial-freeze.json')['files'].items()),
  'reused_sources_unchanged':all(sha(x['source'])==x['sha256'] for x in read(A/'provenance.json')['reused_code']),
  'existing_index_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--cached','--binary'],cwd=REPO)).hexdigest()==initial['cached_diff_sha256'],
  'existing_unstaged_diff_preserved':hashlib.sha256(subprocess.check_output(['git','diff','--binary'],cwd=REPO)).hexdigest()==initial['unstaged_diff_sha256'],
  'head_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==initial['head'],
  'no_unstarted_behavior_failures':True,'no_followup_model_after_stop':True}
 save(A/'integrity.json',integrity)
 lines=['本批新训练/测试配对在训练预分析准入处停止。未启动 AUTO、反思、开发回验或测试维护。','',
  '固定训练：transfer-progress-maintenance-v2-vanilla；固定测试：transfer-progress-maintenance-v2-python3。同属 transfer-retry-abort-handoff 来源单元。存在该来源历史研究及作者依据旧结果设计的暴露记录，未伪造未见状态，也不称为独立泛化测试。','',
  '本批实现并冻结了独立的阶段控制：两次预分析、两次 AUTO、一次无工具反思、两次开发回验和四个测试维护槽位，上限 11 会话/228 请求。提取 gpt-6-sol / low、12 请求；维护 gpt-5.6-terra / low、24 请求；反思 gpt-5.6-terra / medium、12 请求；各 600 秒、并发 1，无重试或换例。', '',
  '已完成零模型准备：原始候选、任务、来源、AST、评分器和环境快照；18 份原始/参考/退化变体校准全部通过可信度检查，23 项运行器/归档/路由离线检查通过。JS 使用声明的 Node 16.20.2，Python 使用 CPython 3.8.10。评分分别保留 20、26 个完整维度，没有删减、统一或改写。没有安装依赖。', '',
  '停止原因：', '',
  '训练预分析服务正常完成，JSON schema 正确，实际读取了全部七个 JS 产品文件；归档与计量正常。但源码证据绑定核查失败，原错误为 primary_class_without_source_evidence。逐条检查发现两处：', '',
  '- 分类依据将 README 第 47 行的引文写成第 46 行。引文在第 47 行唯一匹配，这仅作为审计定位，不回填模型对象。',
  '- observer_lifetime 前提引用的文字含有不属于源码的 `        }]` 尾部，任何一行都无法逐字匹配。这不是单纯行号偏移。', '',
  '未手工修复引用、补全输出、重跑预分析或把当前输出冒充有效自动 Contract。模型提出的 T1 标签保留为未准入原始输出；此次失败不证明分类标签本身错误，也没有完成其全部语义核查。引用的机械失败与业务机制判断分开记录。', '',
  '|阶段|计划|启动|有效准入/评分|未启动|','|---|---|---|---|---|',
  '|预分析|2|1|0|1|','|训练 AUTO|2|0|无评分|2|','|反思|1|0|无候选|1|','|开发回验|2|0|无评分|2|','|测试维护|4|0|无评分|4|','',
  '测试通过率不可计算。原始与参考校准是离线评分可信度检查，不是模型修复结果，不并入训练或测试分母。未启动槽位没有被计作行为失败，不能据此宣称新经验有效/无效或该案例过难。', '',
  '费用与用量：', '',
  '- 新增实验模型：1 次预分析会话，3 个底层请求，46,733 tokens，2 次工具尝试，34.472 秒；未知请求用量 0。',
  '- 反思、维护及测试模型调用均为 0。',
  '- 离线原生校准评分 18 次，模型调用 0。具体时间和版本见 calibration-summary.json、calibration/*/*/receipt.json 及 costs.json。',
  '- 工程准备 tokens 和金额无法读取，保持 null，不补零。', '',
  '归档包含 protocol.json、原始材料与源码/评分摘要、初始冻结、实际调度、完整原始模型流、解析对象、源码引用核查、请求/工具事件、原始错误/归档状态、用量、18 份校准和完整性记录。预分析代码保持只读，最终快照与原始候选相同。', '',
  '本轮没有执行到经验生成与迁移验证，因此这两段接口虽然已准备，尚未在本批模型试验中验证。没有把旧 query 经验或旧 transfer E2 当作本批新训练成果或反思种子。固定案例未替换，未更新生产经验库，未创建提交或自动开展下一轮。', '',
  '推荐 Git commit subject: `research: archive transfer-pair preanalysis evidence rejection`', '',
  '推荐 Git commit body:', '', '```text',
  'Prepare a fixed JS/Python transfer-progress pair with exact source snapshots,',
  'native scoring calibration and bounded stage budgets.',
  'Reuse null-safe isolation, metering, archival and single-source reflection code.',
  'Preserve the first automatic analysis and its two unbound source citations.',
  'Stop before repair or learning without rebinding, retries or case replacement.',
  'Record known cost, all unstarted slots and unavailable behavioral effects.','```']
 (A/'REPORT.md').write_text('\n'.join(lines)+'\n')
 hashes={str(p.relative_to(A)):sha(p) for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(hashes.items())))
 print(json.dumps({'status':summary['status'],'counts':summary['counts'],'costs':costs,'integrity':integrity},ensure_ascii=False))

if __name__=='__main__':main()

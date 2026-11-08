"""Training-only evaluator projection; never reads validation scores or patches."""
from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (A/'stop.json').exists() and not (A/'reflection-input.md').exists()
c=read(A/'cohort.json')['cases'][0];assert c['case']=='transfer-progress-composition-v4-vanilla'
# Relations grounded in task/README and corresponding source; source binding is independent of reference implementation.
relations={
'warm-bootstrap':('Install the panel receiver before a synchronous producer can emit; retain ordinary streaming.',['README.md','src/progress.js']),
'start-switch-admission':('Invalidate admission immediately when synchronous delivery replaces the current visit, including before setup returns its cleanup handle. Already admitted completion still records history.',['README.md','src/progress.js','src/transfer.js','src/queue.js','src/panel.js']),
'accepted-after-hide':('Separate admission lifetime, accepted completion/history lifetime and current-view eligibility.',['README.md','src/progress.js','src/queue.js','src/transfer.js']),
'frame-in-order':('Preserve ordinary stream publication and audit while repairing startup.',['README.md','src/progress.js','src/queue.js']),
'frame-reversed':('Visible full-frame freshness follows packet arrival, not decode completion or payload magnitude; history retains accepted completions.',['README.md','src/progress.js','src/queue.js']),
'cleanup-switch':('Retire ownership before synchronous cleanup, then revalidate the outer navigation request before starting its destination.',['README.md','src/progress-source.js','src/panel.js']),
'cleanup-hide':('A synchronous cleanup navigation/hide supersedes the outer navigation destination.',['README.md','src/progress-source.js','src/panel.js']),
'composed-reverse-cleanup-switch':('Admission, completion/history, visit-wide freshness and cleanup priority must compose on a single event path.',['README.md','src/progress.js','src/queue.js','src/panel.js','src/transfer.js']),
'retry-preserved':('Retry remains in its visit and accepts one command; its cancellation/queue ordering is preserved, while stale completions cannot roll current display back across attempts.',['README.md','src/retry.js','src/notice.js','src/queue.js']),
 'telemetry-scope':('Keep the independent diagnostic consumer live-delta-only and preserve its cleanup and accepted completion.',['README.md','src/telemetry.js'])}
base=read(Path(c['calibration'][0]['raw']));runs=[];target=set();files=[]
for i in [1,2]:
 d=A/'runs'/f'js-base-{i}';s=read(d/'score.stdout.json');rec=read(d/'receipt.json');assert rec['infrastructure_valid'] and rec['scoring_valid']
 required=read(A/'materials'/c['case']/'evaluation/effects.json')['variants']['ungranted']['required']
 failed=[k for k in required if not s['observed_effects'].get(k)];target.update(failed)
 diffs=[]
 for name in failed:
  desc,paths=relations[name];trace=s['schedules'][name]['trace']
  diffs.append({'relation':desc,'sources':[{'file':f,'sha256':c['candidate_files'][f]} for f in paths],'observed_training_trace':trace,'evidence_source':f'runs/js-base-{i}/score.stdout.json schedules/{name}','note':'This relation failed external observation; root-cause responsibility remains a hypothesis until traced to actual patched code.'})
 preserve=[k for k,v in s['observed_effects'].items() if v and k in required]
 runs.append({'repeat':i,'source_bound_differences':diffs,'preserve_observed_relations':[relations[k][0] for k in preserve],'passed_assertions_evaluation_side_only_count':sum(a['passed'] for v in s['schedules'].values() for a in v['assertions']),'model_report':(d/'raw-answer.txt').read_text(),'actual_patch':(d/'patch.diff').read_text(),'unknown_causes':'Observed schedule failure does not alone establish which missing guard or ownership scope caused it; training traces and patch must be inspected.'})
 files.extend([d/'score.stdout.json',d/'patch.diff',d/'raw-answer.txt'])
feedback={'AI_assisted_evaluator_projection':True,'standard_contract_not_delivered':True,'reference_patch_not_delivered':True,'validation_material_not_read':True,'runs':runs,'preservation_requirements':['All accepted history exactly once even after retirement; no newly admitted retired work.','Current visit UI and visit-wide arrival freshness; accepted retry command/queue record and cancellation ordering.','Idempotent cleanup/navigation precedence, four-field queue schema without added authorization.','Diagnostic consumer retains distinct live-delta policy and cleanup.'],'unknowns':['Failures may share a cause; counts are not independent obligations.','Host asynchronous rejection and physical-completion policy outside visible specification remain unknown.']}
save('training-feedback.json',feedback)
source='\n\n'.join('SOURCE '+str(p.relative_to(A/'materials'/c['case']/'candidate'))+'\n'+p.read_text() for p in (A/'materials'/c['case']/'candidate').rglob('*') if p.is_file() and p.suffix in ['.js','.md'])
prompt='''根据以下训练例的源绑定差异与真实维护结果，只进行一次 Reflection，输出一份新的通用时序修复经验。不修改模型权重，不进行搜索或第二轮改写。\n经验必须覆盖：适用机制/前提、应查证的事件关系、应采取的验证动作、应保留的相邻行为、可能不适用情况。\n严禁写入任何案例ID、测试/评分断言名称、测试专用值、可直接复制的补丁、具体文件名或JS API名称；用跨语言事件/身份/生命周期关系描述。不能把推测变成新业务政策。不要提及验证题。只输出经验正文。\n返回JSON，唯一字段report，最多6000个Unicode字符。不能调用工具。\n\n训练原任务：\n'''+(A/'materials'/c['case']/'task.md').read_text()+'\n\n训练候选可见文档和源码：\n'+source+'\n\n评价侧源绑定差异投影及实际训练结果：\n'+json.dumps(feedback,ensure_ascii=False,indent=2)
(A/'reflection-input.md').write_text(prompt)
save('training-targets.json',{'targets':sorted(target),'acceptance':'PLAN.md frozen before reflection','comparison':'corresponding repeat behavioral vectors; no model sampling seed claim','requirements':'At least one target false→true in actual business patch; no loss of any corresponding baseline or original passed assertion/required effect; no forbidden effects or unsupported policy; actual experience implementation and verification.'})
files += [A/'training-feedback.json',A/'reflection-input.md',A/'training-targets.json',A/'PLAN.md']
save('training-feedback-freeze.json',{'frozen_before_reflection':True,'files':{str(p):sha(p) for p in files},'training_only':True})
print('Training feedback frozen; targets',sorted(target))

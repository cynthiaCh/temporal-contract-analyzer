"""Offline projection of this batch's development evidence only; no model calls."""
from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):(A/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (A/'stop.json').exists() and not (A/'reflection-input.md').exists()
rows=read(A/'actual-schedule.json');assert len(rows)==3
rules=read(A/'materials/evaluation/effects.json')['variants']['ungranted'];targets=set();runs=[];files=[]
relations={
 'offline-nonconsuming-detach':'Retiring an initial never-entered paused operation must also settle its attempt and restore an idle activity state; merely skipping invocation may leave an orphaned paused state.',
 'offline-detach-false':'A final observer may retire initial paused work before entry; reconnect cannot start that retired attempt with a live signal.',
 'offline-detach-true':'Observer retirement is independent of the reconnect-refetch presentation option.',
 'offline-detach-always':'Reconnect-refetch options do not replace retryer continuation/attempt validity.',
 'last-observer-offline':'The final observer boundary differs from removal of one observer while others remain.',
 'multiple-observers':'Shared work remains valid while another observer is still attached.',
 'cached-paused-background':'Previously successful cached, unconsumed paused refresh can retain a legitimate background lifetime.',
 'cached-later-consumption':'A cached paused operation retains its allowed future invocation, including a future signal read.',
 'detach-after-resume-queued':'Eligibility release can queue a continuation; observer removal before actual entry still changes attempt lifetime.',
 'nonconsuming-flight-cache':'Already-entered unconsumed work can still complete into the independent cache after observer departure.',
 'retained-context-query-flag':'Consumption ownership and physical controller ownership are distinct; retained context access records consumption on its owning query, without switching controllers.',
 'cached-prior-consumed-success':'Creating a new paused attempt does not by itself erase prior query-level consumption before actual function entry.',
 'cached-prior-consumed-cancelled':'Paused creation and actual entry reset points differ; preserve query-level consumption and previous cached state.',
 'accepted-resume-then-offline':'Do not revoke an already accepted continuation solely because online state changed after eligibility release.',
 'consumed-flight-cancel':'Consumed work cancellation must settle the originating attempt, restore previous state, abort its controller and reject late commits.',
 'cached-consumed-revert':'Cancellation restores prior cached data/status, not a fresh empty state.',
 'late-old-generation':'Completion belongs to its original attempt; old fulfillment cannot overwrite a newer attempt.',
 'nonconsuming-cancel-retry':'Stopping retries does not revoke every legitimate in-flight completion; distinguish retry admission from settlement.',
 'dependency-config-preserved':'Only product source is authorized; dependency lock and build configuration remain unchanged.'}
for i in [1,2]:
 d=A/'runs'/f'base-{i}'/'archive';rec=read(d/'receipt.json');score=read(d/'score/stdout.json');assert rec['infrastructure_valid'] and rec['scoring_status']=='COLLECTED'
 failed=[k for k in rules['required'] if not score['observed_effects'][k]];targets.update(failed)
 diffs=[]
 for k in failed:
  block=score['schedules'].get(k,{});observations=[{'observation_id':q['id'],'actual':q.get('actual'),'passed':q['passed']} for q in block.get('checks',[]) if not q['passed']]
  diffs.append({'source_bound_relation':relations.get(k,'Preserve the README-defined observer/attempt/network-mode/lifetime behavior; inspect the actual failing state and corresponding candidate methods, rather than adding new policy.'),'source_files':[{'path':'README.md','sha256':sha(A/'materials/candidate/README.md')},{'path':'src/session.js','sha256':sha(A/'materials/candidate/src/session.js')}],'observed_calls':block.get('calls'),'observed_state':block.get('state'),'observed_failing_checks_actual_only':observations,'runtime_error':block.get('runtimeError'),'evidence_reference':f'runs/base-{i}/archive/score/stdout.json schedules/{k}','unknown':'Failure alone does not establish which field/guard is responsible. Trace the actual patch; policy must be supported by task/README/source.'})
 runs.append({'repeat':i,'differences':diffs,'observed_preserve_effects':[k for k in rules['required'] if score['observed_effects'][k]],'actual_model_report':(d/'raw-answer.txt').read_text(),'actual_patch':(d/'patch.diff').read_text()})
 files += [d/'score/stdout.json',d/'raw-answer.txt',d/'patch.diff']
feedback={'AI_assisted_projection':True,'standard_contract_or_reference_patch_not_delivered':True,'history_not_used_as_feedback':True,'runs':runs,'preservation':'Keep shared observers, lazy consumption ownership, cached/background completion, cancellation rollback/settlement, generation validity, accepted continuation order, network/focus/retry policy and dependency configuration. Do not infer all work should be cancelled when a view leaves.','unknowns':'No complete upstream-library equivalence or arbitrary external host policy is inferred.'}
save('training-feedback.json',feedback);save('training-targets.json',{'targets':sorted(targets),'criteria_frozen_in':'PLAN.md','comparison':'corresponding independent repeat; no sampling-seed equivalence','no_reference_patch':'all differences source-bound'})
source='\n\n'.join('SOURCE '+str(p.relative_to(A/'materials/candidate'))+'\n'+p.read_text() for p in (A/'materials/candidate').rglob('*') if p.is_file() and p.suffix in ['.js','.md'])
prompt='''根据本批同题开发的源绑定差异与真实维护结果，只做一次Reflection，输出一份通用时序修复经验。训练是经验文本更新，不是权重训练，不进行搜索或第二轮改写。\n经验须写明适用机制与前提、应查证的事件关系、验证动作、必须保留的相邻行为、不适用情况。\n不得写入案例ID、评分/测试断言名称或专用值、文件名/API/字段名、可直接复制的代码补丁。使用事件、身份、归属和生命周期关系表达；不要把观察猜测升级为新政策。只输出经验正文。\n返回JSON唯一字段report，最多6000个Unicode字符。不要调用工具。\n\n原任务：\n'''+(A/'materials/task.md').read_text()+'\n\n候选可见文档与源码：\n'+source+'\n\n仅本批开发差异与补丁：\n'+json.dumps(feedback,ensure_ascii=False,indent=2)
(A/'reflection-input.md').write_text(prompt);files += [A/'training-feedback.json',A/'training-targets.json',A/'reflection-input.md',A/'PLAN.md']
save('feedback-freeze.json',{'before_reflection':True,'files':{str(p):sha(p) for p in files},'one_candidate_only':True})
print('Feedback frozen; targets',sorted(targets))

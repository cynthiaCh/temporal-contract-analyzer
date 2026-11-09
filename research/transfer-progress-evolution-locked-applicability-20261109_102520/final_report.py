"""Derived reporting for the scoped batch, never an experiment launcher."""
import hashlib,json,subprocess
from pathlib import Path
from evolve import A,P,read,save,sha
import report as common
Q=A.parent/'transfer-progress-evolution-20261109_100402'

def finish():
 common.report()
 s=read(A/'summary.json');s['protocol_version']='locked-applicability-1'
 s['locked_metadata_provenance']=read(A/'locked-metadata-provenance.json')
 s['metadata_invariance']=read(A/'development/metadata-invariance.json')
 s['composition']=read(A/'development/composition.json')
 s['previous_rejected_batch_cost_separate_not_recharged']=read(Q/'costs.json')['new_total']
 s['previous_rejected_candidate_unchanged']=True
 s['offline_checks']=34
 # Read-only execution audit. No new execution, scorer invocation or causal
 # intervention is introduced by reporting these archived commands/outputs.
 audit=[]
 for slot in ['session-02','session-03']:
  arc=A/'runs'/slot/'archive';commands=[]
  for line in (arc/'tool-outputs.jsonl').read_text().splitlines():
   event=json.loads(line);item=event.get('item',{})
   if item.get('type')=='command_execution' and ('/runtime/node' in item.get('command','') or 'git diff' in item.get('command','')):
    commands.append({'event_line':event['event_line'],'command':item.get('command'),'exit_code':item.get('exit_code'),'output':item.get('aggregated_output')})
  audit.append({'slot':slot,'patch_sha256':sha(arc/'patch.diff'),'actual_commands':commands,
   'source_review_AI_assisted':{
    'changed_business_files':['src/progress.js','src/queue.js','src/transfer.js'],
    'first_frame':'Both attach listener before start.',
    'admission':'Both pass a live-visit predicate to the listener and check it before decoding each new event; it is usable before the returned cleanup handle is published.',
    'retained_audit':'Both keep record(frame) in the accepted-event completion callback without requiring a current visit, preserving previously accepted delayed audit.',
    'difference':'First repair additionally gates display with listening/cancelled-attempt state; second keeps the original current-visit display guard. The full source difference is preserved; passing the 20 evaluated relations does not prove implementation equivalence outside those relations.'}})
 save(A/'execution-audit.json',{'runs':audit,'extra_test_runs':0,'extra_score_runs':0,
  'first_maintenance_verification_observation':'Actual in-start hide-followed-by-emission self-check initially observed two audits instead of one; after adding current-visit admission gating it passed. This is within-session verification evidence, not an isolated causal experiment.',
  'validation_errors_retained':'First repair initially used unavailable CustomEvent in its own test, then used native Event; it also attempted git diff in a non-Git workspace, which failed. These validation command failures are in the raw trace, not service failures or session retries. Formal patches/snapshots/digests are Python-generated.'})
 save(A/'development-admission.json',{'eligible_for_later_frozen_research':bool(s['observed_improvement_over_AUTO']) and read(A/'development/content-review.json',{}).get('development_eligible',False),
  'target_improvement_observed':s['observed_improvement_over_AUTO'],'all_regressions_recorded':True,
  'two_full_passes_required':False,'production_admitted':False,'no_automatic_test_or_next_round':True})
 save(A/'completion.json',{'sessions':3,'requests':s['costs']['new_total']['requests_started'],'valid_development_scores':s['slots']['valid_scoring'],
  'finished_authorized_scope':True,'no_test_or_next_round':True})
 if read(A/'stop.json',{}).get('kind')=='candidate':
  s['next_action']='Stop: new rules failed semantic/structural eligibility. No second candidate or maintenance with unsupported rules.'
 save(A/'summary.json',s)
 text=(A/'REPORT.md').read_text()
 stale='调用前发生一次冻结清单自引用装配拦截，0会话/0请求；原记录保存在 prelaunch-freeze-correction/。修正仅涉及冻结排除规则，离线检查重验。它不计为模型重试或行为失败。'
 text=text.replace(stale,'调用前34项离线检查及源摘要核对通过。准备阶段的通用驱动材料在任何调用前被本批显式规则修订协议替代，快照见 prelaunch-scope-snapshot/；当时0会话/0请求，无模型重试。')
 lead=['本批修复适用性字段漂移：结构化输出仅有 rules/unresolved；程序从已通过内容核查的父对象精确继承 version/requires/excludes/applicability。',
  '模型规则修订原始对象与程序合成候选分别保存。不是修改上一批被拒对象，也不把程序继承字段冒充模型新输出。正文及逐规则依据仍接受 AI 辅助语义核查。',
  f"元数据保持不变：{(s['metadata_invariance'] or {}).get('unchanged')}；原始规则与合成规则相同：{(s['composition'] or {}).get('model_rules_unchanged')}。",'']
 comparisons=read(A/'comparisons.json',[])
 gains={};losses={}
 for c in comparisons:
  gains[c['label']]=[x['effect'] for x in c['vs_AUTO'][0]['feedback']['improvements']]
  losses[c['label']]=[x['effect'] for x in c['vs_AUTO'][0]['feedback']['regressions']]
 s['gains_over_AUTO']=gains;s['losses_over_AUTO']=losses
 if s['slots']['valid_scoring']==2 and not s['observed_improvement_over_AUTO']:
  lead+=['两次完整开发回验均未观察到相对 AUTO 的改善。按本轮规则停止；后续应转查维护执行与验证接口，不自动继续增加经验文字。','']
 lead+=['新增通过与丢失行为（相对固定 AUTO）：',json.dumps({'gains':gains,'losses':losses},ensure_ascii=False),'']
 lead+=['两份实际补丁均修改 progress、queue、transfer 三个业务文件：监听先于启动；把当前访问有效性传到事件入口并在解码前核对；已接纳事件的审计仍在其解码完成时保留。第一份另有尝试取消/监听状态的显示门控，第二份沿用当前访问的显示门控；不把两份实现描述为完全相同。',
  '第一份维护在启动内部隐藏后再发事件的自测中先观察到多记审计，随后补上访问接纳门控，自测通过。原始失败和通过输出均保留。其自测还出现 CustomEvent 不可用及非Git目录中 git diff 失败，均是会话内验证命令问题，未伪装为成功、未触发额外会话。正式补丁和归档由 Python 产生。完整命令/输出与源码解释见 execution-audit.json。','']
 (A/'REPORT.md').write_text('\n'.join(lead)+text+'\n上一被拒批次仅作历史费用：1请求、86,654 tokens、62.47秒，未计入本次新增费用。\n')
 # The common inherited reporter's suggested body described the old rejection.
 body='research: lock applicability metadata during bounded rule evolution\n\nRestrict reflection output to rules and unresolved issues.\nCompose candidates from exact model rules and frozen, evidence-supported parent metadata.\nReject unexpected fields without stripping them; retain full semantic checks and raw lineage.\nArchive one reflection and the authorized independent development slots with unchanged 20-relation scoring.\nPreserve all gains, losses, costs and unstarted slots without updating production experience.\n'
 (A/'COMMIT_MESSAGE.txt').write_text(body)
 save(A/'summary.json',s)
 sources=[]
 for f in A.iterdir():
  if f.is_file() and (Q/f.name).is_file() and f.suffix in ['.py','.json','.toml']:
   sources.append({'file':f.name,'source':str(Q/f.name),'source_sha256':sha(Q/f.name),'sha256':sha(f),'operation':'byte-identical reuse' if sha(f)==sha(Q/f.name) else 'new batch adaptation/generated material'})
 save(A/'provenance.json',{'valid_parent':str(P),'rejected_previous_batch':str(Q),'full_predecessor_snapshot':'initial-state.json',
  'new_code':['locked_scope.py','test_locked_scope.py','workflow.py','final_report.py'],
  'new_raw_model_output':'development/raw-rule-revision.json','program_derived_candidate':'development/experience-object.json','program_derived_text':'development/experience.md',
  'inherited_metadata':'locked-metadata.json','sources':sources,'no_test_material':True})
 # Freeze and predecessor checks are read-only and cover all historical files.
 assert not read(A/'integrity.json')['errors']
 initial=read(A/'initial-state.json')
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==initial['HEAD']
 assert subprocess.check_output(['git','diff'],text=True)==initial['diff']
 assert subprocess.check_output(['git','diff','--cached'],text=True)==initial['cached_diff']
 hashes={str(f.relative_to(A)):sha(f) for f in A.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='ARTIFACTS.sha256'}
 (A/'ARTIFACTS.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(hashes.items())))
 for name,h in hashes.items():assert sha(A/name)==h
 print(json.dumps({'status':s['status'],'slots':s['slots'],'scores':[r['satisfied_count'] for r in s['evolved_development']],
  'gains':gains,'losses':losses,'new_costs':s['costs']['new_total'],'files_checked':len(hashes)},ensure_ascii=False))

if __name__=='__main__':finish()

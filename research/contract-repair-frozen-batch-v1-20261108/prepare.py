"""Prepare one fixed cohort and run unchanged, host-side, zero-model calibration."""
import csv, hashlib, json, os, random, shutil, subprocess, time
from pathlib import Path

O=Path(__file__).resolve().parent; R=O.parent.parent; B=R.parent/'temporal-contract-bench-git'
IDS=[
 'download-polling-restoration-explicit-react18',
 'audit-commit-attribution-vanilla',
 'transfer-progress-composition-v4-vanilla',
 'cached-feed-lifecycle-repair-vanilla',
 'document-submit-snapshot-vanilla',
 'commit-ack-boundary-vanilla',
 'upload-finalize-barrier-vanilla',
 'feature-flag-readiness-vue3',
 'local-config-readiness-low-cue-vue2',
 'error-reporting-retired-request-vanilla',
]
NODE16=R/'results/ad-model-effort-20261104/runtime/node-v16.20.2-linux-x64/bin/node'
NODE18=B/'results/student-case-expansion-runtime/node18/bin/node'
H=[
 'pending准备继续检查，ready后才交付。保留现有前台invalidateOnClose配置、beginGeneration和卸载失效的行为；旧generation不得写新活动。保留后台面板close仅隐藏而不取消工作。状态编码以候选PREPARATION_STATUS为据，不增加token编码或授权迁移。',
 '每次submit在入口捕获doc、actor和text。commit成功后按receipt revision只记录一次该快照审计；失败不记录成功审计。已接纳提交跨close/reopen保留，saved/error只属于当前visit最新提交。返回Promise在处理结果后定案。保留40ms预览、hide丢弃待处理查询、后续复用。失败传播值及嵌套可变性未规定。',
 '恢复warm source初始进度，保留普通streaming、公共API和相邻telemetry。README定义select创建visit、retry仅替换物理attempt、同文件重选创建新visit，feed对象共享。decode可能异步；不得用较旧帧回退当前显示。保留history与UI各自归属、同步宿主回调、队列记录结构及原导航/取消/cleanup行为；未授权新增byteCount。',
 '接收warm cache首批和后续增量。更换选择或hide后旧visit不再产生可见输出，同feed重用仍是新visit，当前监听继续工作。paintRows可同步导航或返回layout Promise；count只在paint完成且visit仍当前时显示，普通live count仍需保留。已接纳batch解码完成后history仍记录；移除监听不撤销已开始解码/绘制。metrics只看增量，保持其现有策略、API和payload。',
 'edit按现有trailing utility在120ms静默后只写该burst最新值，后续burst仍可保存。close/open返回时离开文档最后接纳编辑已持久化；先退休旧badge。保留按请求开始顺序后发导航优先。submit入口确定文档和文本，无selection返回null，否则同步返回恰好一个不可变receipt；capture前先持久化，接纳提交跨后续导航仍存在。notice只属原visit，导航清旧notice，同文档重开也是新visit。保留public API及40ms预览hide丢弃/可复用。',
 '只修direct profile saving。commit失败不得显示success或导航，成功结果应在commit之后。保留公开run结果形态以及outbox现有enqueue acknowledgement策略，不将它改成等待delivery。',
 '只修application submission。提交record时应已包含所选文件附件；不能先提交metadata再补上传。保留公开接口及相邻telemetry原有metadata flushing时序，不迁移telemetry。',
 '只修premium action，使已entitled用户在flag尚未就绪时的首次click于就绪后得到处理；保留已经就绪路径和普通界面API。不得迁移emergency control现有早期行为；不增加额外权限或输入字段。',
 'Personnel editor改用现有local JSON并保留父身份、声明式rule、option和unit picker行为。SchemaForm的imperative API由mounted后定时发布，rule watcher也支持value；不能把请求延迟当API就绪保证。仅迁移Personnel，不迁移Structure或更改共享接口。具体实现不限于一种。',
 '首个请求仅在error.retryable===true时用提供的timers等待20ms重试一次，第二次不再重试。reporter记录最终load失败，不记录成功或已恢复的初次错误。保留入口id/route、终止报告在close后仍发生的现有行为和current/latest的UI守卫，close/reopen不能把旧UI写到新visit。保留预览和public接口；不推定新的返回值政策。',
]
WHY=[
 '经验来源U2的显式同源变体；候选已有generation及foreground close配置，避免原low-cue评分政策冲突。开发诊断，不算独立泛化。',
 '其他来源，Promise入口快照/审计与UI归属。既有六槽全PASS，保留容易任务及不适用边界。曾与debounce案例共享辅助模板。',
 '其他来源，注册/异步decode/重入cleanup组合。既有可信失败与不稳定来源，不以本轮效果选择。',
 '其他来源，warm bootstrap与异步paint/history不同归属；listener同源派生，旧研究已暴露。',
 '其他来源，debounce/flush/入口快照/同步重入；旧维护和GEPA已暴露，并与C3共享辅助模式。',
 '其他来源，commit先后；旧自主/RAG较易通过，用于检查退步。',
 '其他来源，upload barrier与telemetry相邻策略保留。已有authored corpus暴露。',
 '其他来源，flag首次readiness；旧研究较易通过，用于检查退步。',
 '其他来源，本地配置迁移/API readiness；历史自主/RAG有失败，后续也有通过。',
 '其他来源，timer retry/终止错误与view隔离；与audit共享controller/preview辅助模式，不声称独立来源数量。',
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def locate(cid):
 hits=[p.parent for pattern in ['cases/*/case.json','case-clusters/*/arms/*/case.json'] for p in B.glob(pattern) if p.parent.name==cid]
 assert len(hits)==1,(cid,hits)
 return hits[0]

def main():
 assert not (O/'cohort.json').exists(), 'Never overwrite prepared inputs.'
 # First fix the intended IDs and selection reasons, before any new scoring.
 save(O/'selection-before-calibration.json',{'ids':IDS,'reasons':WHY,'selection_uses_new_repair_results':False,'replacement_policy':'No replacements. Defer any invalid case and freeze reduced size before calls.'})
 rows=[]
 for index,(cid,h,why) in enumerate(zip(IDS,H,WHY),1):
  case=locate(cid); m=json.loads((case/'case.json').read_text()); d=O/'materials'/cid
  assert not list(case.rglob('AGENTS.md')), 'Review applicable instructions before proceeding.'
  shutil.copytree(case/'base',d/'candidate');shutil.copyfile(case/m['diagnostic_tasks']['maintenance']['core_prompt'],d/'task.md')
  (d/'H.md').write_text(h+'\n')
  source_files=[d/'task.md']+list((d/'candidate').rglob('*'))
  source_text='\n\n'.join('FILE '+str(p.relative_to(d))+'\n'+p.read_text() for p in sorted(source_files) if p.is_file())
  (d/'visible-source-bundle.txt').write_text(source_text)
  # Reference contract is researcher-curated from visible sources; no claim of human review.
  save(d/'H.provenance.json',{'status':'AI manually curated source-grounded reference; not independently expert-authored or approved','sources':{'task':str(case/m['diagnostic_tasks']['maintenance']['core_prompt']),'README':str(case/'base/README.md') if (case/'base/README.md').exists() else None,'candidate_files':hashes(d/'candidate')},'not_used':['oracle','reference patch','hidden assertions'],'scope_review_required':True})
  row={'case':cid,'index':index,'source_case':str(case),'unit':m['independent_unit_id'],'provenance':m['provenance'],'mechanisms':m['construct'],'source_group':'same_source_variant' if index==1 else 'other_source','experience_source':False,'prior_exposure':'Historically authored/research-exposed corpus; not independent generalization. '+why,'selection_reason':why,'node':str(NODE18 if index==1 else NODE16),'candidate_files':hashes(d/'candidate'),'task_sha256':sha(d/'task.md'),'case_manifest_sha256':sha(case/'case.json'),'oracle_files':hashes(case/'oracle'),'calibration':[],'status':'awaiting_scope_review'}
  save(O/'cohort-progress.json',rows+[row])
  node=row['node']
  labels=[('unchanged',None),('reference-bounded',case/m['references']['bounded'])]+[(p.replace('/','-'),case/p) for p in m.get('mutants',[])]
  for label,overlay in labels:
   out=O/'calibration'/cid/label;shutil.copytree(d/'candidate',out/'candidate')
   if overlay:shutil.copytree(overlay,out/'candidate',dirs_exist_ok=True)
   command=[node,str(case/m['oracle']['probe']),str(out/'candidate'),'ungranted']
   start=time.time()
   try:
    proc=subprocess.run(command,capture_output=True,text=True,timeout=90)
    (out/'stdout.json').write_text(proc.stdout);(out/'stderr.txt').write_text(proc.stderr)
    try:score=json.loads(proc.stdout);verdict=score['verdict']
    except (ValueError,KeyError):score={};verdict=None
    rec={'label':label,'command':command,'seconds':time.time()-start,'exit_code':proc.returncode,'verdict':verdict,'effects':score.get('observed_effects'),'raw':str(out/'stdout.json')}
   except subprocess.TimeoutExpired as exc:
    (out/'stdout.partial.txt').write_bytes(exc.stdout or b'');(out/'stderr.partial.txt').write_bytes(exc.stderr or b'');rec={'label':label,'command':command,'seconds':time.time()-start,'status':'timeout','verdict':None}
   row['calibration'].append(rec);save(out/'receipt.json',rec)
  row['calibration_valid']=all(x.get('verdict') for x in row['calibration']) and row['calibration'][1]['verdict']=='PASS' and all(x['verdict']!='PASS' for x in row['calibration'][2:])
  rows.append(row);save(O/'cohort-progress.json',rows);print(cid,'calibration',[(x['label'],x['verdict']) for x in row['calibration']],flush=True)
 save(O/'cohort.json',{'cases':rows,'experience_source_case':'download-polling-restoration-low-cue-react18 (diagnosis only, deferred)','deferred':[{'case':'download-polling-restoration-low-cue-react18','reason':'scorer requires lifecycle policies unavailable in candidate task/source'},{'case':'listener-registration-order-vanilla','reason':'existing scorer makes unresolved late-decode policy mandatory'}],'selection_frozen_before_model_calls':True,'independent_generalization_cases':0})
 # Fix case/repeat blocks, then interleave four arms within each block.
 rng=random.Random(2026110801); blocks=[(cid,rep) for rep in [1,2] for cid in IDS];order=[]
 for cid,rep in blocks:
  groups=['N','H','M','E'];rng.shuffle(groups)
  for group in groups:order.append({'slot':'b%03d'%(len(order)+1),'case':cid,'repeat':rep,'condition':group,'status':'NOT_STARTED'})
 save(O/'schedule.proposed.json',{'seed':2026110801,'role':'scheduling only, not model sampling','max_concurrent_maintenance':1,'order':order})
 old=R/'research/contract-extraction-cross-case-v1-20261107'
 shutil.copyfile(old/'run.py',O/'native_backend.py')
 shutil.copyfile(R/'research/u2-contract-repair-diagnostic-v1-20261108/request_guard.py',O/'request_guard.py')
 shutil.copyfile(Path.home()/'.codex/models_cache.json',O/'models-cache.snapshot.json')
 shutil.copyfile(R/'research/contract-extraction-evolution-u2-v2-20261107/contract_extraction_K1.md',O/'contract_extraction_K1.md')
 (O/'research-config.toml').write_text('model = "gpt-5.6-terra"\nmodel_reasoning_effort = "medium"\nservice_tier = "priority"\n')
 save(O/'extraction.schema.json',{'type':'object','properties':{'report':{'type':'string','maxLength':6000}},'required':['report'],'additionalProperties':False})
 save(O/'budget.json',{'intended_cases':10,'repeats':2,'maintenance_sessions':80,'extraction_sessions_max':10,'extraction_reuse':0,'total_sessions_max':90,'per_session_requests':12,'total_requests_reserved':1080,'seconds_per_session':600,'total_session_seconds_reserved':54000,'final_report_characters_per_session':6000,'final_report_characters_total_max':540000,'concurrency':1,'automatic_retries':0,'cost_currency':None,'financial_quota_verified':False,'note':'Final report character cap is not a cap on all reasoning/output tokens. No verified monetary price or account-quota information; no invented dollar estimate.'})

if __name__=='__main__':main()

"""Record source-grounded admission, original metric roles and exposure indexes."""
import json, subprocess
from pathlib import Path
O=Path(__file__).resolve().parent; R=O.parent.parent; B=R.parent/'temporal-contract-bench-git'
def read(p):return json.loads(p.read_text())
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
 cases=read(O/'cohort.json')['cases']; scopes=[];metrics={}
 reasons=[
  '原task规定pending继续/ready交付；候选DownloadDialog传invalidateOnClose=true，usePreparation的beginGeneration、旧generation守卫、clearRetry和close保留政策；后台hook明确注释close不取消workspace工作。评分关闭与重开不再依赖未提供的额外前台政策。',
  '原task规定Promise处理/保留其他消费者；README:3直接规定入口快照、单次成功审计、失败不审计、跨关闭接纳、current/latest UI；README:5预览40ms/hide/reuse。原worker不检查未决拒绝值、宿主异常或嵌套可变性。',
  'task明确首帧、逆序不得回滚及保留retry/navigation/cleanup/audit；README规定visit/attempt/feed同步和Promise关系。源码queue将record与current visit UI分开；panel请求序号防止重入覆盖，progress-source移除后同步通知，telemetry注释delta-only。评分属于这些公开可恢复行为，无新的byteCount授权。',
  'task明确修startup/navigation行和count；README完整规定visit退休、同feed新visit、count等待paint且visit当前、accepted history跨退休、监听移除不取消已启动decode、metrics delta-only。可见规范直接覆盖原评分生命周期要求，与旧C1的政策缺口不同。',
  'task规定120ms静默/后续burst/保留API和preview；README直接规定close/open持久、badge退休、inline回调与后发请求优先、submit入口immutable receipt/先持久化/跨导航保留/visit notice/empty；无未决政策被强制评分。',
  'task直接要求commit失败无success/navigation，只改direct保留outbox；target/adjacent/flow公开结果及events为现有可观察效果。单终止结果是既有公开接口与修复失败success共存缺陷的边界。有限harness无真实数据库时序证明。',
  'task直接要求record包含attachment，明确不得迁移telemetry；source的runTarget和runAdjacent及公开events定义有限模型。评分检查模型输出，不冒称真实文件上传完成。',
  'task直接给early entitled click丢失、仅premium、不迁移emergency；源码input.loadedFlag/clickBeforeReady和相邻早期行为可见。评分是有限流程模型与组件适配，不证明真实远程配置服务。',
  'task直接要求Personnel本地替换和保留现有行为，排除Structure；candidate parentNode/rule watcher、mounted后定时API与picker可恢复保留要求。原双时序检查无要求唯一实现或固定API延时猜测。',
  'task直接规定首个retryable错误、20ms、仅一次、保留其他行为；README明示reporter是逻辑load最终结果。既有controller无条件observe已捕获operation，current/latest只守UI，close仅current=null，足以恢复终止报告与UI不同归属。原worker不强制新增return政策。',
 ]
 adjacent=[[],['preview'],['telemetry-scope'],['metrics-scope'],['preview-delay','preview-hide','preview-reuse','preview-valid'],['outbox-result-observed'],['telemetry-flushes-once'],['emergency-result-observed'],['structure-form-ready','structure-parent-values-preserved','structure-picker-opens'],['preview']]
 for c,reason,exclude in zip(cases,reasons,adjacent):
  cid=c['case'];case=Path(c['source_case']);d=O/'materials'/cid
  effects=read(case/'oracle/effects.json');roles=effects['variants']['ungranted']
  required=roles['required'];forbidden=roles['forbidden'];assert c['calibration_valid']
  if cid.startswith('download-'):target=['download-retries-until-ready-once']
  else:target=[x for x in required if x not in exclude]
  metrics[cid]={'overall':'unchanged original ungranted verdict','target_effects':target,'target_aggregation':'all specified original target effects true, report each separately','required':required,'forbidden':forbidden,'baseline_effects':c['calibration'][0]['effects'],'losses':'original required true->false/missing; forbidden false->true/missing distinguished','score_granularity':'native effects and assertions; no sum of item scores','consumer_outcomes':'preserve raw, never use maintenance_task alone as overall target'}
  sources=[]
  for p in [d/'task.md']+sorted((d/'candidate').rglob('*')):
   if p.is_file():sources.append({'path':str(p),'lines':len(p.read_text().splitlines()),'text':p.read_text()})
  scopes.append({'case':cid,'eligible':True,'AI_scope_review':reason,'independent_human_policy_review':False,'supported_by_visible_sources':True,'blank_draft_confirmation_is_not_blocker':True,'all_required_effects_reviewed':required,'all_forbidden_effects_reviewed':forbidden,'effect_to_source_scope':{effect:reason for effect in required+forbidden},'full_visible_sources':sources,'limitations':'Finite authored fixtures, not independent incidents or exhaustive production behavior. Reference/mutant calibration does not certify normative policy.'})
  provenance=read(d/'H.provenance.json');provenance['scope_review_required']=False;provenance['scope_review_result']=reason
  (d/'H.provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 save('source-scope.json',scopes);save('metric-spec.json',metrics)
 save('admission.json',{'eligible_cases':[c['case'] for c in cases],'model_calls':0,'calibration_invocations':sum(len(c['calibration']) for c in cases),'scope_review':'source-scope.json','calibration':'cohort.json','deferred':read(O/'cohort.json')['deferred'],'note':'No existing scorer altered; all ten intended cases admitted before formal calls. H is AI-assisted manually curated reference, not an independently verified human artifact.'})
 # Index all matching archival document/JSON/CSV paths in a declared scope.
 # This is exposure accounting, never a certificate of unseen data.
 roots=[R/'research',R/'results',R/'experiments',B/'studies',B/'docs',B/'experiments',B/'results/core-24-completion-20261005']
 roots=[p for p in roots if p.exists()]
 args=['rg','-l','-F','--glob','*.md','--glob','*.json','--glob','*.csv','--glob','!**/.runtime/**','--glob','!**/official-src/**','--glob','!**/contract-repair-frozen-batch-v1-20261108/**']
 for c in cases:args+=['-e',c['case']]
 proc=subprocess.run(args+[str(p) for p in roots],capture_output=True,text=True,timeout=120)
 assert proc.returncode in [0,1],proc.stderr
 exposure={c['case']:[] for c in cases}
 for name in proc.stdout.splitlines():
  p=Path(name)
  text=p.read_text(errors='replace')
  for cid in exposure:
   if cid in text:exposure[cid].append(str(p))
 save('exposure-index.json',{'search_roots':[str(p) for p in roots],'formats':['Markdown','JSON','CSV'],'command':args+[str(p) for p in roots],'matches':exposure,'interpretation':'All matching paths in declared scope, including indirect references. A mention is not proof of an actual model run or an exact source version. Known real historical runs and source lineage are separately recorded in cohort.json. Excludes giant unindexed external archives, raw transcripts and unknown pretraining; no case is claimed unseen or independently generalizing.'})

if __name__=='__main__':main()

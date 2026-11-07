from review_utils import *
rows=[]
# C1: quote-based descriptive recovery, not approved normative grading.
for c in ['s01','s07','s02','s08']:
 k1=c in ['s02','s08']
 qs={
 's01':['应呈现初始在线用户状态，并继续呈现后续 presence 更新','原任务还明确禁止修改 metrics consumer。','该函数先 `connect`，后注册监听器','源码只说明移除监听不会取消已开始的解码','未指定事件竞争时的完整顺序规则。'],
 's07':['初始在线用户状态应能出现；后续 presence 更新仍应出现','metrics consumer 不得更改','后者先 `connect`，再注册监听器','`show` 先释放旧订阅再建立新订阅','未规定其结果应否发布。'],
 's02':['初始状态和后续更新均进入面板的发布路径','不得修改 metrics consumer。','在 deferred 模式下排入 microtask','`show` 先执行旧 `release`，再保存新订阅返回的释放函数','缺少产品政策与宿主生命周期约定。'],
 's08':['初始在线用户状态应能呈现；后续 presence 更新应继续呈现','不得修改 metrics consumer。','在 deferred 模式下排入微任务','再把新订阅返回的清理函数赋给共享变量','不能断言这些情形实际发生']}
 q=qs[c]
 rows += [item(c,'C1-N1','完整文本恢复',q[0],'恢复原任务初始状态及后续更新；标准未确认，仅记录输入文本恢复。'),item(c,'C1-N2','完整文本恢复',q[1],'全文合并认可导航、transport复用与metrics增量边界；不把相邻消费者bootstrap政策套给面板。'),item(c,'C1-S1','完整关系描述' if k1 else '部分关系描述',q[2],'K1把同步/deferred调度同connect→注册关系合并描述，并限制为候选channel。' if k1 else '同步漏首事件机制已清楚；deferred主要留在建议/未知中，未展开注册后微任务发射这一对照。'),item(c,'C1-S2','完整核心关系，附术语限制' if k1 else '部分关系描述',q[3],'K1明确返回后赋release、移除不撤销已登记完成，并补充排队bootstrap在复用target时的条件性接收；请求/挂载术语需谨慎，不把条件描述视为原版窗口可达证明。' if k1 else '已有show释放、旧decode完成与政策未知；未明确展开返回后赋新release和排队发射/重开监听关系。',source_accuracy='核心引用有据；请求阶段术语不够贴合事件源码' if k1 else '准确（所引部分）'),item(c,'C1-U1','合理未知与有源验证',q[4],'接受分散表达：未把旧结果去留、外部协议、重入具体状态写为确定义务；未列尽所有未知不自动当错误。')]
# C3: all four recover the visible normative text, while no standard item is approved.
for c in ['s03','s05','s04','s06']:
 k1=c in ['s04','s06']
 qs={
 's03':['`submit` 返回在处理提交结果后才完成的 Promise。','提交失败不创建成功审计。','保存成功或错误的 UI 只属于当前访问及其最新一次提交','搜索预览当前为 40 ms、隐藏时丢弃待处理查询、可复用','同步调用方式只是当前实现事实，不能作为异步规范。','无当前访问时 `submit` 是否也必须返回 Promise'],
 's05':['返回在结果处理后才落定的 Promise。','commit 失败不得创建成功审计。','saved/error 界面更新只属于原访问仍为当前访问','搜索预览仍维持 40 ms、hide 丢弃待处理查询及可复用行为。','当前代码在 src/controller.js:13 同步调用 done','commit 拒绝后，submit 返回的 Promise 应拒绝还是兑现'],
 's04':['submit 应返回一个在结果处理完成后才定案的 Promise。','失败不得写成功审计。','saved/error 界面反馈仅属于当前打开活动中的最新提交。','其 40 ms、隐藏后丢弃待处理查询及可复用性','同步 try/catch 不能处理其异步拒绝','当前无 visit 时返回 null'],
 's06':['`submit` 应返回 Promise，并在成功或失败的结果得到处理后才结算。','失败提交不写成功审计。','saved/error 界面反馈只属于当前打开的 visit 中最新一次提交。','搜索预览的 40 ms、hide 丢弃待执行查询及可复用性','仅用同步 `try/catch` 处理异常','当前返回 `null`']}
 q=qs[c]
 rows += [item(c,'C3-N1','完整文本恢复',q[0],'任务Promise/拒绝适配、处理后settle及公开面保留已恢复；仅为待确认标准下的文本忠实度。'),item(c,'C3-N2','完整文本恢复',q[1],'全文包含入口doc/actor/text、成功后一次audit+revision、失败无成功记录及跨close/open继续历史；来源README明确，但不升级批准。'),item(c,'C3-N3','完整文本恢复',q[2],'current visit/latest owner与历史归属分别表达，原有README条款两组均恢复。'),item(c,'C3-N4','完整文本恢复',q[3],'预览范围、40ms/hide丢弃/复用信息均在全文，建议段的等价表达也认可。'),item(c,'C3-S1','部分关系描述',q[4],'K1新增当前done立即接到Promise本体、同步catch与异步settle不同的明确对照；但字段快照不保证深度不可变这一限制未显式展开。' if k1 else '识别当前同步done不足以适配Promise，未充分展开立即处理返回值/拒绝与同步catch的差别；深度不可变限制也未展开。'),item(c,'C3-U1','部分未知覆盖',q[5],'null与Promise、失败传播及audit/render异常均合理未知；doc/actor/text类型和嵌套可变性未显式记录。只记描述性缺口，不当未确认政策的能力错误。',unknown='所述未知合理；嵌套可变性未单列')]
write('item-review.csv',rows)
comparisons=[]
for pair in sorted({x['pair_id'] for x in rows}):
 r0=[x for x in rows if x['pair_id']==pair and x['condition']=='K0'];r1=[x for x in rows if x['pair_id']==pair and x['condition']=='K1'];assert len(r0)==len(r1)
 for a in r0:
  b=next(x for x in r1 if x['item_id']==a['item_id']);rel=a['kind']=='source_relationship';text=a['kind']=='documented_obligation'
  gain=('同步/deferred与已排队首事件/新监听条件更明确' if a['case']=='C1' else '当前立即处理Promise返回值、同步catch与异步拒绝的区分更明确') if rel else '无已确认Contract增量；原可见条款两组均恢复' if text else '合理未知维持；未见完整未知清单增量'
  comparisons.append({'case':a['case'],'repeat':a['repeat'],'pair_id':pair,'item_id':a['item_id'],'kind':a['kind'],'K0_slot':a['call_id'],'K1_slot':b['call_id'],'K0_descriptive_coverage':a['descriptive_source_coverage'],'K1_descriptive_coverage':b['descriptive_source_coverage'],'K0_quote':a['model_quote'],'K0_reference':a['model_reference'],'K1_quote':b['model_quote'],'K1_reference':b['model_reference'],'source_and_standard':a['standard_items']+'; '+a['source_reference'],'source_relationship_increment':gain if rel else 'not a source-relationship row','documented_clause_recovery_change':'未见丢失或新增（两组完整恢复）' if text else 'not a documented-clause row','confirmed_contract_increment':'NOT_ASSESSABLE_PENDING_CONFIRMATION','retained_correct_content':'原可见条款保持；关系描述未观察到明确反转','unsupported_added_requirements':'未发现明确新增业务要求；C1 K1有请求阶段术语限制，另见qualifications','unknown_change':b['unknown_handling'],'normative_grade':'NOT_SCORED_PENDING_CONFIRMATION','reviewer':'AI executing agent knows condition; not independent blind review'})
write('item-comparison.csv',comparisons)
qualification={'unconfirmed_norms':'Both cases have zero approved normative standard items; source fidelity is descriptive, no policy correctness score or confirmed Contract increments.','source_terminology_flags':[{'call':'s02','quote':'请求进行中、请求结束后的等待间隙及下一次 `show` 期间','citation':evidence('s02','请求进行中、请求结束后的等待间隙及下一次 `show` 期间'),'finding':'C1显式机制是decode与事件微任务，不含轮询请求周期。该句通用请求术语没有逐一对应源操作，描述精确性有限；未当作新增业务要求或已证实逻辑反转。'},{'call':'s08','quote':'请求回调持有其订阅时的 `channel`、`receive`','citation':evidence('s08','请求回调持有其订阅时的 `channel`、`receive`'),'finding':'listener闭包确实使用channel/receive，而then登记的是receive本身；请求回调的指代不够精确，不能据一句模糊表述推断模型整体理解错误。'}],'common_remaining_gaps':['C3四份报告均未单独展开字段快照与嵌套数据深度不可变的区别。'],'observed_definite_new_business_requirements':[],'observed_definite_semantic_reversals':[],'observed_documented_clause_losses':[],'no_observed_error_is_not_proof_error_free':True,'relationship_gains_not_counted_as_contract_gains':True,'case_dependence_limit':'New descriptions span first-event and async-submit mechanisms but are predominantly temporal/lifecycle relations, close to K1 development focus; two historical cases do not establish generalization.'}
save(OUT/'review-qualifications.json',qualification)
save(OUT/'review-complete.json',{'after_all_eight_slots':True,'item_rows':len(rows),'paired_rows':len(comparisons),'all_normative_grades_withheld':True,'condition_known':True,'AI_agent_evaluation':True,'independent_blind_review':False,'quality_total':None})
print('post-batch reviews',len(rows),'paired item rows',len(comparisons))

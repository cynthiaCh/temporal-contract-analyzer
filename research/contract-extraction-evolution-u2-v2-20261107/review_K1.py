from review_utils import *
rows=[];t=[]
c='k1-1'
rows += [
 make(c,'O1','完整覆盖','整个准备活动继续安排后续检查，不能将该次结果当作文件已就绪。','保持原本恢复的持续检查义务；没有选定状态格式或轮询实现。'),
 make(c,'O2','完整覆盖','请求结束至下一次请求之间 `loading` 应显示什么','结合第2节DOM消费、每次检查写入及相邻等待事实，明确字段期间未知；完整指当前证据适用范围，不指恢复隐藏loading=true答案。'),
 make(c,'O3','完整覆盖','只有收到 ready 后才交付文件。','only-ready方向保持；交付接口及是否一次仍合理未知。'),
 make(c,'O4','部分覆盖','当前没有已排队重试，所以不能声称现有弹窗在关闭后仍会轮询。','明确原前台无队列、取消入口和后台卸载取消；仍未展开后台close只隐藏→已排队时仍可能检查的具体路径。'),
 make(c,'O5','完整覆盖','`close` 只改变 visible','合并同段回调仍写共享状态及第3节生命周期政策未知，正确区分事实与应丢弃政策。'),
 make(c,'O6','完整覆盖','因此若旧请求在重开后返回，旧 token 的回调可能与新活动交错','请求捕获身份/共享写入/条件性交错均有源码支持，不断言已发生错误或唯一代隔离方案。'),
 make(c,'O7','部分覆盖','原任务未把它的状态写法、取消策略或去重方式规定为下载弹窗的义务。','明确相邻组件排队/卸载及政策不能搬用，但后台close行为仍缺失，未恢复workspace额外规格也不扣。')]
t += [timer(c,'T1','完整覆盖','当前没有已排队重试','结合相邻组件非完成后排队，辨明原前台与相邻后台的资源存在性。'),timer(c,'T2','完整覆盖','卸载时取消已保存的重试句柄并用 active 阻止回调继续处理','实际组件调用及第10-26行API入口都有定位，不等于外部取消保证。'),timer(c,'T3','部分覆盖','若新增排队重试，还需按其所属活动考察旧任务能否在新 token 下触发','条件化未来路径已有，未具体串起当前相邻后台的close隐藏与排队继续。'),timer(c,'T4','完整覆盖','缺少生命周期政策和宿主卸载行为。','同文明确实际调度时机/取消保证未定义，未把条件风险写成已发生。')]
c='k1-2'
rows += [
 make(c,'O1','完整覆盖','效果：继续安排后续检查；此时不得交付文件。','持续活动跨请求方向正确；未添加间隔或状态编码。'),
 make(c,'O2','完整覆盖','`loading` 在两次请求之间应显示 true 还是 false','前文同时追踪写入、DOM消费及等待期，字段义务合理未知；不要求选loading=true。'),
 make(c,'O3','完整覆盖','只有收到“已就绪”的结果，才交付对应文件。','只在ready之后交付方向保持；实际交付、去重未被捏造。'),
 make(c,'O4','部分覆盖','第18至27行没有排队重试或取消调用','区分原前台无timer、背景队列、卸载尝试取消及外部保证未知；未来仍挂载/可触发条件有描述，但后台close只隐藏没有单独展开。'),
 make(c,'O5','完整覆盖','关闭仅设 `visible=false`','与旧回调写共享状态及第3节关闭政策未知合并认可；没有规定必须取消或丢弃全部旧完成。'),
 make(c,'O6','完整覆盖','旧请求若在重开后返回，可与新活动交错','说明旧token/共享loading/completed，条件正确且产品隔离政策未知。'),
 make(c,'O7','部分覆盖','原任务没有要求下载对话框复制其状态表示或取消方案。','相邻组件参考边界正确，后台close只隐藏仍未陈述，不强制恢复workspace所有权。')]
t += [timer(c,'T1','完整覆盖','第18至27行没有排队重试或取消调用','同段后台未完成时排队；对象和原版本不同，未混淆。'),timer(c,'T2','完整覆盖','并在卸载时尝试取消（第14至17行）','调度取消包装和真实卸载调用位置均明确；尝试一词保留外部保证未知。'),timer(c,'T3','部分覆盖','若未来加入重试且关闭后组件仍挂载、调度仍可触发，后续检查可能继续','有条件化未来关系，未直接解释当前后台close仅隐藏的具体继续路径；不因此判前台已存在漏洞。'),timer(c,'T4','完整覆盖','需要生命周期政策及宿主行为。','另有接口未给调度/取消/传输保证的原句，未知保留充分。')]
append_reviews(rows,t)
data=read(OUT/'review-data.json');comparison=[]
for oid in [x['item_id'] for x in RULES]:
 entries={x['call_id']:x for x in data['items'] if x['item_id']==oid}
 comparison.append({'item_id':oid,'K0_repeat1':entries['k0-1']['coverage'],'K0_repeat2':entries['k0-2']['coverage'],'K1_repeat1':entries['k1-1']['coverage'],'K1_repeat2':entries['k1-2']['coverage'],'comparison':'同一开发案例，按重复编号描述，不作统计独立性或显著性推断','interpretation':{'O1':'原有明确任务义务保持','O2':'增加字段写入/消费、等待区间与合理未知说明；不是新增隐藏字段规范','O3':'原有only-ready约束保持','O4':'T1/T2/T4更明确，T3具体后台close路径仍部分覆盖','O5':'可见close/回调事实更完整，产品取消政策保持未知','O6':'捕获身份/共享状态/条件交错更完整，唯一方案未强加','O7':'相邻组件规范边界保持，但后台close事实仍未完整展开'}[oid],'evidence_references':' | '.join(x['model_reference'] for x in entries.values())})
write_csv('item-comparison.csv',comparison)
# Explicitly separate observed errors from proof of absence.
save(OUT/'unsupported-and-regression-review.json',{'review_mode':'AI executing agent, not independent human review','reports':['k0-1','k0-2','k1-1','k1-2'],'observed_semantic_reversals':[],'observed_unsupported_product_requirements':[],'observed_current_facts_miscast_as_normative':[],'lost_confirmed_obligations':[],'still_partial':['O4/T3: concrete adjacent-background queued-retry-after-close path','O7: adjacent background close only hides'],'unchanged_unknowns':['exact status representation','loading as sole full-activity indicator','foreground cancel/ignore/generation policy','actual file delivery/duplicate handling','scheduler guarantees and host mounting','workspace ownership and authorization migration'],'absence_of_observed_errors_is_not_proof_all_errors_absent':True,'longer_report_not_itself_quality_gain':True})
print('review complete',len(data['items']),'rows')

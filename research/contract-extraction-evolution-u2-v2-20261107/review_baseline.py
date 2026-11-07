from review_utils import *
rows=[];t=[]
c='k0-1'
rows += [
 make(c,'O1','完整覆盖','效果：继续检查该文件的准备状态，不能因 pending 交付文件。','准确恢复任务义务，未指定状态编码或调度策略。'),
 make(c,'O2','未覆盖','这些不足以确立下载对话框的产品规则。','未提loading消费者及单次请求/整体等待区间；不扣未断言loading=true。','其他政策合理未知；此字段期间未展开'),
 make(c,'O3','完整覆盖','只有状态为 ready 后才交付文件。','交付方向正确，另说明completed不等于已确认真实下载。'),
 make(c,'O4','部分覆盖','旁侧组件卸载时取消重试','识别卸载取消，但未解释已排队timer与close隐藏的条件性关系；仅列生命周期待确认不算完整T1-T4。'),
 make(c,'O5','部分覆盖','旧请求及重试应如何处置','保留前台政策未知合理；未展开close只隐藏和回调无生命周期守卫的事实。'),
 make(c,'O6','部分覆盖','关闭、重新打开、更换 token 或卸载时，旧请求及重试应如何处置','关注身份和生命周期，但没有追踪捕获token/共享loading/completed及旧回调交错。'),
 make(c,'O7','部分覆盖','旁侧组件按真假值处理结果只是当前实现事实','相邻实现未当成前台规范，卸载事实已有；未展开后台close只隐藏及挂载时继续的条件。')]
t += [timer(c,'T1','部分覆盖','旁侧组件使用调度器只是实现参考','只提后台调度，未明确关闭时timer存在性与原前台尚无重试。'),timer(c,'T2','部分覆盖','旁侧组件卸载时取消重试','实际取消位置提到；未结合close位置对照。'),timer(c,'T3','未覆盖','另检查关闭、重新打开和卸载时是否出现旧文件交付或遗留重试','这是检查建议，没有陈述关闭后仍可能执行检查的源码条件。'),timer(c,'T4','部分覆盖','这些不足以确立下载对话框的产品规则。','产品政策未知保留；scheduler取消/宿主挂载保证未展开。')]
c='k0-2'
rows += [
 make(c,'O1','完整覆盖','效果：继续发起后续准备检查，且此时不得将该文件视为已可交付。','恢复task规范，并明确不规定间隔次数。'),
 make(c,'O2','部分覆盖','只渲染 visible/loading 属性','识别loading消费者，未追踪字段写入和请求结束到下次检查的区间；不要求猜loading全程保持。','其他政策合理未知；等待字段期间未展开'),
 make(c,'O3','完整覆盖','只有收到 ready 后才交付对应文件。','只有ready后交付方向准确，completed/真实下载未知合理。'),
 make(c,'O4','部分覆盖','且没有安排后续检查','原前台未接后续检查、相邻后台调度已提，但没有已排队→close→可能检查路径和实际取消位置。'),
 make(c,'O5','部分覆盖','关闭、重新打开、更换 token 或卸载时对在途请求和重试的精确规则','合理未知；未具体说明close当前只隐藏及回调无guard。'),
 make(c,'O6','部分覆盖','另检查请求与交付所用的文件身份','有身份验证建议，但未解释reopen改当前token与旧请求捕获token的共享状态交错。'),
 make(c,'O7','部分覆盖','这是可参考的实现事实，不能直接当作下载对话框的完整规范。','前后台规范未混同；未展开后台close与卸载不同边界。')]
t += [timer(c,'T1','部分覆盖','且没有安排后续检查','辨明前台无后续检查与后台调度，但未专门指出关闭时已排队timer前提。'),timer(c,'T2','部分覆盖','同文件第 10–20 行提供重试调度和取消接口','只列包装接口，未定位组件卸载调用。'),timer(c,'T3','未覆盖','关闭、重开和卸载期间是否发生过期交付或无效重试','仅为验证建议，缺少挂载/隐藏/调度触发的关系。'),timer(c,'T4','部分覆盖','现有接口和生命周期代码提供线索，但原任务未指定预期效果。','产品政策合理未知；注入接口和宿主保证不足未展开。')]
append_reviews(rows,t)
feedback={'batch':'v2 only','review_mode':'AI executing-agent evaluation; not independent human review','execution_valid':['k0-1','k0-2'],'used_v1_outputs':False,'genuine_gaps':[{'items':['O2'],'observation':'k0-1未追踪waiting状态消费者，k0-2只提DOM属性；两者未将单次操作结束/后续等待/整体活动分开。','interpretation':'可见事实和待确认字段语义的提取不够具体，不要求给出隐藏loading=true答案。'},{'items':['O4','T1','T2','T3','T4'],'observation':'两份均未完整说明已排队retry时close的关系。k0-1提卸载取消，k0-2仅提取消包装；均未串起原前台无timer、后台已有排队、关闭仅隐藏、仍挂载时可能继续。','interpretation':'缺少条件化资源生命周期说明，不是必须取消的产品结论。'},{'items':['O5','O6','O7'],'observation':'均合理未知具体产品政策，但没有充分展开可见的close/reopen共享状态交错及后台close与卸载差别。','interpretation':'可确认源码事实不必与待确认规范一起省略。'}],'preserve':['O1持续检查和O3 only-ready交付已恢复，禁止损失。','两份都未指定状态编码/间隔/取消政策，无已发现无依据产品要求；保持合理未知。','不要把实现事实变为必须保留的业务义务；不指定唯一修复或变量。'],'not_skill_defects':['输入未提供loading唯一表达、完整前台取消政策、workspace所有权/授权迁移；未恢复不扣为能力失败。'],'evidence_rows':rows,'timer_rows':t,'no_total_score':True}
save(OUT/'difference-feedback.json',feedback)
K0=(OUT/'contract_extraction_K0.md').read_text();baseline={c:(OUT/'runs'/c/'contract.md').read_text() for c in ['k0-1','k0-2']}
template=(OUT/'reflection-template.md').read_text();assert sha(template)==read(OUT/'reflection-design.freeze.json')['template_sha256']
prompt=template.replace('{{K0}}',K0).replace('{{RULES}}',(OUT/'evaluation-v1.csv').read_text(encoding='utf-8-sig')).replace('{{BASELINES}}',json.dumps(baseline,ensure_ascii=False,indent=2)).replace('{{FEEDBACK}}',json.dumps(feedback,ensure_ascii=False,indent=2))
(OUT/'reflection.prompt.md').write_text(prompt)
save(OUT/'baseline-review.freeze.json',{'files':{str(OUT/n):sha((OUT/n).read_bytes()) for n in ['baseline-review.csv','difference-feedback.json','reflection.prompt.md','reflection-template.md']},'before_reflection':True,'no_v1_output_used':True})
print('baseline rows',len(rows),'timer rows',len(t))

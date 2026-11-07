1. 可确认的 Contract
原任务要求适配异步保存：service.commit(snapshot) 返回 receipt 的 Promise，或发生拒绝；submit 应返回一个在结果处理完成后才定案的 Promise。每次提交使用调用入口捕获的 doc、actor、text。成功后，以该快照和返回的 revision 恰好写入一条审计记录；失败不得写成功审计。已受理提交在 close 或重新 open 后仍须完成其历史记录处理。saved/error 界面反馈仅属于当前打开活动中的最新提交。保留编辑器公开方法及其他消费者的行为；搜索预览不在本次改动范围。

2. 每条的条件、效果、来源及依据
- 异步结果：原任务直接规定 commit 的 Promise 形态、拒绝可能性及 submit 的返回时机。当前事实：submit 立即调用 done(service.commit(snapshot))，成功处理会收到 Promise 本身，且同步 try/catch 不能处理其异步拒绝；见 /workspace/src/controller.js:7-13。该现状不是目标要求。
- 快照与审计：每次 submit 调用入口捕获身份和文本；仅 commit 成功后，按捕获值及 receipt.revision 记录恰好一次；失败不记成功审计。依据 /workspace/README.md:1-3。当前事实：snapshot 在 /workspace/src/controller.js:10 构造，observe 在成功回调中调用（:11）；observe 写入快照及 revision，见 /workspace/src/observations.js:1。审计属于历史提交，不随视图关闭而取消，依据 README.md:3。
- 活动与界面：当前事实：open 创建新 visit，edit 仅改当前文本，close 清空 current；见 /workspace/src/controller.js:3-6,15。submit 将 owner 写入该 visit.latest（:8-9）；成功或失败回调仅当 current 仍为捕获的 visit 且 latest 仍为 owner 时 render（:11-12）。README.md:3 明确规定 saved/error 只归当前 visit 的最新提交，因此旧活动或同一活动较早提交的结果不应覆盖当前反馈。回调仍可为旧活动写审计；其界面反馈受身份条件限制。两次提交之间及等待间隙，latest 持续指向最后一次提交，直至新提交改写；它的现有用法是界面归属判定，不能由此推定它独自表达全部在途提交。
- 公开接口及相邻组件：现有公开方法为 open、edit、submit、close，见 /workspace/src/controller.js:4-15；原任务要求保留编辑器行为、公开方法及其他消费者。搜索预览独立使用 trailing task，query 排队、hide 取消；见 /workspace/src/search-preview.js:1-8、/workspace/src/trailing-task.js:15-26。README.md:5 记载其 40 ms、隐藏后丢弃待处理查询及可复用性；原任务明确排除搜索预览改动。这些调度事实不能移植为保存提交的取消要求。

3. 不能确认的候选要求
- submit 对拒绝应兑现为特定值、拒绝原错误，或采用特定错误对象：原任务只规定返回 Promise 在处理后定案；当前 failed 无返回值（/workspace/src/controller.js:12-13），不足以确定新的失败结算协议。
- audit.record 或 render 自身抛错、返回 Promise 时的处理及 submit 定案方式：候选资料没有这些接口保证。同步 commit 抛错是否继续作为兼容输入，也未由新的 Promise 契约明确。
- close 后是否允许再次 submit、未打开时 submit 应返回何种 Promise：当前无 visit 时返回 null（/workspace/src/controller.js:8）；原任务的普遍措辞与既有公开行为之间的边界未明确。
- 保存提交需要定时器、取消入口、卸载处理或独立的全局在途计数：controller 当前没有排队调度或取消调用（/workspace/src/controller.js:1-17）。宿主卸载生命周期未给出，不能推定取消策略或实际缺陷。

4. 建议验证范围
分别覆盖成功与拒绝、两个提交以相反顺序完成、提交后 close、close 后 reopen、同一 visit 再次提交；检查每个 Promise 的定案时机、捕获的 doc/actor/text 与 revision、成功审计次数、失败无成功审计，以及 saved/error 仅对当前 visit 最新提交显示。另核对公开方法和搜索预览既有行为。上述建议尚未执行；即使通过，也不能单独确立未规定的失败返回值、异常传播和宿主卸载政策。
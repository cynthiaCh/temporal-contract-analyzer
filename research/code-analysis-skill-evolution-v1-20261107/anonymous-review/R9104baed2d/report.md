1. 任务目标和保留行为
原任务要求下载对话框在准备状态为 pending 时继续检查，仅在 ready 后交付文件。候选源码没有定义 pending、ready 的状态格式，也没有实际下载接口；当前可观察的完成效果是将 token 加入 completed（src/usePreparation.js:23-26）。对话框仍需通过现有快照暴露 visible、loading，并保留 start、close、reopen 入口（src/DownloadDialog.jsx:6-14；src/usePreparation.js:30-44）。

2. 源码事实及引用
DownloadDialog 用 usePreparation(token)，通过 ref 暴露其返回对象，并将快照中的 visible、loading 写入元素属性（src/DownloadDialog.jsx:6-14）。usePreparation 的共享 ref 保存 token、loading、retryScheduled、checkCount 和 completed；每次检查先读取当前 token、置 loading、增加计数，再调用 checkPreparation（src/usePreparation.js:7-14,18-23）。Promise 完成后无条件清除 loading，状态为真值时追加请求时捕获的 token；没有重试、去重、拒绝处理或卸载清理（src/usePreparation.js:23-27）。close 只隐藏；reopen 更新 token、显示并立即检查（src/usePreparation.js:32-40）。API 将检查、调度和取消直接转交给全局注入函数，未声明状态协议或调度保证（src/preparation-api.js:3-20）。相邻 BackgroundExportPanel 在结果为假值时调度下一次检查，在真值时记录完成，并于卸载时取消已保存的调度句柄（src/BackgroundExportPanel.jsx:14-35）；这只是相邻实现，不能直接视作对话框的业务契约。

3. 关键事件关系及依据
一次 start 先写 loading 和 checkCount，再发布渲染，随后同步调用外部 transport；此时尚无请求句柄或取消函数接入（src/usePreparation.js:18-23；src/preparation-api.js:3-8）。结果回调之后才清除 loading、记录完成并再次发布（src/usePreparation.js:23-27）。close 不取消已发起检查；因此已接纳请求在隐藏后完成时，回调仍可写 completed（src/usePreparation.js:23-35）。reopen 可在旧请求未完成时改变当前 token 并发起新请求；各回调记录各自捕获的 requestToken，却都能写同一个 loading，旧请求先完成即可把它清为 false（src/usePreparation.js:19-27,36-40）。当前对话框没有两次检查之间的等待区间：单次回调即结束该次流程。相邻面板在调度函数返回后才赋值 retry，并随后设置 retryScheduled；若外部调度函数在返回前同步触发回调，存在新检查先于句柄保存的条件性窗口（src/BackgroundExportPanel.jsx:31-34；src/preparation-api.js:10-15）。源码未证明这种回调实际发生。

4. 行为要求及依据
依据原任务，pending 不能提交文件完成效果，应继续检查；ready 才能交付。当前真值即完成、假值即停止的逻辑不满足重复检查（src/usePreparation.js:23-27）。重复检查需区分单次请求结束、等待下一次检查和整体活动结束；loading、retryScheduled 各应表达哪一段期间，任务及对话框源码尚未规定。close、reopen 和异步完成分别改变可见性、当前 token 与完成记录，不能仅凭 visible 推定已发起工作的完成效果须被丢弃（src/usePreparation.js:23-40）。

5. 未知项
未提供 pending/ready 的具体值与错误状态协议；文件交付的调用方、接口及 completed 是否等同交付均未提供。未说明关闭是否取消活动、重新打开是否替换旧活动、同一 token 是否允许重复交付、请求失败如何处理，以及调度器是否可能同步调用或保证取消。因而不能从相邻面板的真值判断、去重或卸载策略推出对话框的唯一政策（src/BackgroundExportPanel.jsx:14-35）。

6. 建议验证范围
建议用可控 transport 与调度器观察：pending 回调后是否安排下一次检查、等待期快照如何变化，以及 ready 后何时记录完成；这可检验轮询顺序，但不能确定未给出的状态协议。让 close 发生在请求中、等待期及 ready 回调前，分别观察后续检查和完成效果，可澄清关闭语义。让 reopen 在旧请求未完成时切换 token，并按不同顺序完成两个请求，观察 token 归属、loading 与 completed，可暴露交错影响。若采用相邻调度器，还应分别观察同步触发回调和取消发生在句柄返回前的顺序；源码只支持分析这种可能窗口，不能证明实际调度器行为。本轮未运行验证。
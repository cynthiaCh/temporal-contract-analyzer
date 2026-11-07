1. 任务目标和保留行为
原任务要求下载对话框在准备状态为 pending 时继续检查，仅在 ready 后交付文件。当前候选代码中，可观察的交付记录是 completed；没有实际文件下载调用。对话框已有 visible、loading、checkCount 和 completed 状态，以及 start、close、reopen、snapshot 接口，应在分析行为时分别考察这些状态和入口（src/usePreparation.js:7-14,30-45；src/DownloadDialog.jsx:6-14）。

2. 源码事实及引用
DownloadDialog 调用 usePreparation(token)，通过 ref 暴露其接口，并把 snapshot 的 visible、loading 写入 DOM 属性（src/DownloadDialog.jsx:6-14）。start 执行 check：读取当前 token，置 loading=true，增加 checkCount，触发渲染，然后调用 checkPreparation；完成回调无条件置 loading=false，若 status 为真则把本次 token 加入 completed（src/usePreparation.js:18-28,30-31）。close 只置 visible=false；reopen 更新 token、置 visible=true 并立即检查；snapshot 返回状态副本（src/usePreparation.js:32-45）。checkPreparation 将调用直接转发给全局传输函数；同文件另有调度和取消重试的全局接口，但 usePreparation 未调用它们（src/preparation-api.js:3-26；src/usePreparation.js:4,18-28）。相邻 BackgroundExportPanel 在结果为假时调度再次 start，在真时记录 completed；它有卸载清理，但它是另一个组件（src/BackgroundExportPanel.jsx:14-35）。

3. 关键事件关系及依据
一次 check 在调用外部传输前已写入 loading 和 checkCount；传输返回值的 then 回调尚未注册。若外部调用抛错，源码没有恢复这两个字段的路径（src/usePreparation.js:19-27；src/preparation-api.js:3-8）。每次回调使用启动时捕获的 requestToken，却直接写入当前共享状态；close 或 reopen 可在请求未完成时改变 visible 或 token，而回调没有检查这些变化（src/usePreparation.js:19,23-26,32-40）。因此输入是否接纳、旧请求是否继续完成、结果是否写入 completed 是不同问题：reopen 会接纳新 token 并启动新检查；已启动请求没有取消逻辑；其回调仍可写入旧 token 的完成记录。源码没有规定这些交错应如何呈现给用户。当前实现没有两次检查之间的等待区间：每次请求结束即将 loading 置为 false，pending 不触发下一次检查（src/usePreparation.js:23-27）。相邻组件在调度函数返回后才把句柄赋给 retry，再设置 retryScheduled；若调度函数调用尚未返回就同步触发回调或卸载，此时句柄尚未发布给清理逻辑。这只是该组件及外部调度接口允许检查的顺序窗口，不能当作下载对话框既有行为（src/BackgroundExportPanel.jsx:14-16,31-34；src/preparation-api.js:10-20）。

4. 行为要求及依据
按原任务，pending 不能产生文件交付，且需要后续检查；ready 才能交付。候选实现把任何真值 status 当作完成，并在假值结果后停止，因此是否符合要求取决于未提供的状态格式；现有代码不足以把真值等同 ready（src/usePreparation.js:23-27）。下载对话框的 loading 展示由 snapshot 驱动；轮询引入后，该字段表示单次请求进行中，还是整个准备活动仍在进行中，需要依据产品契约确定，不能仅从相邻组件在 pending 分支保留 loading=true 的写法推定（src/DownloadDialog.jsx:9-14；src/BackgroundExportPanel.jsx:21-34）。

5. 未知项
未提供 pending、ready、失败状态的具体值和响应协议；重试间隔、停止条件、错误处理、重复交付规则、关闭或重新打开后旧请求结果的产品政策也未说明。全局传输及调度函数的实现、返回值与回调时序保证未提供（src/preparation-api.js:3-20）。completed 是否就是最终下载效果，以及其他消费者是否读取 loading、retryScheduled、checkCount，候选文件中没有证据。

6. 建议验证范围
建议构造 pending 后 ready 的响应序列，观察检查次数、等待期间的 loading 与 visible、completed 写入时机；它能检验轮询及可见效果，不能确定真实下载是否发生。分别构造 close 后完成、reopen 新 token 后旧请求完成、两次请求乱序完成，观察各 token 的 completed 与当前状态；这些场景能揭示交错效果，不能替代缺失的产品政策。还可构造传输抛错、返回拒绝，以及调度回调在调度调用返回前发生的顺序，检查状态与句柄边界；是否需要支持这些情况取决于外部接口契约。本轮未运行这些验证。
1. 任务目标和保留行为
背景任务要求让已有缓存进度的传输在开始时显示初始进度，并防止较旧的完整进度帧在异步解码后使显示倒退。同时保留公开传输、重试、导航、清理、审计、队列记录、普通流式进度、诊断遥测及后续使用的行为。候选文档明确说明同一文件的 feed 会跨尝试和访问共享，start() 可同步发出缓存数据，decode() 可返回值或 Promise（README.md:8-12）；队列记录的既定形状及其他保留范围见 README.md:14-25。

2. 源码事实及引用
- 入口 createTransferWorkspace 暴露 select、retry、hide、dispose 和 snapshot，并保存各回调及当前访问状态（src/workspace.js:4-18）。select 建立新 visit、入队并发布 queued；retry 在当前 visit 内取消旧尝试、入队新尝试并发布 queued（src/panel.js:10-26；src/retry.js:4-15）。
- 入队先递增 attemptId 并写入 {fileId, attemptId, visitId, kind}，再创建进度回调和传输。record 回调写进度历史；receive 仅在该 visit 仍为 current 时调用 showProgress（src/queue.js:3-19）。
- createTransfer 先调用 transport，再安装进度监听；取消触发 stopProgress 和 onCancel。若安装期间已经中止，安装返回后再停止监听（src/transfer.js:3-16）。
- watchTransferProgress 的监听器解码事件；同步结果立即依次交给 record、receive，Promise 结果则在兑现后同样交付。当前调用顺序是 feed.start() 在 addEventListener 之前（src/progress.js:2-11）。候选 feed 的 start() 可同步 dispatch 初始包，emit() 派发后续包（src/progress-source.js:23-31）。因此该初始事件发生时，此处监听器尚未注册。
- 诊断消费者 collectProgressTelemetry 也调用 start() 后注册监听，但只把收到的解码帧交给 recordDelta；文档称缓存启动数据不属于诊断 delta（src/telemetry.js:1-11；README.md:21-23）。移除进度监听时，feed 先完成移除再同步调用可重入的 onDetach（src/progress-source.js:8-22）。

3. 关键事件关系及依据
- 一次入队中，队列记录先于 createTransfer；createTransfer 内 transport 先于进度监听安装（src/queue.js:8-18；src/transfer.js:10-13）。
- 现有 watchTransferProgress 中，start 的同步初始派发先于注册监听。因此在候选 feed 的同步派发情形，初始包不会进入该监听器的 decode、record 或 receive；后续 emit 只有在监听已注册时才可进入该路径（src/progress.js:3-11；src/progress-source.js:26-30）。
- 对已收到的包，decode 调用先于交付；Promise 的兑现时间可能改变不同帧的交付次序。当前 deliver 未比较帧的新旧，直接依次写历史和请求显示（src/progress.js:4-7）。不同 Promise 的具体兑现顺序没有源码保证。
- 取消先触发移除监听再调用 onCancel；移除可能同步引发 onDetach，进而重入 select 或 hide。相应入口会改变 current，receive 通过 current === visit 限制显示（src/transfer.js:6-9；src/progress-source.js:19-22；src/panel.js:10-18,29-34；src/queue.js:13-15）。已进入 Promise 链的交付是否仍发生，不能仅由移除监听推断。

4. 行为要求及依据
- 初始显示应覆盖 warm feed 的同步缓存包；依据是背景任务目标，以及 start 可同步派发的候选契约（README.md:8-12；src/progress-source.js:26-29）。
- 完整帧异步解码可能乱序，当前显示不得被较旧帧回滚；这是背景任务要求。候选接收路径目前没有新旧判断（src/progress.js:4-7；src/queue.js:13-15）。
- 进度历史与面板显示是两个输出：前者由 recordProgress 写入，后者受当前 visit 限制（README.md:14-16；src/queue.js:11-15）。诊断路径应保持其只记录实时 delta 的语义（src/telemetry.js:1-11）。队列记录形状、重试、导航和取消等保留要求见 README.md:8-25 及背景任务。

5. 未知项
候选文件未定义完整帧用于判定新旧的字段、单调性或跨尝试比较规则；不能凭变量名推定帧序号。未见具体 host 的 transport、回调或 decode 实现，故无法确定实际异步兑现顺序、重入频率和外部显示效果。候选文档未规定历史记录对乱序完整帧的取舍细则，也未给出除本候选 feed 以外其他 feed 实现的行为保证。

6. 建议验证范围
本轮未运行测试。建议后续验证：同步初始包在首次选择时能否进入进度历史及当前面板；后续 emit 是否保持正常交付；两个完整帧按接收顺序进入却按相反顺序解码完成时，分别观察显示与历史；同步值和 Promise 混用时观察同样结果。另观察 retry、重新选择同一文件、hide、dispose、取消时 onDetach 重入，以及诊断消费者的缓存包与实时 delta、队列记录和 queued 通知。这些场景可核对可观察的事件顺序及保留行为，但不能单独确定未定义的帧新旧规则或所有外部 feed 的契约。
1. 任务目标和保留行为
原任务要求恢复热进度源的首次进度显示，并避免较早完成解码的完整进度帧使当前显示倒退。须保留传输、重试、导航、清理、审计、队列记录、普通流式进度、诊断遥测及后续使用的行为。文档确认同一文件的进度源跨尝试和访问共享，start() 可同步发送缓存包，decode() 可同步返回或返回 Promise（README.md:8-12）。

2. 源码事实及引用
入口 createTransferWorkspace 提供 select、retry、hide、dispose 和 snapshot；状态含当前访问、访问及尝试计数、任务映射（src/workspace.js:4-18）。选择文件先清空当前访问并释放旧访问，再建立新访问、入队、接入返回的句柄和发布 queued；若入队期间所有者改变，则取消返回句柄（src/panel.js:10-26）。重试先取消原句柄，再在同一访问入队；句柄接入和 queued 发布分别检查当前访问（src/retry.js:5-14）。队列记录结构为 fileId、attemptId、visitId、kind；进度历史无当前访问判断，面板显示有当前访问判断（src/queue.js:4-18）。
createTransfer 先安装 abort 回调，再调用外部 transport，然后设置进度监听清理函数，最后返回句柄；abort 回调先清理进度监听，再调用 onCancel（src/transfer.js:3-16）。watchTransferProgress 目前先 start 后注册监听；收到事件后解码，同步结果立即交给 record、receive，Promise 结果在完成时交给两者（src/progress.js:2-11）。进度源 start 同步派发初始包（若存在）；emit 派发后续包；移除监听先完成移除，再同步调用可重入的 onDetach（src/progress-source.js:8-30）。诊断消费者也先 start 后监听，其收到的帧只交给 recordDelta（src/telemetry.js:1-11）。

3. 关键事件关系及依据
对热源，当前进度观察者执行 start 时尚未注册监听，因此该次同步初始事件无法由该观察者接收；随后到达的事件可以接收（src/progress.js:3-11；src/progress-source.js:26-30）。每个包的解码结果独立交付，源码没有帧顺序或最新帧检查；Promise 完成顺序若与输入顺序不同，旧结果可能在新结果之后调用显示（src/progress.js:3-8；src/queue.js:13-15）。
transport 是句柄返回前的外部调用；进度监听清理函数在 watchTransferProgress 返回后才赋值。若期间同步取消，abort 回调当时调用的仍是初始空清理函数；随后若已 aborted，才再次清理新监听（src/transfer.js:5-16）。选择操作在 enqueueTransfer 返回前也尚未给 visit.handle 赋值；外部回调可能改变 current，返回后由所有权检查决定接入或取消句柄（src/panel.js:17-25）。移除监听的 onDetach 可同步触发 select 或 hide，因而取消及释放过程可改变当前所有者（src/progress-source.js:8-22；src/panel.js:4-15,29-33）。已收到事件的 Promise 完成后仍调用 record，再调用 receive；只有 receive 在执行时检查访问是否仍当前，因此历史记录和面板显示的提交条件不同（src/progress.js:3-7；src/queue.js:11-15）。

4. 行为要求及依据
首次缓存包应能到达面板进度路径；面板所见完整帧须避免较旧帧在异步解码完成后覆盖较新帧（原任务；README.md:10-12）。进度历史与显示分别由 recordProgress 和 showProgress 承担，不能从显示的当前访问限制推断历史也须丢弃（README.md:14-17；src/queue.js:11-15）。诊断消费明确只统计实时增量，缓存启动包不是诊断增量，故其现有行为需保留（src/telemetry.js:1-11；README.md:21-23）。队列记录字段及重试、导航、取消和清理行为属于明确保留范围（README.md:14-19；src/queue.js:4-5）。

5. 未知项
候选文件未定义帧中的序号、时间戳或其他可比较字段，也未给出“较旧完整帧”的正式判定协议；不能据此指定具体排序算法。未见 transport、decode、recordProgress、showProgress 等宿主实现及其重入或异常保证；只能说明源码允许的顺序窗口。未见任务映射的删除路径或异步传输完成协议，不能推断任务生命周期或最终审计政策（src/workspace.js:5-6；src/queue.js:17-19）。

6. 建议验证范围
建议构造 start 同步发送缓存包、随后 emit 普通包的顺序，分别观察面板显示与进度历史，以确认首次更新及后续流式交付；该场景不能确定未知帧排序协议（src/progress-source.js:26-30；src/queue.js:11-15）。构造两个完整帧按输入顺序到达、解码 Promise 反序完成的顺序，观察显示是否倒退，并分别检查历史记录；需先明确可比较的帧字段（src/progress.js:3-8）。构造取消时 onDetach 同步 select 或 hide，以及 transport 调用期间取消的顺序，观察所有权、句柄接入、清理和 queued 记录；这些场景只检验所设交错，不证明所有宿主回调路径（src/transfer.js:5-16；src/panel.js:17-25；src/progress-source.js:19-22）。单独观察诊断消费者在缓存 start 与后续 emit 下的 recordDelta，确认其既有实时增量行为（src/telemetry.js:1-11）。本轮未运行上述验证。
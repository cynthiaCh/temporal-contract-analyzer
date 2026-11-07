1. 任务目标和保留行为
原任务要求恢复已有缓存进度源的首次显示，并防止较旧的完整进度帧在异步解码后使显示倒退；本轮仅分析。原任务要求保留传输、重试、导航、清理、审计和队列记录行为。候选文档另说明诊断消费者应维持现有行为，队列记录仍为 `{fileId, attemptId, visitId, kind}`（README.md:14-25）。

2. 源码事实及引用
工作区通过 `select`、`retry`、`hide`、`dispose` 暴露操作（src/workspace.js:7-16）。选择文件会结束前一次访问、建立新访问并入队传输（src/panel.js:10-25）。入队先写队列记录，再创建传输；进度记录写入 `recordProgress`，面板显示仅检查当前访问是否相同（src/queue.js:8-18）。创建传输先调用 `transport`，随后订阅文件的进度源（src/transfer.js:3-16）。订阅函数先调用 `feed.start()`，再注册事件监听器（src/progress.js:2-11）；候选进度源的 `start()` 可同步派发初始包（src/progress-source.js:23-30）。监听器解码事件，若返回 Promise 则在其兑现时交付；交付先记录、再调用显示接收方（src/progress.js:3-7）。诊断消费者也先启动源再注册监听器，其交付只调用 `recordDelta`（src/telemetry.js:1-11）。

3. 关键事件关系及依据
当前实现中，传输调用先于进度订阅（src/transfer.js:10-12）；订阅时 `start()` 先于监听器注册（src/progress.js:9-10）。因此，若初始包由候选进度源在 `start()` 内同步派发，本次新监听器无法接收该事件（src/progress-source.js:26-29）。后续 `emit()` 派发的事件可由已注册监听器接收（src/progress-source.js:30；src/progress.js:10）。Promise 解码的交付发生在兑现时，源码没有按事件到达顺序约束不同 Promise 的兑现顺序（src/progress.js:5-7）；较旧帧晚交付时，当前接收方会直接调用显示回调（src/queue.js:13-15）。重试沿用当前访问并更换尝试，先取消旧句柄，再入队新传输（src/retry.js:5-13）。移除监听器先完成移除再调用可重入的主机回调；该回调可能触发重新选择或隐藏（src/progress-source.js:8-22）。

4. 行为要求及依据
恢复初始进度应针对面板传输路径，同时保留后续流式事件；诊断路径明确将缓存初始状态与实时增量区分（README.md:21-23；src/telemetry.js:1-11）。防倒退要求关注异步解码后的完整帧交付顺序，而不只是事件接收顺序（原任务背景；src/progress.js:3-7）。进度历史与面板显示是两个对外效果，现有交付顺序为先记录后显示（README.md:14-16；src/progress.js:4；src/queue.js:11-15）。队列记录字段及访问、重试、取消等行为有明确保留要求（README.md:8-19）。

5. 未知项
候选源码未定义完整进度帧的字段、版本或新旧比较规则，也未说明 `decode` 的拒绝处理规则（src/progress.js:3-7）。没有证据表明 `feed.start()` 每次都产生初始包，或共享源的多次启动如何相互影响（README.md:10-12；src/progress-source.js:26-29）。`recordProgress` 是否应保留每个乱序帧、面板是否应按尝试隔离旧异步结果，均不能仅由现有实现推断为业务政策（src/queue.js:11-15）。

6. 建议验证范围
建议验证同步初始包、后续普通包以及 Promise 乱序兑现时的 `recordProgress` 和 `showProgress` 调用顺序与内容；这可判断初始显示及倒退现象，不能单独确定帧的新旧比较规则。还应观察重试、再次选择同一文件、隐藏、取消和移除监听器回调中的重入，以及诊断增量和队列记录；这可检查要求保留的对外效果，但不能证明未展示的主机实现行为。本轮未运行验证。
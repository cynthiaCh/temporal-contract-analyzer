1. 原任务目标与需要保留的行为
原任务要求解决 presence 面板刚打开时偶发缺少初始在线用户状态的问题，同时保留后续更新和工作区导航行为；明确要求不改 metrics consumer。本轮仅分析。

2. 关键源码事实及路径、行号
- 面板 `show` 先调用旧订阅的 `release`，再将新订阅返回的解除函数赋给 `release`；`close` 解除当前订阅（src/presence-panel.js:4-14）。`renderPresence` 展示面板后等待一个微任务，再发送更新并关闭面板（src/presence-panel.js:18-26）。
- `subscribeChannel` 目前先 `connect`，后注册 `presence` 监听器；监听器将事件交给 `decode`，若返回 Promise，则在其完成时调用 `receive`。解除函数只移除监听器（src/subscription.js:1-11）。
- `connect` 在同步模式中立即发送 bootstrap，在 deferred 模式中用 `queueMicrotask` 安排发送；`emitUpdate` 立即发送 update（src/channel.js:8-20）。
- 工作区导航将发布值传给 `renderState(value, navigation)`；该回调可同步切换房间或隐藏面板，工作区还支持稍后复用同一 transport 对象（src/workspace-navigation.js:3-13）。
- metrics 路径经 `collectMetrics` 使用同步模式的 `observeChannel`；其注释说明有意在同步 bootstrap 之后注册监听器，只计增量（src/metrics-consumer.js:3-5；src/channel.js:24-31）。

3. 相关事件顺序及其依据
在当前同步模式下，面板的 bootstrap 发送先于监听器注册，因此该监听器无法接收这次同步事件；随后发出的 update 可以被接收（src/subscription.js:9-10；src/channel.js:14-20）。在 deferred 模式下，bootstrap 被排入微任务，通常会在当前调用栈注册监听器后发送；具体呈现还取决于解码完成时间及导航回调。Promise 解码已启动后，即使移除监听器，其完成回调仍可能发布值（src/subscription.js:1-11）。发布回调也可能在 `show` 的订阅赋值完成前同步触发导航操作（src/presence-panel.js:7-10；src/workspace-navigation.js:3-10）。

4. 不同消费者、阶段或效果是否采用不同条件
面板需要接收初始状态和后续更新，这是原任务要求；metrics 明确只计增量，当前特意跳过同步 bootstrap（src/metrics-consumer.js:3-5）。因此两条消费路径的监听时机不能视为同一业务规则。`decode` 可同步返回或返回 Promise，两种路径的发布时机不同（src/subscription.js:1-8）。

5. 能确认的要求、仅有线索的判断及未知项
可以确认同步 bootstrap 与面板监听注册的顺序构成漏收初始事件的直接条件。工作区注释和调用方式表明同步发布可能引发重入导航，异步解码可能在解除订阅后完成；它们是保留导航行为时需要考虑的线索，尚不能据此断定线上缺失的唯一原因。源码未定义真实在线用户数据结构、解码失败处理、跨房间发布的期望规则或生产环境中各 bootstrap 模式的使用比例。

6. 建议验证的行为范围
后续可验证同步与 deferred bootstrap 是否各被面板收到一次、后续 update 是否仍被收到；验证发布时同步 `select` 或 `hide`、复用同一 channel，以及解码 Promise 在切换或关闭后完成时的可见状态。另应观察 metrics 仍只接收增量。这些验证能区分漏收、重入和延迟发布的影响；本轮未运行测试，不能据此宣称实际修复效果。
1. 可确认的 Contract
原任务明确要求：打开 presence panel 后，初始在线用户状态应能呈现；后续 presence 更新应继续呈现；修复时应保留 workspace 导航行为；不得修改 metrics consumer。这里的“呈现”指向调用方可观察的发布结果，在线用户状态的具体数据格式未给出。

2. 每条的条件、效果、来源及依据
- 初始状态：panel 打开并连接 channel 时，初始 presence 结果应到达发布回调。依据是原任务对初始状态缺失的修复要求。当前实现事实：`show` 调用 `subscribeChannel`（`/workspace/src/presence-panel.js:7-10`）；订阅函数先 `connect`，后注册监听器（`/workspace/src/subscription.js:9-10`）；示例 channel 在默认同步模式下于 `connect` 内发出 bootstrap，在 deferred 模式下排入微任务（`/workspace/src/channel.js:14-17`）。因此同步 bootstrap 有被现有监听顺序漏掉的条件；这只能说明候选源码中的机制，不能证明所有实际传输都同步发出。
- 后续更新：打开后仍有效的订阅应继续发布 presence 更新，依据是原任务明确要求保留 later presence updates。当前实现事实：`emitUpdate` 发出 update（`/workspace/src/channel.js:18-20`），监听器解码后调用 `receive`；解码若返回 Promise，则在其完成后调用（`/workspace/src/subscription.js:4-8`）。示例渲染在一次微任务等待后触发更新，再关闭 panel（`/workspace/src/presence-panel.js:18-26`）。这些代码只展示该调用路径，不规定更新的频率或内容。
- 导航：presence 发布可能同步选择另一房间或隐藏 panel，同一 transport 对象也可能在后续访问中复用；修复应保留这些可观察行为。依据是原任务的导航保留要求，以及 workspace 导航源码的明确注释和 `select`、`hide` 入口（`/workspace/src/workspace-navigation.js:3-11`）。当前实现事实：`show` 先调用旧 `release`，再把新订阅返回的清理函数赋给共享变量；`close` 调用该函数并复位（`/workspace/src/presence-panel.js:5-14`）。若订阅建立期间同步发布引起嵌套 `select` 或 `hide`，共享 `release` 的赋值顺序可能与导航动作交错；源码支持这一条件性风险，未证明某种具体错误已经发生。
- metrics：不得修改 metrics consumer，依据是原任务的明确限制。相邻组件当前行为是同步 bootstrap 后才监听，且注释称其只计增量（`/workspace/src/metrics-consumer.js:3-5`；`/workspace/src/channel.js:24-31`）；这是该组件的行为说明，不能移作 panel 漏掉初始状态的规范。workspace 渲染同时调用 presence 与 metrics（`/workspace/src/render-workspace.js:4-9`）。
- 生命周期与身份的当前事实：关闭或重开调用的清理函数只移除事件监听（`/workspace/src/subscription.js:10-11`），不会阻止已启动的异步解码完成；源码注释也明确说明这一点（`/workspace/src/subscription.js:1-2`）。deferred bootstrap 已排入微任务后，channel 代码没有取消入口（`/workspace/src/channel.js:14-17`）。请求回调持有其订阅时的 `channel`、`receive`，而 panel 的 `publish` 可作用于同一个调用方状态（`/workspace/src/subscription.js:3-8`；`/workspace/src/presence-panel.js:4-10`）。因此，在仍挂载、调度仍触发且旧异步解码晚于重开完成时，旧结果有与新活动的发布交错的可能；已排队的 bootstrap 是否被接收，取决于触发时的监听器及是否复用同一 target。源码没有宿主卸载规则，不能断言这些情形实际发生，也不能据此指定唯一的取消或隔离方案。

3. 不能确认的候选要求
- 关闭、重开、切换房间或卸载后，旧解码结果应一律丢弃：这是值得核对的候选要求；原任务未给出旧结果的产品政策、宿主生命周期或解码接口保证。
- bootstrap 与 update 必须按特定顺序、恰好发布一次，或必须采用特定订阅和取消手段：候选源码不足以确立这些协议要求。
- `token:bootstrap` 等字符串就是在线用户列表的业务格式：`/workspace/src/channel.js:8-20` 仅展示示例事件编码，不能据此确认真实状态结构。

4. 建议验证范围
分别检查同步与 deferred bootstrap 打开时的发布结果，以及之后更新是否仍到达；检查发布回调同步触发 `select`、`hide`，包括复用同一 channel 的再次访问。用延迟解码覆盖请求在途、请求结束后的等待间隙、后续打开和关闭后的回调交错，记录每次结果所归属的 channel 与活动、监听及已排队工作的状态。核对 metrics 行为及文件未受改动。上述验证只能确认所测条件下的可观察效果；旧结果应如何处理及卸载后的责任，仍需产品或宿主规范确认。
1. 原任务目标与需要保留的行为
任务要求修复 presence 面板刚打开时偶尔缺失初始在线用户状态的问题，保留后续 presence 更新和工作区导航行为；明确要求不改 metrics consumer。本轮仅分析，未修改或运行代码。

2. 关键源码事实及路径、行号
- `createPresencePanel.show` 先调用上一次的 `release`，再调用 `subscribeChannel` 并保存其返回值；`close` 解除订阅并重置 `release`。[src/presence-panel.js](/workspace/src/presence-panel.js:4)
- `subscribeChannel` 在注册 `presence` 监听器之前调用 `channel.connect`。监听器收到事件后调用 `decode`；同步结果直接交给 `receive`，Promise 结果在兑现后交给 `receive`。返回的解除函数只移除监听器。[src/subscription.js](/workspace/src/subscription.js:1)
- 此候选实现中，`connect("synchronous")` 立即派发 bootstrap；`connect("deferred")` 将 bootstrap 排入微任务。`emitUpdate` 立即派发 update。[src/channel.js](/workspace/src/channel.js:8)
- 工作区导航通过 `select` 显示面板、通过 `hide` 关闭面板；源码注释说明状态发布可同步触发切换房间或隐藏面板，且再次访问可复用同一 transport。[src/workspace-navigation.js](/workspace/src/workspace-navigation.js:3)
- metrics 通过 `observeChannel` 使用同步 bootstrap；其注释明确说它有意在 bootstrap 后注册监听器，只计增量。[src/metrics-consumer.js](/workspace/src/metrics-consumer.js:3) [src/channel.js](/workspace/src/channel.js:24)

3. 相关事件顺序及其依据
- 同步模式下，`connect` 在监听器注册前派发 bootstrap，因此该订阅收不到这次初始事件；之后派发的 update 可被已注册监听器接收。[src/subscription.js](/workspace/src/subscription.js:9) [src/channel.js](/workspace/src/channel.js:14)
- deferred 模式下，bootstrap 被排入微任务；正常同步调用链中的监听器注册先于该微任务执行。`renderPresence` 在 `show` 后等待一个已兑现的 Promise，再派发 update 并关闭面板。[src/channel.js](/workspace/src/channel.js:15) [src/presence-panel.js](/workspace/src/presence-panel.js:18)
- `receive` 若同步引发导航，可能在 `show` 尚未保存新的 `release` 时调用 `select` 或 `hide`。此外，解除监听器不会阻止已经开始的异步 decode 在完成后调用 `receive`。这些是源码允许的顺序，不代表已观察到的实际故障。[src/presence-panel.js](/workspace/src/presence-panel.js:7) [src/subscription.js](/workspace/src/subscription.js:4) [src/workspace-navigation.js](/workspace/src/workspace-navigation.js:3)

4. 不同消费者、阶段或效果是否采用不同条件
presence 面板需要展示初始状态及后续更新，这是原任务要求；metrics 的注释则规定只计增量，且其观察路径故意晚于同步 bootstrap 注册。两者对初始事件的需求不同，不能据 metrics 的行为推定面板也应忽略 bootstrap。[src/metrics-consumer.js](/workspace/src/metrics-consumer.js:3) [src/presence-panel.js](/workspace/src/presence-panel.js:18)

5. 能确认的要求、仅有线索的判断及未知项
可确认：原任务要求保留工作区导航、不改 metrics consumer；当前同步 bootstrap 存在明确的注册顺序缺口。线索：导航回调重入和异步 decode 完成后的发布可能影响切换或关闭后的状态，但源码未给出生产环境的具体触发频率或结果。未知：真实 transport 的事件及 decode 契约、`renderState` 的状态语义，以及原任务所说“偶尔”是否还包含其他原因。

6. 建议验证的行为范围
建议后续验证同步与 deferred 初始事件及 update 的可见顺序；在状态发布期间同步 `select`、`hide`，以及复用 channel 再次进入时的订阅归属；异步 decode 在切换或关闭后完成时的发布对象；metrics 仍只记录预期增量。这些验证可判断初始事件是否被接收、导航与旧订阅是否干扰当前状态；它们本身不能证明真实环境的发生频率或排除未展示的外部因素。本轮未运行验证。
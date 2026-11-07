1. 可确认的 Contract

- Presence 面板打开后，应呈现初始在线用户状态，并继续呈现后续 presence 更新；修复须保留工作区导航行为。依据是原任务明确要求。原任务还明确禁止修改 metrics consumer。
- 工作区导航中，presence 发布可能同步触发切换房间或隐藏面板；再次进入时可以复用同一 transport。候选源码对此有明确注释，可作为需保留行为的依据。[workspace-navigation.js](/workspace/src/workspace-navigation.js:3)

2. 每条的条件、效果、来源及依据

- **打开面板时**：初始状态必须可被面板接收并发布；之后的更新仍应出现。来源：原任务。当前实现事实：`show` 调用 `subscribeChannel`；该函数先 `connect`，后注册监听器，而示例 channel 的同步 `connect` 会立即派发 bootstrap。因此当前顺序存在遗漏同步初始事件的路径。[presence-panel.js](/workspace/src/presence-panel.js:7)、[subscription.js](/workspace/src/subscription.js:9)、[channel.js](/workspace/src/channel.js:14)。这些源码证明现有路径，不单独规定唯一修复方式。
- **发布初始状态或更新时**：若工作区回调同步选择另一房间或隐藏面板，应保持该导航效果；以后再次选择同一 transport 也应可用。来源：[workspace-navigation.js](/workspace/src/workspace-navigation.js:3)。当前实现事实：`select` 转发到 `panel.show`，`hide` 转发到 `panel.close`；`show` 先释放旧订阅，`close` 释放当前订阅。[workspace-navigation.js](/workspace/src/workspace-navigation.js:8)、[presence-panel.js](/workspace/src/presence-panel.js:7)。注释支持上述行为约束，但未指定事件竞争时的完整顺序规则。
- **维护范围**：不得修改 metrics consumer。来源：原任务。当前实现事实：它在同步 bootstrap 后附加监听，只统计后续变化。[metrics-consumer.js](/workspace/src/metrics-consumer.js:3)、[channel.js](/workspace/src/channel.js:27)。这是现有设计说明，不能据此要求 presence 面板也跳过初始状态。

3. 不能确认的候选要求

- 异步 `decode` 已启动、随后面板关闭或导航切换时，其结果是否仍应发布：源码只说明移除监听不会取消已开始的解码，没有给出 UI 应如何处理的业务要求。[subscription.js](/workspace/src/subscription.js:1)
- 多次打开、重复 bootstrap、快速切换时的去重、排序和旧结果过滤规则：候选源码展示了相关入口，但缺少产品规格或明确预期。不能将当前 `release` 实现直接视为完整规则。[presence-panel.js](/workspace/src/presence-panel.js:4)

4. 建议验证范围

- 分别让 bootstrap 同步和延迟派发，观察面板是否收到初始状态及随后更新；这只能验证所覆盖的派发时序。[channel.js](/workspace/src/channel.js:14)
- 在初始状态发布回调内同步切换房间、隐藏面板，并再次使用原 transport，观察导航结果及后续接收情况；还需另行明确异步解码结果的预期。[workspace-navigation.js](/workspace/src/workspace-navigation.js:3)
- 核对修改范围未涉及 metrics consumer，并观察其仍只统计后续变化；以上均为建议，未执行验证。[metrics-consumer.js](/workspace/src/metrics-consumer.js:3)
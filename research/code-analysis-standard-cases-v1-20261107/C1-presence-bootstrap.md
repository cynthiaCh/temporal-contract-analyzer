# C1 草稿：首事件与监听注册

**AI 辅助编写，全部待用户确认，非独立人工审查。**评价对象仅为本目录冻结的原始候选；没有采用历史补丁或评分结论。

## 1. 一句话说明

首个状态是在监听前还是监听后发出，会影响面板能否看到它；面板和只统计增量的消费者不能自动套用同一政策。

## 2. 原任务与保留范围

[原任务](cases/C1/task.md:3)明确要求解决面板初始在线状态缺失、保留导航行为，并禁止修改 metrics consumer（3–7 行）。源码注释明确 metrics 只计增量；导航注释允许发布时同步切换／隐藏、以后复用 transport。没有完整产品文档，不能仅凭这些注释确定所有迟到解码结果的业务去留。

来源单元 `listener-registration-order`，非 U1/U2；重建项目，已用于历史官方 GEPA test，不再作为独立测试。版本、完整文件摘要和来源见 [manifest](source-manifest.json)。

## 3. 源码事实表

| ID | 原始源码的有限事实 | 依据 |
|---|---|---|
| C1-S1 | `connect` 同步派发 bootstrap，或在 deferred 模式排微任务；`emitUpdate` 派发 update，默认 decode 原样返回。 | [channel.js](cases/C1/candidate/src/channel.js:8)，8–20 行 |
| C1-S2 | listener 调用 decode；返回 thenable 则登记 `then(receive)`，否则立即 receive。订阅先 connect，后 addEventListener，最后返回移除函数。 | [subscription.js](cases/C1/candidate/src/subscription.js:3)，3–11 行 |
| C1-S3 | show 先执行当前 release，再调用订阅，订阅返回后才赋新 release；close 执行 release 再置空函数。 | [presence-panel.js](cases/C1/candidate/src/presence-panel.js:4)，4–14 行 |
| C1-S4 | 示例 renderPresence 打开后等待一个 Promise 微任务，再 update、close，收集的是 events 数组。 | [presence-panel.js](cases/C1/candidate/src/presence-panel.js:18)，18–26 行 |
| C1-S5 | metrics 明确选择同步模式；它的 observeChannel 同样先 connect 后监听，再等待、update。 | [metrics-consumer.js](cases/C1/candidate/src/metrics-consumer.js:3)，3–5 行；[channel.js](cases/C1/candidate/src/channel.js:24)，24–31 行 |
| C1-S6 | 注释允许 publication 同步触发导航／隐藏和 transport 复用；select/hide 分别调用 panel.show/close。两种消费者同时用于工作区渲染。 | [workspace-navigation.js](cases/C1/candidate/src/workspace-navigation.js:3)，3–10 行；[render-workspace.js](cases/C1/candidate/src/render-workspace.js:4)，4–9 行 |

## 4. 两种关键顺序

- **原始源码可推导，未新运行：**使用提供的 channel、默认同步 decoder 时，connect → 同步 bootstrap → 注册 listener → 后续 update。新 listener 不会补收已派发的 bootstrap；这解释实现层缺口，不证明任意外部 channel 都有相同表现（S1/S2/S4）。
- **原始源码可推导，未新运行：**deferred connect 排微任务 → 注册 listener → bootstrap 微任务 → 示例等待恢复后 update。这里首次事件能经过该 listener。条件是提供的 channel 和正常完成的默认 decoder，不能推广到所有 thenable（S1/S2/S4）。

另外，移除监听只阻止之后经该监听进入的事件，不撤销已经登记的完成回调（S2）。S3 的赋值顺序值得结合 S6 核查，但**晚取得 release 不自动证明某个重入窗口在原始版本可达**；需要具体调用路径。不能引用历史修复后的故障替原始版本证明可达性。

## 5. 行为要求及依据

| ID | 要求／待核查关系 | 来源与边界 |
|---|---|---|
| C1-R1 | 面板需处理任务所述初始状态缺失；不得把“所有消费者都必须收到 bootstrap”当任务要求。 | task:3–7；S5 的增量政策 |
| C1-R2 | 保留导航和 metrics 行为；应区分入口退订、已开始解码的完成和不同消费者。 | task:5–7、S2/S5/S6；迟到结果的具体业务政策仍未知 |
| C1-R3 | 验证建议应分别覆盖同步／deferred 首事件、后续更新及导航／消费者边界。 | 上述事实与原任务导出的建议范围，不是已执行测试或唯一修复 |

未引用隐藏测试或历史测试预期作为要求；没有唯一修复代码。

## 6. 未知项

- C1-U1：真实 renderState、外部 channel 和调用方未提供；需要其实现／接口保证才能判断所有重入路径及迟到显示资格。
- C1-U2：任意 decoder 的拒绝、同步重入与取消政策未完整定义；已登记回调“仍可能完成”不等于业务上“必须展示”。
- C1-U3：事件数组不能证明完整界面正确；实际环境调度和界面效果需要另行证据，本轮不执行。

## 7. 模型报告评价清单

统一用“满足／部分满足／不满足／证据不足”；接受同义及分散表达，区分未写出、写错与合理未知，不合计总分。

| ID | 只评价候选可见材料支持的内容 |
|---|---|
| C1-A1 | 准确定位 dispatch、listener、decode、receive，引用对应原始行。 |
| C1-A2 | 区分两种首事件顺序及适用条件，不借历史补丁断言原始重入必达。 |
| C1-A3 | 区分面板初始状态需求与 metrics 的增量政策。 |
| C1-A4 | 说明 release 返回／赋值／执行与实际移除条件，不把完成回调视为自动撤销。 |
| C1-A5 | 将迟到结果政策、外部调用可达性保留未知，区分事实与要求。 |
| C1-A6 | 建议验证首事件、后续事件及导航保留关系，未把分析任务替换为唯一补丁。 |

## 8. 用户确认表

| ID | 关键问题 | 状态 | 用户选择 | 备注 |
|---|---|---|---|---|
| C1-Q1 | 是否同意以“面板初始状态应可见、metrics 仍只统计增量”为本例的需求边界？ | 待确认 | 确认／需要修改／无法判断 | |
| C1-Q2 | 是否同意迟到解码的显示政策及原始重入窗口暂列未知，不要求报告断言它们？ | 待确认 | 确认／需要修改／无法判断 | |

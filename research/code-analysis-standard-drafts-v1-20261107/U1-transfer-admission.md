# U1：切换后旧来源的新输入——代码分析标准报告草稿

**状态：待人工确认；不是已批准金标准。** 本报告不运行代码，不提供唯一补丁。

案例：`transfer-progress-composition-v4-vanilla`。历史修改运行：`e-5b07bf1156dc48d0`。来源根目录：[U1 原始归档](../development-feedback-mechanism-v1-20261106/evidence/U1/)。

## 1. 通俗说明：这次要理解什么

原任务是修复“已有初始进度，却要等下一条消息才显示”，同时保持原有导航、重试、清理、审计和队列记录行为，避免解码乱序使当前显示倒退。

难点是：为了收到初始消息，提前监听后，启动期间就可能执行消息回调。回调可能触发切换；切换前已经接纳的工作迟到完成，与切换后旧来源又送来一条新消息，不能未经核查就视为同一类事情。

一句话待确认要求：**旧来源不应在失去接纳资格后继续接纳新输入；此前已经接纳工作的历史记录是否继续，需按其独立规则处理。** “失去资格”的准确边界需从项目要求确认，不能只凭这个概括决定补丁。

## 2. 本报告使用的材料

| 标识 | 材料 | 用途 |
|---|---|---|
| T | [原任务](../development-feedback-mechanism-v1-20261106/evidence/U1/task.md) | 确认修复目标和保留范围 |
| D | [候选 README](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/README.md) | 访问、尝试、共享 feed、同步回调与效果说明 |
| P | [历史补丁](../development-feedback-mechanism-v1-20261106/evidence/U1/patch.diff) | 观察该次模型实际改了什么；不是参考补丁 |
| O | [原始评分与事件轨迹](../development-feedback-mechanism-v1-20261106/evidence/U1/raw-score.json) | `schedules.start-switch-admission` 中的实际/预期及 trace |

## 3. 直接可核对的源码事实

以下行号属于原始 `candidate-start`，不是历史补丁后的代码。

| ID | 事实 | 来源 |
|---|---|---|
| S1 | `start()` 调用 `initialPacket`（若为函数）并同步派发 progress 事件 | [progress-source.js](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/src/progress-source.js) 26–28 行 |
| S2 | 原始 `watchTransferProgress` 先 start，再注册监听，最后返回退订函数 | [progress.js](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/src/progress.js) 9–11 行 |
| S3 | 解码返回 thenable 时，`deliver` 被登记到完成回调；`deliver` 先记录、再交给显示消费者 | 同文件 3–7 行；不证明所有解码都会暂停 |
| S4 | `record` 不检查当前访问，`receive` 检查 `state.current === visit`；不能据此把两者生命周期等同 | [queue.js](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/src/queue.js) 11–15 行 |
| S5 | 取消时调用 `stopProgress()`；但该变量要等 `watchTransferProgress(...)` 返回后才接到其返回值 | [transfer.js](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/src/transfer.js) 5–13 行 |
| S6 | `selectFile` 建立当前 visit 后调用 `enqueueTransfer`；返回后才赋 `visit.handle`，若期间 visit 已改变则取消返回的 handle | [panel.js](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/src/panel.js) 17–25 行 |
| S7 | retry 保留当前 visit，取消旧 handle 后创建新 attempt | [retry.js](../development-feedback-mechanism-v1-20261106/evidence/U1/candidate-start/src/retry.js) 5–14 行 |

历史补丁 P 改变了上述部分结构：提前注册监听、增加显示顺序控制、提前构造并发布 handle、增加当前 attempt 的显示条件。**不能把 S6 的原始句柄发布时间直接当成历史补丁的状态。** 补丁仍在 watcher 返回后才赋 `stopProgress`，且 `record(frame)` 没有新增输入接纳判断。

## 4. 历史测试实际观察到了什么

O 的 `schedules.start-switch-admission.trace` 记录：

```text
step 4–7：A 启动，发出 A1，A1 被记录并显示
step 8–9：回调路径中选择 B，A 被取消
step 10–16：B 启动，B1 被记录并显示
step 17–18：旧来源 A 发出新的 A2，A2 仍被记录
step 19：A 的监听被移除
```

| 项目 | 结果 |
|---|---|
| 测试预期历史 | A1、B1 |
| 实际历史 | A1、B1、A2 |
| 当前显示 | 对应断言通过；本次失败不能简化为“旧界面被更新” |
| 最终监听清理 | 对应断言通过；最终清理成功不能排除清理前的窗口 |

这说明该测试失败方向是**额外记录了新输入**。它不是“少记录了已经接纳的旧消息”，也不是“只要阻止旧显示就能解决”。

## 5. 需要人工确认的契约关系

| ID | 拟采用的标准要求 | 当前依据与边界 |
|---|---|---|
| R1 | 修复初始进度，保留原有导航、重试、记录及诊断行为 | T/D 直接支持；不要仅以通过一条初始显示测试验收 |
| R2 | 本次切换后旧来源 A 的新输入 A2 不应进入历史 | O 明确要求；需要人工核验它与 T/D 及接口语义一致，不能仅因为 expected 如此就整体批准 |
| R3 | 已接纳工作的完成与新输入接纳需要分别核查；不能一律用“当前 visit 是否相同”决定所有效果 | S3/S4、D 及归档中 `accepted-after-hide` 等路径支持区分；不同边界的具体政策须分别确认 |
| R4 | 正常显示、乱序解码、retry、telemetry 与清理不得因修复被破坏 | T/D 及 O 的已通过项；不意味着有限评分覆盖一切 |

## 6. 机制判断与未知

**有依据的候选机制：**提前监听后，启动回调可能在 watcher 返回前造成取消/切换；退订函数尚未接到 `stopProgress` 时，取消不能立即移除该监听。历史轨迹与“先记录 A2、后移除监听”一致。

**尚未证明：**原始 trace 没有完整调用进入/返回标记，仅凭 trace 不能断言每一层调用栈；需结合补丁和测试驱动代码确认。也没有证明只有一种正确修复方式。句柄发布、接纳边界和退订可能都有关，不应直接指定唯一变量或补丁。

## 7. 用本稿检查模型分析报告

| ID | 应检查的内容 | 不足或错误示例 |
|---|---|---|
| A1 | 识别同步 start 与监听注册顺序 | 只写“存在异步问题” |
| A2 | 区分原始代码和实际被评估补丁的句柄/退订顺序 | 把未修改代码的事实套到修改后 |
| A3 | 识别启动中切换、旧来源随后新输入的窗口 | 只检查解码完成后更新旧 UI |
| A4 | 分开输入接纳、历史记录和当前显示资格 | 要求切换后取消所有历史记录 |
| A5 | 保留 retry、正常/乱序帧和诊断行为 | 为避免回退而丢弃所有稍晚完成帧及历史 |
| A6 | 保留不确定性并给出针对性验证方法 | 宣称列出两种顺序就已经证明安全 |

可接受等价表述，不要求复述本稿。每项记录“满足／部分满足／不满足／证据不足”及具体引用。不以条目总分替代关键要求是否正确。

后续可执行验证应分别驱动：初始消息、启动中同步切换后新输入、已接纳解码迟到完成、retry 和正常/逆序帧。**本稿只提出验证范围，本次未新增或运行测试。**

## 8. 请你填写确认结果

| 请确认 | 结论：确认／需要修改／无法判断 | 修改理由或疑问 |
|---|---|---|
| S1–S7 的事实及原始/补丁区别是否准确？ | 待填写 | |
| R2：切换后 A2 不应记录，有没有充分项目依据？ | 待填写 | |
| R3：哪些已接纳工作可以继续记录？边界是否清楚？ | 待填写 | |
| 机制解释是否合理，未知项是否足够明确？ | 待填写 | |
| A1–A6 是否覆盖你希望模型理解的关键内容？ | 待填写 | |

复核人：待填写。日期：待填写。整体状态：待确认。批准进入标准的条目 ID：待填写。未决条目：待填写。

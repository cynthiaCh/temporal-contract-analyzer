# U2：pending 重试期间的等待状态——代码分析标准报告草稿

**状态：待人工确认；不是已批准金标准。** 本报告不运行代码，不提供唯一补丁。

案例：`download-polling-restoration-low-cue-react18`。历史修改运行：`e-0f86af18a30343df`。来源根目录：[U2 原始归档](../development-feedback-mechanism-v1-20261106/evidence/U2/)。

## 1. 通俗说明：这次要理解什么

服务可能先返回 pending，之后才 ready。原任务要求对 pending 继续检查，只有 ready 后才交付文件。

问题是：**一次请求已经返回，不等于整个准备过程已经结束。** 历史补丁能够重试并最终完成，却在等待下一次检查时丢失了等待指示。

待人工确认的关键政策：等待指示应覆盖哪些阶段，是否包括 pending 返回后到 retry 触发前的间隙。原任务没有直接定义 `loading` 标志的完整语义，不能把本稿解释自动当作明确要求。

## 2. 本报告使用的材料

| 标识 | 材料 | 用途 |
|---|---|---|
| T | [原任务](../development-feedback-mechanism-v1-20261106/evidence/U2/task.md) | pending 继续检查、ready 才交付 |
| P | [历史补丁](../development-feedback-mechanism-v1-20261106/evidence/U2/patch.diff) | 观察该次修改的状态、重试和生命周期处理 |
| O | [原始评分](../development-feedback-mechanism-v1-20261106/evidence/U2/raw-score.json) | `schedules.downloadPending.assertions` 的实际/预期 |

此冻结候选没有 README，不引用不存在的接口文档。源码根目录为 `candidate-start/src/`。

## 3. 直接可核对的源码事实

以下行号属于原始 `candidate-start`，不是历史补丁后的代码。

| ID | 事实 | 来源 |
|---|---|---|
| S1 | 开始检查时捕获 token、设 loading=true、增加检查计数并发布 | [usePreparation.js](../development-feedback-mechanism-v1-20261106/evidence/U2/candidate-start/src/usePreparation.js) 18–22 行 |
| S2 | 原始完成回调一律 loading=false，按 status 真值决定是否加入 completed；没有接入重试调度 | 同文件 23–27 行 |
| S3 | 对话框将 snapshot.loading 输出为 `data-loading`，visible 单独输出 | [DownloadDialog.jsx](../development-feedback-mechanism-v1-20261106/evidence/U2/candidate-start/src/DownloadDialog.jsx) 9–14 行；不能据此证明真实挂载 UI 的完整表现 |
| S4 | API 包装提供检查、调度重试和取消重试；实际 transport/scheduler 由宿主注入 | [preparation-api.js](../development-feedback-mechanism-v1-20261106/evidence/U2/candidate-start/src/preparation-api.js) 3–20 行 |
| S5 | 原始 close 设 visible=false；reopen 更新 token、visible 后开始检查。原始回调没有访问版本守卫 | [usePreparation.js](../development-feedback-mechanism-v1-20261106/evidence/U2/candidate-start/src/usePreparation.js) 23–40 行 |
| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 | [BackgroundExportPanel.jsx](../development-feedback-mechanism-v1-20261106/evidence/U2/candidate-start/src/BackgroundExportPanel.jsx) 14–16、19–38 行 |

S6 只是相邻实现的证据，**不是前台对话框必须采用完全相同政策的证明**。API 包装没有完整状态 schema，不得发明 `status.ready` 等字段或任意重试间隔。

## 4. 历史补丁和实际失败

P 增加了 generation、mounted、retry 等控制，加入 pending 重试和关闭/重开失效处理。其完成回调通过 generation/mounted 检查后，**先执行 `state.current.loading = false`，再判断 ready 或 pending**。

```text
开始准备：loading=true
    ↓
一次检查返回 pending
    ↓
补丁先把 loading 设为 false，再登记 retry
    ↓
等待下一次检查：准备尚未 ready
    ↓
后续检查返回 ready，最终完成
```

O 中 `schedules.downloadPending.assertions[0]` 的记录为：

| 测试项 | 实际 | 预期 |
|---|---|---|
| waits | false | true |
| completesOnce | true | true |

因此，本次明确失败是**中间等待指示缺失**，不是最终没有交付或没有 retry。测试将它判为失败；等待指示的具体产品政策仍需人工确认。

## 5. 需要人工确认的契约关系

| ID | 拟采用的标准要求 | 当前依据与边界 |
|---|---|---|
| R1 | pending 继续检查，ready 才交付 | T 直接支持；不能将 pending 当作整个过程完成 |
| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 | O 明确要求；S1/S3/S6 提供线索，但 T 未直接定义 loading 的全区间含义，必须人工确认 |
| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 | O 的其他路径及 P 中保护支持该诊断目标；具体政策需核对任务和调用方，不从函数名直接推出 |
| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 | T 的维护目标、S5/S6 及 O 的已通过项；保留政策应独立确认 |

## 6. 机制判断与未知

**有依据的候选机制：**补丁以“单次请求完成”为边界清除状态，而评估期待“整体准备尚未完成”期间继续等待。P 的赋值位置与 O 的中间失败一致。

**尚未证明：**`loading` 是否必须独自表示整个过程；是否允许由 loading 与 retryScheduled 组合表达等待；原任务没有明示完整字段协议。包装 API 没有明确异常处理、超时、重试间隔、重试次数或所有返回值形状，不能在标准中擅自添加。

该次反思证据记录没有证明运行过真实挂载的 React 行为验证。hook 替代检查、snapshot 检查和真实组件表现应分开报告。

## 7. 用本稿检查模型分析报告

| ID | 应检查的内容 | 不足或错误示例 |
|---|---|---|
| A1 | 区分单次请求与整体准备过程 | 请求返回就认为任务完成 |
| A2 | 找到 waiting 的实际消费者和状态来源 | 仅凭 loading 变量名规定业务含义 |
| A3 | 覆盖 pending 返回到下一次检查前的间隙 | 只检查最后是否成功交付 |
| A4 | 分别核查 ready 交付、等待表现和已排队 retry | 因最终成功，就称全流程正确 |
| A5 | 区分前台访问、旧回调与后台组件的政策 | 关闭任何面板都取消所有后台工作 |
| A6 | 标明产品政策、API schema 和验证覆盖的未知 | 发明返回字段，或将相邻后台实现当作强制规范 |

可接受等价表述，不要求复述本稿。每项记录“满足／部分满足／不满足／证据不足”及引用。不以文字完整程度替代语义正确。

后续验证应在每个阶段观察 waiting、retry、completed：开始、pending、retry 间隙、retry 触发、ready、close、reopen 后旧结果与当前结果。真实 React 挂载与替代 harness 的范围分别说明。**本次未新增或运行测试。**

## 8. 请你填写确认结果

| 请确认 | 结论：确认／需要修改／无法判断 | 修改理由或疑问 |
|---|---|---|
| S1–S6 的源码事实和原始/补丁区别是否准确？ | 待填写 | |
| R2：等待指示是否应覆盖整个 pending/retry 间隙？ | 待填写 | |
| waiting 必须由 loading 表达，还是可以组合表达？ | 待填写 | |
| close/reopen 与后台工作的政策，哪些有充分依据？ | 待填写 | |
| A1–A6 是否覆盖你希望模型理解的关键内容？ | 待填写 | |

复核人：待填写。日期：待填写。整体状态：待确认。批准进入标准的条目 ID：待填写。未决条目：待填写。

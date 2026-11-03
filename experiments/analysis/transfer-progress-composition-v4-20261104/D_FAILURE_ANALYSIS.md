# D 为何从 A 的 9/10 降为 5/10

实验：`e-17fd00c46db24e49`，`gpt-5.6-terra / medium`，A/D 各一次。以下区分已验证的补丁机制与尚未证明的报告因果效应。

## 直接根因：显示守卫同时阻止了审计记录

A 的 progress.js 在 deliver 内先 `record(frame)`，再仅对 `receive(frame)` 应用 active 与到达顺序守卫。D 在 deliver 入口执行 `if (!active || frameNumber < deliveredFrame) return`，导致 record 和 receive 一起被跳过。

原 README 区分 recordProgress（历史）与 showProgress（界面），并指向 queue.js；原 queue.js 的 record 无当前 visit 守卫，receive 才检查 `state.current === visit`。保留历史与阻止过期界面更新是不同条件。

| D 额外未通过场景 | 失败断言 | 机制 |
|---|---|---|
| accepted-after-hide | retired.audit-retained | 关闭后，先前接纳的帧完成解码，本应继续记录；active=false 提前丢弃 |
| frame-reversed | reversed.audit-all | 新帧先完成后，旧帧不得回退 UI，但仍需记录；排序守卫把旧帧历史一起丢弃 |
| composed-reverse-cleanup-switch | composition.audit-split | 反序完成与切换组合时，旧的已接纳帧历史丢失 |
| retry-preserved | retry.audit | 新 attempt 已显示后，旧 attempt 已接纳的帧完成；历史仍需保留 |

这些场景的失败断言均为 audit，不能描述为 D 的 UI 回退保护完全未起作用。

## 临时副本干预回放

验证当前 oracle 文件与已保存 evaluation 的摘要一致，并核对归档 candidate 文件摘要。使用同一 Node v16.20.2，对临时副本执行同一探针；原始输入、结果、评分和 oracle 未改。

只对 D 临时副本把 `record(frame)` 从入口守卫之后移到之前，其余文件和逻辑保持不变。

| 回放输入 | 场景通过 | 整体结果 | 未通过 |
|---|---:|---|---|
| A 原补丁 | 9/10 | UNDERREACH | start-switch-admission |
| D 原补丁 | 5/10 | UNDERREACH | 上述共同遗漏 + 4 项 audit |
| D 临时副本：先 record，再做 UI 守卫 | 9/10 | UNDERREACH | start-switch-admission |

证据支持：这次额外四项失败由 record 放在统一丢弃守卫之后造成。第三行是执行者的局部干预，不计为新的 Agent 成功或正式修复结果。细节保存于 D_FAILURE_REPLAY.json。

## 两组共同遗漏

`start-switch-admission` 在 A/D 均失败。start 同步发 A1 → 回调切到 B → B1 → 外层 A 的 start 继续发 A2。A2 是访问退休后才到达的新帧，探针要求它不得新增旧访问审计；这不同于退休前已接纳、退休后才完成的帧。调整 deliver 内 record 的顺序不能补上接纳时机与跨文件身份传递。

该旧 case 的专项核查曾标记这项 latent admission 义务依据需要独立语义复核，oracle 也有已知漏检。这里准确报告探针行为，不据此宣称所有 hidden 要求均无争议。

## 报告与可见搜索轨迹

D 报告选中的文件是 progress-source.js、progress.js、telemetry.js、transfer.js；未覆盖定义两种输出业务关系的 queue.js。报告提示“移除监听后，已开始的工作完成时是否还有有效性检查？”，也明确询问“哪些边界应使旧结果失效，哪些工作应继续？”。它没有要求删除审计历史。

A 可见轨迹读取了 README.md、queue.js、panel.js 等，并在自测中断言旧帧仍出现在 recorded/audits 里。D 可见轨迹读取集中在报告涉及的四个文件，未见 README.md、queue.js、panel.js、retry.js 的读取。D 的相关自测将 record 参数替换为 `() => {}`，只检查 display 与 telemetry，因此审计丢失无法使自测失败。D 还修改了 progress-source API 和 telemetry，但临时副本保持这些修改仍恢复 9/10，故这些额外修改不是四个评分差异的必要解释。

“报告使注意力集中到局部生命周期守卫，并缺少保留条件”是与轨迹一致的解释；单次 A/D 没有排除随机性或其他影响，不能证明报告必然造成退化。

## 对工具设计的启示

1. 给每个效果单独核查：record 与 receive 是否共享失效规则，哪些副作用必须继续。
2. 检索应补充调用方和回调实参来源：从 watchTransferProgress 的 record/receive 追到 queue.js，再看到 recordProgress/showProgress 的不同约束。
3. 当前新增 helper 主要沿词法定义与导入展开，参数回调尚不能自动追到调用方；本次 D 也未启用该 helper，不能宣称已有 RAG 已解决此问题。
4. 评估采用原报告、报告加调用方上下文、同预算通用检索对照；既测补缺，也测破坏已有行为。自测覆盖审计与 UI 两类效果，防止全部断言只验证新加守卫。

# 低噪声展示（0.6.2）

实现假设：先保留原始分析接口和证据，再收紧面向人的默认输出。筛选证据完整性，不依据已知修复结果选择提示，也不声称已验证用户或 LLM 的收益。

- Markdown、HTML 默认使用 focused 视图；新归档报告的 Markdown/HTML 也采用此视图，MCP 读取新归档的 full 材料时得到该 Markdown。历史归档和冻结的 A–G 实验材料不修改。
- CLI `scan` / `compare` 使用 `--view exploratory` 恢复全部提示与语法事件。
- CLI JSON、`analyze_sources`、归档 JSON 保持完整原始证据，不受 `--view` 影响。需要紧凑结构化输入时，使用 `temporal_contract_analyzer.review.focused_review(report)`。
- 默认只展示 `reentrant-state-publication` 的 `write_after_call`：文件解析成功，guard/callback/write 和展开路径引用均存在于该文件，存在对应的 `external_call_before_state_write` 关系，且无已记录的不确定性。
- 同一文件、入口、状态绑定、guard 和 write 合并为一张卡，保留原提示 ID 和各条调用证据。不同状态和不同入口不合并。
- `write_before_call` 只列顺序事实；`not_established` 和其他规则计入隐藏原因，不转成报警。未展示候选不等于安全。当前默认筛选尚未覆盖其他时序问题类别。
- 单条源码摘录上限 240 字符，截短显式标注并保留文件/行号；原始源码和原始报告不截短。
- 解析失败、跳过范围和分析限制始终可见。对照两侧分别筛选，卡片消失不等于已修复。

示例：

```sh
python3 -m temporal_contract_analyzer scan /path/to/project --format md
python3 -m temporal_contract_analyzer scan /path/to/project --format html --view exploratory
```

这次修改不重建 VSIX，不改变旧实验筛选条件，不计算缺陷概率。输出更少只是报告长度和展示数量变化；准确率及实际辅助效果需要独立项目评估。

## 已有真实修复的展示检查

在仓库内 `external-tests/reentry-publication-v1/fixtures/p-debounce/snapshots/{before,after}/index.js` 上重新运行 0.6.2 分析，分别渲染同一份原始结果的两种 Markdown 视图：

| 版本 | 原始提示 | 默认问题卡 | 探索视图字符数 | 低噪声视图字符数 |
|---|---:|---:|---:|---:|
| 修复前 | 4 | 1 | 11,090 | 1,855 |
| 修复后 | 4 | 0 | 10,337 | 848 |

修复后另保留一条顺序事实：`currentPromise` 在 L121 写入，外部调用位于 L129。上述是报告字符数，不是 token、费用、准确率或 LLM 成功率；该案例已参与规则开发，不是独立验证集。


## 0.6.3 增补

同一筛选策略现在也能展示受限正分支中的一次性回调清空候选；不用放宽“证据完整且无已记录不确定性”的门槛。onetime 固定源码由 0 张卡变为 1 张，证据指向 L17 guard、L18 调用、L19 清空；详细边界见 `STATE_PUBLICATION_REVIEW.md` 的 0.6.3 小节。原始开发检查和历史报告不覆盖。


## 0.6.4 增补

默认门槛保持不变；新的有界嵌套路径可提供完整 guard/调用/标志写入关系。component/once 原版识别为写入在前，仅保留顺序事实；人工延迟写标志变体识别为写入在后，展示 1 张卡并带外层接收者条件。不同分支不合并；this[key] 状态仍未覆盖。见 `STATE_PUBLICATION_REVIEW.md` 的边界说明。


## 0.6.5 增补

默认筛选门槛不变；现在支持严格 null 早退后的简单一跳参数副本调用。默认卡保留副本复制位置，区分“原绑定清空”与“副本覆盖”。Async.once 原版仅列清空在前的事实，人工延迟清空变体展示 1 张卡；完整限制见 `STATE_PUBLICATION_REVIEW.md`。


## 0.6.6 增补

默认门槛保持不变。接收者函数的 Reflect.apply/construct 两条候选按调用分别保存，选定条件臂不混合执行；同一标志的候选在默认视图合并，保留两种调用位置和来源。@ungap/once 原版仅列两条调用前写入事实，人工变体合并为 1 张问题卡。限制见 `STATE_PUBLICATION_REVIEW.md`。


## 0.6.7 增补

默认筛选可使用新的调用后清空证据，不降低源码/关系完整性门槛。报告把“入口状态写入顺序”和“回调绑定随后清空”分开：后者附中性说明，不自动作为问题。just-once 原版保留清理且不报警，人工延迟标志变体展示 1 张卡。新的关系字段缺失时保守隐藏。


## 0.6.8 增补

默认门槛保持不变。新增受限数字预算检查：原版先递减再调用只列顺序事实，调用后递减可形成 1 张核查卡。若关联到条件清理，报告单独展示其条件，不能将清空当成所有路径必然执行的动作。结论依赖有限安全整数预算及实际用途，详见 STATE_PUBLICATION_REVIEW.md。

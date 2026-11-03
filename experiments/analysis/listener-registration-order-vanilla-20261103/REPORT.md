# listener-registration-order-vanilla：最新 A/D 对照分析

实验：`e-90856b1211eb4fe3`；北京时间 2026-11-03 23:38–23:44。模型：`gpt-5.6-terra / low`。每条件一次，顺序 A→D。

观察：A 无报告为 UNDERREACH，D 附加审查报告为 PASS。参考修复校准 PASS。D 补上了 A 遗漏的旧异步解码交付有效性检查。当前数据是一次机制性观察，不能估计总体收益。

| 指标 | A：无报告 | D：审查报告 | D 相对 A |
|---|---:|---:|---:|
| Agent 墙钟秒数 | 197.76 | 156.87 | -20.7% |
| 累计输入 token | 100,154 | 123,401 | +23.2% |
| 缓存输入 token（输入内的子项） | 86,784 | 95,232 | +9.7% |
| 输入减缓存 token | 13,370 | 28,169 | +110.7% |
| 输出 token | 2,175 | 1,896 | -12.8% |
| 单列 reasoning output token | 950 | 602 | -36.6% |
| 输入 + 输出 token | 102,329 | 125,297 | +22.4% |
| 初始提示词字符数 | 433 | 14,706 | D 含 14,216 字符报告及包装 |
| 修改文件数 | 2 | 2 | 相同 |
| shell 命令次数 | 3 | 3 | 相同 |

## 功能差异

两组都将监听注册提前到 connect 之前，并给同步重入后的清理句柄写入增加代次检查；两组都未修改 metrics consumer。A 直接把 publish 传给订阅，代次只检查清理句柄赋值。D 用回调包裹 publish，在每次异步交付时检查 currentGeneration === generation，并在 show/close 时推进代次。

A 未通过：decode-after-switch、decode-after-close、same-channel-reopen；D 在这三个场景以及其余四类调度中均满足该探针检查，无越界效果。D 自编检查也覆盖了异步 decode 后 close，A 自编检查只覆盖 bootstrap、同步切换/关闭。

## 与工具报告的关系

D 实际 prompt 附加的报告包含 continuation-and-listener-removal，核查问题是“若二者相关，移除监听后，已开始的工作完成时是否还有有效性检查？”，并包含 continuation-lifecycle-boundaries 等提示。D 的交付代次守卫与这些提示一致。但轨迹未明确逐条引用报告，不能证明某条提示导致了修复。

## 时间和资源解释

D 比 A 少 40.89 秒（20.7%），但两组都发生多次连接超时和 HTTP 回退，尚无可靠的纯推理耗时。不能据此声称工具加速了 20.7%。

D 累计输入 +23.2%、输入加输出 +22.4%；输出 -12.8%、单列 reasoning output -36.6%。不重复叠加缓存或 reasoning 字段。输入减缓存从 13,370 增至 28,169（+110.7%）。这不是费用计算：没有账单、定价或重试计费明细；累计输入也不是单份报告的 token 长度。

## 范围与下一步

本实验只测旧的 D 冻结审查报告，未使用新增自动上下文补全。案例属于已接触开发材料，不能用作独立留出证据。

建议在独立副本上比较无辅助、原报告、报告加上下文三条件，固定模型/配置与预算、平衡运行顺序并重复。完整保留网络异常与缓存字段，分别报告成功率和资源；再用两个拆分开发题定位帮助来自同步重入还是异步交付。若结论声称分析引导检索优于一般检索，还需加入相同预算的检索基线。

## 原始证据

- Manifest：/Volumes/Extreme/paper+survey/temporal-contract-reports-experiments/e-90856b1211eb4fe3/manifest.json
- 行为验证：/Volumes/Extreme/paper+survey/temporal-contract-reports-experiments/e-90856b1211eb4fe3/evaluations/v-bd139da61ce34c88/summary.json
- A/D 改动：各 jobs/j-001、jobs/j-002/changes.json
- 轨迹与网络异常：各 jobs/j-001、jobs/j-002/events.jsonl、stderr.log

量化表的机器可读来源：METRICS.json。原始运行和验证文件未修改。

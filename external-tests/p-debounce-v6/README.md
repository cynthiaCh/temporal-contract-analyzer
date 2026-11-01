# 小型开源探查：p-debounce 6.0.0

日期：2026-11-01。结论：项目足够小，已经完成当前时序分析器的扫描与行为核对；没有确认新 bug，没有比较 Agent 有无工具的收益。

## 先看什么

1. [147 行原始实现](upstream/index.js)。
2. [可直接打开的分析报告](REPORT.html)。
3. [四个简短行为探查](probe.mjs)，以及 [实际输出](BEHAVIOR.json)。

上游：https://github.com/sindresorhus/p-debounce
固定版本：`7fd1617e1ee9dac490fb659f59bd1e9f04d92c47`，package version `6.0.0`。
完整源码档案只有约 15 KB，运行时依赖为零。源码保留在忽略目录 upstream/；其 MIT 许可证另存为 UPSTREAM_LICENSE.txt。未改上游实现，也未安装依赖。

## 这次实际结果

| 项目 | 结果 |
|---|---|
| 核心扫描范围 | 只有 index.js，147 行；readme/test 不进入分析器 |
| 静态解析 | parsed，104 个语法事件、4 条提示、0 条候选直接调用连接 |
| 效果定位 | 4 张卡中 3 张没有具体效果引用 |
| 上游 Node 运行测试 | 102 项，102 通过，0 失败 |
| 独立编写的行为探查 | 4/4 通过 |
| 未执行 | npm test 中的 xo lint、tsd 类型检查；Agent 对照 |

Python 分析器版本 0.6.0。初次扫描使用系统 Node 16；标准化复跑使用本机 VS Code 内已有的 Node 24.21.0，满足上游 >=22 要求。LATEST.json 指向标准化复跑。不同 Node 环境的历史报告不用于前后提示差异比较。

## 最容易理解的时序问题：取消发生在哪个阶段

同一个 abort，在不同阶段有不同结果：

| 场景 | 实际观察 |
|---|---|
| 等待期间 abort | 原函数未执行，调用 promise 用原取消原因拒绝 |
| 原函数已经开始后 abort | 原函数完成，调用 promise 返回结果 |
| after:true，A 执行时连续传入 B、C | 执行 A、C；三名调用者结果是 A、C、C；最大同时执行数为 1 |
| 原函数同步重入包装函数 | 共享进行中的 promise；原函数只调用一次 |

第二项不是本次发现的 bug。上游 test.js:1270 的测试明确要求执行中的函数继续完成。源码 index.js:51 在调用前移除 abort listener，并在 :45 保存本次调用者列表；之后的完成通知应针对该列表。不能仅因 await 后 signal 已取消就认定这些完成通知必须丢弃。

重入的关键是 index.js:113 先设置 currentPromise，再在 :116 调用传入函数。本地 probe.mjs 用可控 Promise 屏障重放这些边界；启动前取消另观察了一个有限计时窗口。这些是有界行为证据，不是全程序证明。

## 四条提示怎样解释

| 提示 | 执行者源码核查 |
|---|---|
| hint-1：完成回调与监听移除共现 | :116 和 :51 属于两个不同 API；没有证明它们构成同一取消链 |
| hint-2：调度/重试线索 | 找到的是防抖计时器，不能直接解释成重试循环 |
| hint-3：延续与生命周期边界 | 是有用的检查入口，但未区分启动前取消和启动后完成的政策 |
| hint-4：保护状态核查 | 混入参数合法性检查和多处局部变量赋值，尚未解释哪条保护约束哪个效果 |

这是 assistant 执行者的核查，不是独立人工 gold。结论保存在 ANALYST_REVIEW.json，没有冒充 human notes 写入报告库。

## 这个例子对工具改进的价值

它提供一个很小的真实回归对象：下一版应更清楚地列出 resolveFunction/rejectFunction 等候选效果，分别连接等待窗口、执行阶段和调用者列表，保留未知，而非把同文件的 finally 与取消直接合并。还可检查能否呈现 currentPromise 在用户函数调用前赋值的重入保护关系。

成功标准应是补出有依据的关系、减少无关关联；提示更多并不等于更好。此项目与行为测试已被执行者阅读，后续只能作为开发/探索材料，不能改称未见盲测。

## 一条命令复跑

从分析器仓库根目录执行：

```sh
python3 -B external-tests/p-debounce-v6/run.py
```

脚本自动选择已有 Node >=22。当前机器可直接复用 VS Code 自带运行环境。也可用 `--node /absolute/path/to/node` 指定。不会自动安装 Node、npm 包或改全局配置。源码目录缺失时才下载这个固定版本；已有目录不覆盖。每次复跑产生新的报告 ID 和 reruns/ 日志，不覆盖历史归档。

## 用现有边界审查网页查看

```sh
python3 -B -m temporal_contract_analyzer reports open \
  --store "/Volumes/Extreme/paper+survey/temporal-contract-analyzer/external-tests/p-debounce-v6/reports" \
  --report-id r-20261101T011431992056Z-a2087708703d
```

报告 ID：`r-20261101T011431992056Z-a2087708703d`。存储在本探查目录，没有向你原有研究报告库混入这次数据，也没有修改分析器规则。

## Task 1/2/3 与工作量

- Task 1：选择并固定一个单文件开源库；范围是独立探查目录，未扩展分析器。
- Task 2：完成单文件扫描、上游运行测试、四个行为探查；新增一个小型复跑脚本与探查脚本，无新依赖。
- Task 3：核对提示、记录局限并生成报告。工作量是一轮小型工程试跑，不包含新提取算法、模型实验或完整准确率评估。

建议 Git 提交文本（本次未提交）：

```text
chore(temporal): add a small pinned p-debounce pilot

- Record source provenance, scan output and bounded analyst observations.
- Add dependency-free behavior probes and a repeatable local runner.
- Validate 102 upstream Node tests and four probes; keep lint, type and agent studies unrun.
```

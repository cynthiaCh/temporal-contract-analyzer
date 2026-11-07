# 三个代码分析标准草稿（2026-11-07）

本轮只建设评价材料：**三个草稿均待用户确认，AI 辅助编写不是独立人工审查。**没有新模型报告，因此没有跨案例模型弱点或方法有效性的结论。没有修改技能、业务代码、原题库、评分器或历史文件，没有运行模型、GEPA、维护或评分，也不创建提交。

## 案例与阅读顺序

建议先读 **[C2：延迟写入结算](C2-draft-settlement.md)**：候选 README 明确给出返回前／归档前的边界，便于先确认“要求来自哪里”。然后可读 [C1：首事件与监听](C1-presence-bootstrap.md) 和 [C3：异步提交归属](C3-submit-attribution.md)。

| 草稿 | 项目／来源单元 | 不同的主要机制 | 最关键待确认事项 |
|---|---|---|---|
| C1 | Presence EventTarget workspace；listener-registration-order | bootstrap 与注册的先后，以及消费者不同政策 | 面板接收初始状态、metrics 仍只统计增量的边界是否正确？ |
| C2 | Document draft workspace；debounced-submit-flush | 延迟保存与同步离开／提交的结算边界 | 不足 120 ms 时，是否仍保留返回前可读／归档前持久化？ |
| C3 | Audit commit controller；audit-commit-attribution | 操作入口快照与异步完成后的历史／界面归属 | 关闭／重开是否只改变提示资格，而不取消已接纳提交的成功历史义务？ |

三例不是 U1/U2 的改名；原来源单元不同，也没有把一个文档案例拆成两例凑数。但这**不证明三个独立真实项目／事故**：C1 是因果模式的 clean-room 重建，C2/C3 是 authored 开发题；C2/C3 共享计时／预览辅助模式，timers.js 字节相同。未来划分须保留来源单元及同源变体，保守把 C2/C3 作为关联编辑器辅助家族，不仅按案例名分组。C1 与 U1 都涉及事件，但这里的重点是首事件／增量消费者，不沿用 U1 的历史补丁结论。

另考察了 commit-ack-boundary（上下文过于压缩）、quote-acceptance（混合结算与快照关系）、draft-autosave-handoff-order-example（与 C2 同单元），未选为额外案例。没有为找案例启动模型或外部搜索。

## 冻结对象和可追溯性

| 案例 | 不可变输入归档（仓库根目录相对路径） | 已知暴露 |
|---|---|---|
| C1 | research/gepa-official-skill-experiment-v1-20261106/trials/reports-experiments/e-76911b3bf19540d2/input | 官方 GEPA 历史 test 执行，现按已暴露开发来源 |
| C2 | research/gepa-official-skill-experiment-v1-20261106/trials/reports-experiments/e-6eb27eb9536640d6/input | 官方 GEPA 历史 val 执行，现按已暴露开发来源 |
| C3 | results/selective-prospective-v1-20261104/screening/reports-experiments/e-7dee73af7d7046e3/input | 已有筛选记录；该次 prepared/not_started、model_calls=0，不代表完整历史从未暴露 |

[cases/](cases/) 保存上述 input 的完整必要候选文件：共 24 文件，另有 3 份准确原任务（manifest.task），逐字核对原 prompt。评价对象始终是**原始 input，不是历史 job 工作区／输出 patch**。原 task、文件清单、SHA256、行数、精确归档与项目单元见 [source-manifest.json](source-manifest.json)。外部本地 bench 元数据／base 只用于身份和版本交叉核对，复制源仍来自本仓库归档；provenance 的 source_record_sha256 是来源声明，未冒充独立溯源证明。

历史 manifest／暴露目录仅用于定位输入和记录暴露；本轮没有把历史补丁、隐藏评分、测试断言或模型自述写成事实或规范。C1 缺完整产品说明；C2 尚未接入延迟工具；C3 尚未等待 Promise 完成。这些限制在草稿内显式保留。没有引用测试预期；若以后引入，必须标“这是既有测试要求，仍需人工确认与任务及项目语义一致”，不能自动批准。

## 研究侧与模型侧

草稿、确认表、manifest、校验和历史材料均属于研究侧。后续如另行开展独立分析，每例只可提供对应 task.md 和 candidate 内源码／文档；不直接提供本标准、评分、历史修复或其他报告，并须实际隔离。本轮没有启动该实验。

[common-rubric.md](common-rubric.md) 仅定义未来可检验的共同维度，未填结果；不把篇幅增长当改善，不把事实条目当独立任务。允许分散／等价表达，未写出、反向写错、合理未知分别记录。

## 离线检查与状态

[validation.json](validation.json) 记录摘要、来源、引用行号、ID、待确认状态和既有文件保护检查；源码含义为执行 Agent 的有限证据核对，机械检查不等于语义正确或人工批准。未发现适用于本工作目录的 AGENTS.md；归档官方 GEPA 源码中的 AGENTS.md 不适用于本新增目录。起始 tracked diff 为空，最终保护结果见 validation。

所有确认选择均未填写，不继承 U1/U2 的批准。缺少宿主回调、数据类型、具体业务政策等证据的关系保持未知，不要求模型知道未提供情境。不称独立泛化测试，也不推断修复收益。

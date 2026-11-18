# 70训练 / 30测试输入与顺序粗审

**状态：proposed_not_frozen（建议方案，未冻结）。只完成公开元数据检查，未做动态运行校验或逐例真实时序语义复核。**

## 成员从哪里来

- 来源固定为提交 `4e61d07a5076bb3a46e6863f8d6265fb3c3c4c94` 中 `experiments/analysis/train70-gpt56-test30-summary-20261117/` 对应的70训练和30测试。用户给出的目录日期末尾多了一个7。
- 训练成员来自 `examples/tempoevo-v4/case-selections/incremental100-20261117/training_70_cases.csv`。测试成员来自 `experiments/testing-runs/tempoevo-gpt56-sol-medium-low30-untrained-workers8-20261117_180752/testing_30_cases.csv`，**不是**原 incremental100/split.json 中另一组30测试；不得混用。
- 70个训练ID、30个测试ID各自唯一，交集为0；与summary中的100例成员一致。训练70覆盖24个core、11个source_unit；测试30覆盖14个core，这14个core均见于训练。
- `manifest` 保留来源CSV的相对路径元数据，未打开这些manifest或验证其在当前运行环境可解析。输入包本身不证明solver/grader可运行。

## 为什么只调训练顺序

原顺序前22例都属于 `debounced-submit-flush`，前20例虽然语言多，但仅覆盖一个来源家族。`query-paused-initial-fetch-10266` 到第23例才出现，RxJS组集中在第67–70例。整体成员已有多类需求，不需为本次粗审大改划分；面向每10例一个checkpoint的新实验，调整训练顺序即可。

| 训练位置 | 原source/core组数 | 建议source/core组数 | 建议批次内debounced例数 |
|---|---:|---:|---:|
| 1–10 | 1 / 2 | 7 / 10 | 4 |
| 11–20 | 1 / 2 | 6 / 10 | 5 |
| 21–30 | 3 / 3 | 7 / 9 | 4 |
| 31–40 | 5 / 5 | 6 / 9 | 4 |
| 41–50 | 7 / 10 | 6 / 9 | 5 |
| 51–60 | 7 / 8 | 7 / 10 | 4 |
| 61–70 | 5 / 5 | 7 / 10 | 4 |

建议顺序只由 `source_unit → core_case → case_id` 决定。每一步优先选择相对于全70例比例“目前少安排”的来源，再在该来源内同样轮换core；平手用字典序，core内case_id也用字典序。不用随机种子，不读历史通过率、难度成绩或隐藏评分器。公式及可复算实现见 `validate_inputs.py:balanced_order`。测试30例保持原rank顺序。

该算法仅均匀分散已有分组，不保证每批包含所有机制，不建立“最好”的课程顺序，也未按成绩优化。30/70训练来自同一debounced家族的总体不平衡仍保留。CSV中的 `mechanism_hint` 只是 `source_unit` 的别名，不能把语言移植计作独立机制；测试source_unit由训练CSV内相同core的唯一映射补足。

### 建议顺序每批公开来源分布

- 第1批：async-generator-close-python × 1；debounced-submit-flush × 4；download-polling-restoration × 1；query-paused-initial-fetch-10266 × 1；reentrant-lifecycle-handoff × 1；rxjs-asyncsubject-reentrant-6520 × 1；transfer-retry-abort-handoff × 1。
- 第2批：debounced-submit-flush × 5；listener-registration-order × 1；local-config-readiness × 1；query-paused-initial-fetch-10266 × 1；subscription-lifetime-scope × 1；transfer-retry-abort-handoff × 1。
- 第3批：async-generator-close-python × 1；debounced-submit-flush × 4；download-polling-restoration × 1；draft-autosave-handoff-v2 × 1；reentrant-lifecycle-handoff × 1；rxjs-asyncsubject-reentrant-6520 × 1；transfer-retry-abort-handoff × 1。
- 第4批：debounced-submit-flush × 4；listener-registration-order × 1；local-config-readiness × 1；query-paused-initial-fetch-10266 × 2；subscription-lifetime-scope × 1；transfer-retry-abort-handoff × 1。
- 第5批：async-generator-close-python × 1；debounced-submit-flush × 5；download-polling-restoration × 1；reentrant-lifecycle-handoff × 1；rxjs-asyncsubject-reentrant-6520 × 1；transfer-retry-abort-handoff × 1。
- 第6批：debounced-submit-flush × 4；draft-autosave-handoff-v2 × 1；listener-registration-order × 1；local-config-readiness × 1；query-paused-initial-fetch-10266 × 1；subscription-lifetime-scope × 1；transfer-retry-abort-handoff × 1。
- 第7批：async-generator-close-python × 1；debounced-submit-flush × 4；download-polling-restoration × 1；query-paused-initial-fetch-10266 × 1；reentrant-lifecycle-handoff × 1；rxjs-asyncsubject-reentrant-6520 × 1；transfer-retry-abort-handoff × 1。

## 历史结果不能直接当本次增长曲线

原summary是已完成训练和跨模型测试的回顾总结：70训练中26例复用历史结果、44例实际补跑，且开始时已有39条经验，并采用并发执行。它不等于从空经验库按本顺序完成70例的轨迹。输入包不导入历史成绩或经验，不把旧结果重新贴成M0/M10等新节点；本次经验库初态与运行约束仍须在正式协议中冻结。

8个计划节点为 **M0、M10、M20、M30、M40、M50、M60、M70**，数字表示已处理训练case数，不是通过数或已接受经验条数。每个节点使用同30测试；测试期间不更新经验、不把Gold反馈传入训练。这里只声明计划，没有声称任何新节点已完成。

## 独立性与适用范围

这组30测试由既往目标模型基线表现筛选；来源报告记录24/30有先前测试暴露，17/30与训练任务文本完全相同，0/30任务文本与公开源码同时完全相同。后一个0不能排除近似任务或语义重复。成员ID不重叠不等于来源/机制独立。因此适合标为“同源变体、已有暴露背景下的经验迁移/开发性复测”，不能宣称全新独立留出集或无泄漏跨来源泛化。

以上是公开标签和已有公开审计结论的粗查，未读取隐藏Oracle/reference，未进行昂贵逐例语义复核。调整顺序不会消除原成员选择偏差；若要评估顺序敏感性，应另设预先登记的重复实验，而不是看新结果后再重排。

## 文件与校验

- `training-order.csv`：建议70训练顺序，每10例一批；`source_rank`记录原训练CSV行号。
- `testing-cases.csv`：原30测试成员及顺序；`selected-cases.csv`：合计100行公开元数据。所有历史成绩/模型结果字段已删除。
- `evaluation-split.json`：兼容官方 `tempoevo-incremental-split-v1`，selection_file为仓库相对路径且带SHA；额外声明建议状态和8节点。没有修改全局split注册表。
- `provenance.json`：固定来源提交、来源文件SHA、各输入文件SHA及逐批计数。自身不做自引用SHA。
- `validate_inputs.py`：只读重算成员、顺序、8节点、每批10例及哈希，读取固定Git提交中的公开CSV/summary；不联网、不写文件、不调用模型/评分器、不打开case manifest。

在仓库根目录运行：

```powershell
python -B experiments/experience-growth/train70-test30-20261118/inputs/validate_inputs.py
```

校验通过只表示输入元数据一致，不能据此跳过正式冻结、运行参数核对和动态小试。

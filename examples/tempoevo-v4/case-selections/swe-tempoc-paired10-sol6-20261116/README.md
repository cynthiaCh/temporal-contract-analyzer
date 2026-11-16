# SWE-TempoC：训练10 + 同机制测试10（2026-11-16）

本目录保留选例时的 **`gpt-6-sol / medium`** 历史依据；当前执行模型为 `gpt-6.1-sol / medium`。当前流程见 [WORKFLOW.md](../../../../docs/WORKFLOW.md)，经验构建不更新模型权重。

## 选择依据

- 全部来自冻结242条 roster；每条都有精确 case、精确模型与力度的历史 L（latent-maintenance）有效记录，原始通过率均 ≤50%。
- 只以 L 成绩判定难度；给定 Contract 和 Generic 成绩不参与筛选。异常、污染和未评分排除，不能计作失败。
- 10组一一配对：9组同父case跨语言/框架，1组为同源 autosave 不同父case的相似机制。双方精确ID不重叠。
- 全部是分析器覆盖的 Python、JS/React/jQuery/Vue；保留确认身份、共享取消、进度窗口、导航重入和轮询等机制。
- 训练最多使用旧训练case，不把旧预留测试case挪入训练；测试排除全部旧训练case。此目录不改写原25+25注册或全局模型默认值。

## 配对清单

下表通过率均为 gpt-6-sol / medium 原始 L 的通过数/有效次数。

|组|机制|训练case|原始L|测试case|原始L|
|---:|---|---|---:|---|---:|
|1|提交前刷新、退出屏障|`draft-autosave-handoff-vanilla-port-react`|0/3|`draft-autosave-handoff-vanilla-port-python3`|0/1|
|2|提交前刷新、退出屏障|`draft-autosave-handoff-vue3-port-jquery`|0/3|`draft-autosave-handoff-vue3-port-react`|0/3|
|3|提交前刷新、退出屏障|`draft-autosave-handoff-order-example-python3`|1/3|`draft-autosave-handoff-vue3-port-vue2`|0/3|
|4|确认入口身份与快照绑定|`review-confirmation-binding-python3`|0/3|`review-confirmation-binding-react`|0/3|
|5|确认入口身份与快照绑定|`review-confirmation-binding-vue3`|0/3|`review-confirmation-binding-jquery`|0/3|
|6|共享请求、惰性消费与取消|`query-paused-initial-fetch-10266-python3`|0/3|`query-paused-initial-fetch-10266-vue3`|0/3|
|7|同步首帧、接收窗口与乱序防回退|`transfer-progress-composition-v4-window-cued-vue3-eval-v2`|1/3|`transfer-progress-composition-v4-window-cued-vue2-eval-v2`|0/3|
|8|进度订阅、生命周期与清理|`transfer-progress-maintenance-v2-python3`|1/2|`transfer-progress-maintenance-v2-react`|1/3|
|9|导航重入、草稿归属与状态发布|`workspace-draft-projection-latent-vanilla-port-python3`|1/3|`workspace-draft-projection-latent-vanilla-port-vue3`|0/3|
|10|pending轮询、恢复与前后台所有权|`download-polling-restoration-python3-eval-v2`|0/2|`download-polling-restoration-jquery-eval-v2`|0/3|

第3组为不同父case：Python order-example 的尾沿合并、退出flush与草稿归属，迁移到 Vue2 编辑器；不能记为独立来源。其余9组父case相同。

## 历史基线规模

|集合|case数|有效运行累计|逐case通过率均值|
|---|---:|---:|---:|
|训练|10|4/28 (14.3%)|15.0%|
|测试|10|1/28 (3.6%)|3.3%|

累计是历史有效运行次数，不是新流程的成功率或pass@k。17条有3次有效记录，训练2条只有2次、测试1条只有1次，0/1不代表稳定0%。训练/测试各排除2次异常执行。

## 历史模型选择依据

选例时使用 gpt-6-sol / medium 是基于历史记录匹配：它在这20条上有完整的低L基线；gpt-6.1-sol / medium 在部分候选上缺L记录，另一些已高通过，不适合直接继承本清单的难度判断。
历史模型用于解释选例难度，不代表当前执行配置或模型优劣结论。当前模型设置以 [WORKFLOW.md](../../../../docs/WORKFLOW.md) 和实际冻结协议为准。
`model-profiles.json` 保留历史 sol6-medium 配置，仅用于重现选例依据；当前执行使用仓库 sol61-medium 配置。

## 用于训练和测试

使用本目录 training_10_cases.csv 和 testing_10_cases.csv；两份rank各为1–10，selected_20_cases.csv 中训练为1–10、测试为11–20。学习和测试都使用公开L任务与源码；当前系统生成自己的Auto-Contract，不能把历史给定Contract作为工具的输入或收益。
当前只运行完整已审核经验单组测试：冻结经验库、业务适用性检索、Auto-Contract、一次 Action、最终独立 Gold；不再做 A/B 或无经验对照，也不再执行 Contract Review。
选例依据已知历史结果，且同源变体有意跨集合配对，所以只能报告同机制/跨表示迁移，不能报告未见来源泛化或独立盲测。训练流程最多3次Action，测试按当前实现1次Action/最终Gold；不要把二者的重试成功率直接相减。

## 就绪程度与限制

选例阶段仅完成原始回执核对、输入指纹冻结与模型配置；后续执行状态以末尾链接的当前批次配置和原始运行目录为准。额外的当前全库完整性检查和旧catalog接入检查见 benchmark-acceptance-check.json 与 catalog-readiness.json；这些是选例之外的运行前状态，不包含在 selection validation 的PASS内。
当前 SWE-TempoC 全库不匹配 MANIFEST.json，因此不能继承已发布242/242验收结论；新执行前需核对源码差异并重新校准环境。部分新case尚未接入当前训练catalog，且 --swe-tempoc-root 适配器目前仅支持testing；本清单不能直接宣称为已校准、可执行的训练批次。测试case也不能因catalog缺项被改作训练。

## 文件与复现

- `selection.json`：20条精确case、10组关系、规则和历史统计。
- `baseline-trials.jsonl`：仅选中模型在这20条的原始L回执索引，包含异常记录；逐份源回执SHA已核对。
- `provenance.json`、`public-input-sha256.json`：历史表、roster、旧split、公开任务和源码指纹。
- `validation.json`：计数、阈值、角色限制、回执与公开输入检查。

```bash
python3 -B examples/tempoevo-v4/case-selections/swe-tempoc-paired10-sol6-20261116/build_selection.py \
  --history /home/sribd/Downloads/wangshu/tempoevo-swe-tempoc-history-20261116/swe242-per-case-model.csv \
  --trials /home/sribd/Downloads/wangshu/tempoevo-swe-tempoc-history-20261116/deduplicated-trials.jsonl \
  --bench /home/sribd/Downloads/wangshu/swe-tempoc
```

现行经验构建与测试设置见 [WORKFLOW.md](../../../../docs/WORKFLOW.md)。选题时的低历史通过率属于 gpt-6-sol/medium；恢复 V8 后模型改为 gpt-6.1-sol/medium，不应把旧模型通过率当作新模型的实测基线。

当前测试采用 [业务适用性单组全量经验配置](testing-protocol-business-full-memory.json)：冻结全部已审核经验，4 workers，test10；历史 A/B 方案不再执行。

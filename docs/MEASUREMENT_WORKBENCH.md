# 义务测量工作台

义务测量工作台把源码扫描、人工语义测量和独立复核连接起来，但不把三者混为一种证据。

## 证据边界

1. Analyzer 扫描候选源码，产生位置、语法事实和待核查问题。
2. 研究者建立义务，明确 activation、identity、deadline、continuing work 和 forbidden effects。
3. 工具检查证据引用、充分集、时序关系、所有权和 application chain，并据已声明结构推导 E/T/L/H。
4. 行为 witness 单独记录。扫描命中不能替代测试或轨迹，未知也不能当作通过。
5. 两位不同于作者、声明 outcome-blinded、完成全部检查且与推导结果一致的复核者，才能通过复核门禁。

任何扫描 finding 都不会自动写入正式义务或标签。正式测量是人工语义声明的机械校验，不是自动契约推断，也不是程序正确性证明。

## 从归档报告开始

先扫描并取得报告 ID：

```sh
python3 -B -m temporal_contract_analyzer reports scan /path/to/project
```

生成绑定该源码快照的空白草稿：

```sh
python3 -B -m temporal_contract_analyzer reports measurement-template REPORT_ID \
  --output /path/to/measurement.draft.json
```

也可以从一条扫描 finding 开始：

```sh
python3 -B -m temporal_contract_analyzer reports measurement-template REPORT_ID \
  --finding-id FINDING_ID --output /path/to/measurement.draft.json
```

这种草稿只把 finding 引用的语法事件复制成 `candidate-syntax-clue` 证据单元，仍然不创建义务、不填写 predicate，也不推导正式标签。网页“证据与核查”中的“建立候选测量草稿”执行同一操作。

草稿的 `obligations` 和 `evidence_units` 为空。研究者应填写：

- `conditions`：候选可见条件及其 prompt/specification 材料；
- `evidence_units`：语义事实及其精确源码或条件材料锚点；
- `sites`：失效边界和 commit 位置；
- `witness_artifacts`：嵌入并按 SHA-256 绑定的测试命令、测试输出、轨迹或复核记录；
- `obligations`：确认记录、五部分 predicate、行为 witnesses；
- 每个 condition × obligation 的规则证据、时序关系、ownership 和 application chain；
- condition 级 consumer policy，用于推导 H。

保存草稿或正式测量：

```sh
python3 -B -m temporal_contract_analyzer reports measurement-add REPORT_ID \
  /path/to/measurement.json
```

`workflow_status=draft` 允许逐步保存；`workflow_status=final` 要求每条义务已经人工确认，并完整覆盖所有 condition × obligation 单元。报告库网页的“义务测量”页也可生成、编辑和追加 JSON 草稿。

## 独立复核

取得 `measurement-add` 返回的 `record_id` 后生成复核表：

```sh
python3 -B -m temporal_contract_analyzer reports measurement-review-template \
  REPORT_ID MEASUREMENT_RECORD_ID --reviewer reviewer-a \
  --output /path/to/reviewer-a.json
```

复核者独立填写标签、application counts、八项检查、分歧和备注，再追加记录：

```sh
python3 -B -m temporal_contract_analyzer reports measurement-review-add \
  REPORT_ID MEASUREMENT_RECORD_ID /path/to/reviewer-a.json
```

网页中的每条测量记录也提供同样的“生成复核表”和“校验并追加复核”入口；复核表始终绑定该测量的 SHA-256。

身份独立性和 outcome blindness 是自我声明，工具只能检查声明、记录覆盖与结果一致性，不能证明真实组织关系或认知隔离。

## Paper 1 v0.6 只读兼容

Paper 1 的冻结 MeasurementBench 仍留在 `temporal-contract-bench`，不会被本工具替换。已经由原验证器生成的 v0.6 measurement report 可以只读导入：

```sh
python3 -B -m temporal_contract_analyzer reports measurement-import-v06 \
  REPORT_ID /path/to/v06-measurement-report.json
```

导入器保存原报告摘要和 SHA-256，不重跑原验证器、不更改 Paper 1 数据，也不声称 benchmark tree hash 与 analyzer 源码快照等价。若要在独立工具中取得正式门禁，应重新建立原生测量文档并完成复核。

## 三种使用层级

- **source-only**：只有归档源码；可以建立义务与源码证据，行为见证保持 unknown。
- **test-aware**：witness 通过 `artifact_ids` 引用具体测试命令、输出、断言或轨迹；confirmed/failed witness 必须至少绑定一份 artifact。
- **benchmark compatibility**：只读展示原 MeasurementBench 0.6 结果；完整 Oracle 验证仍由冻结的 Paper 1 工具负责。

Agent 的 B–G 材料仍只来自候选源码扫描。正式义务、Oracle、行为结果和复核记录不会自动进入 Agent 输入。

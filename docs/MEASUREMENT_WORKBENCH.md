# 边界审查与高级测量工作台

日常使用采用“边界审查卡”，完整 E/T/L/H 留作研究分析的可选层。主入口围绕“这里跨过了什么边界，哪些效果需要重新检查”组织。用户无需先填写完整 v0.6，通用工具也无需先恢复项目中的全部义务才能提供帮助。

## 默认流程：扫描、查看卡片、核查

macOS 可双击仓库根目录的 [启动边界审查工作台.command](../启动边界审查工作台.command)。并排检出的 `temporal-contract-bench` 根目录也提供同名入口。入口使用系统 Python 3.9+ 与已配置的共用报告库，重新启动服务以加载当前源码并打开浏览器。服务在终端前台运行，关闭终端或按 Ctrl+C 会停止服务，已有报告和核查记录保留。首次打开尚无报告时，可点击“新建扫描”。

先归档源码扫描，再打开报告库并选择报告：

```sh
python3 -B -m temporal_contract_analyzer reports scan /path/to/project
python3 -B -m temporal_contract_analyzer reports open
```

默认页“边界审查卡”每张只回答四个问题。下表是**人工核查后的示例**，不是工具已从任意仓库证明的事实：

| 核查项 | 示例：modal 关闭后仍收到通知 |
|---|---|
| **执行边界在哪里？** | `await` 返回、通知回调开始 |
| **什么可能已经变化？** | 发起工作的 modal 已关闭 |
| **影响什么效果？** | 回调继续写入 `modal.value` |
| **仓库要求与保护是什么？** | 若仓库要求关闭使旧通知失效，检查关闭状态或取消信号是否约束写入 |

工具将现有 finding 的源码引用整理为候选边界、写入/效果及保护位置，并保留成立条件。变化描述是待核查的可能性；没有定位到具体效果时明确要求追踪延续或回调。语法共现、名称线索、`if` 或取消调用的存在，都不足以证明业务关系或保护充分。

人工主要判断三件事：

- **这条关系是否成立？** 使用 `confirmed / dismissed / uncertain`，对应核查成立、核查不成立、待确认；这里确认的是审查关系，不是“确认 bug”。
- **现有保护是否充分？** 单独记录 `sufficient / insufficient / uncertain`，因此关系成立仍可有充分保护。
- **还缺什么证据？** 记录仓库要求与保护依据的位置，以及尚缺的调用路径、API 语义、测试或轨迹。证据不足保留待确认。

卡片初始为待确认；人工意见追加到绑定报告 ID 与 finding ID 的 `notes` 中，不改写归档源码、正式义务或标签。旧的纯文本意见兼容读取。查找仓库规范、调用处或测试后，才逐步形成有仓库依据的义务；完整义务标注不构成扫描或日常审查的前置条件。

## 修改任务：优先检查改动涉及的卡片

在卡片页填写本次改动的相对文件路径，或在有关联基线的报告中点击“使用基线间变化文件”。工具按卡片源码引用及报告中已有候选直接调用关系筛选相关卡片，并展示显示数量、指定路径、关联文件与未捕获路径。随时可返回全部卡片。

当前扩展是**文件层面的候选直接调用关系**，可能纳入同文件内无关函数，不能宣称覆盖完整调用链。动态派发、对象实例、回调目标、框架调度和扫描范围外的路径未完整覆盖。“扫描范围与未覆盖内容”保留解析失败、跳过文件和分析限制；未显示或未命中的路径不计为通过。

## 交给 Agent 的材料

“复制给 Agent 的核查材料”生成含候选边界、变化、效果、核查问题、成立条件、最近人工意见、缺失证据及源码位置的文本，并附报告 ID 与输入摘要。日常交接可以很短，例如：

> 此异步延续可能跨越 modal 关闭边界，完成后会写入页面状态。请核查关闭是否使该次工作失效，并检查待完成通知和关闭后通知是否都受到约束。证据：对应源码位置。

接收者先核对当前代码与归档快照，再检查关系和保护。复制只生成交接材料；人工意见仍是审查依据，不是 oracle。实验若提供这些意见，应独立记录辅助条件，不混入原有冻结 B–G 材料。

## 论文与工具的衔接

| 用途 | 判定依据与标注范围 |
|---|---|
| case 分组 | 使用研究中既有语义类别，允许一个 case 有多个标签；不由卡片数量或规则命中推导分组 |
| 结果判定 | 按具体义务及可信 oracle 统计通过、违反；待确认不算通过或违反 |
| 结构解释 | 对需要深入分析的子集展开完整 v0.6；未展开的 case 不补默认 E/T/L/H |
| 工程使用 | 默认扫描、查看卡片、确认或排除线索；需要深入测量时才进入高级层 |

减少的是结构标注负担。论文中义务是否合理、oracle 是否正确仍需核查，不能由卡片确认、保护充分性判断或扫描变化替代。

## 高级层的证据边界

1. Analyzer 扫描候选源码，产生位置、语法事实和待核查问题。
2. 对选定的深入分析子集，研究者建立义务，明确 activation、identity、deadline、continuing work 和 forbidden effects。
3. 工具检查证据引用、充分集、时序关系、所有权和 application chain，并据已声明结构推导 E/T/L/H。
4. 行为 witness 单独记录。扫描命中不能替代测试或轨迹，未知也不能当作通过。
5. 两位不同于作者、声明 outcome-blinded、完成全部检查且与推导结果一致的复核者，才能通过高级测量的复核门禁。

任何扫描 finding 或卡片确认都不会自动写入正式义务或标签。正式测量是人工语义声明的机械校验，不是自动契约推断，也不是程序正确性证明。高级层的独立复核门禁不要求每张日常卡片完成。

## 可选高级层：从归档报告建立结构测量

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

这种草稿只把 finding 引用的语法事件复制成 `candidate-syntax-clue` 证据单元，仍然不创建义务、不填写 predicate，也不推导正式标签。网页“边界审查卡”的折叠入口“可选：深入结构测量”中的“建立候选测量草稿”执行同一操作。

空白草稿的 `obligations` 和 `evidence_units` 为空；从 finding 建立的草稿只预填候选语法证据，`obligations` 仍为空。研究者应填写：

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

`workflow_status=draft` 允许逐步保存；`workflow_status=final` 要求每条义务已经人工确认，并完整覆盖所有 condition × obligation 单元。报告库网页的“高级测量 · E/T/L/H”页也可生成、编辑和追加 JSON 草稿。

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

## 高级层的三种证据条件

- **source-only**：只有归档源码；可以建立义务与源码证据，行为见证保持 unknown。
- **test-aware**：witness 通过 `artifact_ids` 引用具体测试命令、输出、断言或轨迹；confirmed/failed witness 必须至少绑定一份 artifact。
- **benchmark compatibility**：只读展示原 MeasurementBench 0.6 结果；完整 Oracle 验证仍由冻结的 Paper 1 工具负责。

冻结实验的 Agent B–G 材料仍只来自候选源码扫描。正式义务、Oracle、行为结果和复核记录不会自动进入实验输入；网页手动复制的卡片材料可能包含人工判断，应单独记录这种辅助条件。

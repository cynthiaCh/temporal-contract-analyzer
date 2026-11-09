# 七类时序义务与经验路由

Web 执行入口现位于 **七类训练与测试**（`/experience`），支持显式发起分析、开发反思、人工审核、回验冻结和经验 A/B 测试，见 [Web v2 流程](EXPERIENCE_WEB_V2.md)。下述纯材料接口继续不直接调用模型，旧实验也不会自动切换。

自 2026-11-09 起，当前工具接口统一采用 `temporal-obligation-taxonomy-7-v1`。它沿用 bench 论文覆盖审计的七类义务，作为分类、经验检索和展示的共同词汇。这里选择的是有既有定义与覆盖记录的工程口径，尚未比较不同分类方案的准确率或修复收益。

## 七类分别问什么

| 标签 | 名称 | 通俗问题 |
|---|---|---|
| R | 就绪条件协调 | 数据、服务或准备条件满足后，才能继续哪一步？ |
| O | 前置顺序与重入一致性 | 哪一步必须先做？同步回调返回时，原状态还有效吗？ |
| B | 提交与完成屏障 | 返回、交接或后续动作之前，哪些工作必须结算完成？ |
| L | 生命周期约束下的接纳与副作用 | 关闭、取消或换主人后，哪些工作还能进入或产生效果？ |
| I | 操作身份与快照绑定 | 这个结果属于入口时的哪次请求、访问或数据快照？ |
| F | 结果新鲜度与版本一致性 | 同一逻辑主人内，较旧的结果能否覆盖较新的结果？ |
| A | 已接纳工作保留与效果次数约束 | 已接纳工作是否必须保留？效果能发生零次、一次还是多次？ |

严格纳入与排除条件以包内 [contract-taxonomy.json](../temporal_contract_analyzer/contract-taxonomy.json) 的 `codebook` 为准，CLI、HTTP 和页面都读取这一份定义。来源文件及 SHA256 记录在 `provenance`，运行时不依赖旁边另一个仓库。

一个案例可有多个标签。比如某工作先等待服务可用、关闭后停止接纳新输入、保留已接纳结果，可分别核查 R、L、A；不能只凭这个描述就给某个真实案例贴标签，仍须当前任务或源码的引用。

三个容易重复计数的边界：

- 监听先注册再启动属于 O，不额外算 R；真正的就绪条件属于 R。
- 返回前必须结算属于 B，普通异步解码本身不算 B。
- 旧 visit 失效属于 L/I；同一保留 owner 内的结果版本竞争才算 F。普通回归测试结果相等不自动算 A。

## 以前的四类和五类放在哪里

| 记录 | 现在的含义 | 处理方式 |
|---|---|---|
| `refine-logs/experience-toolflow-v1-20261108` 的 T1–T4 | 旧版四组机制路由 | 历史保留，不再作为当前分类定义 |
| `repair.py:FAMILIES` 的五组 | 开发侧失败假设提示模板 | 保留提示行为，不能当作隐藏测试输入的分类器 |
| 原题库五条问题 | 五条可检索材料 | 条目数与类别数无须相同，原文不改 |
| D1/D2、Test-1/Test-2 | 开发／测试案例别名 | 不是义务标签，也不是独立来源定义 |

T4 不能直接改名为 L，T3 也不能直接改名为 B。旧分组可能同时涉及多类。重新使用某条旧经验时，另建带引用的七类元数据；不改原正文、冻结摘要、分母或历史分类。页面明确显示“历史四类路由”，不假装原实验已用七类执行。

语言、框架、来源 cluster 和义务分类分开记录。训练／测试的来源隔离不能靠标签不同来证明；同一 cluster 的变体仍须说明历史暴露。

## 新接口怎样走完整流程

1. **开发**：Agent 读取任务、候选源码及可选 AST，提取候选 Contract、七类多标签和机制前提。标准 Contract 留在开发评价侧。
2. **比较与反思**：运行器整理标准要求、实际结果、改善、退步及未知原因，交给反思器修订通用经验。这里没有替换既有反思函数，也没有新增模型调用。
3. **冻结**：经验正文与七类标签、适用／排除条件一起绑定摘要。摘要一致只说明内容未变，不说明规则正确或已获接纳。
4. **测试**：只用当前可见输入提取多标签。先按标签取候选，再核对机制前提、排除条件和语义审查。选零至一条冻结经验；未知、空库或候选冲突回退 AUTO。
5. **交付与评分**：A 为原任务＋同一候选自动 Contract；B 仅追加命中经验正文。工具、模型、effort、预算及评分版本另行冻结。测试期间不改经验，不把标准答案交给维护 Agent。

七类用于组织义务，不代表七条经验已经学好。新接口的机制前提词典沿用现有试验的可见机制，并不声称覆盖七类全部实现。当前 v2 注册表为空，旧经验待逐条重新标注；未投放经验时 A/B 相同，差异不能归因于经验。

实现位于 [taxonomy.py](../temporal_contract_analyzer/taxonomy.py) 与 [experience_routing.py](../temporal_contract_analyzer/experience_routing.py)。这是可运行的离线接口；旧研究运行器仍按冻结版本复现，不会被自动切换。本次未执行新的七类训练／测试，也未把一次 Reflection 改称官方 GEPA。

## 根据分类追加通用提醒

[contract-reminders.json](../temporal_contract_analyzer/contract-reminders.json) 保存一段共同提醒及 `by_label` 下的 R/O/B/L/I/F/A 七段核查问题。名称与类别边界仍从唯一 codebook 读取，不在提醒文件重复定义分类。这是预先编写的初始检查表，不是反思得到的经验，也不含具体案例的标准 Contract。

分类结果为多标签时，按 codebook 顺序追加所有对应提醒，每类一次。未知分类只保留共同提醒与未知说明，不默认追加全部七类。分类应依据当前任务和源码，不能读取测试标准后再选提醒。

`maintenance-prompt` 从已绑定可见引用的分析对象生成“原任务＋候选 Contract＋共同提醒＋命中类别提醒”，不启动维护模型：

```sh
python3 -B -m temporal_contract_analyzer maintenance-prompt analyzed-input.json --output maintenance-prompt.txt
```

比较经验增量时，A/B 必须使用同一自动 Contract、同一组标签与同一版提醒；B 仅追加冻结经验正文。Python 调用为 `maintenance_prompt(task, contract, obligation_labels=codes)` 和 `maintenance_prompt(task, contract, experience_text, obligation_labels=codes)`。提醒版本和摘要可通过 `reminders.material(codes)` 归档。只比较类别提醒本身的效果时，应另立对照，不与经验增量混算。

原有调用若不传 `obligation_labels`，保持此前共同提示正文；旧归档、冻结脚本与历史 E/F 固定提醒不改。新命令及参数是显式接入点，既有服务器运行器需要调用它们才会使用七类提醒，不会自动改写旧实验。

## 离线命令

```sh
python3 -B -m temporal_contract_analyzer taxonomy
python3 -B -m temporal_contract_analyzer taxonomy --format json
python3 -B -m temporal_contract_analyzer taxonomy --format schema
python3 -B -m temporal_contract_analyzer experience-prompt public-input.json --output analysis-prompt.txt
python3 -B -m temporal_contract_analyzer experience-review-template analyzed-input.json --output review.json
python3 -B -m temporal_contract_analyzer route-experience route-input.json --output route.json
```

这些命令只生成材料或计算路由，不调用模型、不读取隐藏评分、不启动实验；输出路径已有文件时拒绝覆盖。

`public-input.json` 仅含 `task`、`sources`（候选内相对路径到源码正文的对象）及可选 `AST`。`experience-prompt` 的输出须与 `taxonomy --format schema` 配套提供给既有结构化输出后端；本接口不替调用者发请求。

模型分析对象必须包含 `taxonomy_version`、`contract`、`obligation_labels`、`facts`、`unknowns`。标签逐条包含 `code`、义务 `statement` 和 `evidence`；机制事实包含 `predicate`、`state` 和 `evidence`。状态为 `known`／`unknown`／`contradicted`。引用为 `{file, line, quote}`，行号从 1 开始，`TASK` 表示原任务；文本必须出现在该行。源码中的现象不自动成为应保留的政策，AST 也不证明完整可达性。

`analyzed-input.json` 仅含 `task`、`sources`、`analysis`。生成的审查模板默认 `approved: null`，审查当前义务方向、前提和未知范围后才填写。`reviewer` 须如实选 `execution_agent_visible_input_only` 或 `human_visible_input_only`，并给 `reason`、当前 `evidence`；AI 自查不算独立人工复核。路由绑定整个输入及 codebook 摘要，任意内容变化后旧审查失效。存在引用不等于语义正确，这一步仍依赖实际审查。

`route-input.json` 仅含 `task`、`sources`、`analysis`、`library` 和可选 `review`。标签未知、审查缺失、适用前提未知、排除条件未被反证、摘要不一致或多个候选未消歧时返回 AUTO 并写明原因；格式不合格的 CLI 输入报错。`primary_class` 等旧字段禁止无声混入新接口。

Python 调用者可用 `freeze_entry(text, obligation_labels, requires, excludes, version)` 生成完整性绑定对象，交给 `route(...)`；它不会批准或写入经验。使用 `maintenance_prompt(task, contract)` 构造 A，使用同一函数仅增加选中条目的 `text` 构造 B。该公共提示模板属于新版本，不能冒充旧实验 prompt 的逐字复现。

当前流程入口为 [v2 METHOD](../refine-logs/experience-toolflow-v2-20261109/METHOD.md)。经验重新标注、语义核查与行为接纳必须分别记录，不能靠修改类别名称跳过。

# temporal-contract-analyzer

`temporal-contract-analyzer` 是一个不执行候选程序、不调用模型的静态时序契约分析器。它从候选源码中提取可追踪、可校验的时序证据，供 Coding Agent、实验运行器和人工审查使用。

当前重点是异步延续、生命周期边界、监听顺序、重入和状态快照等应用层时序关系。规则命中是待核查线索，不是缺陷判决或契约证明。

经验研究的统一主控入口为根目录 [MASTER_PROMPT.md](MASTER_PROMPT.md)。它固定“输出接口 → 经验表示 → 检索投放 → 同类 Prompt 优化”的研究顺序、阶段准入、材料边界和停止规则，供协调 Agent 读取；维护模型只接收对应角色的允许材料。该文件是英文流程规范，尚不代表运行器已自动加载或强制执行，也不会自行启动实验。

当前统一使用 **R / O / B / L / I / F / A 七类时序义务标签**，一个案例可同时涉及多类。分类、经验检索接口及“经验开发”页面共用一个版本化 codebook；过去的 T1–T4 路由分组、五组提示模板与五条题库问题分别保留为历史分组、模板和条目，不再混作当前分类。定义、迁移边界和离线使用方法见[七类分类与经验路由](docs/CONTRACT_TAXONOMY.md)。旧实验保持原样，本次升级不启动模型。

七类通用提醒保存在 `contract-reminders.json`，`maintenance-prompt` 可按当前分析支持的标签生成维护提示，仅追加命中类别的核查问题。固定提醒与学习得到的冻结经验单独保存；比较经验增量时，两组使用相同提醒，经验组再追加经验正文。

源码分析器 0.6.9 增补了三类有范围限制的检查：严格 null 守卫抛错后的回调快照清理顺序；同文件、可识别数组实现的监听注册与退订顺序；最近一次参数缓存中先更新键、再计算结果的异常与重入窗口。默认报告要求对应来源和顺序证据完整，不凭 `off` 或 `memoize` 等名称报警。详见[六案例改进记录](external-tests/six-small-cases-v1/IMPROVEMENTS-0.6.9.md)。本次未重建下述 VSIX 安装包。

## 仓库边界

- Paper 1：继续使用 `temporal-contract-bench` 内置的冻结版本及其原有运行器、归档和结果。
- Paper 2：在本仓库研究分析器本身，包括证据选择、B/C/D 分层、通用审查提示及其对 Agent 行为的影响。
- 本仓库独立演进；Paper 1 的实验来源、运行器、评分器和历史结果仍留在原仓库。
- 分析器实现或规则变化后使用新的实验批次，不混用既有实验输入。

本仓库目前未声明对外发布许可证；在许可证确定前，它是内部研究项目。

## VS Code 插件

日常审查可使用 `vscode-extension/` 中的 **Temporal Contracts** 插件，安装包位于
`dist/temporal-contract-analyzer-0.2.0.vsix`。在 VS Code 扩展面板的 `…` 菜单中选择
**Install from VSIX…** 安装。插件内置当前分析器和 Vue/Babel 依赖，仅需 Python 3.9+。

- 保存 Vue、JS/TS 或 Python 文件后自动扫描，也可手动扫描未保存内容或指定目录。
- 在 Problems 和 Temporal Contracts 侧栏查看信息级提示，点击证据跳到原始源码。
- 源码变化会清除旧定位；最近的完整报告以只读 Markdown 展示。
- 默认将每次结果与实际源码快照归档；用“打开统一报告库”查看历史、核查记录和前后对比。

配置、范围限制、构建与测试方法见 [插件使用说明](vscode-extension/README.md)。
插件复用本仓库的 Python 规则，并保留下面的独立 CLI；不是另写一套检测器。

## 统一报告库、边界审查卡与 Codex

新增可选的 **源码上下文补全**：从归档分析线索自动选取证据位置，沿可识别的词法定义与本地导入补充相关源码，保留来源、预算限制及未解析项。边界卡点击“补充相关源码”，或使用 `reports context REPORT_ID` / MCP `read_context`。实现复用现有 Babel/Vue 解析基础，不依赖外部 helper 路径；仅使用归档快照，不改变冻结实验层。功能、示例和范围见[上下文补全说明](docs/CONTEXT_ENRICHMENT.md)。

CLI、插件与 Codex MCP 共用同一报告目录和报告 ID。本地网页集中查看历史证据、源码快照、人工核查和 Agent 材料交付记录。

配置和使用方法见 [统一报告库使用说明](docs/REPORT_CENTER.md)。

报告库默认使用“边界审查卡”：执行边界在哪里、什么可能已经变化、影响什么效果、仓库要求与保护是什么。工具整理候选位置与引用，人工判断关系是否成立、保护是否充分、还缺什么证据；证据不足保留待确认。修改任务可筛选改动文件及候选直接调用关系涉及的卡片，并查看未覆盖范围，也可复制简短材料交给 Agent。

“高级测量 · E/T/L/H”保留为可选研究入口，连接人工确认的 predicate、证据单元、时序关系、所有权、application chain、行为 witness 与独立复核。扫描命中和卡片确认不会自动成为正式义务、oracle 结果或 E/T/L/H 标签。日常流程与高级测量命令见 [边界审查与高级测量工作台](docs/MEASUREMENT_WORKBENCH.md)。

## Codex 实验页面

新增 **七类训练与测试**（`/experience`）：从 Web 发起候选分析、两次 AUTO、反思、人工审核、开发回验与研究冻结，冻结后可创建独立 A/B 测试批次。输入隔离、改善门槛和运行边界见[Web v2 流程](docs/EXPERIENCE_WEB_V2.md)。历史“经验开发”继续只读。

新增 **经验开发** 归档页：查看开发修复、差异反馈、反思原文、E1/E2 变化、回验与冻结决定。
复现批次与新训练分开，中断步骤保留未启动；页面只读，不调用模型。
从实验工作台侧栏或报告库顶部进入，详见[经验开发展示](docs/EXPERIENCE_DEVELOPMENT.md)。

已评分失败现在可点击 **准备修复对照**：两组从同一已评分补丁继续，一组仅收到当前 D，另一组增加具体失败假设、可反证步骤及调用和状态证据。结果分别展示新增通过项和丢失原通过项；退步候选不接纳、不覆盖父补丁。CLI 使用 `reports repair EXPERIMENT_ID --job j-002` 准备，增加 `--run` 才运行。范围和预算说明见[失败反馈学习 v2](docs/FAILURE_LEARNING.md)。

实验性 **RAG-only** 只交付原任务和从候选快照检索的代码、可见文档，不附加 D 解释或失败反馈。使用本地 BM25 与有限定义/导入展开，可通过批量脚本与历史同补丁对照比较，见[RAG-only 说明](docs/RAG_ONLY.md)。

实验性 **选择性 A/D 门控** 支持先按任务和函数范围内的源码证据决定是否交付 D，否则保持 A。`reports route` 只作判断，`reports selective` 准备单次选择，加 `--run` 才调用模型。当前规则仅是少量探索任务上的候选，不是成功概率预测；回放中的交付减少不等于相同比例的算力节省。见[选择性辅助说明](docs/SELECTIVE_ASSISTANCE.md)。

新增 **失败经验辅助（开发）**：校准后的已评分失败可自动沉淀为候选经验，后续同案例、同输入与任务可显式选用经验驱动的核查问题和源码检索；旧实验可点击“从失败提炼经验”。新条件单独标明反馈已暴露，原 A/D 保持不变。首版是经验记忆与检索策略更新，不会自动发布分析规则。详见[失败反馈学习](docs/FAILURE_LEARNING.md)。

本地报告中心新增 **Codex 实验** 入口。页面沿用 bench 的研究工作台布局：案例目录、运行配置、运行档案和运行中心分开呈现。选择案例后，即可使用本地 Codex 运行无报告／审查报告对照。自动发现已安装的 Codex，沿用本地登录；可使用本地默认模型，也可从本地模型目录选择较早版本。路径和任务自动读取，模型、重复次数与超时在案例配置窗口设置，其余报告条件可展开选择；每次使用独立副本。页面保存回答、事件日志、文件改动和用量；Codex 完成后调用 bench 行为验证，分别展示进程状态与修改成功／失败／尚未验证。

macOS 可双击根目录的 [启动Codex实验工作台.command](启动Codex实验工作台.command)，也可从终端打开：

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports open --experiments
```

如果服务在更新前已经启动，先运行 `reports stop` 再打开。详细流程与范围见 [Codex 实验工作台](docs/CODEX_EXPERIMENTS.md)。

## 环境

- Python 3.9+
- Node.js（分析 JavaScript/TypeScript/Vue 时需要）
- npm 9+（冻结的 lockfile 使用版本 3；系统 npm 6 无法读取）
- 固定解析器依赖：`@babel/parser` 7.29.8、`@vue/compiler-sfc` 3.5.13

安装 JavaScript/TypeScript/Vue 解析器：

```sh
npm ci --prefix tools/temporal-contract-analyzer --ignore-scripts --no-audit --no-fund
```

如果系统仍是 npm 6，可显式使用临时的 npm 9，而不改写 lockfile：

```sh
npx -p npm@9 npm ci --prefix tools/temporal-contract-analyzer \
  --ignore-scripts --no-audit --no-fund
```

仓库检出后可直接通过模块入口运行，无需安装：

```sh
python3 -B -m temporal_contract_analyzer --help
```

若需要命令行入口，可使用 pip 23+ 做可编辑安装：

```sh
python3 -m pip install --upgrade 'pip>=23'
python3 -m pip install -e .
```

安装后可使用 `temporal-contract-analyzer` 命令。当前只保证从源码检出目录直接运行或可编辑安装。固定的 Node 解析器仍采用仓库相对路径，尚未作为可发布 wheel 的运行时资源打包；正式发行设计属于后续工作。

## 使用

扫描候选源码并写入一个全新报告文件：

```sh
python3 -B -m temporal_contract_analyzer scan /path/to/candidate \
  --format json --output /path/to/report.json
```

冻结 B/C/D 及开放式审查条件的完整输入包：

```sh
python3 -B -m temporal_contract_analyzer freeze /path/to/candidate \
  --max-chars 60000 --output /path/to/new-bundle

python3 -B -m temporal_contract_analyzer verify-bundle /path/to/new-bundle \
  --candidate /path/to/candidate
```

工具拒绝覆盖已有输出。报告摘要证明输入和生成物的字节绑定，不证明启发式命中就是缺陷，也不证明分析语义正确。

## Vue 支持（0.5.0）

支持 Vue 2 / Vue 3 单文件组件中的内联 `<script>` 和 `<script setup>`，以及
`lang="ts"`、`lang="jsx"`、`lang="tsx"`。采用与 `temporal-contract-bench`
相同的 SFC 提取方式和固定 Vue 解析器版本，再用 Babel 提取脚本语法事实。
不编译模板、不执行组件，不跟随导入读取扫描范围外的文件，也不加载候选工程的构建配置。

- 所有源码片段、行号与 UTF-16 列号对应原始 `.vue` 文件，保留 CRLF 和 Unicode 位置。
- 普通脚本与 setup 脚本分别使用 `<module>` / `<setup>` 作用域；跨块绑定、组件实例派发和框架调度保持未知。
- 模板表达式、样式、响应式依赖、watch flush 顺序及宏展开不在分析范围内。
  `parsed` 仅表示声明范围内的语法解析完成；纯模板组件没有脚本事件，也不代表安全。
- 外部 `<script src>`、外部模板、非 JS/TS 脚本语言、自定义块及解析错误会使报告成为 `partial`，拒绝冻结实验包并说明原因。
- Vue 报告的 JSON、Markdown、HTML 和 B/C/D/G 层均标明分析范围；解析器元数据记录 Vue 编译器版本与实现摘要。

扫描 Vue 工程的命令与其他源码工程相同。例如，在两个仓库并排检出时：

```sh
python3 -B -m temporal_contract_analyzer scan \
  ../temporal-contract-bench/cases/form-api-registration-vue3/base --format md
```

该命令只读候选源码。本次改动不更新 bench 的实现、冻结输入或历史实验；使用 0.5.0 生成的新输入应单独建立实验批次。

## 证据条件

| 条件 | 内容 |
|---|---|
| A / `none` | 不增加工具材料 |
| B / `locations` | 规则筛选出的源码位置和作用域 |
| C / `facts` | B，加源码片段、语法字段和有限关系 |
| D / `review` | C，加启发式解释、成立条件和核查问题 |
| E / `audit` | 不给项目线索的通用时序审查提示 |
| F / `risk` | E，加“是否检测到时序线索”的粗粒度信号 |
| G / `audit_review` | E，加明确标注为默认不完整的 D 报告 |

B/C/D 来自同一次扫描并共享同一组位置。它们是不同信息干预，不是由弱到强的正确性保证；尤其 D 不是完整检测器或修复方案。

## 测试

```sh
python3 -m unittest discover -s tests
```

`case-clusters/` 和 `templates/` 中只保留了冻结单元测试所需的最小夹具，它们不是独立 benchmark 的案例注册表或 Paper 1 数据副本。

## 尚未迁移的部分

模型调度、案例条件物化、bench Web 页面、评分器、运行档案和 Paper 1 结果仍属于 `temporal-contract-bench`。`temporal_contract_analyzer.experiment` 中与 benchmark 资源统计相关的适配点暂时保留；独立 CLI 的扫描、冻结和校验路径不依赖这些运行器功能。

Paper 1 的 MeasurementBench v0.6 仍是冻结实现。本仓库只提供其已验证报告的只读兼容视图；不会导入 Oracle、运行器或评分器，也不会反向改写 Paper 1 的实验条件。

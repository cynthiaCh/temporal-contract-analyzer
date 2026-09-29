# temporal-contract-analyzer

`temporal-contract-analyzer` 是一个不执行候选程序、不调用模型的静态时序契约分析器。它从候选源码中提取可追踪、可校验的时序证据，供 Coding Agent、实验运行器和人工审查使用。

当前重点是异步延续、生命周期边界、监听顺序、重入和状态快照等应用层时序关系。规则命中是待核查线索，不是缺陷判决或契约证明。

## 仓库边界

- Paper 1：继续使用 `temporal-contract-bench` 内置的冻结版本及其原有运行器、归档和结果。
- Paper 2：在本仓库研究分析器本身，包括证据选择、B/C/D 分层、通用审查提示及其对 Agent 行为的影响。
- 本仓库独立演进；Paper 1 的实验来源、运行器、评分器和历史结果仍留在原仓库。
- 分析器实现或规则变化后使用新的实验批次，不混用既有实验输入。

本仓库目前未声明对外发布许可证；在许可证确定前，它是内部研究项目。

## VS Code 插件

日常审查可使用 `vscode-extension/` 中的 **Temporal Contracts** 插件，安装包位于
`dist/temporal-contract-analyzer-0.1.0.vsix`。在 VS Code 扩展面板的 `…` 菜单中选择
**Install from VSIX…** 安装。插件内置当前分析器和 Vue/Babel 依赖，仅需 Python 3.9+。

- 保存 Vue、JS/TS 或 Python 文件后自动扫描，也可手动扫描未保存内容或指定目录。
- 在 Problems 和 Temporal Contracts 侧栏查看信息级提示，点击证据跳到原始源码。
- 源码变化会清除旧定位；最近的完整报告以只读 Markdown 展示。

配置、范围限制、构建与测试方法见 [插件使用说明](vscode-extension/README.md)。
插件复用本仓库的 Python 规则，并保留下面的独立 CLI；不是另写一套检测器。

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
python3 -m unittest discover -s tests -p 'test_temporal*.py'
python3 -m unittest discover -s tests -p 'test_profile_evidence.py'
```

`case-clusters/` 和 `templates/` 中只保留了冻结单元测试所需的最小夹具，它们不是独立 benchmark 的案例注册表或 Paper 1 数据副本。

## 尚未迁移的部分

模型调度、案例条件物化、Web 页面、评分器、运行档案和 Paper 1 结果仍属于 `temporal-contract-bench`。`temporal_contract_analyzer.experiment` 中与 benchmark 资源统计相关的适配点暂时保留；独立 CLI 的扫描、冻结和校验路径不依赖这些运行器功能。

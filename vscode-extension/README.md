# Temporal Contracts

在 VS Code 中审查 Vue、JavaScript、TypeScript 和 Python 的时序源码线索。

## 安装与日常使用

1. VS Code 扩展面板右上角 `…` → **Install from VSIX… / 从 VSIX 安装…**，选择 `temporal-contract-analyzer-0.2.0.vsix`。
2. 本机需要 **Python 3.9+**。插件自动查找，也可以在设置中搜索 `Temporal Contracts` 并填写 **Python Path**。分析器、Babel 和 Vue 解析器已内置，无需 pip、npm 或单独安装 Node。
3. 打开并信任你的项目，编辑 Vue 文件后保存，即可自动扫描。也可在命令面板执行 **Temporal Contracts: 扫描当前文件**，分析未保存的编辑内容。
4. 在 **Problems / 问题** 或资源管理器的 **Temporal Contracts** 侧栏查看提示。展开提示查看相关证据，点击跳转到源码。悬停提示可查看成立条件和核查问题。
5. 需要包含其他文件时，右键项目目录 → **Temporal Contracts: 扫描目录…**。目录扫描纳入已打开文件的未保存内容；单文件扫描只分析当前文件。

每次扫描会替换编辑器中的上一次提示，并默认将报告和实际源码快照归档。源码修改后，旧定位立即清除；重新保存或手动扫描以更新。侧栏的报告按钮可打开最近一次完整 Markdown 报告，它是只读快照，不会向项目写入文件。历史报告会明确标记为过期。

命令面板中的 **Temporal Contracts: 打开统一报告库** 可查看历史证据、源码快照、人工核查和前后对比；**复制最近报告 ID** 可将同一份报告交给 Codex。CLI、插件和 Codex MCP 使用同一全局配置，完整说明见源码仓库的 `docs/REPORT_CENTER.md`。清除编辑器结果不会删除归档。

支持多根工作区中的单文件和选定目录；远程开发时，Python 需要安装在运行此插件的远程主机。网页版 VS Code 和虚拟文件系统不支持。

## 设置

| 设置 | 默认值 | 说明 |
|---|---|---|
| `temporalContracts.scanOnSave` | `true` | 保存后扫描当前文件；关闭后仅手动扫描 |
| `temporalContracts.pythonPath` | 自动发现 | Python 可执行文件路径，不是 shell 命令 |
| `temporalContracts.archiveEnabled` | `true` | 每次扫描保存报告与源码快照 |
| `temporalContracts.reportStore` | 全局配置 | 统一归档目录；应位于被扫描工程之外 |
| `temporalContracts.timeoutSeconds` | `90` | 分析超时时间 |

`Temporal Contracts: 查看运行日志` 可查看状态和错误；没有弹窗的自动扫描失败也会显示在侧栏和状态栏。

## 结果意味着什么

提示是**需要人工核查的语法线索**，以信息级别显示，不宣称已经发现 bug。无提示不代表安全。解析失败以“分析未完成”显示，不能被误认为零风险。

Vue 2 / Vue 3 的内联 `<script>`、`<script setup>` 支持 JS / TS / JSX / TSX。保持原始 `.vue` 行列定位。模板表达式、响应式依赖、watcher 调度、跨脚本块绑定和组件实例派发仍未建模。外部脚本、自定义块等不支持情况会明确说明。

分析完全在扩展宿主本地进行，不调用模型、不上传源码、不执行项目代码、不安装项目依赖、不提供自动修改。目录扫描沿用分析器的排除规则和大小限制；在 `temporal-contract-bench` 中请选择具体候选工程的 `base/`，不要扫描整个研究仓库。

## 开发与打包

在仓库根目录安装锁定的解析器依赖，再准备插件：

```sh
npm ci --prefix temporal_contract_analyzer/javascript --ignore-scripts --no-audit --no-fund
cd vscode-extension
npm ci --ignore-scripts --no-audit --no-fund
npm run stage
npm test
npm run test:host
npm run test:browser
npm run package
```

构建建议使用 Node 22+；最终用户不需要 Node。`runtime/` 是构建时从本仓库复制的分析器与解析依赖，不应手工修改。Python 分析器仍是规则的唯一实现；VS Code 只负责调用、展示和跳转。

`test:host` 默认使用本机 VS Code（macOS），或通过 `VSCODE_EXECUTABLE_PATH` 指定可执行文件；其他环境由测试工具下载测试宿主。测试使用临时用户数据目录，避免修改你的编辑器设置。

浏览器测试使用本机 Chrome，也可设置 `CHROME_PATH`；测试报告写入临时目录。

输出：`../dist/temporal-contract-analyzer-0.2.0.vsix`。这是供本地使用的私有扩展，目前没有发布到 Marketplace，也没有为项目选择开源许可证。第三方解析器的许可证随依赖保留。

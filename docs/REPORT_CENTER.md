# 统一报告库（Analyzer 0.6 / VS Code 0.2）

独立 CLI、VS Code 和 Codex MCP 共用一个磁盘报告库。每次扫描生成新的报告 ID，网页读取该 ID 对应的结果与源码快照，不会为了展示旧报告重新扫描当前工程。

## 第一次配置

从本仓库运行，使用 Python 3.9+；macOS 本机可使用 `/usr/bin/python3`：

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports init \
  --store "$HOME/.temporal-contract-analyzer/reports" \
  --node /usr/local/bin/node
/usr/bin/python3 -B -m temporal_contract_analyzer reports open
```

`--node` 应填写本机实际安装的 Node 路径。全局配置保存在 `~/.temporal-contract-analyzer/config.json`。报告目录优先级为：命令参数 / 插件设置、`TCA_REPORT_STORE`、全局配置、默认 `~/.temporal-contract-analyzer/reports`。`TCA_CONFIG` 可指定独立配置文件，方便测试隔离。

报告库必须在被扫描工程之外，两者不能互相包含。它保存源码快照，应与研究材料一起管理；目前没有自动清理策略。服务只监听 `127.0.0.1`，无需账户、数据库或外部 CDN。关闭网页不会停止后台服务；再次打开会复用服务，端口可能在重启后改变：

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports open --no-browser
/usr/bin/python3 -B -m temporal_contract_analyzer reports stop
```

更新分析器后可先 `stop` 再 `open`，让网页服务使用新版本。远程开发时，报告库与服务在扩展宿主所在机器；浏览器需要访问该机器转发后的端口，本版未实现自动转发。

## 日常使用

- **VS Code**：保存或手动扫描会默认归档。在命令面板选择 **Temporal Contracts: 打开统一报告库**，或 **复制最近报告 ID**。`archiveEnabled=false` 可关闭归档；`reportStore` 留空即可跟随全局配置。清除编辑器提示不会删除历史报告。
- **网页**：新建扫描、按项目/规则/任务/来源筛选、查看四问边界审查卡及当时源码、分别记录关系判断和保护充分性、补充仓库依据与缺失证据、以当前报告为基线再次扫描并对比提示变化。
- **CLI**：原来的 `scan`、`freeze` 保持原有行为；使用 `reports scan` 才写入统一归档。

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports scan /absolute/path/to/vue-project \
  --project my-app --label before-fix --task-id task-001
/usr/bin/python3 -B -m temporal_contract_analyzer reports list --project my-app
/usr/bin/python3 -B -m temporal_contract_analyzer reports show REPORT_ID
/usr/bin/python3 -B -m temporal_contract_analyzer reports verify REPORT_ID
/usr/bin/python3 -B -m temporal_contract_analyzer reports scan /absolute/path/to/vue-project \
  --label after-fix --parent-report-id BEFORE_ID
/usr/bin/python3 -B -m temporal_contract_analyzer reports compare BEFORE_ID AFTER_ID
```

`REPORT_ID` 等占位符需替换为返回值。同一绝对项目路径与同一扫描范围才能关联或比较；跨工具/解析器版本不满足可比条件时拒绝计算提示变化。`reports scan` 对 partial / empty / failed 返回退出码 2，同时尽可能保留可展示的记录。参数不合法、报告目录不可写、进程被强制终止等情况不保证生成记录。

## 在 VS Code 的 Codex 中使用

Codex 通过本地 MCP 调用同一分析器，不需要操纵另一个插件的界面。以下命令注册服务器，路径需要指向本机检出位置：

```sh
codex mcp add temporal_contracts -- /usr/bin/python3 -I -S -B -X utf8 \
  /absolute/path/to/temporal-contract-analyzer/temporal_contract_analyzer/hub_entry.py \
  reports mcp
```

Codex CLI 与 IDE 扩展使用同一 MCP 配置。注册后重新加载 Codex 会话；必要时重新加载 VS Code 窗口。配置机制见 [Codex 官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。

可直接对 Codex 说：

> 用 temporal_contracts 的 scan_project 扫描当前 Vue 项目的绝对路径，然后用 read_report 读完整报告；有 next_offset 就继续读取。先核查证据，再修改和测试。修复后用相同扫描范围再次扫描，传入修改前的 parent_report_id，比较两份报告，最后给我报告 ID。

也可以从插件复制 ID 后说：

> 用 temporal_contracts 的 read_report 读取报告 REPORT_ID，并通过 read_source 核查其中的源码快照。先确认快照与当前代码的差异，再给出修改建议。

| MCP 工具 | 功能 |
|---|---|
| `scan_project` | 扫描磁盘上的绝对文件/目录路径，归档并返回 ID |
| `list_reports` | 搜索历史记录 |
| `read_report` | 按 ID 分页读取完整报告或冻结层 |
| `read_source` | 按 ID 分页读取当时源码 |
| `read_context` | 从归档线索补充候选定义，分页读取带来源和缺口的独立 JSON 材料 |
| `compare_reports` | 比较同一项目及范围的两次扫描 |

网页新增“源码上下文”标签，边界卡也可直接点击“补充相关源码”。CLI 使用 `reports context REPORT_ID`。详细参数与范围见[上下文补全说明](CONTEXT_ENRICHMENT.md)。受限的冻结层 MCP 会话仍只提供指定层，不暴露此工具。

插件可以保存未保存的编辑器内容；Codex/网页扫描读取磁盘。因此要研究同一份输入，应让 Codex **读取插件给出的报告 ID**，而不是重新扫描并假定内容相同。配置共享 Node 可减少不同入口的解析器运行环境差异。归档和网页本身不调用模型；通过 MCP 返回给 Codex 的材料会进入当前 Codex 会话。

## 研究留痕及边界

每条归档包含 `metadata.json`、`snapshot.json`、成功生成的 `report.json/md/html`、校验清单，以及仅在完整解析时生成的 `bundle/`。保留项目路径、范围、时间、来源、任务 ID、父报告、工具与输入摘要。快照是**纳入分析的源码**，不是整个 Git 仓库、依赖或运行环境备份。

默认入口为“边界审查卡”。改动范围筛选基于显式文件路径或关联基线间的变化文件，并按候选直接调用关系在文件层面扩展；动态调用和完整回调链未覆盖。旧的 E/T/L/H 测量工作台、单题实验与历史浏览入口已移除，当前模块关系见 [ARCHITECTURE.md](ARCHITECTURE.md)。原有外部测量数据不删除，但当前报告接口不再读取、验证或追加它们。

人工意见另存于 `notes/REPORT_ID/`，可标记 confirmed / dismissed / uncertain（成立、排除、待确认）并写说明；网页还记录保护充分性、仓库要求与保护依据、尚缺证据。旧的纯文本记录仍可读取。这些是人工判断，不自动成为实验真值。修改前后提示的增减也不能直接作为修复成功率。

`deliveries/REPORT_ID/` 记录 MCP 分页返回的确切文本、层、摘要、会话和客户端标识。网页的 **Agent 交付** 可查看：

- `prepared_for_tool_response`：已准备返回的材料。
- `transport_written`：服务器已写出该工具响应。

这些记录不能证明客户端已经接收、模型注意到了材料或据此修改代码，也不包含完整对话轨迹。正式实验仍需单独关联任务、模型配置、完整轨迹及测试结果。人工意见和交付记录不改写冻结报告；摘要校验用于发现内容不一致，不提供防篡改签名或正确性证明。

若某次研究会话只应获得一份指定层，可启动受限 MCP：

```sh
/usr/bin/python3 -I -S -B -X utf8 \
  /absolute/path/to/temporal-contract-analyzer/temporal_contract_analyzer/hub_entry.py \
  reports mcp --report-id REPORT_ID --layer facts
```

该服务器只暴露指定报告的指定冻结层，不能列举其他报告、读取源码或切换层。但它不限制 Agent 的其他工具与文件权限，不能单独保证条件隔离，也不替代 bench 的受控实验运行器。正式实验需另行隔离其他材料通道；不要同时启用不受限的服务器。partial / empty / failed 不可作为完整冻结材料交付。

现有 `temporal-contract-bench` 实验、冻结输入、评分器和历史数据均未迁移或改写。本报告库用于工具日常使用及后续研究留痕。

## 验证

```sh
/usr/bin/python3 -B -m unittest discover -s tests
cd vscode-extension
npm run stage
npm test
npm run test:host
npm run test:browser
npm run package
```

浏览器测试用 Playwright 驱动本机 Chrome；非 macOS 可设置 `CHROME_PATH`。全部集成测试使用临时报告库和合成候选源码，不会向正式研究报告库混入测试结果。

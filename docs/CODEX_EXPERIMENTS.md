# Codex 实验工作台

页面用于探索：同一任务下，提供工具报告是否改变 Codex 的分析和修改。参考相邻 bench 的冻结报告层与串行任务运行方式；本功能在 analyzer 中独立实现，不改写 bench 的实验、运行器或历史结果。

## 打开

macOS 可双击仓库根目录的 [启动Codex实验工作台.command](../启动Codex实验工作台.command)。它会复用已运行的服务；发现旧版空闲服务时会更新；旧服务仍有实验运行时会保留运行并提示稍后重试。打开页面不会启动模型。服务在后台运行，关闭启动终端不会停止实验；需要停止时使用 `reports stop`。

需要 Python 3.9+、已安装并登录的 Codex CLI；JS/TS/Vue 扫描还需要 README 中的固定解析器依赖。启动时自动查找 CODEX_BIN、bench 的有效 codex_binary 配置、PATH、Codex.app 和 VS Code/Insiders 扩展中的 Codex；无需重复安装。

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports open --experiments
```

若已有旧服务，先 `reports stop` 再打开。也可在已有报告库顶部点击 **Codex 实验**。停止报告中心会请求取消正在运行的实验。

## 选择并运行

1. 在左侧案例列表选择一个案例，可按名称或语言搜索。
2. 点击 **运行实验**，直接使用已安装的本地 Codex 及其默认模型、推理配置和登录。
3. 页面自动读取 bench 的候选代码和维护任务，冻结报告并启动 Codex；默认比较 A（无报告）和 D（审查报告）。
4. 在右侧查看运行进度、回答、日志和文件改动。历史实验位于左侧折叠区。

无需选择模型或填写路径、提示词。高级设置默认折叠，可修改报告条件、重复次数和超时。一次选择一个案例，运行时允许 Codex 修改独立副本。只打开页面不会调用模型，点击 **运行实验** 会开始实际调用。

案例来自相邻 `temporal-contract-bench/experiments/temporal-diagnostics-v1/corpus.json`；只读导入支持的 legacy-js/Python 案例的 `base/` 和已登记的 latent-maintenance core prompt，授权条件为 ungranted。原始案例、reference、oracle 和研究结果不会复制到候选工作目录。bench 排除的案例不可运行；需要其他适配器的案例标明未接入。已被开发者接触过的案例不因此成为新留出样本。

可以通过环境变量 `TCA_BENCH_ROOT` 指向另一份本地 bench 检出。默认网页调用不传模型或推理强度覆盖，直接由本地 Codex 配置决定；运行记录标明 local_codex 和 config_source。显式传模型的底层 API 继续支持原有对照方式。

本版本采用 **报告全文附加到初始提示词**，不是 MCP 按需拉取。已有 MCP 继续用于日常报告读取。底层离线准备 API 保留，网页采用直接运行流程。

## 保存的材料

实验存放于报告库的相邻目录：例如报告库 `/data/reports` 对应 `/data/reports-experiments`。这是为了使输入快照与报告库分开放置。

- `manifest.json`：任务、模型、强度、条件、顺序、源文件清单、跳过范围、报告 ID、任务状态及局限。
- `input/`：一次捕获的共同输入。
- `jobs/j-NNN/`：`prompt.md`、`report.md`、独立 `workspace/`、`events.jsonl`、`stderr.log`、`answer.md`、`changes.json`、`result.json`。

页面对大日志显示末尾 100000 字节；完整文件保存在磁盘。文本 diff 每文件最多展示 100000 字符；完整修改在 workspace 中。用量只展示 CLI 的 `turn.completed` 实际返回字段，缺失则留空，不根据字符数估算 token。

## 结果的含义

`completed` 表示 CLI 退出 0 且观察到 `turn.completed`，不表示修复通过、契约成立或模型使用了报告。`stdin_file_attached` 只表示提示词文件关联至该进程的标准输入，不证明模型阅读或采纳。任务成功始终 `unscored`。

超时、CLI 错误、取消分别保留；未启动的任务不会伪装为已运行。重启服务在没有其他持锁运行器时将残留 running 记录标为 interrupted，不自动续跑。

## 输入与实验范围

- 捕获普通非隐藏文件，包括候选目录内的 README 和测试；排除 node_modules、vendor、build、dist、coverage、__pycache__ 和隐藏目录／文件。上限 1000 个文件、合计 25 MiB，符号链接拒绝。跳过内容列入记录。
- 保存文件字节及可执行位（规范为 0644/0755），不复制所有权、时间戳或空目录；启动时记录实际本机 Codex CLI 版本。
- 不自动安装依赖。对于依赖原项目环境的任务，需要另行设计环境准备；此版适合自包含候选代码。完整扫描失败会阻止准备所有条件，不将失败扫描当成无风险。
- Codex 采用新的 ephemeral 调用。网页默认继承用户本地 config（含模型、服务商及 MCP 配置），不传模型和强度覆盖；工作目录与 workspace-write 明确指定，execpolicy rules 不加载，审批为 never。显式模型 API 运行继续使用 ignore-user-config。登录由本机 Codex 负责，不复制或显示凭据。继承配置意味着不同实验可能受到本地工具或配置变化影响，记录不等同于完整环境冻结。
- 工作目录副本、独立进程和提示词约束不提供严格的文件读取隔离。此页不构成正式盲测或条件隔离；需要测因果收益时，应额外隔离工具与文件访问、控制环境、随机化顺序并设计独立 oracle。
- 不自动运行评分器、不加载隐藏测试，也不把提示数量的变化视作修复成功。现有行为探针尚未接入此页。

## 验证

```sh
/usr/bin/python3 -B -m unittest discover -s tests -p test_experiment_workbench.py
node vscode-extension/test/experiment-browser.cjs
```

这两个检查明确使用模拟 CLI 和合成源码，不调用模型；所得数字不属于研究实验结果。

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
2. 选择模型，可保留 **本地 Codex 默认配置**，或选择本地目录列出的较早模型，然后点击 **运行实验**。仍使用已安装的本地 Codex 与登录。
3. 页面自动读取 bench 的候选代码和维护任务，冻结报告并启动 Codex；默认比较 A（无报告）和 D（审查报告）。
4. Codex 结束后自动调用该案例的 bench 行为验证器，右侧显示修改结果：成功、失败或尚未验证。可以展开行为验证与日志查看依据。历史实验位于左侧折叠区，旧记录可点击「验证修改结果」补测。

无需填写路径、提示词。模型下拉框将本地 Codex 模型缓存中的较早 GPT-5 版本优先列出；隐藏的内部模型不展示，不硬编码退役模型。缓存目录不是实际调用的账号可用性验证。高级设置默认折叠，可修改报告条件、重复次数和超时；选择具体模型后还可选择它声明支持的推理强度，默认 medium（如支持）。一次选择一个案例，运行时允许 Codex 修改独立副本。只打开页面不会调用模型，点击 **运行实验** 会开始实际调用。

案例来自相邻 `temporal-contract-bench/experiments/temporal-diagnostics-v1/corpus.json`；只读导入支持的 legacy-js/Python 案例的 `base/` 和已登记的 latent-maintenance core prompt，授权条件为 ungranted。原始案例、reference、oracle 和研究结果不会复制到候选工作目录。bench 排除的案例不可运行；需要其他适配器的案例标明未接入。已被开发者接触过的案例不因此成为新留出样本。

可以通过环境变量 `TCA_BENCH_ROOT` 指向另一份本地 bench 检出。选择本地默认时不传模型或推理强度覆盖；选择具体模型时传入模型 ID 和支持的强度，仍继承本地配置。记录包含 model、effort、model_override 及模型缓存来源/时间。显式模型的旧 API 继续保留原有对照方式。

本版本采用 **报告全文附加到初始提示词**，不是 MCP 按需拉取。已有 MCP 继续用于日常报告读取。底层离线准备 API 保留，网页采用直接运行流程。

## 保存的材料

实验存放于报告库的相邻目录：例如报告库 `/data/reports` 对应 `/data/reports-experiments`。这是为了使输入快照与报告库分开放置。

- `manifest.json`：任务、模型、强度、条件、顺序、源文件清单、跳过范围、报告 ID、任务状态及局限。
- `input/`：一次捕获的共同输入。
- `jobs/j-NNN/`：`prompt.md`、`report.md`、独立 `workspace/`、`events.jsonl`、`stderr.log`、`answer.md`、`changes.json`、`result.json`。

页面对大日志显示末尾 100000 字节；完整文件保存在磁盘。文本 diff 每文件最多展示 100000 字符；完整修改在 workspace 中。用量只展示 CLI 的 `turn.completed` 实际返回字段，缺失则留空，不根据字符数估算 token。

## 结果的含义

进程状态 `completed` 表示 CLI 退出 0 且观察到 `turn.completed`。修改是否成功由另外的行为验证决定：

- **成功 / passed**：bench oracle 返回 PASS，且退出码为 0。
- **失败 / failed**：bench oracle 返回 UNDERREACH、OVERREACH 或两者组合，且退出码为 1。报告保留缺失效果与禁止效果。
- **尚未验证 / unverified**：尚未评分、Codex 未正常完成、运行环境不满足要求、参考修复验证失败、验证协议异常或验证超时。不会把这些情况当成成功或语义失败。

验证使用与案例匹配的本地运行时，先将 base 与 bounded reference 合并，确认参考修复在同一环境通过，再验证保存的修改副本。JS 保持该次运行的 ungranted 授权条件；Python 使用已有 probe 协议。通过表示满足所选检查，不证明任意执行顺序都正确，也不证明 Codex 理解或采用了报告。

`evaluations/v-*/` 追加保存验证时间、当前 bench manifest/oracle 摘要、运行时版本、参考校准、候选副本及其文件清单、完整 stdout/stderr。旧实验的原始 manifest、result.json 和 Agent 材料保持原样；API/网页根据最新评估展示派生的 task_success，同时保留 recorded_task_success。旧记录补测使用当前可信 bench oracle，不宣称这个 oracle 在旧实验开始前已冻结。

超时、CLI 错误、取消分别保留；未启动的任务不会伪装为已运行。重启服务在没有其他持锁运行器时将残留 running 记录标为 interrupted，不自动续跑。

## 输入与实验范围

- 捕获普通非隐藏文件，包括候选目录内的 README 和测试；排除 node_modules、vendor、build、dist、coverage、__pycache__ 和隐藏目录／文件。上限 1000 个文件、合计 25 MiB，符号链接拒绝。跳过内容列入记录。
- 保存文件字节及可执行位（规范为 0644/0755），不复制所有权、时间戳或空目录；启动时记录实际本机 Codex CLI 版本。
- 不自动安装依赖。对于依赖原项目环境的任务，需要另行设计环境准备；此版适合自包含候选代码。完整扫描失败会阻止准备所有条件，不将失败扫描当成无风险。
- Codex 采用新的 ephemeral 调用。网页继承用户本地 config（含服务商及 MCP 配置）；本地默认不传模型和强度覆盖，模型选择则显式覆盖这两项；工作目录与 workspace-write 明确指定，execpolicy rules 不加载，审批为 never。显式模型 API 运行继续使用 ignore-user-config。登录由本机 Codex 负责，不复制或显示凭据。继承配置意味着不同实验可能受到本地工具或配置变化影响，记录不等同于完整环境冻结。
- 工作目录副本、独立进程和提示词约束不提供严格的文件读取隔离。此页不构成正式盲测或条件隔离；需要测因果收益时，应额外隔离工具与文件访问、控制环境、随机化顺序并设计独立 oracle。
- 行为验证器只在 Codex 结束后由服务运行，oracle/reference 不进入 Agent 工作目录或提示词。提示数量变化不作为修复成功标准。独立 behavior-probe 原型尚未接入此页。

## 验证

```sh
/usr/bin/python3 -B -m unittest discover -s tests -p test_experiment_workbench.py
node vscode-extension/test/experiment-browser.cjs
```

这两个检查明确使用模拟 CLI 和合成源码，不调用模型；所得数字不属于研究实验结果。

模型选择机制参考 [OpenAI 官方 Codex 模型文档](https://learn.chatgpt.com/docs/models)。建议固定案例集，分别报告较早模型和较强模型的结果，不能只凭较早模型上的收益推断普遍有效。

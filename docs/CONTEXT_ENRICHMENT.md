# 分析线索驱动的源码上下文补全

第一版已经接通：**归档分析线索 → 定义补全 → Agent 核查材料**。

它复用 `rag-context-helper` 的输入位置、依赖展开、深度/预算和来源记录思路，使用本仓库已安装的 Babel/Vue 解析器重新实现定义定位，不依赖外部工具的安装路径。上下文是独立材料，不改变扫描报告或冻结 B/C/D 等实验层。

## 网页使用

更新后重启本地报告中心：

以下命令从本仓库源码运行。现有 VSIX 尚未重建；扩展的 runtime 打包脚本已纳入新解析入口，后续重新构建安装包时会带上上下文功能。

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports stop
/usr/bin/python3 -B -m temporal_contract_analyzer reports open
```

新建项目扫描，选择报告。在边界审查卡点击 **补充相关源码**，或打开 **源码上下文** 标签。选择单条/全部线索、展开深度、代码字符预算和可选路径别名。页面列出原始证据、补充定义、来源原因及未解析项，可跳转到归档源码或复制完整材料交给 Agent。

网页生成材料不会调用模型，不等于已经向 Agent 发送；MCP 交付另有交付记录。

## CLI

先扫描并归档同一份源码：

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports scan \
  examples/context-enrichment --project context-demo
```

将返回的报告 ID 替换下方 `REPORT_ID`：

```sh
/usr/bin/python3 -B -m temporal_contract_analyzer reports context REPORT_ID \
  --depth 2 --max-chars 12000 --format md
```

可选参数：

- `--finding-id FINDING_ID`：只使用指定线索的证据位置；默认全部。
- `--aliases '{"@":"src","Constants":"src/constants"}'`：显式路径别名，以快照根为基准；最长前缀匹配。不加载 tsconfig、Webpack、Vite 等配置。
- `--depth 0..5`：默认 1；0 保留原始证据，遇到未展开的可识别依赖会记录深度缺口。
- `--max-chars 1..100000`：默认 12000；只计源码正文的 Unicode 字符，不是 token 预算，也不包含说明文字。
- `--format json|md`：默认 JSON。
- `--output /outside/project/context.md`：写入新文件，拒绝覆盖和写入原候选工程。
- `--store PATH`、`--node PATH`：沿用现有配置机制。

种子代码超预算时会明确失败，可选单条线索或增加预算；补充定义超预算时整段省略，并在未解析项记录。相邻/重叠片段合并，代码不重复计费。没有 finding 时返回空上下文，不自动搜索全仓库。

## MCP

正常 MCP 会话新增 `read_context`：

```json
{
  "report_id": "REPORT_ID",
  "finding_id": "FINDING_ID",
  "depth": 2,
  "max_chars": 12000,
  "aliases": {"@": "src"},
  "offset": 0,
  "limit": 12000
}
```

仅 `report_id` 必填。`text` 是上下文 JSON 的一页，必须沿 `next_offset` 读完，再解析整份 JSON。后续页需保持报告、线索、深度、预算和别名参数相同。返回沿用报告/源码的交付记录与传输回执；记录不证明模型注意到或使用材料。当前会话缓存最近四组生成参数，避免每页重新解析源码。

给 Agent 的示例指令：

> 扫描项目后，先 read_report 阅读报告，再用 read_context 获取相关线索的补充源码，沿 next_offset 读完。结合 reasons 与 unresolved 核查关系和保护，验证快照与工作区差异，再考虑修改和测试。

受限实验会话 `reports mcp --report-id ... --layer ...` 仍只暴露指定层的 `read_report`，不提供上下文或额外源码。

## 技术与支持范围

- 从 finding 的 evidence ID 定位报告事件，取原始源码行作为种子；不会自动扩展到完整所在函数。
- 单独的 `context.cjs` 用现有 `@babel/parser` 解析 JS/TS、用 `@vue/compiler-sfc` 提取内联脚本，输出词法绑定、引用位置和有限导出定义。原扫描器的 AST 输出保持原样。
- 对可识别的函数/块/循环/catch 作用域处理参数与声明遮蔽，忽略普通属性名、注释、字符串及类型引用。它仍不是完整 JS/TS 语义解析器。
- 支持同文件词法定义、静态本地命名/默认导入、函数/变量/类声明、有限导出列表；只在归档清单内解析模块。
- 按确定性的广度优先顺序展开。扩展名省略时若多个候选同时存在，报告 `ambiguous-module`，不猜测工程的真实解析配置。
- Python 等语言保留原始证据，并记录不支持定义补全；无法启动解析器时仍返回种子与解析器缺口。
- namespace import、转导出、CommonJS/动态导入等关系不会展开；可识别到时记录缺口。Vue 模板、跨脚本块绑定和框架调度不建模。
- 不推断对象成员派发、运行时重赋值、完整调用方、控制流、数据流或状态写入集合。不识别的全局名称不逐个报警；空 `unresolved` 不代表依赖完整。

## 输出与解释

`temporal-context-1` 包含：`report_id`、`input_sha256`、`scan_status`、`finding_ids`、`aliases`、`parser`、`generator`、`limits`、`snippets`、`unresolved`、`usage`、`qualification` 和 `limitations`。

`snippets` 给出 `file/start_line/end_line/code/kind/reasons`。`kind=seed` 表示合并后的范围包含原始证据；同一片段也可以包含补充定义。`usage.seeds` 是含种子的合并片段数；`usage.definitions` 是有定义关系依据的片段数，包含已在种子内的定义，不是符号数或检索成功率。

上下文仅来自已校验的扫描快照（包括归档的编辑器 overlay），不读取当前项目文件。不在快照中的依赖保留缺口；单文件扫描不会自动读取邻接模块，需另建包含依赖目录的报告。上下文生成器版本与摘要独立记录；更换生成器或选项意味着新的上下文条件。

测试验证功能路径、快照隔离、词法遮蔽、预算和交付行为，尚未证明检索质量或 Agent 修复效果。

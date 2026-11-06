# 核查记录

所有正式调用前，PLAN.md、候选11文件、公共材料、A/B/C完整prompt、配置、种子与9槽位调度均已冻结。首次离线核查通过后发现保护清单包含大量无关忽略依赖；在零模型调用时缩小保护清单到7228份文件，保留所有已跟踪文件、三个既有未跟踪实验、选定bench案例和冻结材料。离线检查重新全部通过，详见 offline-inventory-revision.json、preflight.json。该修订仅改变保护元数据和相应脚本，不改变任何条件输入、执行环境或评分标准。

- A 与最近 prompt-evolution 开发P0归档实际prompt逐字节一致；原任务、RAG、五题及三阶段记录限制保留。
- 11份输入文件与原候选/历史manifest的路径、内容摘要一致。每个运行从相同未修补输入开始。
- B 是冻结候选源码的逐行编号摘录。材料逐项可见性及研究者选择原因在 materials/visibility.json，研究侧原因和历史索引未挂载给执行者。
- B = A + evidence；C = B + question。证据字节、顺序、格式一致，新增包共同上限6500字符/2200代理token，无等长填充。
- 问题引用可见函数调用顺序和原任务保留行为，询问关系，不声明未知义务或给出修复方案；源码摘录没有研究侧解释。
- 新增提示无条件标签、隐藏检查名、评分器、历史成绩或参考答案。隔离中只有该次候选、输出和stage可写；原仓库、研究侧和其他运行均不可见。
- 完整CLI宿主及helper可执行，合成候选写入和node语法检查通过，stage不混入候选，/proc无法绕过隔离读取研究目录。
- 现有评分器离线原样UNDERREACH、参考PASS；每个正式可信评分还自带参考校准。参考和评分器始终位于Agent隔离之外。
- 每次实际prompt、完整CLI事件/工具输出、patch/changes、answer、manifest/用量、原始评分均由现有Workbench归档。没有补跑/搜索/优化模型或Agent委派。

原样候选已有通过的检查与逐场景断言都独立比较；同时单列历史P0及配对条件的已通过项丢失，避免用检查项总分抵消退步。完整自动对账见 audit.json、summary.json、EVIDENCE.md；逐运行语义复核见 process-review.json。

运行环境沿用前轮：默认候选 shell 的 node 为系统Node v22，而可信评分固定Node v16.20.2；隔离同时提供 /runtime/node16。这个既有环境差异没有在本轮改动；候选node检查通过不等于在评分版本验证过。原始工具退出码保留：快照无.git导致git diff失败、自建测试断言失败、rg匹配不存在test*退出非零，均与正式执行异常分开，不静默认作成功。

公开静态 o200k_base ranks 从 https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken 保存并冻结；run.py使用已有regex与标准库BPE计数，无新安装依赖。其token仅为可复核代理长度；未宣称为gpt-6-sol未公开的精确编码。真实累计用量直接来自CLI，包括缓存与重复上下文，未换算金额。

根及祖先路径无AGENTS.md，仓库rg扫描也未找到AGENTS.md。初始已跟踪diff为空，既有三个未跟踪研究目录保留；结束时再验证冻结摘要、HEAD与diff。没有提交、生产改动、题库改动、AST改动或评分标准变更。

汇总阶段曾因patch元数据与人工注释字段重名导致报告渲染TypeError；改为patch_path后仅重跑无模型报告渲染。正式运行、原始评分和冻结输入均不受影响，见postprocessing-issues.json。

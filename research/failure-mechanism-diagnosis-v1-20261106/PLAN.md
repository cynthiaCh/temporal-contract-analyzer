# 冻结计划：小型失败机制诊断

2026-11-06；在本轮任何模型结果出现前冻结。一个案例×A/B/C×三次，共9次正式 CLI Agent 调用；无预跑、搜索模型、优化器、补跑、架构/题库演化。每次 CLI 内工具循环不是另一个正式调用。

## Task 1：选择、已知事实及假设

案例 transfer-progress-composition-v4-vanilla。这是 authored development / 研究者已暴露的开发诊断案例；独立泛化案例0。选择理由是最近两轮已归档、校准有效的重复行为失败，非服务容量、工具宿主或评分基础设施异常。优先使用现存重复证据，不搜索新案例。

历史 staged-ReAct A/B 两次共4个有效结果均未通过整体，start-switch-admission 均失败；最近 prompt-evolution 的 P0/P1/P2 亦均失败（8/10、8/10、9/10）。本轮 A 精确重放最近 P0 的完整提示词、公共材料、配置和未修补候选，不接续历史补丁。

原任务：恢复 warm source 的初始进度；防止异步完整帧逆序回退显示；保留 transfer/retry/navigation/cleanup/audit/queue、普通流、telemetry 和后续使用。可见 README 定义 visit 与 attempt 区分、共享 feed、同步 start、异步 decode、记录与显示的消费者。完整原任务见 materials/task.md。

失败行为：初始进度/逆序修复后，某些启动期间先发生导航的路径与 retry 归属仍不满足原有行为。研究侧检查名只用于结果索引，不交付候选。

最近 P0 实读：events 7 README、11 progress-source、13 progress、15 telemetry、17 panel、20 queue、21 transfer；23 全局 rg。公共 RAG 已包含除 transfer/notice 外的大多数相关实现。P0 只修改 progress.js：监听提前、到达序号与显示水位、start 异常清理；未新增事件接纳有效性或当前 attempt 判断。事件30 smoke通过；32验证 showProgress 中切换通过；35 git diff 失败（快照无.git），不能当验证成功。

与失败相关的候选事实：progress-source 的 initialPacket 函数在 dispatch 前运行；panel 导航先清 current 再取消；transfer 在 watch 返回后才获得 stopProgress 并处理已 abort；queue 将 history 与当前 visit 的显示分开；retry 保持 visit 替换 attempt。这些事实多数已读，尚不能断言是信息缺失。可能是关系/事件顺序理解不足、补丁未落实，或验证选错了顺序。不会根据模型自述分类。

B 是人工按已知失败定向挑选的源码摘录，不代表自动检索能力。本轮增补也可能仅引起重复阅读或注意变化。C 问题是待判断关系，不预定隐藏义务。B/C 无效也是完整结果。

## Task 2：条件与冻结控制

A：最近可信 prompt-evolution P0 原始实际 prompt 逐字节，公共源码 RAG、固定五题、三阶段 workflow 及原记录限制均保留。
B：A 后附候选可见的精确路径/行号源码片段。只给源码，无原因、方案或核查问题。
C：B 后只增加一个问题；B 源码包字节、顺序和格式完全一致。两组新增包统一上限6500 Unicode字符、2200 o200k_base token，不填充。记录实际字符、UTF-8字节与 token；本地 o200k_base 是公开代理计数，不能假称未公开模型精确编码。真实模型累计输入/输出另取 CLI usage。

gpt-6-sol / low，workspace-write，approval never，600秒，原 CLI 输出设置，无新增输出 token 硬上限；同一已验证 bubblewrap 隔离/CLI helper、Node工具与可信评分器。每运行独立冻结 input/workspace、profile、output、stage；研究目录、隐藏评分器、参考修复、历史结果和条件标签均不可见。模型不能看到其他条件结果。种子2026110602只控制调度，模型无采样种子；按rep配对，每个rep随机排列A/B/C，串行交错。冻结后不按结果调整材料、案例、顺序或配置。

每次正式 launch 前记账；执行失败单列，不补跑。归档实际prompt、完整events/tool输出、changes/diff、answer、usage、运行配置与可信评分。研究侧评分在候选隔离外，参考校准不交付候选。离线只做非模型隔离/工具宿主/写读检查、原样/参考校准、字节/泄漏核对。

## Task 3：预定分析

主要指标为可信整体行为通过，逐项原通过项丢失和禁止效果，目标 start期间切换接纳行为，retry另列；不以总分抵消退步。报告token、缓存、壁钟、工具调用，执行和验证异常。

先可信评分，再人工研究侧复核实际读取、事件顺序、业务要求/源码事实/假设、不同副作用有效性、补丁落实与候选验证覆盖。模型的“已检查”不算证据。逐rep记录稳定性，A/B、B/C检查得失分别列出。

B改善只支持定向证据可能有帮助；C增益只支持具体问题可能有帮助；均无改善则继续区分理解/实施/验证；A全过则原失败未复现。任何退步单列。一个已暴露案例每组三次仅描述，不推断因果、显著性或独立泛化。下一步建议依据实际行为及轨迹决定，默认不扩大。

## 仓库保护

根与祖先无 AGENTS.md；仓库内扫描亦无 AGENTS.md。起始已跟踪 diff 为空，三个既有未跟踪研究目录保留。原生产代码、AST、题库、评分标准与全部历史档案字节哈希保护。新增内容全部在本目录，不创建提交、不引入依赖。

# U1技能开发集内补丁效果实验：执行前冻结

待检验假设：先前未盲化代理审查观察到的F1动作设计增量可能帮助U1目标修复，也可能无效或引起退步。独立人工复核尚未完成，风险核查不等于复核通过。本案已反复研究暴露；不作独立泛化、因果证明、显著性或稳定有效结论。

## 固定材料与候选

只用transfer-progress-composition-v4-vanilla，原执行job e-5b07bf1156dc48d0的准确task、input和完整common。起点为该job的冻结input（原未修复候选），不是它的9/10历史补丁；与原failure诊断案例的源摘要相同。原维护目标为恢复warm初始进度，并保留transfer/retry/navigation/cleanup/audit/queue、流式、telemetry及反序完整帧不回滚。公共源码RAG/固定五题逐字节复用原官方实验common，不重检索；原执行未交AST，本轮也不加。不会额外提供上轮反馈、评分、轨迹、代理review、说明notes或evidence-key给执行Agent。

K=U1原父K0；F0/F1各取U1本条件**首次生成**，由条件映射sequence最小选取：F0 C8ec8c3ddfc/r03；F1 C4509bd4e1d/r04。仅skill原文，无拼接、修订、按评价筛选或换候选。候选与父版本SHA/字符数和来源记录在candidate-sources.json。风险见RISK_REVIEW.md；无已确认阻断项才运行，否则停止不换人选。特别保留F1排序语句风险。

完整prompt使用原公式：common + BASE + temporal-contract-skill + END。三组只有技能块不同；K完整prompt须与历史job逐字节相同。公共prefix/suffix、任务/源/配置/输入文件摘要见input-control.json；三份完整prompt在根目录。六份独立input和prompt在trials目录。

## 执行与预算

固定gpt-6-sol/low，600秒/会话，workspace-write、approval never，原始自主Codex CLI/IsolatedWorkbench路径、bubblewrap隔离与原输出限制（无新增显式token cap），Node可见系统版本和可信评分Node沿用历史。工具权限及启动环境保持一致，不接入ReAct外层、Stop续行或证据状态机。

三个条件各两次，最多6次正式维护CLI；不预跑模型、不反思、不生成技能、不GEPA、不重试/补跑。每次新工作区从同一input开始，研究目录/隐藏评分/参考修复/其他job不挂载。请求记账使用原Pre/PostModelRequest hook；本目录仅增加阻止传输失败后自动重试的计量守卫，不读取工具输出、不控制行动或任务结束。正常自主工具循环可有多次底层请求，不把会话数冒充请求数。失败/超时消耗槽位且单列，后续仍按冻结顺序运行，除非隔离或输入摘要被破坏则停止全部剩余槽位。不根据结果调整候选、工具或限制。

调度种子2026110607，先对K/F0/F1随机排列，第二重复反转，同一重复配对交错；完整顺序与job ID见schedule.json。该种子不是模型采样种子。六次结束之后才汇总比较，不看中途分数来改变实施。

## 离线与评分

正式前核查输入/准确原任务、K prompt历史同字节、其余仅skill变化、风险边界、code-mode host存在、namespace隔离、无模型假事件的请求计数和重试拦截。复用既有unchanged可信评分作同冻结起点比较，不另立评分规则；原WorkBench在每次正常结束后使用同一可信评分流程，隔离于执行Agent，并做原参考校准。评分器/原题库/参考均不改。

主要指标独立记录：整体PASS、目标start-switch新输入关系、交付、全部原有检查与断言得失。参照对象明确分三层：
1. 同冻结起点unchanged原始评分：原通过checks/assertions哪些丢失/哪些未发出；
2. 同重复K：F0/F1 checks和assertions的gained/lost/not-emitted；
3. 历史K0 e-5b07bf1156dc48d0的9/10结果仅作已知失败/保留锚点，额外报告得失，不混称本轮起点或配对K。

未知/未发出不当通过。不得用局部总分抵消退步或整体失败。执行异常/评分异常与行为失败分开。每次保存prompt、原始事件/工具输出、patch、changes、评分/校准、CLI用量与底层请求账本。统计输入/输出/缓存、时间、工具数、CLI与native数，说明账本与turn汇总是否一致。

## 机制与停止

六次完成后依据实际代码/工具输出及patch逐项核查：新输入接纳vs已接纳完成；源码依据；技能要求动作是否在轨迹发生；判断是否落实补丁；是否压掉合法迟到工作；排序/串行化/取消范围；验证有无驱动目标startup导航+新输入与已接纳完成的对照路径。模型自述只作声明，不能证明动作；无证据标未知。不会把当前Agent分析叫独立人工复核。

全部输出放本独立目录；不改变生产、题库、技能原件、评分器或历史；不创建提交、不安装依赖。即使F1有收益也只称这个已暴露开发案例中的初步补丁收益；两次不一致完整展示。结束后不选新候选或追加运行。

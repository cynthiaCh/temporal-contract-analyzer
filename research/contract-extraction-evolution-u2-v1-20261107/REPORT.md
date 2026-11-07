# U2 Contract 提取技能实验：执行阻断记录

**本轮没有完成技能自演化比较。**两次 K0 会话均因源码读取工具后端被关闭而失去有效性；已停止反思和 K1，未补跑。此为执行代理的配置错误，不能解释为提取技能缺陷。所有评价为 **AI 辅助评价，非独立人工复核**。

## Task 1：评价补齐与固定范围

只使用已暴露开发案例 U2，原任务及原始候选复制到 [materials](materials/)，逐文件摘要见 [scope-and-sources.json](scope-and-sources.json)。已有用户确认涵盖 S1–S6、R1–R4、A1–A6，保留原未知与版本边界。复用此前 O1–O7 映射，没有重新制作金标准。根目录和祖先未发现适用 AGENTS.md；归档 GEPA 源码中的局部规则不适用。

[evaluation-v1.csv](evaluation-v1.csv)在模型执行前冻结，分别评价覆盖、语义方向、来源准确、无依据新增、未知处理，不计算总分。O1持续检查至ready、O3未ready不交付可按任务规范评价。O2等条目只评价可恢复事实与合理未知，不要求猜中全程loading=true、前台必须取消、唯一generation实现、workspace所有权或授权迁移规格。

O4新增T1–T4：关闭时待执行retry是否存在及所属对象、取消包装及实际调用位置、继续检查的条件、接口／宿主证据缺失。评价要求区分原前台尚未接入retry与相邻后台已有调度路径；不预判必须取消或代码有错。版本和规则摘要冻结于 [protocol.json](protocol.json)。

验证：零模型检查通过候选只读、研究档案不挂载、命令约束、请求硬上限及反思无工具限制。但它**漏检了CLI实际读取工具所依赖的宿主**；因此不能把该检查通过说成执行环境完整可用。

## Task 2：模型输出与技能变化

[contract_extraction_K0.md](contract_extraction_K0.md)为本轮独立通用提取技能，不含U2七条答案，与旧代码分析K0不同。执行固定gpt-6-sol／low，每会话600秒，提取每槽最多12底层请求、反思最多1次，总上限49，最多5顶层会话，未进行模型预跑或自动重试。

两次K0的传输和JSON格式均完成，但事件记录明确报：`Code Mode is unavailable because code-mode host is disabled`。冻结runner误禁用`code_mode_host`，两份报告也明确承认未读取源码。候选虽然可见且只读，工具实际不可执行；这两槽记为基础设施失败，不作为有效基线。原始receipt的传输状态保留，另存validity.json说明实验有效性，未覆盖原记录。

- [K0-1输出](runs/k0-1/contract.md)：恢复“pending继续检查、仅ready后交付”，并说明“未读取到候选源码或文档”。
- [K0-2输出](runs/k0-2/contract.md)：同样恢复上述任务义务，说明“候选源码和文档未被读取”。
- 逐项记录见 [baseline-review.csv](baseline-review.csv)（14行）及 [timer-boundary-review.csv](timer-boundary-review.csv)（8行）。没有源码依据的阶段关系无法评价；不把缺少timer描述归因于模型理解。

没有建立可信的技能缺口反馈，因此未调用反思、未生成K1、未手工修补候选，也未运行K1两槽。[difference-feedback.json](difference-feedback.json)记录为何不发送反思；[skill-changes.json](skill-changes.json)明确变化为空；skill.diff仅为“未生成”说明，不冒充真实差异。剩余三个槽位的slot.json保存NOT_RUN和null实际输入输出，不伪造归档。

## Task 3：改善、成本与限制

**模型原先漏了什么？**两份输出都正确恢复了任务直接给出的O1/O3。其余源码关系未恢复，但原因是读取工具失败，无法判定技能本来会漏什么。未发现把当前实现冒充要求或编造具体状态协议的输出。

**一次反馈更新后补上了吗？**无法判断，反思及K1未执行。

**有没有把原来正确的内容改坏？**无法判断，没有前后比较；不能把“没有K1”说成“没有回退”。

[costs.json](costs.json)：实际2个顶层会话、4次底层模型请求，约40.96秒；输入44,495 tokens（其中缓存30,976，已包含在输入中），输出925 tokens（推理49，属于输出子集）。成功工具调用0；两个会话都记录宿主不可用，未暴露到hook的尝试次数无法精确统计。美元价格未核验，成本不编造。其余3会话预算未消耗；无补跑、K2、维护评分、ReAct或官方GEPA。

[summary.json](summary.json)状态为STOPPED_INFRASTRUCTURE_FAILURE。[final-validation.json](final-validation.json)仅证明归档、引用、用量和保护检查通过，不证明实验成功。HEAD、暂存／未暂存diff、已有tracked文件、前轮映射及标准均保持；隔离候选未变，临时认证已移除。不创建提交，不接纳任何生产技能。

本轮停止。后续若另开实验，应先离线验证CLI实际读取工具链，再冻结执行配置；不得把本轮失败槽位改写为有效基线。同一开发案例即使完成回测也不能证明泛化，两次重复不作显著性判断。

建议Git commit subject：`research: record blocked U2 contract extraction pilot`

Body：`Freeze source-scoped contract evaluation with a separate queued-retry boundary. Preserve two infrastructure-invalid baseline slots, native request accounting and unchanged source artifacts. Stop before reflection and K1 without reruns, maintenance scoring or production skill changes.`

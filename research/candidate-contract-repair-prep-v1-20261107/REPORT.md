# 候选 Contract 修复对照：离线补评与准备

**本轮0维护调用、0提取重跑、0评分／校准执行。**关键政策仍待确认，H尚不能形成，未启动N/M先跑。人工Contract的作用本轮不可观察，已有模型Contract是否保留其作用也无法判断。

本次是**AI辅助离线补评与准备，非独立人工复核**。完成日期为2026-11-08（Asia/Shanghai），目录保留创建时的20261107名称。仅新增本目录，不改原标准、技能、8份输出、评分器、业务代码或历史材料，不创建提交。

## Task 1：可评价范围与未决政策

[standard-applicability.json](standard-applicability.json)逐项保留来源和批准状态：

- **C1初始状态：**原任务直接支持面板初始状态应可见；**metrics增量：**任务禁止改metrics，源码注释明确只计增量。这些有项目依据，但C1-Q1仍为待确认，未找到后续批准记录。
- **C3历史与UI：**可见README:3明确入口快照、成功一次审计、失败无成功审计、已接纳提交跨关闭／重开保留、saved/error只归当前visit的最新提交。不是单凭实现猜测，但C3-Q1仍待确认。
- **实现线索：**监听/解码/释放顺序、当前同步done及audit/UI守卫可核对源码事实；它们不自动成为业务政策。
- **额外规格：**历史C1提供的Contract还规定旧visit结果失效等更具体政策，原任务/源码不能唯一确定，不能借评分预期自动批准。C3失败传播、null返回协调、嵌套可变性等未知保持。

复用已有8份原始输出，另存[supplemental-review.csv](supplemental-review.csv)44行补评：核对原句、源码关联及适用范围；事实/关系、引用、无依据新增和未知可评价，已确认义务评分为“不适用：批准列表为空”。保留原评价。两组主要可见条款恢复、K1部分关系补充及C1请求术语限制沿用有源记录；不将关系增多算成Contract增益，也不将未确认项算确定错误。

## Task 2：实际固定的材料与来源匹配

[contract-selection.json](contract-selection.json)固定“实际执行时间最早的K1输出”，不是挑最好或按重复编号排序：C1=s02，C3=s04，二者均是标为重复2的运行。机械提取规则只取准确第1标题之后至第2标题之前的正文，保留全部空白和列表，不从其他栏目补齐。M正文见[contracts/C1/M.md](contracts/C1/M.md)、[contracts/C3/M.md](contracts/C3/M.md)。

完整C1报告已在第2栏目说明metrics增量，而M仅保留第1栏的“不得修改metrics”；C3预览细节也主要在第2栏。未来差异可能来自栏目包装，不能直接归为完整提取报告未理解；概括性的保留约束也可能与细节等价。未人工修正M。

H只有BLOCKED状态记录，没有空白H或冒充人工确认的草稿。N/M准备文本和H不可执行模板保存在[planned-prompts/](planned-prompts/)，M/H采用相同警示与包装：

> 以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

三组都要求实际修改代码完成原维护。共同RAG及其他额外辅助关闭；原候选完整提供。12个研究侧起点副本按例摘要一致，尚未修改或执行。候选、原任务、8个提取工作区、标准冻结副本、原始input归档与当前bench base已逐字对应，见[source-score-bindings.json](source-score-bindings.json)。

**历史与评分：**C1实际历史N／提供Contract配对使用同一base及case manifest，结果UNDERREACH／PASS；这是gpt-5.6-terra/medium的单次旧结果，不能当本轮效果。当前oracle逐文件摘要匹配既有v-5adc5d73fac8467b校准PASS记录，但校准不是政策批准，历史后缀也没有当前人工确认凭据，不能直接作为H。C3原始筛选归档为prepared/not_started；在限定核查的归档/两张历史索引内未定位完整N/H实际配对或可信校准记录。当前suffix不能冒充历史实际输入。未反复扩搜或临时重建案例。

## Task 3：预算、开跑缺口与结论

[PLAN.md](PLAN.md)与[schedule.proposed.json](schedule.proposed.json)保存最多两例×N/M/H×两重复的12槽交错顺序，种子2026110710；当前全部禁用，实际0槽。若后续只有一例满足全部条件，仅按预声明顺序筛为该例6槽，不换题。

研究配置为gpt-6-sol/low、priority；拟沿用600秒、最终report6000字符、每槽12底层请求及全局49请求硬上限。采用原Codex自主exec，不加ReAct。这里只准备配置与独立副本，**没有将旧的提取只读隔离检查冒称为维护可写工作区验证**；启动前还须明确H、补足C3校准来源（若运行C3）、取得精确起点effect向量，并完成维护隔离/运行时/计量的必要离线检查。状态见[configuration-and-isolation-readiness.json](configuration-and-isolation-readiness.json)。不改原可信评分以凑齐实验。

本轮没有补丁、实际维护prompt、轨迹或新评分，相关结果为缺失而非通过。未来仍须分别记录整体/目标行为、起点及配对N的原通过项丢失、实际补丁和成本，不以总分抵消关键退步。两次重复不当独立案例，不由H/M/N相关性推定某条Contract因果作用。

[costs.json](costs.json)中本轮模型请求及token均0，旧8次提取成本单列，不算重跑。[validation.json](validation.json)核验来源、引用、M机械提取、公共包装、候选一致性及已有工作保护；原有cross-case未跟踪目录和bench已有两个改动均保持。

尚需明确的政策仅列[confirmation-needed.json](confirmation-needed.json)中两问，不要求整份标准批准；其他未知不因此升级。结论：[summary.json](summary.json)。**人工Contract作用本轮不可观察；模型Contract是否保住该作用未知。**停止于离线准备，不自动接纳技能或继续调用。

建议Git commit subject：`research: prepare gated candidate contract repair comparison`

Body：`Reuse eight frozen extraction outputs for scoped offline supplementation. Fix mechanical model-Contract selection and paired repair materials while preserving pending policy approvals. Bind source and scoring versions, record missing human Contracts and calibration evidence, and stop with zero maintenance calls.`

# C1/C2/C3 独立代码分析基线

**结论：原始分析K0已能识别三例的主要事实、事件顺序和效果归属。发现局部论证／建议范围问题，尚没有跨两个不同案例、证据充分的重复缺口，不支持立即优化技能。**本轮没有技能演化、GEPA、代码维护或评分。

## Task 1：输入、确认和边界

输入来自 research/code-analysis-standard-cases-v1-20261107 的原task及24份候选文件，与归档manifest逐字／SHA256核对。C1原始代码在注册监听前connect并派发首事件、C2原始edit同步写、C3原始done立即接收commit返回值；不使用历史补丁后的事实。具体来源单元、摘要和暴露记录见[source-verification.json](source-verification.json)。三例已暴露开发来源，C2/C3共享计时／预览模板，不能称独立泛化样本。

原K0准确复用此前analysis_skill_K0.md，SHA256为4a66821d212dd4749db2dce88bf61ba94d0f8369e8045f219064d0afdca72b66；未用K1、未改写技能。公共提示词要求统一六部分，三例只替换原任务，没给标准考点。报告上限6000 Unicode字符，全部原样归档，无裁剪。

三份标准仍为草稿：用户已确认标准条目为0，六个确认题全待确认，没有继承U1/U2批准。原task/候选README可被模型引用；研究评价不把未批准业务政策当确定错误。36条分析清单评价与18条待确认政策观察分开，见[confirmation-status.json](confirmation-status.json)、[review.csv](review.csv)。没有适用于当前目录或祖先路径的AGENTS.md；没有采用不相关归档项目的规则。

## Task 2：执行与逐例发现

正式前冻结[PLAN.md](PLAN.md)、protocol、完整prompt、源码摘要和调度。固定gpt-6-sol/low；独立bubblewrap namespace实际只读挂载候选，不挂宿主home／研究仓库。各槽独立profile/output/meter，模型无法读取标准、确认、隐藏评分、参考补丁、历史输出或别槽轨迹。允许只读查看，禁止候选执行；零模型探针验证隔离、计数12次上限、超限kill及重试阻断。原始事件含真实工具输出，各workspace摘要结束后仍相同。

种子2026110708仅决定顺序：C1/1、C2/1、C3/1、C2/2、C3/2、C1/2。六槽全部结束后才评价。完成6/6，失败／超时／超限／格式异常为0，无额外冒烟、反思、补跑或judge。

| 槽位 | 案例/重复 | 状态 | 底层请求 | 工具项 | 字符 | 输入token | 缓存输入 | 输出token | 秒 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| [a01](runs/a01/report.md) | C1/1 | 完成 | 4 | 3 | 1769 | 46767 | 33792 | 1181 | 34.37 |
| [a02](runs/a02/report.md) | C2/1 | 完成 | 5 | 4 | 1826 | 61892 | 47232 | 1375 | 46.14 |
| [a03](runs/a03/report.md) | C3/1 | 完成 | 4 | 9 | 1698 | 48190 | 31616 | 1170 | 34.07 |
| [a04](runs/a04/report.md) | C2/2 | 完成 | 4 | 11 | 2017 | 50723 | 47488 | 1353 | 38.18 |
| [a05](runs/a05/report.md) | C3/2 | 完成 | 4 | 3 | 1818 | 47625 | 34688 | 1296 | 41.84 |
| [a06](runs/a06/report.md) | C1/2 | 完成 | 3 | 2 | 2459 | 35248 | 31488 | 1276 | 46.26 |

- C1：两次都解释同步／deferred首事件、decode完成和退订、metrics差异。局部“show保存新release前发布”缺具体原始路径，但报告也说只是可能／线索，故只记论证前提不足，不能判窗口已发生或必然可达。原句a01:12/18、a06:14/20，源码subscription:9–11、panel:7–9、navigation:3–5。
- C2：两次都区分原始立即写与任务目标延迟写、批次/flush/cancel、持久化与visit通知。a04没明确复述README:10–12的后发导航请求优先，a02:8有；这一文档政策仍待确认，只记录覆盖差异。
- C3：两次都解释立即done与未来Promise完成、同步catch与拒绝，以及入口历史／current+latest显示条件。两次读到并描述预览（a03:11、a05:11），第17行建议却未列40ms/hide/复用保留检查；这是局部建议遗漏，非未读源码或实际测试退步。

完整有限判断、逐项标准/源码/原句与工具引用见[case-comparison.md](case-comparison.md)和review.csv。六份报告没有被重写。评价为执行Agent的**未盲化AI代理评价**，脚本只编码判断／核对引用，不作语义关键词打分，不增加LLM judge；同义、分散表达和合理未知已接受，未要求历史故障或唯一修复。

## Task 3：重复缺口、成本及结论

上述三类局部问题不同，不能合并成“都不够仔细”。C1的局部可达性前提不足仅在C1出现，C3验证建议局部缺项仅在C3出现；C2的未复述政策又未确认。**候选重复缺口列表为空**，不人为制造优化空间。原始核心事实和关系未识别到已证实的跨例错误，没有可扣分的已批准新标准政策。不以满足条目数汇总总分，也不称三例整体任务通过或代码修复有效。

成本：6个CLI会话、24次原生PreModelRequest、24次完成、32个完成工具项。输入290445 token（其中缓存226304），输出7651 token（reasoning 118为输出子项，不另相加）；CLI与原生PostModelRequest用量逐槽一致。累计会话墙钟240.87秒，整个调度246.09秒，不含准备和代理评价时间。货币账单／固定费率未提供，USD留空而非估价。原生钩子计数不是网络包或重连次数；未观察到失败请求重试，无显式补跑。[costs.json](costs.json)保留两套原始计数与用量。

每会话硬上限600秒/12请求，全轮6会话/72请求；实际均未达到。候选源、原标准、旧研究、生产文件、HEAD和已有diff保持原样，保护检查见[execution-validation.json](execution-validation.json)。原标准目录在开始时已是未跟踪工作，原样保留。未引入依赖、未创建提交。

限制：三例每例两次仅开发内描述；C2/C3关联、标准未确认、代理评价非独立人审，均限制结论。有限清单满足不表示所有行为已覆盖；没有泛化、显著性、稳定性或因果结论，更没有修复收益结论。

**唯一下一步：D，基线已经较好，暂不继续提示词优化。**没有自动执行下一阶段。

Git commit subject: `research: establish source-only C1 C2 C3 analysis baseline`

Body: `Reuse frozen analysis K0 in six isolated read-only sessions. Archive native request usage and evidence-based proxy reviews, keeping pending policies separate and reporting no confirmed cross-case recurring gap.`

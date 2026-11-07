# 人工标准驱动分析技能自演化：离线准备与准入阻塞

日期2026-11-07（Asia/Shanghai）。**未启动模型，尚未检验技能演化效果。** 来源核验通过；标准批准范围仍不能从文件或当前对话说明中映射到具体条目。按用户第一节“批准范围无法判断时，完成离线准备后报告阻塞，不启动模型调用”，本轮停在准入阶段。

## Task 1：标准、案例和输入边界

开始核对仓库与祖先目录，未发现适用的AGENTS.md；官方GEPA源码内有局部AGENTS，本轮不使用或修改该目录。初始git状态/diff/HEAD及原文件摘要见[initial-state.json](initial-state.json)。

已读取标准目录README、U1/U2报告和source-manifest。23份声明来源均存在、解析到本仓库路径且SHA256全部匹配，见[source-verification.json](source-verification.json)。两组原任务和完整candidate-start源码/文档复制到materials；原始评分、历史补丁、evidence-key、标准报告及确认记录不进入候选输入目录。案例均已暴露，仅用于开发内研究。

### 分开记录的两类确认状态

- **对话事实：**用户明确说明已在对话中表示“检查通过”。已记录此确认，不把它抹去，也不虚构复核人、日期、独立性或条目级结论。
- **文件状态：**[原README:3](../code-analysis-standard-drafts-v1-20261107/README.md)仍称待确认、未批准；[README:28](../code-analysis-standard-drafts-v1-20261107/README.md)要求明确哪些条目进入标准。U1第95–101行、U2第101–107行确认表、批准ID和未决项全空；source-manifest第3行仍为awaiting-human-confirmation。

因此可以确定“用户说检查通过”，但尚无法确定U1/U2分别哪些S/R/A条目作为评价标准、哪些政策保留未知。特别是U1-R2的新输入接纳边界、R3的已接纳工作记录政策、U2-R2的pending/retry等待区间、loading必须单独表达还是允许组合表达，以及前台/后台政策。原稿本身明确要求对这些政策确认，不能从一句整体检查通过推导唯一具体政策。

[confirmation-status.json](confirmation-status.json)逐项记录状态与未决范围。已通过消息工具询问适用条目范围；当前未获得对应范围答复。只需补充已有确认的适用范围和未决项，不要求凭空重做独立审核。原标准文件保持不变，本轮没有把它们改名为复核通过。

### 标准与可见输入的另一个边界

原稿包含历史补丁和原始评分事实；分析模型按本轮规则只获得原任务与原始候选源码。因此不能要求报告复述它未获得的历史补丁句柄发布、generation/mounted实现或具体评分输出。U1-A2须限定为所分析代码版本的准确区分；没见历史补丁而保留未知是合理行为，不算遗漏。U2同理。此适用性约束写入PLAN，待确认范围明确后再冻结正式逐项评价规则。

## Task 2：离线准备与实际调用

新增独立目录中的材料：

- [PLAN.md](PLAN.md)：准入状态、九会话方案、输入和评价边界及停止条件。
- [analysis_skill_K0.md](analysis_skill_K0.md)：独立命名的通用分析技能，非此前维护K0；不包含案例结论、具体失败序列或修复步骤。
- [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)、report.schema.json：六部分输出；唯一report字段最多6000 Unicode字符，含空白/标题/英文，原始超限输出不裁剪、不补跑。
- materials/U1、materials/U2：原task、候选源码/文档和两份完整K0.prompt；不加入标准、评分、历史反馈或旧模型输出。
- [K0.freeze.json](K0.freeze.json)：任何模型调用前冻结K0、模板、schema及完整K0输入摘要。
- source-verification、confirmation-status、proposed-schedule、proposed-limits、review-template.csv、offline_check.py、offline-validation、summary和本报告。

拟议统一gpt-6-sol/low；分析每会话600秒/最多12底层请求，反思600秒/最多1底层请求，最多9顶层/97底层；4次K0→1次更新→4次K1。调度种子2026110701不是采样种子。K1与K0字节相同、候选泄漏/越界或执行失败均按原规则停止或保存，不补跑。**这些是离线拟议上限，没有宣称实际runner、namespace隔离和请求硬保护已经验证。**确认范围解决后必须先做零模型隔离/计数检查、冻结正式配置，方可调用。

当前实际调用：

| 项目 | 实际值 |
|---|---:|
| K0分析／技能更新／K1分析会话 | 0／0／0 |
| 底层实验模型请求／模型工具调用 | 0／0 |
| 实验输入／输出token | 0／0 |
| 业务代码修改／维护评分／GEPA搜索 | 0／0／0 |

没有生成基线报告，因此没有真实差异反馈、K1、技能diff、K1输入/报告、匿名输出或语义评分。review-template只是空表，不伪装已完成审查。也没有把缺失结果填为失败分数或用旧报告替代新运行。

## Task 3：验证、限制与结论

[offline_check.py](offline_check.py)仅用标准库核对23份来源、候选复制完整性、K0/模板/原task在输入中的关联、拟议预算算术和原仓库保护；[offline-validation.json](offline-validation.json)记录来源/输入校验通过、准入阻塞、正式运行隔离检查未开始。13339份已有文件摘要未变，HEAD及tracked/staged diff不变；没有新依赖、提交或原文件改动。

本轮没有基线分析缺口或演化增量可报告，也不能回答K1是否保留K0正确内容。独立人工盲评未完成；后续当前Agent的逐项分析只能标为代理评价。即使未来开发内覆盖增加，也不能推断补丁、稳定性或泛化提高。

最终问题“人工标准指出的缺口，是否通过一次技能演化被模型补上？是增加了正确理解，还是只增加了文字？”——**尚未检验。**当前阻塞在批准条目范围，而不是观察到技能无效；没有反思/新报告可供区分理解与文字增加。

Git commit subject：`research: prepare gated analysis-skill evolution inputs`

Body：`Verify U1/U2 source digests and freeze a generic analysis skill and report format. Record conversation confirmation separately from pending draft approval scope, with zero model calls and unchanged standards.`

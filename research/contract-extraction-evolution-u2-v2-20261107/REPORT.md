# U2 Contract 提取技能自演化 v2

**本批次观察到有限改善。**排除源码读取故障后，一次标准差异反馈生成的K1，在两次输出中都更具体地提取了可见的等待阶段、旧回调与身份关系，并保留未决政策。原本正确的两条明确任务义务保持，未发现新增无依据产品要求或语义反转；queued-retry的具体后台关闭路径仍未完整说明。不是全部七条历史规范被自动恢复。

这是**已暴露开发案例、AI执行代理评价，非独立人工复核**。同例反馈后回测、每条件两次，仅为描述性观察，不证明稳定因果收益、泛化或修复收益。K1未接纳为生产版本。

## Task 1：配置修复与边界验证

v1全部结果、失败记录和账本保留，v2是用户授权的整批重做，不是选择性补跑；v1输出未进入反思或效果比较。起始Git状态仅含前两轮未跟踪归档，tracked及暂存diff为空。祖先和仓库无适用AGENTS.md；归档GEPA子树规则不适用本目录。

[配置diff](config-v1-v2.diff)只修复提取会话的`code_mode_host`，显式保持原有`shell_tool`启用，并增加单槽调度和执行有效性门。[配置说明](execution-config-review.md)解释每项变化。原K0、外围prompt、task、候选五文件、schema、request_guard及七条评价表逐字复用，未制作新标准；源码/来源摘要见[scope-and-sources.json](scope-and-sources.json)。600秒、6000字符report、4000字符候选技能、每提取12请求／反思1请求／总49请求不变。

[离线检查](environment-check.json)核验精确CLI参数下的有效features、宿主二进制启动、候选正文与摘要、只读挂载、研究路径不可见和请求硬门。反思工具关闭，模型只能使用原候选读取命令；没有扩大到研究仓库。离线检查未冒称模型读取已成功。

第一份正式基线计入预算。[执行门证据](first-baseline-gate.json)以真实成功工具输出匹配四份源码正文，不采用文件列表或模型自述。四个提取槽均通过同一读取检查，无拒绝或越界调用；报告质量未用于决定继续。

**环境限制：**最终核验发现全局配置新增`service_tier`字段，来源未知，未回写。[观察记录](global-config-observation.json)显示mtime晚于末槽复制配置及启动记录；删除该单字段后的摘要与起始摘要完全一致。实验子进程只挂载临时副本，脚本无全局写入。正式槽位未各存配置副本摘要，故不声称其字节身份已逐槽独立认证，也不从用时推断性能收益。显式模型、effort和工具参数一致；仓库与v1保护检查通过。

## Task 2：实际槽位与自动技能变化

| 槽位 | 条件 | 实际请求 | 成功工具项 | 源码正文读取 | 结果 |
|---|---|---:|---:|---|---|
| k0-1 | K0重复1 | 4 | 3 | 四份源码 | 完成，执行门PASS |
| k0-2 | K0重复2 | 3 | 2 | 四份源码 | 完成 |
| reflect-1 | 一次反思 | 1 | 0 | 无工具 | 生成K1 |
| k1-1 | K1重复1 | 3 | 2 | 四份源码 | 完成 |
| k1-2 | K1重复2 | 3 | 2 | 四份源码 | 完成 |

[完整实际输入输出及轨迹](runs/)、[输入等价检查](input-equivalence.json)保存关联：K0两次prompt相同且与v1冻结prompt逐字一致；K1两次prompt相同，与K0相比只有技能块替换，工作区互相隔离。四次候选摘要未变。反思只收到有效v2基线、冻结规则和[差异反馈](difference-feedback.json)，没有v1无效输出。

原始[反思输出](runs/reflect-1/raw-answer.txt)生成的[K1](contract_extraction_K1.md)原样保存，无人工润色。对照[K0](contract_extraction_K0.md)、[skill.diff](skill.diff)和[变更依据](skill-changes.json)，新增三类方法：

1. 分开一次请求、等待间隙、后续请求和整个活动，追踪状态写入及消费者。
2. 追踪已排队工作是否存在、归属、取消入口与实际调用、条件性后续效果。
3. 追踪请求捕获身份与共享状态，区分相邻组件事实和目标行为要求。

[候选边界检查](K1-boundary-review.json)未发现案例标识、文件名、源码标识、隐藏断言或专用政策答案；执行代理语义检查认为仍为可复用方法，未扩大工具或任务。通过检查不证明泛化。候选在K1运行前冻结；没有第二次反思、换候选或K2。

## Task 3：逐项结果、成本与限制

评价表保持[evaluation-v1.csv](evaluation-v1.csv)原字节。五维分别记录于[item-review.csv](item-review.csv)，无总分；[item-comparison.csv](item-comparison.csv)和[timer-boundary-review.csv](timer-boundary-review.csv)附报告原句、源码及标准关联。

| 条目与本轮可评价目标 | K0重复1／2 | K1重复1／2 |
|---|---|---|
| O1：pending持续检查；O3：未ready不交付 | 均完整 | 均完整 |
| O2：等待区间、状态写入/消费及字段未知 | 未覆盖／部分 | 完整／完整 |
| O4：已排队timer与关闭关系 | 部分／部分 | 部分／部分；T1/T2/T4更明确 |
| O5：关闭及旧响应的可见事实、政策未知 | 部分／部分 | 完整／完整 |
| O6：捕获身份、共享状态和条件交错 | 部分／部分 | 完整／完整 |
| O7：后台事实与规范来源边界 | 部分／部分 | 部分／部分 |

这里“完整”只针对冻结表中的**输入可支持目标**，不表示额外产品政策已恢复或所有行为已验证。O2不要求猜中全程loading=true；O5/O6不要求自行规定全部旧响应必须丢弃。workspace所有权、授权迁移、完整状态编码和交付/去重规则仍不作必答。

**原先漏了什么？**K0正确提取任务目标并保留未知，但遗漏或简略带过可从源码恢复的请求间隙、关闭当前效果、捕获身份与共享写入、排队工作与取消位置。不能把这些说明不足解释为不知道未提供的业务政策。

**更新后补上了吗？**两份K1都新增了“请求结束时清状态但等待语义未定”“当前前台未排队”“旧请求重开后可能改共享状态”等具体、有引用的关系。K1-1还明确外部调度与取消保证未知，K1-2陈述了仍挂载且调度可触发的未来条件。但两份仍未单独说明相邻后台close只隐藏及其具体排队继续路径，O4/T3和O7保留部分覆盖。

**有没有改坏原来正确内容？**O1/O3方向保持，未发现新增无据政策、实现事实升格为规范或关键义务丢失；这不是穷尽证明。[错误/退步记录](unsupported-and-regression-review.json)保留范围。K0报告1825/1241字符，K1为1916/1987字符；收益依据是新增可核查关系与未知边界，而非篇幅。仍需独立复核，不能由同例两次重复断言稳定技能效果。

成本见[costs.json](costs.json)，缓存包含在输入、推理包含在输出中，不重复相加；美元价格未核验。

| 批次 | 顶层会话 | 底层请求 | 输入tokens（其中缓存） | 输出tokens | 会话累计秒 |
|---|---:|---:|---:|---:|---:|
| v2 | 5 | 14 | 177,793（141,312） | 5,047 | 175.29 |
| v1已发生，单列 | 2 | 4 | 44,495（30,976） | 925 | 40.96 |

无模型预跑、自动重试、补跑、额外LLM judge、维护评分、业务修改、ReAct或官方GEPA。临时认证移除，原标准、原评价、v1所有文件、历史归档、HEAD和Git diff保持。最终离线核验见[final-validation.json](final-validation.json)，环境变化单列，不冒称全局配置未变。本轮结束，不自动接纳K1或继续优化。

建议Git commit subject：`research: rerun U2 contract extraction with verified source access`

Body：`Restore the source-read backend in an isolated v2 batch and gate continuation on real source-body reads. Reuse frozen evaluation and K0, generate one unedited K1, and compare four valid extractions. Record limited within-case gains, remaining timer coverage gaps, separate v1 costs and the observed global config drift without maintenance scoring or production changes.`

# 冻结 K1 的跨案例 Contract 提取检查

**唯一建议：D．标准边界不足，无法完成已确认 Contract 提取质量的比较。**本轮八槽执行均有效，来源完整；限制来自C1/C3标准仍全部待确认，不能把输入可见文档或源码关系的恢复自动升级为已确认规范效果。两组主要原任务/README条款的描述性恢复均较完整；K1新增了一些源码关系，也出现了术语精确性限制。

本次为**历史暴露开发案例、AI执行代理评价，评价者知道条件；不是独立盲评**。不生成K2、不升级生产K1、不自动执行后续工作，不推断修复收益或泛化。

## Task 1：配置、技能、案例与标准边界

起始HEAD为a4fc795，Git状态和暂存/未暂存diff为空；祖先与仓库根无适用AGENTS.md，归档GEPA源码规则不适用本目录。初始保护快照及来源摘要已保存，原有材料未变。

使用U2 v2实际冻结的提取技能，逐字复制且核对父子关系：[skill-lineage.json](skill-lineage.json)。

- K0 SHA256：`3edad002954c70817e9d6798c057cb54485f4a4d0184f00b76ff23dfee1fd575`。
- K1 SHA256：`abc40e735b34769798e854639e95371cdfb8ff863f22e02ae27a2fff1e62fa84`，等于U2 v2单次反思原始JSON中的skill；本轮未改写。

[来源与暴露核查](source-and-exposure.json)、[反思暴露审计](exposure-audit.json)核对了真实U2反思prompt及其无工具记录：其中没有C1/C3材料的标识/路径，输入是U2规则、两份有效基线及差异反馈。C1曾作为历史GEPA test并进入旧代码分析实验；C3有筛选和旧代码分析暴露，并与C2共享辅助模式。未进入该次反思不等于全新未见，也不证明独立真实事故样本。旧分析报告没有充当本轮提取基线。

调用前选定C1（首事件/监听/增量消费者）与C3（异步提交入口快照/历史与界面归属），未看结果换题。原任务、源码和C3 README完整冻结。[确认范围](approval-scope.csv)显示两例六个R条目均待确认，批准列表为空。因此[evaluation.csv](evaluation.csv)规定：记录可见原文的描述性恢复和源码事实/未知；业务规范正确性不评分，遗漏不算确定业务错误或已确认义务丢失。不能把源码关系增加换算成Contract义务增量。

[配置说明](CONFIGURATION.md)、[离线隔离检查](environment-and-isolation.json)记录：研究侧配置锁定gpt-6-sol/low、service_tier=priority，不逐槽继承全局config；同一缓存快照和工具后端，独立只读/workspace，无标准/历史/研究目录挂载。每槽配置前后快照和argv均归档，八槽配置副本字节一致；本轮全局配置摘要未变。v2 service_tier历史变化来源仍未知，客户端锁定不证明服务器实际路由可认证。

## Task 2：执行与评价

[PLAN.md](PLAN.md)、[schedule.json](schedule.json)在调用前冻结；种子2026110709只用于交错调度，不是模型采样种子。每槽600秒、12底层请求、report6000字符，保守沿用全局49请求上限。没有模型预跑、反思、自动重试、补跑或扩大规模。

| 顺序/槽位 | 案例 | 条件 | 重复 | 请求/成功工具项 | 秒 |
|---|---|---|---:|---|---:|
| s01 | C1 | K0 | 1 | 3 / 2 | 25.81 |
| s02 | C1 | K1 | 2 | 3 / 2 | 32.02 |
| s03 | C3 | K0 | 1 | 3 / 2 | 28.37 |
| s04 | C3 | K1 | 2 | 3 / 2 | 30.07 |
| s05 | C3 | K0 | 2 | 3 / 2 | 26.91 |
| s06 | C3 | K1 | 1 | 3 / 2 | 33.22 |
| s07 | C1 | K0 | 2 | 3 / 2 | 29.17 |
| s08 | C1 | K1 | 1 | 4 / 3 | 36.88 |

[首槽执行门](first-run-gate.json)依据成功工具输出中的五份源码正文通过，不采用列表或自述。八槽均通过真实正文读取、配置、只读摘要和越界检查。每例两个条件的外围prompt相同，仅任务材料与技能按设计替换，见[input-config-equivalence.json](input-config-equivalence.json)及[runs/](runs/)。执行门不使用质量选择；八槽全部结束后才开始评价。

[item-comparison.csv](item-comparison.csv)按案例/重复配对，提供22行条目比较；[item-review.csv](item-review.csv)保存44行原句、标准和源码引用。六维分开记录：输入原文恢复、事件方向、引用、无据新增、未知、原正确内容保留；无质量总分。行数与重复不是独立案例数。

## Task 3：逐例结果、成本与限制

| 案例/重复配对 | 原文条款两组都能恢复 | K1新增的有依据关系 | 保留与限制 |
|---|---|---|---|
| C1/1：s01→s08 | 初始状态、后续更新、导航/复用、metrics限制 | 同步/deferred对照；release返回后赋值；排队bootstrap在重开复用target时遇到新监听的条件 | 未见条款丢失；“请求回调持有channel”指代不够精确 |
| C1/2：s07→s02 | 同上 | 更明确分开监听移除、已开始decode完成、排队发射和新监听 | 未见新增确定业务要求；“请求结束后的等待间隙”未逐一对应事件源码操作 |
| C3/1：s03→s06 | 异步返回、入口快照、成功一次审计/失败无审计、历史跨关闭、当前最新UI及预览保留 | 更明确done立即处理commit返回值及同步catch与异步兑现/拒绝不同 | 条款保持；嵌套值/深度不可变限制未单列 |
| C3/2：s05→s04 | 同上 | 明确当前done收到Promise本体，不把同步实现当异步目标；相邻预览取消不等于提交取消 | 条款保持；同一深度不可变限制仍未单列 |

接受分散等价表达：例如K0在验证建议中保留40ms预览的完整描述，没有因段落位置判丢失。C3 K1“成功回调”的用语结合其明确“当前立即done”说明理解，不仅凭单句断言其已把原版当成登记好的异步回调。

**可确认的描述性观察：**K1增加的主要是事件/生命周期关系，两个机制都有此类增量，不只是轮询文本。但C3主要文档条款K0原本已恢复；C1 K1引入了与U2相近的“请求/等待/挂载”措辞，部分不能精确对应该事件实现。见[review-qualifications.json](review-qualifications.json)。这些限制不是已证实的业务要求新增或语义反转，也不能因文字更多就认定改善。未观察到明确的原文条款丢失或新增业务义务，不等于穷尽证明无错。

**不能得出的结论：**已确认Contract增量和已确认义务退步均不可评，因为批准集合为空。C3对字段快照/嵌套可变性未展开仅记共同说明缺口，不要求模型猜数据类型或业务政策。仅两个历史案例，无法证明收益稳定、只依赖/不依赖U2相近机制，不能将条目或重复当更多案例做显著性判断。无补丁或维护评分，不能推断修复收益。

[costs.json](costs.json)：8会话、25底层请求、17成功工具项；输入294,203 tokens（其中缓存250,496，已含在输入），输出10,289 tokens（推理222，属于输出子集），累计会话242.45秒。美元价格未核验，不编造。K1报告更长：C1重复1/2为2494/2457字符，K0为1885/1734；C3 K1为2970/2161，K0为2014/1685。关系增量依据具体源码和原句，不依据长度，成本也不等于收益。

[最终离线检查](final-validation.json)核验引用、版本、配置、计量及原有文件保护；不是独立人工语义复核或规范批准。仅新增本目录，原技能、标准、历史材料、业务代码、HEAD和diff保持，无提交。最终仅选 **D**；本轮结束，不自动执行下一步。

建议Git commit subject：`research: check frozen contract extraction skills across C1 and C3`

Body：`Freeze research-side execution settings and compare eight isolated K0/K1 extractions with source-body read gates. Preserve pending standard approvals, separate descriptive source relations from Contract gains, and document exposure, costs and limitations without skill updates or maintenance scoring.`

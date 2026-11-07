# Candidate Contract 修复对照（2026-11-08）

本轮完成 C3 六次正式自主维护；N/M/H 各两次，全部通过既有评分。**明确提供 Contract 未观察到额外修复收益；模型 Contract 与 H 获得相同的已测结果。属于评分天花板，不是效果等价证明。** C1 因评分适用冲突暂缓。原历史“未执行”记录保留。

## Task 1：来源与未知

逐字核对冻结任务及候选源码，路径、摘要、行号及原句见 [source-applicability.json](source-applicability.json)。C1 的初始状态、后续更新、导航保留、不得修改 metrics，以及源码“只计增量”注释匹配。C3 README 明确入口 doc/actor/text 快照、成功后按 receipt revision 审计一次、失败无成功审计、已接纳提交跨 close/reopen 保留、saved/error 仅属当前 visit 最新提交；README 还规定预览 40 ms、hide 丢弃待处理查询、可复用。未发现源文档冲突。

这些条目从“有依据但确认栏空白导致阻断”更新为“候选可见文档支持”，不声称独立人工复核，不生成用户批准。新旧 H 状态保存在 contracts/C1/H.status.json 与 contracts/C3/H.status.json；H 正文及逐项来源分开保存。迟到解码显示资格、失败传播/结算值、无 visit 返回、宿主异常及嵌套可变值政策保持未知，未补入 H 或本轮评分。

沿用首份实际执行 K1：C1=s02、C3=s04。核对运行 receipt、开始时间、完整原始输出摘要及 report 对应关系；只机械取第1栏目正文，逐字匹配前轮 M，未补其他栏目。见 [selection-reverification.json](selection-reverification.json)。M/H 用相同包装，要求辅助材料不能替代原任务，冲突或依据不足回源码核查；N 仅任务与相同公共材料。

## Task 2：评分准入与实际执行

[admission.json](admission.json)记录逐例结论。C1 当前 manifest、起点及 oracle 摘要与前轮一致，也有历史参考 PASS 校准；但 ungranted 的 required 明列 decode-after-switch、decode-after-close、same-channel-reopen。probe.cjs 会将这些未决显示政策直接计入整体通过，不能因参考通过就升级政策。缺少与当前冻结版本匹配且排除未知必答政策的既有评分入口，故暂缓；没有删改断言或拼综合评分。

C3 旧完整 N/H 配对未找到，这不作为准入条件。本轮复用已有 oracle，按原 bench 的“base + overlay”流程进行无模型校准：冻结起点 UNDERREACH、既有 bounded reference PASS、两类既有 mutant 均 UNDERREACH。首次误将 reference overlay 当完整候选直接调用导致模块加载异常，原 stderr 保留在 calibration/C3/reference-direct-invocation-error；修正调用方式后完成校准，未改 oracle、reference 或 base。实际六次无模型 oracle 调用含重复起点一次及该异常一次，四项最终校准见 [calibration/C3/summary.json](calibration/C3/summary.json)。

C3 worker 不检查拒绝兑现/抛回的值、无 visit 返回或宿主异常；检查成功/失败、快照/审计、close/reopen、逆序完成与最新成功 UI、Promise 定案和预览。覆盖有限：未穷举过期 error UI 或全部公开方法语义，未将未测项目标为已证实。

冻结配置见 [frozen-config.json](frozen-config.json) 与 [protocol.json](protocol.json)。使用 gpt-6-sol/low、priority，原始自主 Codex exec，无 ReAct。600秒/槽、12底层请求/槽、全局49请求、最终 report 6000字符，0重试、0补跑、0扩容。源码后端 code_mode_host/shell_tool 可用，工作区可写和 Node v16.20.2 离线核验通过。研究侧独立 profile 与 bwrap 文件系统隔离，未挂载评分、标准、历史和其他运行；原全局配置始末摘要相同。priority 为客户端配置证据，服务端路由无独立证明。

按原种子2026110710筛选 C3，实际顺序 **p02 M-r1 → p04 N-r2 → p06 H-r1 → p08 M-r2 → p10 N-r1 → p12 H-r2**。各组从相同冻结起点独立复制，只改变 Contract 材料。评分在各维护进程退出后由研究侧运行，不提供给后续执行模型。实际输入、完整事件、原始交付、补丁、评分及配置始末见 runs/ 各槽。没有提取、反思、额外模型预跑或 GEPA。

## Task 3：修复、退步与成本

|组|整体通过|目标任务通过|起点/配对N已过项丢失|输入token（其中缓存）|输出token|秒|工具调用|底层请求|
|---|---|---|---|---|---|---|---|---|
|N|2/2|2/2|0/0|142154（135040）|2110|71.81|10|12|
|M|2/2|2/2|0/0|117163（112768）|2202|66.89|8|10|
|H|2/2|2/2|0/0|146842（126848）|2364|79.12|10|12|

目标要求通过涵盖原评分 task、ui、observation 断言，预览和必要保留行为另由整体评分覆盖。输入 token 包含缓存部分，不能相加；耗时为各维护会话墙钟耗时之和，工具次数来自 item.completed，底层请求由原生请求 hook 计量。无冻结价格表，未估算货币成本。逐槽结果及按断言对比见 [outcomes.json](outcomes.json)，用量见 [costs.json](costs.json)。

所有组均将异步 commit 结果处理接入 Promise 定案，同时保留入口快照、成功审计与当前 visit/latest 的 UI 限定。具体修改和实际自检以每槽 patch.diff、raw-answer.txt 与 events.jsonl 为准，逐槽源码及交付摘录见 [patch-review.json](patch-review.json)。六份补丁都仅修改 src/controller.js：M-r1 同步取得 commit 再用 Promise 链处理，M-r2 使用 async/await；N-r2 在微任务调用 commit，N-r1 与两份 H 同步调用 commit 后接处理链。M-r1 保留无 visit 返回 null，其他五份通过 async 或显式 Promise 改为 Promise 返回。同步异常、宿主回调异常的处理范围也有实现差异；这些未决边界仅描述，不计收益或退步。起点的异步保存相关情景不通过，六份修复均使其通过；原通过的预览及其他断言未丢失。相对各自配对 N，M/H 没有新增通过项或丢失项。未测政策上的代码差异只作为实现选择记录，不作为退步或收益。

1. **H 相比 N 是否收益：**整体和目标通过均为2/2，未观察修复收益，现有测试呈天花板；成本差异单独列示。
2. **M 是否保留 H 作用：**已测成功和保留行为相同，但 H 本轮未显示相对 N 的增益，不能声称 M 保留了一个已证明的额外作用。
3. **差异是否对应具体 Contract/补丁/验证：**可核对每槽实际补丁和自检，但没有分离出造成修复结果差异的条款；不得以条款和实现同时出现推断因果。
4. **是否有新退步：**既有评分断言相对起点与配对 N 均未观察到；有限评分不证明所有行为无退步。执行失败0，正式评分异常0。

本案例已有历史暴露，只作开发探索；单一 authored 案例的两次重复不支持显著性、独立泛化或效果等价。本轮不包含 GEPA，不能称为 GEPA 优化收益。原业务、标准、技能、题库、历史和评分器未改；独立运行副本补丁仅归档，没有创建提交，不进入下一轮。保护核验见 [validation.json](validation.json)。

Git commit subject（建议，未创建）：`research: run source-grounded candidate contract repair comparison`

Git commit body：

```text
Resolve document-supported H scope without fabricating human approval.
Defer C1 because its frozen scorer requires unresolved decoding policy.
Calibrate C3 with existing reference and mutants, then run six frozen native
N/M/H maintenance sessions. Preserve prompts, traces, patches, raw scores,
usage and the all-pass ceiling result without GEPA or historical rewrites.
```

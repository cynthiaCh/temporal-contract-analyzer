# 冻结经验后的同题对照报告

本次整体通过率相同；目标行为局部改善，同时出现保留行为退步，未观察到整体修复率提高。

## Task 1：来源、协议变化与离线检查

实际案例：`query-paused-initial-fetch-10266-vanilla`，由旧 manifest/cohort 的一致 ID 确定，未按目录名猜测、未替换案例。新批次从 HEAD `07b7cdcdec0dd8caf016be8f8d67378c83c53156` 开始；原有用户修改及旧批次全部保留，跟踪 diff 与起始一致。

旧批次 `query-paused-same-case-low-20261108_140200` 的 AUTO 开发为 26/29、26/29，整体0/2；AUTO_EXP 开发为27/29、29/29，整体1/2。旧经验准入失败及停止结果保持不变，不并入本次正式分母。一次开发回验损失 `cached-prior-consumed-success`、`retained-context-query-flag`，没有隐去。

本次是看过开发结果后提出、在正式调用前冻结的探索性后续实验。仅把候选准入改为“有改善信号即可参加对照，允许局部退步”，不改变原评分器、正确答案、29项要求或整题通过判定。不是未见案例独立测试，不是整个研究过程的事先预注册。

候选、任务、自动 Contract 实际交付文本、NEW_EXPERIENCE.md 均逐字节复用。A 为旧 AUTO 实际 prompt；B 严格等于 A 加两个换行再加原经验全文，与旧 AUTO_EXP 实际 prompt 相同。没有重新抽取、人工润色、反思、GEPA、第二份经验、开发补丁或评分反馈交付模型。来源/摘要见 sources.json、protocol.json、source-evidence/。

维护配置：`gpt-5.6-terra / low`，priority；CLI `codex-cli 0.164.0-alpha.11.1`，SHA256 `e6d386e8822288f6d5f327e966a5a5e1de928de8795bb6149716005a410f38f2`，Node `v16.20.2`；与四个旧维护会话一致。每槽24请求/600秒，stdout16MiB、JSON report≤6000字符，并发1，总计最多6槽/144请求/3600会话秒。服务端 effort/路由没有独立证明，实际 hook model 与 CLI effort 声明均已核验。

调用前本地核验两组隔离命名空间的读写/验证、合法 cp/diff/for 命令及工具 RPC；宿主快照、归档与计量目录不可见；候选核验前后未变。原运行器模块逐字节复用，复用15项离线归档测试及10份版本对应评分校准记录，无重跑校准或隐藏模型预跑。offline-validation.json 记录离线实验模型请求、维护执行、案例评分重跑均为0。

协议、prompt、输入、经验、配置、评分版本、调度与分析规则先写入 protocol.json 并冻结 protocol.sha256；所有正式启动时间都晚于冻结。调度种子20261108只控制块内顺序，不控制模型采样。

## Task 2：六槽实际执行与整体结果

冻结顺序：block-1-A、block-1-B、block-2-A、block-2-B、block-3-B、block-3-A。每槽独立工作区与独立会话，无记忆/补丁传递，无重试或追加槽位。外部评分在模型停止后执行，不向维护模型或后续会话反馈；全部槽位结束后统一分析。

| 槽位 | 条件 | 有效 | 整体 | 行为通过 | 底层请求 | 工具 | 秒 | 异常/资源 |
|---|---|---|---|---:|---:|---:|---:|---|
| block-1-A | AUTO | True | UNDERREACH | 27/29 | 5 | 4 | 68.89 | 无 |
| block-1-B | AUTO_EXP | True | UNDERREACH | 27/29 | 9 | 8 | 116.96 | 无 |
| block-2-A | AUTO | True | UNDERREACH | 26/29 | 6 | 5 | 90.09 | 无 |
| block-2-B | AUTO_EXP | True | UNDERREACH | 27/29 | 6 | 5 | 99.78 | 无 |
| block-3-B | AUTO_EXP | True | UNDERREACH | 27/29 | 7 | 6 | 91.79 | 无 |
| block-3-A | AUTO | True | UNDERREACH | 27/29 | 6 | 5 | 90.01 | 无 |

| 组别 | 完整通过/有效分母 | 通过率 | 已启动 |
|---|---:|---:|---:|
| A/AUTO | 0/3 | 0.0% | 3 |
| B/AUTO_EXP | 0/3 | 0.0% | 3 |

B-A整体通过率差：+0.0个百分点。
本次整体通过率相同；目标行为局部改善，同时出现保留行为退步，未观察到整体修复率提高。

未启动槽位：[]。停止记录：null。资源耗尽按原 runner 分类单列，正常失败未剔除、未补跑。所有已启动槽位均保存完整归档。

工具级非零返回另见 tool-diagnostics.json：6个槽位各有一次 git diff/check 在无 .git 的独立工作区返回129。这些是模型自验证工具诊断，不是 Python 自动归档 diff 失败或基础设施故障；全部保留，没有以此重试会话或剔除行为失败。两组工作区条件与旧批次一致。六槽输出格式均有效。

复用函数：runner.session/command/verify/source_proof，Archive.prepare/finalize/collect/write_manifest 与 GuardServer；control.py 的 score 回调原样复制旧函数。仅新建 prepare/preflight/freeze/control 与离线分析/报告适配。未重写框架，未修改生产代码、案例原始源码、评分规则、旧冻结文件或全局配置，未新增依赖、未创建提交。

会话流程：Python 冻结输入→复制独立业务工作区→挂载业务目录与合法运行工具→外层保存事件、stderr、请求/工具/token→停止模型→保存最终候选、自动 patch.diff、回答和计量→外部原评分器评价同一最终候选→核对评分前后摘要。归档目录不挂载给模型；机械归档职责和公共 prompt 对两组完全一致。diff 0/1正常，其余记录工具异常；不删除模型新增文件，不请求模型修复归档。

## Task 3：分项得失、成本、限制与结论

目标三项：`cached-later-consumption`, `cached-paused-background`, `offline-nonconsuming-detach`。以下给出全部29项次数，完整每槽向量与原始 scorer 输出均保留。

| 行为 | 原始候选 | 目标 | A通过次数/有效分母 | B通过次数/有效分母 |
|---|---|---|---:|---:|
| offline-detach-false | 失败 |  | 3/3 | 3/3 |
| offline-detach-true | 失败 |  | 3/3 | 3/3 |
| offline-detach-always | 失败 |  | 3/3 | 3/3 |
| offline-nonconsuming-detach | 失败 | 是 | 2/3 | 3/3 |
| active-offline-resume | 通过 |  | 3/3 | 3/3 |
| multiple-observers | 通过 |  | 3/3 | 3/3 |
| last-observer-offline | 失败 |  | 3/3 | 3/3 |
| unknown-unsubscribe | 通过 |  | 3/3 | 3/3 |
| consumed-flight-cancel | 通过 |  | 3/3 | 3/3 |
| nonconsuming-flight-cache | 通过 |  | 3/3 | 3/3 |
| cached-paused-background | 通过 | 是 | 0/3 | 3/3 |
| cached-consumed-revert | 通过 |  | 3/3 | 3/3 |
| remount-generation | 通过 |  | 3/3 | 3/3 |
| late-old-generation | 通过 |  | 3/3 | 3/3 |
| always-mode | 通过 |  | 3/3 | 3/3 |
| focus-gates-resume | 通过 |  | 3/3 | 3/3 |
| focus-does-not-gate-first-start | 通过 |  | 3/3 | 3/3 |
| offline-first-retry | 通过 |  | 3/3 | 3/3 |
| nonconsuming-cancel-retry | 通过 |  | 3/3 | 3/3 |
| reentrant-unsubscribe-at-entry | 通过 |  | 3/3 | 3/3 |
| framework-unmount | 失败 |  | 3/3 | 3/3 |
| cached-later-consumption | 通过 | 是 | 0/3 | 3/3 |
| accepted-resume-then-offline | 通过 |  | 3/3 | 3/3 |
| detach-after-resume-queued | 失败 |  | 3/3 | 3/3 |
| independent-query-keys | 失败 |  | 3/3 | 3/3 |
| cached-prior-consumed-success | 通过 |  | 3/3 | 0/3 |
| cached-prior-consumed-cancelled | 通过 |  | 3/3 | 3/3 |
| retained-context-query-flag | 通过 |  | 3/3 | 0/3 |
| dependency-config-preserved | 通过 |  | 3/3 | 3/3 |

相对原始候选21项原正确行为的损失：

- block-1-A：cached-paused-background、cached-later-consumption。
- block-1-B：cached-prior-consumed-success、retained-context-query-flag。
- block-2-A：cached-paused-background、cached-later-consumption。
- block-2-B：cached-prior-consumed-success、retained-context-query-flag。
- block-3-B：cached-prior-consumed-success、retained-context-query-flag。
- block-3-A：cached-paused-background、cached-later-consumption。

块内B相对A的描述性得失（不是同一采样种子，不据此断言单次因果）：

- 块1：新增通过 cached-paused-background, cached-later-consumption；新增损失 cached-prior-consumed-success, retained-context-query-flag。
- 块2：新增通过 offline-nonconsuming-detach, cached-paused-background, cached-later-consumption；新增损失 cached-prior-consumed-success, retained-context-query-flag。
- 块3：新增通过 cached-paused-background, cached-later-consumption；新增损失 cached-prior-consumed-success, retained-context-query-flag。

补丁范围与无据改动由本会话代码复核（无独立人工审阅、未另调用评委模型）：

- block-1-A：仅修改 src/session.js：新增 started，在最后观察者离开时取消所有尚未启动尝试，未区分带缓存刷新；原评分确认 cached-paused-background、cached-later-consumption 两项损失。未见业务无关改动或归档文件。
- block-1-B：仅修改 src/session.js：把取消/结算未启动工作限制到初始 pending 尝试，三目标全通过；同时将消费标记由 q.consumed 迁移至 a.consumed 并删除 query 标记，属于原需求未支持的消费归属变化。评分确认 cached-prior-consumed-success、retained-context-query-flag 两项原正确行为损失。无业务无关改动或归档文件。
- block-2-A：仅修改 src/session.js：新增 started，在无人观察且未启动时跳过恢复，未结算暂停状态且范围包含缓存刷新；原评分缺失 offline-nonconsuming-detach 和两项缓存保留行为。未见业务无关改动或归档文件。
- block-2-B：仅修改 src/session.js：区分未启动的 pending 尝试与缓存刷新，三目标全通过；getter 虽同时写 q.consumed/a.consumed，unsubscribe 改为只依据 a.consumed，仍忽略原 query 级保留标记，属于原需求未支持的消费归属变化。评分确认同两项消费相关保留行为损失。无业务无关改动或归档文件。
- block-3-B：仅修改 src/session.js：用 pending 且 data=null 结算初始未启动尝试，三目标全通过；迁移为 attempt 级消费并删去 query 标记，属于原需求未支持的消费归属变化。评分确认同两项消费相关保留行为损失。无业务无关改动或归档文件。
- block-3-A：仅修改 src/session.js：以 retryCancelled 在 resume 中提前结算/取消，覆盖了允许续行的缓存刷新；原评分确认两项缓存保留行为损失。未见业务无关改动或归档文件。

| 成本 | A | B |
|---|---:|---:|
| 实际请求 started | 17 | 22 |
| 请求 completed | 17 | 22 |
| 阻止的派发 | 0 | 0 |
| 工具调用 | 14 | 19 |
| 会话秒数 | 248.99 | 308.54 |
| input_tokens | 219468 | 322297 |
| cached_input_tokens | 160256 | 251136 |
| cache_write_input_tokens | 0 | 0 |
| output_tokens | 9945 | 13009 |
| reasoning_output_tokens | 4333 | 4615 |

成本变化 B-A：请求 +5，工具调用 +5，会话时间 +59.55秒，input tokens +102829，output tokens +3064。

合计：6个维护会话、39次底层请求、33次工具调用、557.52会话秒。计量缺失：False。缓存输入和reasoning输出是各自总量子集，不能重复相加；不估算货币费用。主控聊天准备/分析本身的平台token与请求不可见，不计入维护成本，也不声称为0。

本轮正式调用只包含授权维护会话。Contract提取、GEPA、反思、经验生成、额外模型评委、隐藏模型预跑和重试均为0；离线准备阶段维护执行与评分重跑为0。正式外部评分每已启动槽位一次，没有评分补跑。

完整性检查：PASS，798份冻结文件及18631份既有文件摘要核验通过；原始候选、最终快照/工作区、评分输入及评分前后摘要一致。每槽 SHA清单核验、实际prompt、模型与计量核验均保留于 integrity-validation.json。

限制：各组三次，只是同题探索性后续；已经看过该案例的开发结果，不能称独立测试、新题泛化、稳定有效或统计显著，也不能据此概括自进化整体成功/失败。调度种子不控制模型随机性；经验增加了上下文长度，成本以实际计量报告。不能声称已经节省请求或提高普遍修复率。后续可比结论需要采用同版运行器的额外对照，但本次不自动追加任何运行或更新生产经验库。

材料：PLAN.md、sources.json、protocol.json/sha256、schedule.json、prompts/、offline-validation.json、actual-schedule.json、runs/*/archive/{events.jsonl,stderr.log,patch.diff,final-candidate,score,usage.json,receipt.json,ARTIFACTS.sha256}、behavior-vectors.json、behavior-counts.csv、summary.json、scope-review.json、integrity-validation.json、ARTIFACTS.sha256。

推荐提交（仅建议，未创建提交）：

```text
research: record frozen-experience same-case follow-up

Reuse the frozen low repair runner and unchanged experience for six blocked A/B sessions.
Archive prompts, patches, unchanged oracle scores, behavior vectors and usage.
Document exploratory admission change, regressions and small-sample limits.
```

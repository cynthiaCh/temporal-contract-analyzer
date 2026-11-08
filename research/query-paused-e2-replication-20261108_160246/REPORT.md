# 冻结E2的同题独立复现

新批次再次观察到同题整体修复增量。

## Task 1：来源对应、冻结和离线检查

唯一源批次：`/home/sribd/Downloads/wangshu/temporal-contract-analyzer/research/query-paused-e2-low-20261108_151511`。实际case由源manifest/cohort核定为 `query-paused-initial-fetch-10266-vanilla`。起始HEAD `f8c83a46b340e08067d876d863463e943bfd27ab`；跟踪diff与起始状态一致，既有修改/历史文件保留，仅新增本研究目录。

E2 SHA256 `85c058e4065322155ac3ae3a8486df020da62745c3c64f25db5fd1b7570904c1` 与用户指定值一致。A/B实际prompt均逐字节复用源文件，B严格等于A加两个换行加E2。候选、任务、自动Contract实际交付文本、评分场景/规则、原始行为要求及依赖摘要核验通过，没有修正E2已记录歧义、重新提取、训练、反思或提供历史补丁/评分解释给维护模型。

源REPORT/summary、experience-freeze、cohort/config/protocol、源六槽实际prompt与配置、原评分与SHA清单、完整性记录均核对；源结果为AUTO 0/3、AUTO+E2 1/3，仅作历史参照，不进入本新批分母。源批已经结束，没有恢复或修改其停止/完成记录。输入与复用摘要见sources.json、source-evidence/。

CLI `codex-cli 0.164.0-alpha.11.1`，二进制SHA `e6d386e8822288f6d5f327e966a5a5e1de928de8795bb6149716005a410f38f2`；Node `v16.20.2`。runner.session/command/verify/source_proof、Archive、GuardServer及native backend/配置/schema逐字节复用；control.py（含原score）与源完全相同，未增加AST、RAG、检查表、ReAct、工具黑名单或模型请求预算。

宿主全局默认service_tier已在本次之前由priority变成default；这是与历史保护记录不同的唯一文件。源运行器本来就不加载该文件，而是使用仓库外临时profile。离线命名空间证明：宿主home/config不可见、实际profile字节及完整CLI参数与源一致，仍显式指定low/priority；宿主环境被清空，只保留原协议允许的代理变量。本批保护当前宿主摘要，保留历史差异，未修改全局配置。host-config-isolation.json记录完整证明及可核对的配置边界，不把CLI声明当成服务端路由/effort/tier的独立认证。

第一次准备检查将这个不被加载的宿主默认文件也与历史摘要强比，因此在复制输入前停下；随后本地preflight因runner尚未复制而导入失败，未运行任何模型/评分。适配后仅将宿主默认配置按当前基线保护，要求实际隔离profile/参数一致再继续，所有其他旧保护文件都保持原摘要。offline-preparation-notes.json保留记录，没有重试模型或评分器。

零模型离线检查通过：临时小候选与假事件分别验证无修改、改动/新增/删除及补丁应用、超时保留轨迹/候选、diff异常不覆盖原退出原因、请求封顶/被阻止派发、真实命名空间读写/Node验证与归档隔离。fake CLI为本地Python，fake score回调只写假材料，不是案例评分器。复用源版本对应15项归档测试和10份真实评分校准，真实案例评分预跑0。详见offline-validation.json。

protocol.json/sha256在任何正式调用前冻结本协议、实际两组prompt、所有关键输入/经验摘要、配置、评分版本、六槽调度与解释规则。认证、临时profile和本地夹具都在Git仓库外。

## Task 2：六槽执行及整体结果

固定维护：gpt-5.6-terra/low，priority；每槽最多24请求/600秒，stdout16MiB，原JSON report≤6000字符，并发1；本批最多6维护会话/144请求/累计会话3600秒/6次真实外部评分。每次从同一原始候选独立复制、独立ephemeral会话，不继承记忆、补丁、工具状态或评分反馈。

调度种子2026110803只控制块内顺序，不控制模型采样。冻结顺序A、B、A、B、A、B；三个块各有A和B一次。严格按序，不依据中间表现取消正常槽位、改经验或增加重复。原评分器在模型停止、Python保存最终候选后评分一次，评分不暴露或反馈后续维护，六槽结束后统一分析。

| 槽位 | 条件 | 有效 | 整体 | 行为通过 | 请求 | 工具 | 秒 | 异常/资源 |
|---|---|---|---|---:|---:|---:|---:|---|
| block-1-A | AUTO | True | UNDERREACH | 27/29 | 6 | 5 | 92.32 | 无 |
| block-1-B | AUTO_EXP | True | PASS | 29/29 | 6 | 5 | 73.05 | 无 |
| block-2-A | AUTO | True | UNDERREACH | 26/29 | 8 | 7 | 81.01 | 无 |
| block-2-B | AUTO_EXP | True | PASS | 29/29 | 9 | 8 | 108.53 | 无 |
| block-3-A | AUTO | True | UNDERREACH | 26/29 | 6 | 5 | 73.32 | 无 |
| block-3-B | AUTO_EXP | True | PASS | 29/29 | 7 | 6 | 142.67 | 无 |

| 组别 | 完整通过/有效分母 | 通过率 |
|---|---:|---:|
| A/AUTO | 0/3 | 0.0% |
| B/AUTO_EXP(E2) | 3/3 | 100.0% |

B-A通过率差：+100.0个百分点。
新批次再次观察到同题整体修复增量。

未启动槽位：[]。停止记录：null。所有已启动槽位及异常、实际计量都在actual-schedule.json；资源耗尽沿用源分类，正常失败未因结果而剔除/改标。无有效评分的缺失不代填成功或失败。

历史参照单列：源E2批AUTO 0/3（27、27、27/29）、AUTO+E2 1/3（27、29、27/29）。这是历史观察，本次没有把它、开发回验或E1结果并入新分母，也没有以跨批汇总替代本次结果。独立指新会话/工作区，不是未见案例独立测试。

## Task 3：复现解释、完整分项、成本和限制

重点核对两组保留关系：cached-prior-consumed-success、retained-context-query-flag；cached-paused-background、cached-later-consumption。以下给出全部29项次数，完整逐槽向量见behavior-vectors.json；原评分不变，部分通过不改判整题通过。

| 行为 | 原候选通过 | 目标 | A通过次数/有效分母 | B通过次数/有效分母 |
|---|---|---|---:|---:|
| offline-detach-false | False |  | 3/3 | 3/3 |
| offline-detach-true | False |  | 3/3 | 3/3 |
| offline-detach-always | False |  | 3/3 | 3/3 |
| offline-nonconsuming-detach | False | 是 | 1/3 | 3/3 |
| active-offline-resume | True |  | 3/3 | 3/3 |
| multiple-observers | True |  | 3/3 | 3/3 |
| last-observer-offline | False |  | 3/3 | 3/3 |
| unknown-unsubscribe | True |  | 3/3 | 3/3 |
| consumed-flight-cancel | True |  | 3/3 | 3/3 |
| nonconsuming-flight-cache | True |  | 3/3 | 3/3 |
| cached-paused-background | True | 是 | 0/3 | 3/3 |
| cached-consumed-revert | True |  | 3/3 | 3/3 |
| remount-generation | True |  | 3/3 | 3/3 |
| late-old-generation | True |  | 3/3 | 3/3 |
| always-mode | True |  | 3/3 | 3/3 |
| focus-gates-resume | True |  | 3/3 | 3/3 |
| focus-does-not-gate-first-start | True |  | 3/3 | 3/3 |
| offline-first-retry | True |  | 3/3 | 3/3 |
| nonconsuming-cancel-retry | True |  | 3/3 | 3/3 |
| reentrant-unsubscribe-at-entry | True |  | 3/3 | 3/3 |
| framework-unmount | False |  | 3/3 | 3/3 |
| cached-later-consumption | True | 是 | 0/3 | 3/3 |
| accepted-resume-then-offline | True |  | 3/3 | 3/3 |
| detach-after-resume-queued | False |  | 3/3 | 3/3 |
| independent-query-keys | False |  | 3/3 | 3/3 |
| cached-prior-consumed-success | True |  | 3/3 | 3/3 |
| cached-prior-consumed-cancelled | True |  | 3/3 | 3/3 |
| retained-context-query-flag | True |  | 3/3 | 3/3 |
| dependency-config-preserved | True |  | 3/3 | 3/3 |

相对原始候选21项原正确行为的损失：

- block-1-A：cached-paused-background, cached-later-consumption。
- block-1-B：无。
- block-2-A：cached-paused-background, cached-later-consumption。
- block-2-B：无。
- block-3-A：cached-paused-background, cached-later-consumption。
- block-3-B：无。

块内B相对A描述性得失（不声称共同采样种子或单次因果）：

- 块1：增加通过 cached-paused-background, cached-later-consumption；增加损失 无。
- 块2：增加通过 offline-nonconsuming-detach, cached-paused-background, cached-later-consumption；增加损失 无。
- 块3：增加通过 offline-nonconsuming-detach, cached-paused-background, cached-later-consumption；增加损失 无。

全部补丁逐份复核（本会话AI辅助，无独立人工审阅/额外模型评委）：

- block-1-A：仅修改src/session.js：新增attempt.started，把所有未启动尝试与已消费工作统一取消，未区分合法缓存刷新；原评分27/29，cached-paused-background和cached-later-consumption损失。query级消费标记保持。未见业务无关改动、额外文件或归档产物。
- block-1-B：仅修改src/session.js：用attempt.started区分已进入执行，保留query级消费记录及getter/controller归属；最后观察者离开先按原q.consumed取消，再仅终结未启动且previous为pending/无缓存的初始工作，其他保持取消重试语义。避免源批B1分支绕过消费判断。原评分29/29，未观察到原正确行为损失。无业务无关改动、额外文件或归档产物。
- block-2-A：仅修改src/session.js：新增started，在resume入口及异步续行处按观察者/是否启动限制工作；未结算无人观察的初始暂停状态，且阻断合法缓存刷新。原评分26/29，缺offline-nonconsuming-detach与两项缓存行为。未见业务无关改动、额外文件或归档产物。
- block-2-B：仅修改src/session.js：保留query消费语义，记录attempt.started，并额外加入query.started（历史上是否进入过执行）参与fresh判定；仅query/attempt均未启动且状态pending时终结初始工作，其余继续原消费取消判断。原评分29/29，无观测退步。额外设计是query级历史启动维度，原任务未显式要求该新状态，不能凭29项全通过断言它对未覆盖生命周期必然必要或充分；没有反事实补丁/额外评分。无业务无关文件或配置改动。
- block-3-A：仅修改src/session.js：恢复前及实际入队回调都要求存在观察者，初始取消后遗留paused，且禁止无人观察的合法缓存刷新；原评分26/29，同三项缺失。未见业务无关改动、额外文件或归档产物。
- block-3-B：仅修改src/session.js：对未started且previous为pending的初始工作结算取消，其余按原query消费取消/取消重试，保留缓存刷新、惰性消费重置与旧context控制器归属。原评分29/29，无观测退步；本评分范围之外未作等价性声称。无业务无关改动、额外文件或归档产物。

工具非零诊断另列，原始输出全部保留，不事后混作基础设施/归档故障或改变有效分母：

- block-1-A：事件14 exit=129，无.git工具诊断。
- block-1-B：事件11 exit=129，无.git工具诊断。
- block-2-A：事件16 exit=129，无.git工具诊断。
- block-2-B：事件12 exit=128，无.git工具诊断。
- block-3-A：事件14 exit=129，无.git工具诊断。
- block-3-B：事件14 exit=129，无.git工具诊断; 事件17 exit=1，详见原输出。
- block-3-B：事件17的缓存刷新自验只等待一个微任务，过早断言缓存结果而exit1；事件19改为等待两个微任务后通过，未再次修改业务源码。属于会话内必要自验证，不是重启模型会话或外部评分补跑。

| 成本 | A | B |
|---|---:|---:|
| requests_started | 20 | 22 |
| requests_completed | 20 | 22 |
| blocked_dispatches | 0 | 0 |
| tool_calls | 17 | 19 |
| 会话秒数 | 246.65 | 324.25 |
| input_tokens | 267752 | 325581 |
| cached_input_tokens | 212480 | 286208 |
| cache_write_input_tokens | 0 | 0 |
| output_tokens | 11113 | 16259 |
| reasoning_output_tokens | 3844 | 7312 |

本批维护合计6会话、42次底层请求、36次工具调用、570.90会话秒；token={"input_tokens": 593333, "cached_input_tokens": 498688, "cache_write_input_tokens": 0, "output_tokens": 27372, "reasoning_output_tokens": 11156}，计量缺失=False。B-A请求差+2，工具差+2，时间差+77.60秒。缓存输入和reasoning输出是各自总量子集，不重复相加；不估算货币费用。

真实外部评分6次。提取、反思、GEPA、新经验、额外模型评委、真实模型预跑、自动/会话重试、评分补跑均为0。主控聊天准备/分析本身的平台计量不可见，不并入维护成本，也不声称为0。

完整性检查：PASS；1012份冻结文件及19658份既有文件摘要核验。候选原始起点一致，最终快照等于业务工作区，评分前后输入摘要与该快照一致。实际prompt、角色参数和请求计量核验保留；宿主当前配置与源批所有文件均未修改。各槽archive包含输入/实际prompt、事件/工具/stderr、原始回答、用量、最终候选、patch.diff、原评分、异常与SHA清单。

会话与归档复用源Python能力：模型只修业务和必要自验证；Python创建独立业务目录，保存输入摘要/快照/prompt/config、持续事件与计量、停止后的最终源码/差异/回答，并收集外部原评分。归档不挂载给模型，不请模型制作或修补归档；diff 0无差异、1正常差异、其余错误；新增文件不静默删除，归档操作不得改变最终源码。没有修改生产代码、原始案例、评分器/参考实现、E2、自动Contract、全局配置或依赖，未创建提交。

每组三次仍是小样本，结果只描述本次同题复现观察，不支持稳定有效、统计显著或新题泛化。E2曾由本题反馈生成，这不是独立未见测试，也不称整个研究过程事先预注册。无论正负，本轮到此结束，不进入E3、新案例、追加实验或生产经验库。

材料：PLAN.md、sources.json、source-evidence/、host-config-isolation.json、offline-validation.json、protocol.json/sha256、experience-freeze.json、frozen-config.json、schedule.json、prompts/、NEW_EXPERIENCE.md、runs/*/archive/、actual-schedule.json、summary.json、behavior-vectors.json、behavior-counts.csv、scope-review.json、tool-diagnostics.json、integrity-validation.json、ARTIFACTS.sha256。

推荐提交（仅建议，未创建）：

```text
research: replicate frozen E2 on the same case

Reuse unchanged E2, prompts, repair runner and evaluator for six fresh A/B sessions.
Archive complete behavior vectors, usage, regressions and replication limits.
```

# E2：一次经验修订及同题对照

本次小样本观察到同题整体修复增量。

## Task 1：离线定位、唯一E2与冻结

实际案例 `query-paused-initial-fetch-10266-vanilla` 来自原manifest，模型、原始候选、任务、固定自动Contract、CLI/工具、Node与评分版本不变。只新增本研究目录；起始HEAD `07b7cdcdec0dd8caf016be8f8d67378c83c53156`，用户既有修改与历史文件保留。

第1步结论：E1没有明确要求把取消能力消费记录迁到单次尝试。三份B公开说明都主动选择了该实现，且实际补丁可核对。E1强调尝试分类，但未明确区分共享消费记录的归属、继承/重置时机与单次控制器生命周期，可能留下被过度推广的空间。公开说明证明选择了什么，不能证明不可见内部推理，也不能证明某句经验是唯一原因。

源码与旧标准共同规定：getter惰性标记其所属共享query，返回来源attempt的controller；共享标记只在实际执行入口重置，创建新暂停尝试不重置；最后观察者离开按既有共享标记结算。三份E1-B补丁都改为依据attempt消费作取消判定，其中一份虽仍同时写query标记，也不再按该标记作判断。

两条失效链：先前消费成功后创建新暂停尝试，原共享消费状态被忽略；旧context延迟读取时，未使当前暂停尝试按共享消费状态结算。原评分均观察到2次调用而标准是1次。可见自验证覆盖同次取消、未消费缓存刷新等，遗漏这两条跨尝试链。完整证据见 DIAGNOSIS.md、diagnosis.json、evidence/ 与 training-feedback.json。

正向证据同样反馈：E1-B三次均修好三项目标，保留其初始终结/idle结算/续行竞态、合法缓存刷新和未消费完成关系。反思器同时收到原始源码、实际变化、原评分观察与标准依据；未收到人工修补候选、参考答案或旧完整成功补丁。原开发同E1曾29/29只作为因果限制记录，不混入新分母。

只执行一次Reflection，沿用原开发反思配置 `gpt-5.6-terra / medium`、12请求/600秒上限，实际1次请求、19.13秒、工具调用0。E2原样取唯一JSON report，SHA256 `85c058e4065322155ac3ae3a8486df020da62745c3c64f25db5fd1b7570904c1`，未人工润色、未生成第二候选或E3。E2原文见 NEW_EXPERIENCE.md，原E1见 E1.md，完整反思prompt/轨迹在 reflection-input.md 和 training-runs/reflection/archive/。

E2明确加入共享记录与单次控制器/结算资格的不同生命周期，并加入旧上下文晚读、暂停创建保留记录等验证。其第2段“读取是否只在实际执行入口惰性记录”可能混淆惰性标记与入口重置，已在调用前的experience-review.json如实记下；原文不修改，不宣称文本无歧义或预先保证成功。

离线检查模型调用/维护执行/评分重跑均为0，版本对应的15项归档测试和10份评分校准复用，实际命名空间读写/验证、工具RPC、归档隐藏与角色参数检查通过。本地反思无hook时没有ledger文件，检查脚本原先错误假定存在，修正后通过；保留失败夹具与offline-preflight-correction.json，未改实际会话计量或归档运行器。

分两段冻结：reflection-protocol.json/sha256在反思前冻结诊断、反馈、实际反思prompt、角色配置、六槽调度和分析规则；experience-freeze.json与protocol.json/sha256在所有维护前冻结原始E2、实际两组prompt及反思归档。A逐字节复用上一批AUTO；B严格为A加两个换行再加E2，公共任务/工具/输出/自动归档职责完全相同。维护看不到诊断、补丁、标准评分反馈或旧E1。

## Task 2：六槽实际执行与整题指标

维护配置不变：gpt-5.6-terra/low、priority，每槽24底层请求/600秒，stdout≤16MiB、唯一JSON report≤6000字符，并发1；六槽合计最多144请求/3600会话秒。反思另有原来的12请求/600秒单次上限，合计最多7会话/156请求/4200秒，未提高任何角色单次预算。服务端路由/effort无独立证明，CLI声明及hook model实际检查，限制与旧批相同。

种子20261108只用于块内A/B调度，顺序A、B、A、B、B、A，不控制采样。每槽同一起点、独立工作区/会话，不传递记忆、补丁或评分。外部原评分在停止模型并归档最终候选后执行，六槽全部结束后统一分析；没有按中间质量改变顺序、剔除正常失败或补跑。

| 槽位 | 条件 | 有效 | 整题 | 分项 | 请求 | 工具 | 秒 | 模型/基础设施异常 |
|---|---|---|---|---:|---:|---:|---:|---|
| block-1-A | AUTO | True | UNDERREACH | 27/29 | 8 | 7 | 93.19 | 无 |
| block-1-B | AUTO_EXP | True | UNDERREACH | 27/29 | 7 | 6 | 127.33 | 无 |
| block-2-A | AUTO | True | UNDERREACH | 27/29 | 5 | 4 | 54.71 | 无 |
| block-2-B | AUTO_EXP | True | PASS | 29/29 | 5 | 4 | 60.12 | 无 |
| block-3-B | AUTO_EXP | True | UNDERREACH | 27/29 | 7 | 6 | 98.90 | 无 |
| block-3-A | AUTO | True | UNDERREACH | 27/29 | 6 | 5 | 84.24 | 无 |

| 组别 | 完整通过/有效分母 | 通过率 |
|---|---:|---:|
| A/AUTO | 0/3 | 0.0% |
| B/AUTO_EXP(E2) | 1/3 | 33.3% |

B-A整题通过率差：+33.3个百分点。
本次小样本观察到同题整体修复增量。

全部已启动槽位和异常见 actual-schedule.json，未启动槽位：[]；停止记录：null。有效性沿用旧规则；正常行为失败或资源耗尽不为提高成功率而剔除，缺失评分不代填成功或失败。

历史单列：原开发AUTO 0/2（26、26/29）、E1 1/2（27、29/29）；上一冻结E1正式AUTO 0/3（27、26、27/29）、E1 0/3（27、27、27/29）。这些已经见过的结果只用于开发背景，不并入本轮正式分母。本轮E2使用先前同题反馈训练，不是未见案例的独立测试或整个研究过程事先预注册。

## Task 3：完整得失、成本、完整性与停止

| 行为 | 原始通过 | 目标 | A通过次数/有效分母 | E2通过次数/有效分母 |
|---|---|---|---:|---:|
| offline-detach-false | False |  | 3/3 | 3/3 |
| offline-detach-true | False |  | 3/3 | 3/3 |
| offline-detach-always | False |  | 3/3 | 3/3 |
| offline-nonconsuming-detach | False | 是 | 3/3 | 3/3 |
| active-offline-resume | True |  | 3/3 | 3/3 |
| multiple-observers | True |  | 3/3 | 3/3 |
| last-observer-offline | False |  | 3/3 | 3/3 |
| unknown-unsubscribe | True |  | 3/3 | 3/3 |
| consumed-flight-cancel | True |  | 3/3 | 3/3 |
| nonconsuming-flight-cache | True |  | 3/3 | 3/3 |
| cached-paused-background | True | 是 | 0/3 | 2/3 |
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
| cached-later-consumption | True | 是 | 0/3 | 2/3 |
| accepted-resume-then-offline | True |  | 3/3 | 3/3 |
| detach-after-resume-queued | False |  | 3/3 | 3/3 |
| independent-query-keys | False |  | 3/3 | 3/3 |
| cached-prior-consumed-success | True |  | 3/3 | 2/3 |
| cached-prior-consumed-cancelled | True |  | 3/3 | 3/3 |
| retained-context-query-flag | True |  | 3/3 | 2/3 |
| dependency-config-preserved | True |  | 3/3 | 3/3 |

每槽原正确行为损失：

- block-1-A：cached-paused-background, cached-later-consumption。
- block-1-B：cached-prior-consumed-success, retained-context-query-flag。
- block-2-A：cached-paused-background, cached-later-consumption。
- block-2-B：无。
- block-3-B：cached-paused-background, cached-later-consumption。
- block-3-A：cached-paused-background, cached-later-consumption。

块内E2相对A的描述性得失（不是共同采样种子，不单独证明因果）：

- 块1：增加通过 cached-paused-background, cached-later-consumption；增加损失 cached-prior-consumed-success, retained-context-query-flag。
- 块2：增加通过 cached-paused-background, cached-later-consumption；增加损失 无。
- 块3：增加通过 无；增加损失 无。

六份补丁均逐一复核，无独立人工审阅或额外模型评委：

- block-1-A：仅修改src/session.js：以started识别是否进入执行，但对所有未启动尝试直接结算，未区分带缓存刷新；原评分确认cached-paused-background与cached-later-consumption两项损失。共享消费getter与判断仍保留。未见业务无关改动或归档文件。
- block-1-B：仅修改src/session.js：保留原query消费标记和getter，未再迁移到attempt。但新增if(!started)外层分支，使带缓存且尚未启动的工作进入空分支，绕过后面的else if(q.consumed)；原有跨尝试消费虽然被记录，却未在最后观察者离开时用于结算当前工作。三目标通过，cached-prior-consumed-success与retained-context-query-flag仍失败（2次调用而非1次）。这是控制流绕过原语义，不是字段归属再次迁移；无业务无关改动或归档文件。
- block-2-A：仅修改src/session.js：新增started，并在最后观察者离开时取消所有未启动尝试或已消费工作；取消范围覆盖了原本合法的缓存刷新，损失两项缓存行为。消费状态仍属query。无业务无关改动或归档文件。
- block-2-B：仅修改src/session.js：以未started、online模式、原pending且无缓存区分全新初始尝试，终结并恢复idle；其他分支继续判断q.consumed，保留原getter/重置点及控制器归属。原评分29/29，未观察到原正确行为损失。仅本评分范围内完整通过，不声称覆盖整个上游库。无业务无关改动或归档文件。
- block-3-B：仅修改src/session.js：保留query消费语义，但if(!started||q.consumed)把带缓存的尚未启动刷新也取消；三目标中缓存刷新两项退步，而两项跨尝试消费行为通过。原评分27/29。与E2关于合法缓存刷新保留的要求不一致，未见支持扩大取消范围的原需求依据。无业务无关改动或归档文件。
- block-3-A：仅修改src/session.js：保留query消费标记，用consumed或未started条件取消；未区分缓存刷新与全新初始工作，损失两项缓存行为。无业务无关改动或归档文件。

工具级诊断（保留所有原输出，不把自验证命令失败混为评分、归档或基础设施异常）：

- block-1-A：事件12 exit=128，见原命令输出; 事件16 exit=1，见原命令输出。
- block-1-B：事件9 exit=1，见原命令输出; 事件16 exit=129，无.git的git诊断。
- block-2-A：事件14 exit=129，无.git的git诊断。
- block-2-B：事件14 exit=129，无.git的git诊断。
- block-3-B：事件17 exit=129，无.git的git诊断。
- block-3-A：事件14 exit=129，无.git的git诊断。

补充诊断：block-1-A一次git status返回128，一次自验因只等待一个微任务而过早断言缓存成功，随后按可见说明增加微任务等待并通过；这是会话内必要自验证，没有重启维护或重跑外部评分。block-1-B曾find ..寻找AGENTS，在隔离命名空间的/etc和/proc遭遇权限错误，属于偏离仅/workspace说明的工具行为；没有观察到宿主归档/评分器暴露，也未事后改变有效分母。详见tool-diagnostics.json和原始事件。

| 维护成本 | A | E2 |
|---|---:|---:|
| requests_started | 19 | 19 |
| requests_completed | 19 | 19 |
| blocked_dispatches | 0 | 0 |
| tool_calls | 16 | 16 |
| 会话秒数 | 232.14 | 286.36 |
| input_tokens | 250378 | 264492 |
| cached_input_tokens | 191488 | 220672 |
| cache_write_input_tokens | 0 | 0 |
| output_tokens | 9967 | 11688 |
| reasoning_output_tokens | 3172 | 4968 |

维护合计：6会话、38请求、32工具调用、518.49秒；计量缺失：False。E2-A请求差+0、工具差+0、时间差+54.22秒。

反思另计：1请求、19.13秒；token={"input_tokens": 24502, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 832, "reasoning_output_tokens": 72}。全部角色合计7会话、39请求、537.62秒。缓存输入和reasoning输出是各自总量子集，不重复相加；不估算货币费用。主控准备/分析聊天的平台请求和token不可见，不混入维护成本、不声称为0。

正式原评分调用6次，评分补跑0；Contract重新提取、GEPA、第二次反思/E3、额外模型评委、隐藏模型预跑、会话重试均为0。E2由唯一一次反思生成，不是人工写的经验或补丁。

完整性：PASS。950份冻结文件及19085份既有文件摘要通过；维护原始候选一致，最终快照等于工作区，评分前/后候选与该最终快照摘要一致；实际prompt唯一差异为E2；反思原始report等于E2。每槽事件、工具/stderr、patch.diff、最终候选、原评分/全行为向量、用量和SHA清单保存在各archive目录。

复用而非重写：原runner.py、archive.py、native_backend.py、GuardServer/guard_client/request_guard/read_policy、配置/模型目录/输出schema逐字节复用；control.py与score函数沿用上一批。新增prepare/preflight/reflection/freeze及离线分析报告适配。Python负责所有机械快照、事件/stderr/计量、最终补丁与评分归档，归档不挂载给模型，不请模型备份/修补归档，不删除它产生的额外业务文件。未修改生产代码、原案例、评分规则、全局配置、旧批次或创建Git提交。

结论范围仅此同题小规模探索。各组三次不支持统计显著、稳定有效或新题泛化，E2又使用了先前本题反馈；不得把开发或E1历史池化增强证据，也不能只挑E2成功补丁。经验文本的措辞歧义已保留在审查记录，不因结果好坏事后改写。

本轮观察到整题增量；仍只完成这一轮，不要求每次100%，不自动扩展、不生成E3或更新生产经验库。

主要材料：DIAGNOSIS.md、training-feedback.json、reflection-input.md、E1.md、NEW_EXPERIENCE.md、两段protocol/sha256、experience-freeze.json、prompts/、schedule.json、reflection-receipt.json、actual-schedule.json、training-runs/、runs/、behavior-vectors.json/csv、summary.json、scope-review.json、tool-diagnostics.json、integrity-validation.json、ARTIFACTS.sha256。

推荐提交（未创建）：

```text
research: revise frozen experience once and evaluate E2

Ground the revision in three repeated regressions and preserved target gains.
Freeze one reflector-generated E2 and archive six unchanged-budget A/B sessions.
Report whole-task outcomes, regressions, costs and same-case limitations.
```

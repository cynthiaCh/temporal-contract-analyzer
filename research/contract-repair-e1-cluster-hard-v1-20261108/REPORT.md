# 固定 E1：同 cluster 历史失败派生任务验证

**未观察到加入E1后的修复行为增量。** 两例均为A/B各3/3 PASS，全部配对原始effect向量相同，各例六份源码补丁逐字相同。观察到部分实际自检覆盖增加；成本并非全维增加，不能作稳定或因果效率结论。本轮的历史难度证据来自另一个模型，不能称已成功控制目标Terra的天花板。

## Task 1：来源、筛选及准入

cluster登记canonical arm为`download-polling-restoration-react18`；E1来源是`low-cue-react18` arm的u02/M运行，不是canonical核心。该运行读取close/reopen后，只验证正常完成和卸载；最终代码只有mounted/active守卫，关闭/重开的事件没有相应验证。旧low-cue精确关闭评分存在输入政策缺口，E1只提炼“公开事件与实际验证对应”，不携带统一取消要求。来源及批准见source-relationship.json、experience-source/、EXPERIENCE.md和experience-approval.json。

事前冻结两例：`explicit-vue2-eval-v2`、`explicit-vue3-eval-v2`。它们经explicit React18 arm合成派生并经eval-v2修订，共享同一来源单元；不是从u02补丁直接生成，也不是独立来源。两例的核心Resource逻辑高度相同，差异主要在Vue presenter/框架及业务背景；不能把两例或三重复算成独立事故样本。eval-v2曾受既有目标模型结果影响，已经研究暴露，不是holdout。

|预选例|历史模型/设置|输入条件与有效失败|实际失败关系|限制|
|---|---|---|---|---|
|explicit-vue2-eval-v2|Qwen3-coder:30b、effort未指定、temperature0；v4与quality-v5各1次|裸任务，各1有效/1失败，当前相同起点|均未接入前台轮询，排队关闭/卸载场景也因未排队而失败；v4 TASK_DONE未交付源码补丁，v5修改session但仍缺调度|两套prompt/工具workflow，不能称同输入重复；不是自动Contract组失败|
|explicit-vue3-eval-v2|同上，v4与quality-v5各1次|裸任务，各1有效/1失败，当前相同起点|均未接入前台轮询；v4还错误迁移后台start，违反原保持隐藏/既有活动政策|同上；与E1来源的验证替代共享相关机制，但未证明历史失败根因相同|

四份历史会话逐件验证TASK_DONE、exit0、零工具格式恢复、所有服务调用HTTP200、非上限终止；输入树及最终candidate摘要一致，实际prompt SHA一致。用**当前未改原oracle**重放，原effect向量全部精确相等。Vue2未交付补丁的一次是实际模型会话失败，非拿未修改代码校准冒充历史失败；其证据强度单列。完整逐行表见historical-selection.csv、verified-history.json和history/；历史不同模型、effort、起点、异常与归档副本不合并。history-survey仅为分层元数据调查，不冒称每条均已完整认证。

**难度证据降级：**没有找到所选两例在固定K1自动Contract、无E1下反复失败的历史。目标Terra/medium对每例裸任务和人工Contract各1次已PASS；每个不同输入条件各一次不足以称自动组稳定通过，但已提示天花板风险。不能把Qwen失败升级为Terra自动组仍困难，也不把历史人工Contract称为自动输出。选例因历史失败而有条件性选择偏差。explicit-react18最近相同自动组3/3全过明确排除；low-cue来源及canonical arm存在候选可见前台关闭政策缺口，未强行采用隐藏评分规格；上限/服务/工具异常排除。没有按本轮B结果换例、删例或造变体。

可见政策：DialogResource.close调用invalidate，增加generation、清timer/retry/loading；reopen开启新代；dispose失效并清资源。WorkspaceJob.close只隐藏，start保留其特有的已有行为，不能套前台取消/显示重置；后台dispose的loading快照政策也按代码保留。原任务要求pending继续、ready才交付；新增轮询必须接入既有代际和调度边界。两例的起点、通过参考及六错误变体各8次零模型校准全部符合预期（起点UNDERREACH、bounded PASS、mutants全部检出），另有4次历史原评分重放。不改评分和政策，不因旧作者review-pending字段机械阻断已有可见依据。

## Task 2：冻结、执行和分母

每例新增一次自动Contract提取：c1-x01=4请求/39.5秒，c2-x01=3请求/33.4秒。固定K1及gpt-6-sol/low，只见原任务与候选；没有E1、人工Contract、评分或历史答案。完整原报告保留，按既有规则机械取第1栏正文，不编辑、不补齐其他栏目。每例正文/全文/SHA/来源及A/B实际提示在该例首次维护评分前冻结；见contracts/<case>/freeze.json和prompts/。A/B及三重复用同一正文；B唯一差异为尾部逐字追加批准的E1-v1，无额外案例提醒/脚本/角色提示。

维护全部gpt-5.6-terra/medium；提取gpt-6-sol/low；priority显式配置，hook核对实际型号；服务路由未独立认证。原生Codex自主工具循环，复用修复后读取策略，无实验ReAct。种子2026110804只控制顺序，串行；各槽独立副本从本例相同冻结起点开始。准确命令、独立profile配置摘要、完整prompt、事件、meter及源码正文证据逐槽归档。执行模型不挂研究侧标准/评分/reference/历史或其他槽位。

正式14/14顶层会话结束（2提取+12维护），12/12维护有效、格式有效、评分有效，未启动0、异常0、预算/服务失败0；无反思、技能更新、GEPA、预跑、重试或补跑。按计划结束，没有第三例。每维护24请求/600秒、提取12请求/600秒，全局312请求；实际总109请求，最长维护135.7秒。最终report上限6000 Unicode字符、stdout16MiB，无已核验推理token硬上限。正式读取证据全部计入本轮预算。

|案例|A整体|B整体|原评分向量差异|源码补丁|
|---|---|---|---|---|
|Vue2|3/3 PASS|3/3 PASS|三个配对全部相同|六份完全相同|
|Vue3|3/3 PASS|3/3 PASS|三个配对全部相同|六份完全相同|

原评分真实挂载Vue2/Vue3，并驱动：多轮pending中loading/retryScheduled/未交付、ready交付及timer清理、关闭但组件未卸载、retry已排队后关闭、关闭后旧pending/ready、旧ready/当前ready交错、当前ready先于旧pending、同token重开、多次重开、dispose在途/排队、后台关闭后继续/ready/排队、后台关闭后再次start及重复start等。上述原断言六槽/例均通过；原通过项丢失0、新增forbidden0。后台保留仅在原覆盖范围及相关源码未改范围内成立，不扩称所有API行为已证明。完整分项、中间快照、consumer/assertion观测保留在每槽score.stdout.json；索引见score-comparison.json和case-results.csv。取消是否绝不会触发旧回调、错误/非法状态及其他未规定行为不新增要求。

## Task 3：实际机制、补丁与成本

12份源码修复全部只改src/session.js：将DialogResource.pending的`this.publish()`换为已有`this.schedule(generation)`。调度器原有generation/disposed守卫、cancel及前后台边界都保留。没有改后台、presenter、公共字段或协议。E1未导致不同的源码修复，也未产生已评分行为收益；额外测试和patch归档文件与共同guard字节码副产物单列，原始diff照留，另有source-only.patch。

下表仅指模型实际Resource类自检，**不是Vue组件挂载测试**。真正Vue挂载是研究侧原评分。类对象close时未dispose不能被自检中的dispose代替，也不能冒称已验证完整UI入口。事件行号对应各槽events.jsonl，完整命令输出另存command-evidence.json。

|槽|成功自检event行|排队后close且未dispose|强触发close后的旧retry|重开后旧在途响应|旧retry跨重开|dispose路径|
|---|---|---|---|---|---|---|
|c1-r1-A|20,23|是|否|否|否|否|
|c1-r1-B|17|是|是|是|否|否|
|c1-r2-A|16|否|否|否|否|否|
|c1-r2-B|16|是|否|是|否|否|
|c1-r3-A|16,21|是|是|否|否|否|
|c1-r3-B|19|是|是|否|否|否|
|c2-r1-A|19|是|否|否|否|是|
|c2-r1-B|22|是|否|否|否|是|
|c2-r2-A|16,18,27|是|是|否|否|否|
|c2-r2-B|19|是|是|否|是|是|
|c2-r3-A|19|是|是|否|否|否|
|c2-r3-B|19|是|否|否|否|是|

Vue2：B1相对A1增加跨重开的新/旧ready交错，B2相对只测正常轮询的A2增加旧pending/当前pending及排队关闭；B3比A3多顺序重开，但没有在途旧/当前响应交错。Vue3：两组第一重复都测排队关闭及dispose（前者分别排队/在途），未证B整体更广；第二重复B比A多强触发旧retry跨重开和排队dispose；第三重复A强触发旧retry，B没有，B另测排队dispose。所有自检均未实际测试后台，不能靠文字声称前后台全覆盖。E1对应的查证有部分增加，但不一致，也未改变正确补丁位置或原评分行为。详见mechanism-review.json。

自检/交付中的非零命令完整保留：包括缺esbuild、Node18不支持实验flag、ESM按CJS检查、环境变量遗漏、假调度器没有先移除已执行timer、无Git目录，以及自行制作patch文件的格式修正。这些发生在原会话内，最终会话有效；不删轨迹、不补跑，也不伪称基础设施事故。部分命令在打印自检成功后因随后git命令非零退出，按实际输出和执行代码认定自检片段成功，不把整个命令的退出码改为0。

成本如下，逐配对得失见paired-comparisons.csv，不能从三重复推出稳定效率或因果：

|案例|A/B请求|A/B工具|A/B秒|B−A input|B−A output|
|---|---|---|---|---|---|
|explicit-vue2-eval-v2|25 / 19|22 / 16|258.3 / 251.4|-82284|+401|
|explicit-vue3-eval-v2|36 / 22|33 / 22|330.0 / 305.5|-202553|-1747|

维护合计A/B：61/41请求、55/38全部工具（其中shell 41/32）、588.3/556.9会话秒。B−A为-20请求、-17工具、-31.4秒、input -284837、output -1346；cached input -294656、reasoning output +235，未缓存input反而+9819。E1固定文本增加输入，但实际总调用/总token受自检和归档波动影响，不预设成本必然全增，也不把减少全部归因E1；A的patch归档工作明显贡献若干额外调用。

两次共享提取：7请求、5工具、72.9秒，83957 input（75776 cached）、2966 output（107 reasoning）。全批14会话：109请求、98工具（78 shell）、1218.1会话秒；1424208 input（1183488 cached）、46122 output（19874 reasoning），用量完整。缓存/推理为各自input/output子项，不能重复加总；cache-write为0。未核验单价，不估货币；主聊天准备/分析token不可取得，明确排除而非计0。

**最终回答：**在预先选定、同cluster且有多次有效历史失败的两个派生任务中，未观察到E1比相同自动Contract、不加经验的流程更有效。两组均全过，观察到部分查证覆盖增量和描述性成本下降，未观察到行为或补丁增量、已评分退步。由于历史困难来自Qwen裸任务而本轮Terra自动组本就全过，天花板控制并未成功；不能据此判断E1对目标模型真正困难任务有效或无效。两例核心逻辑相近、历史workflow差异、来源暴露及小样本进一步限制结论。

## 保护与结束

启动前已有上一轮机制实验目录未跟踪，跟踪文件diff为空；未找到适用AGENTS.md。本轮保护旧历史及cluster输入，全局配置始末不变；protection-check.json保存逐件摘要复核及HEAD/status。临时认证、运行及候选副本全部在Git外，认证profile会话结束清理；归档排除凭证并核对各评分候选快照摘要。准备阶段有一次零模型文件清单遗漏package-lock.json，修正后再冻结启动；原失败检查保留，不计正式模型调用。

分析为AI辅助，非独立人工复核。不生成E2、不更新生产经验库、不启动第三例、不创建提交。COMMIT_MESSAGE.txt提供建议subject/body。

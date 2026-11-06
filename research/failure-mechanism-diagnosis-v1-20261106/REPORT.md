# 失败机制诊断：定向问题有局部收益，但出现一次只核查不修复

完成9/9正式执行，0补跑、0额外模型调用。整体通过：A 0/3、B 0/3、C 2/3。所有9份可信评分均校准通过。单个已暴露开发案例，每组三次，仅描述，不推断因果、显著性或独立泛化。

## Task 1：选定失败及冻结依据

案例为 `transfer-progress-composition-v4-vanilla`，authored development / 研究者已暴露的诊断案例，独立泛化案例0。历史分阶段ReAct A/B各两次均未整体通过；最近prompt-evolution P0/P1/P2为8/10、8/10、9/10，启动期间切换均失败。没有额外搜索模型调用；未因本轮早期结果换题。历史环境校准有效，没有以服务容量、工具缺失或评分异常作为所选行为失败。可信仅指沿用评分器及校准一致，不等同独立人审认证。

原任务要求恢复warm初始进度、防止异步完整帧使显示回退，并保留transfer、retry、navigation、cleanup、audit、queue、telemetry、普通流和后续使用。候选README区分visit/attempt、共享feed、同步start和异步decode。原样与公共材料完整见 [materials](materials/)，冻结前选择、事实与假设见 [PLAN.md](PLAN.md)。

历史P0实际读README、progress-source、progress、telemetry、panel、queue、transfer（events 7/11/13/15/17/20/21），只改progress.js的监听时机、帧序号和显示水位。其smoke和showProgress内切换检查通过，仍缺少start期间导航后继续派发和旧attempt迟到完成。多数关键材料已经读过，不能把失败先归为漏读。

候选相关证据是initialPacket调用在dispatch之前、导航先清current再取消、watch返回后才交付stop、queue分别记录与显示、retry保持visit而替换attempt。冻结前保留的假设包括：关系/事件顺序理解不足、补丁未落实及验证顺序遗漏；本轮不预设哪个条件有效。完整历史来源索引见 [historical-selection.json](historical-selection.json)，该索引在启动后由未变的历史档案生成；案例选择本身已在PLAN/protocol中提前冻结。

## Task 2：条件、执行与新增材料

A精确重放最近可信P0的完整实际prompt（原任务、源码RAG、固定五题、阶段workflow与记录限制），从未修补起点开始。B只在A后附源码路径/行号摘录；C在完全相同B字节后只追加一个核查问题。B包没有原因解释、修复方案或问题；C询问start内导航后派发与已进入decode后导航/retry两类顺序的接纳、记录、显示关系，请执行者区分事实与待验证假设，没有指定未知业务义务。

这是人工根据已知失败定向挑选材料，不是自动检索能力评估。逐项原候选可见性、文件摘要、选择理由和问题依据见 [visibility.json](materials/visibility.json)。研究侧理由、历史结果、隐藏评分器/断言和参考修复均未进入执行Agent工作区。

|新增包|字符|UTF-8字节|o200k_base代理token|共同上限|
|---|---:|---:|---:|---|
|B|6138|6138|1569|6500字符 / 2200 token|
|C|6399|6601|1701|6500字符 / 2200 token|

代理token为归档公开o200k_base的可复核BPE计数，并非声称等于gpt-6-sol内部编码；实际模型用量另见下表。没有无意义等长填充。

|完整prompt|字符|UTF-8字节|代理token|
|---|---:|---:|---:|
|[A](materials/A.prompt.md)|17267|21947|5173|
|[B](materials/B.prompt.md)|23405|28085|6741|
|[C](materials/C.prompt.md)|23666|28548|6873|

固定gpt-6-sol / low、workspace-write、approval never、600秒，沿用已验证的CLI/helper、工具环境与原输出设置，无新增输出token硬上限。每次独立input/workspace、profile、stage、output；11份起始候选文件摘要一致，无历史补丁接续，无中间结果共享。研究侧评分和参考校准位于bubblewrap隔离外。

调度种子2026110602（仅调度，模型采样种子不可控）：重复1 C→B→A；重复2 C→B→A；重复3 C→A→B。串行配对交错，无根据结果改材料/问题/顺序。每次启动前写入唯一调用账本；正式运行前只有无模型离线校准和隔离/宿主检查。

离线核查验证A字节一致、B/C包一致、C只多问题、来源可追溯、无隐藏信息和预期胜者标签、实际prompt/工具输出/补丁/用量完整归档。保护清单在零模型调用时剔除无关忽略依赖，保留7228份冻结文件；修订收据和重跑离线核查见 [VALIDATION.md](VALIDATION.md)、[offline-inventory-revision.json](offline-inventory-revision.json)、[preflight.json](preflight.json)。

所有新增材料位于本独立目录：PLAN/protocol及摘要；materials/input、公共材料、evidence/question与三组prompt；run.py/analyze.py/finalize.py；runs/invocations/results；trials下9套实际prompt、完整events、changes/patch.diff、阶段记录、answer、配置/用量与可信评分；calibration；summary/audit/process-review/trajectory-evidence及本报告。没有新依赖、通用prompt优化、Agent架构、题库演化、生产代码/AST/评分变更或历史改写。

## Task 3：行为、退步、成本与轨迹

|重复|A|B|C|
|---:|---|---|---|
|1|UNDERREACH 8/10|UNDERREACH 8/10|PASS 10/10|
|2|UNDERREACH 8/10|UNDERREACH 9/10|PASS 10/10|
|3|UNDERREACH 8/10|UNDERREACH 8/10|UNDERREACH 1/10|

|指标|A|B|C|
|---|---:|---:|---:|
|整体通过|0/3|0/3|2/3|
|目标启动期间切换通过|0/3|0/3|2/3|
|retry通过|1/3|1/3|2/3|
|原样已通过检查丢失运行|0/3|0/3|0/3|
|原样已通过断言丢失运行|0/3|0/3|0/3|
|历史P0已通过检查丢失运行|1/3|0/3|1/3|
|禁止效果运行|0/3|0/3|0/3|

原样候选只有telemetry及队列禁止字段检查已通过，须同时看逐断言保存情况，不能把原样检查丢失为0说成所有修复均无退步。历史P0及配对已通过项丢失单列：

- A2 相对历史P0丢失：`required:frame-in-order`。
- C3 相对历史P0丢失：`required:warm-bootstrap`, `required:accepted-after-hide`, `required:frame-in-order`, `required:frame-reversed`, `required:cleanup-switch`, `required:cleanup-hide`, `required:composed-reverse-cleanup-switch`。

|重复|比较|整体差值|新增通过|已通过项丢失|
|---:|---|---:|---|---|
|1|B-A|0|无|无|
|1|C-B|1|required:start-switch-admission, required:retry-preserved|无|
|2|B-A|0|required:frame-in-order|无|
|2|C-B|1|required:start-switch-admission|无|
|3|B-A|0|无|无|
|3|C-B|0|无|required:warm-bootstrap, required:accepted-after-hide, required:frame-in-order, required:frame-reversed, required:cleanup-switch, required:cleanup-hide, required:composed-reverse-cleanup-switch|

C3没有候选补丁，可信评分仅1/10，不能因为其契约回答有一定依据就排除该次失败。它相对配对B3丢失的检查见上表；这与原样已通过项丢失是不同参照，禁止用其他通过项抵消。

|成本（三次合计）|A|B|C|
|---|---:|---:|---:|
|输入token（含缓存）|622187|728980|579996|
|缓存输入token|592256|694400|544896|
|输出token|8127|10048|8499|
|模型运行壁钟秒（含工具/网络）|227.974|260.094|221.277|
|含评分秒|233.188|265.295|226.565|
|工具调用|25|31|21|
|非零shell调用|6|7|3|

全轮输入 1931163、缓存输入 1831552、输出 26674 token；模型运行合计 709.345秒、工具 77次。输入为累计重复上下文，未换算费用；时间含服务/工具波动。逐运行成本在summary.json，不能把较低成本当行为更优。

执行失败 0；评分未验证 0；9次参考校准PASS。C3正常完成且工具有效，属于未落实修复的行为失败。候选工具非零退出单列summary：不存在test*的rg、无.git的git diff、自建telemetry/Promise预期失败。默认候选node为v22、可信评分为v16.20.2，沿用前轮环境，未变更；候选可见测试不等于在评分版本验证，可信结果由v16评分取得。

### 实际轨迹与补丁复核

先可信评分，再审实际工具输出和补丁。完整命令、退出码、输出、events行号及原始评分链接见 [EVIDENCE.md](EVIDENCE.md)；以下逐运行判读见 [process-review.json](process-review.json)，是研究者事后复核，无额外审查模型，也不冒称独立盲审。

**A1**：events 7实际cat启动/队列/重试/导航/feed/telemetry；10在修改前记录计划。 10计划将同步导航交给既有late-handle清理；这个判断未区分start返回前的新事件接纳与已接纳decode完成。不是单纯未读到源码。 changes仅progress.js：监听提前、帧序号和显示水位；没有接纳谓词或attempt显示归属。 14 warm/逆序/history/telemetry及showProgress中hide；16仅同步retry/reselect；都通过，未覆盖start内导航后继续事件或旧attempt异步完成。git diff在16失败。

**A2**：events 7实际读取所有相关源码；不存在关键文件不可见或未获得的证据。 修改queue能落实旧attempt不重绘；progress用order===newest把最新已接纳当作最新已显示，改变了普通顺序完成时的显示行为。 changes progress.js的order===newest是核心差异；queue当前attempt判断正确但未增加事件接纳判定。 14只验证旧帧在新帧显示后完成、不覆盖两pending依次完成；21验证旧attempt retry后完成通过。16 git diff失败。可信frame-in-order失败，属相对历史P0的新退步，不冒称原样已通过项丢失。

**A3**：events 7实读transfer/feed/progress/telemetry/README；queue/panel/retry已在共同prompt获得，未见单独展开读取，不能把阶段记录声称的读取当实际工具阅读。 10计划捕捉晚返回stop句柄问题；但补丁没有事件接纳谓词，queue没有attempt条件，清理句柄提前不等于导航期间旧事件失效。 progress增加onSubscribe(stop)在start之前交付清理，transfer登记stop；序号水位保留record。queue保持原样。 14共享telemetry预期失败；17只保存一个resolver导致两个消费者Promise只完成其一，再失败；19收集全部resolver后通过。验证showProgress中hide与detach/普通逆序，没覆盖仍在start栈的新事件及retry迟到结果。21 git diff失败。

**B1**：events 7实际cat所有关键模块；B包在prompt可见。 19最终阶段记录归因于transfer:13与panel的晚取消处理，但19晚于补丁，不能证明修改前完成了契约核查。 changes仅progress.js：监听提前、帧水位；接纳与attempt归属仍缺失。 14共享telemetry期望错误导致断言失败；17改为分离telemetry feed后通过。17没有导航前派发/异步retry归属用例，测试修正没有覆盖目标失败。12 git diff失败。

**B2**：events 7实际cat全部源码；12写阶段1/2记录晚于10首次修改。 12仍计划只改progress；17之后补queue当前attempt显示条件，落实了retry归属，但没有事件进入decode前的接纳判断。 progress按lastDisplayed水位处理逆序，queue增加state.nextAttempt===attemptId；未修改transfer或添加listener入口有效性。 12 telemetry预期错误失败，15按共享feed事实更正后通过；19实际输出retry and reentry checks passed，覆盖旧attempt异步完成和showProgress内切换，未覆盖切换后在start未返回时的新事件。19尾随git命令失败；23异常start清理/语法通过。

**B3**：events 9读取transfer，13 README，15 progress；其他关键模块已在B包和共同材料提供，不能从阶段自述扩为实际重新读了全部。 18计划限定progress修复，保持queue原样；未落实listener接纳和当前attempt显示判断。 changes仅progress.js，先监听、start异常清理、按lastShown水位阻止回退；没有事件接纳谓词或attempt检查。 22共享telemetry预期失败；25单resolver只完成一消费者Promise再失败；27保留所有resolver后通过；29 showProgress中hide通过。未验证start栈中的后续派发或retry旧attempt完成；31 git diff失败。

**C1**：events 7实际读取全部关键实现；问题引用的关系可由源码直接追溯。 补丁与14测试分别处理派发前hide、decode内hide；已接纳历史继续、当前显示受visit/attempt约束。 changes同时修改progress/queue/transfer：listener入口accept；queue当前visit和attempt；decode完成record不受后续导航抹除；display另判断。 14 preNav initialPacket hide与decode hide、逆序/telemetry通过；19旧attempt异步完成保留记录但不显示、start异常清理通过。19尾随git diff失败，不能将整条工具退出非零当测试未执行。

**C2**：events 7读取progress/queue/transfer等，10读panel/retry/telemetry/workspace；progress-source片段已在B包获得；12修改前阶段计划引用initialPacket导航。 12区分事件admission与已admitted记录完成；17与19实际验证支撑，非仅模型自述。 changes新增visit.progressAttemptId及accept，transfer合并abort与accept，progress入口检查但record保留完成，display另看attempt。 17 preNav及已decode后hide、逆序/history/telemetry通过；19 pending旧attempt retry后完成及detach通过；21 git diff失败。

**C3**：events 7实际cat及9 nl关键源码；完整C包与另外两次相同。 阶段2与最终回答区分start派发前导航、已进入decode后导航、同visit retry，并指出源码事实与边界假设；这些内容由实际源码支持，但没有动态测试。 changes.files=[]，仅/stage/records.jsonl发生写入，候选与起点字节相同。 无候选行为测试，无Stage3。阶段2明确写“No code change requested in latest question; answer source facts”；最终回答仅答核查问题，遗漏原任务修复。在600秒时限内正常结束、turn.completed、无stderr错误、可信参考校准PASS，故是任务完成行为失败而非执行/环境异常。

1. **获得并利用证据**：A/B都有实际工具读取，C3也重复读取；C1/C2将证据关系落实到accept/attempt与测试。不能将A/B失败一概归为没读文件。B补充的多数内容与共同RAG重复，transfer是共同RAG未摘出的实现，但基线多次主动读过。

2. **要求、事实与假设**：原要求是修复并保留可见行为。initialPacket先调用再dispatch、Promise取消不撤销完成、同visit retry等是源码事实；事件接纳义务应由任务及当前输出关系判断。C3明确承认边界仍需验证，却把附加问题解释成最新任务而停止修复，不能因此声称理解全面或任务完成。A/B中“晚取消足够”等宽泛判断缺少目标顺序的动态证据。

3. **事件顺序与副作用**：C1/C2的真实测试区分派发前导航、decode接纳后导航、retry后旧attempt完成；记录不被导航抹除、显示另判断归属。失败修复主要验证显示回调内hide/select，此时事件已接纳，与start仍在栈中后的新事件不是同一顺序。

4. **补丁落实**：C1/C2的listener入口有效性与queue当前attempt检查对应其验证；A/B多数补丁没有同时落地两者。C3没有任何候选改动，是最直接的判断/执行断裂。

5. **验证覆盖与退步**：A2用最新接纳序号压制尚未被更新显示替代的帧；候选只测逆序，遗漏普通顺序的两pending完成。部分B/A修正了共享telemetry与resolver测试预期，但未转而覆盖目标顺序。所有测试通过的自述均以实际输出限定。

6. **重复稳定性**：A整体失败重复，但局部修复及错误范围变化；B的retry收益不完全稳定；C两次完整修复、一次只答问题，不能称稳定可靠。

### 判断边界与下一步

B相对A没有整体通过增量，局部得失见配对表；不足以支持扩大检索或声称单纯补充源码解决问题。C相对B有两次整体改善，也有一次明显损失，支持“证据之外，具体核查问题可能有帮助”的有限解释；同时暴露注意/任务解释偏移风险。不是A稳定通过导致诊断无区分力；原失败在A三次均复现。

当前失败更符合**契约关系/事件顺序的解释、补丁落实与验证覆盖共同缺口**，信息遗漏的直接证据较弱。无法用这九次把理解、实现、验证的各自因果贡献拆开；也无法排除采样、提示长度/末尾问题位置、额外验证投入或有限评分覆盖的影响。C3的“只回答”可能是问题改变了任务重心，但一次样本不能证明原因。

**下一步优先补丁验证，暂不扩大实验。** 在现有执行方式中优先检查原修复是否实际交付，并用候选可见代码构造接纳前/后导航、retry旧attempt与顺序/逆序完成的区分性检查；保留每类副作用和已有通过项。证据绑定契约辅助可继续作为局部诊断手段，但C3说明仅问清关系不足以保证任务落实，当前不据此推广通用prompt或增加Agent架构。该建议尚未实施，未修改原题库或生产验证规则。

一个已暴露案例，每组三次，只能描述本轮；不声称统计显著、因果证明、独立泛化或自动检索已具备人工定向定位能力。

冻结文件、实际prompt和候选评分字节、模型/配置/权限及规范化命令已对账；原仓库HEAD与已跟踪diff保持不变，原三个未跟踪研究目录保护，未创建提交。见 [audit.json](audit.json)。

## 建议提交信息（未创建提交）

```text
research: diagnose transfer repair failures with frozen evidence conditions

Archive nine gpt-6-sol/low runs, calibrated scores and tool/patch audits.
Record targeted-question gains, an unimplemented repair and preservation losses.
```

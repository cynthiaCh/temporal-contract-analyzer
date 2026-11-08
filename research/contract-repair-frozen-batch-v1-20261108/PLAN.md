# 单一经验增量的冻结批量对照计划

2026-11-08（Asia/Shanghai）。只新增本目录；不改生产代码、历史、评分器或全局配置，不引入依赖，不创建提交，无GEPA、无额外子Agent。状态：准备完成后等待E1-v1明确确认；未确认不启动增强组。本计划为一轮固定干预，不称长期自演化。

## Task 1：诊断与唯一干预

先完成 DIAGNOSIS.md。旧低线索U2的五项失败同时涉及未传递生命周期上下文、未实现关闭／重开处理、未验证这些公开事件及评分政策超出输入；不能认定完整提取主要失败。明确的D是卸载自检替代关闭／重开验证。E1-v1只作用于修复阶段，全文在 EXPERIENCE.md，标注AI提炼、待专家确认；不规定案例关闭政策或修复方案。

原低线索U2及原listener-registration-order因现有评分包含未决政策暂缓，不修订旧评分凑数。已有U2确认按其原文未知边界使用，不把整体确认扩展成新的字段或全部取消政策。其他候选的任务、README及可恢复既有行为足以支持时，不因旧确认栏空白阻断。

## Task 2：案例、配置、预算、执行有效性

十例ID及选择理由在 selection-before-calibration.json，于新维护调用和新评分前固定；不按本轮模型效果换题。cohort.json绑定原manifest、任务、base、oracle与runtime摘要。无模型校准按原base+overlay语义，完整保存原始stdout、stderr、命令及时间；起点、既有bounded reference和所有既有mutants都保留。校准PASS不自动成为政策批准，逐例评分适用性另见 admission.json、source-scope.json。

|顺序|案例|时序机制|来源及用途|
|---|---|---|---|
|1|download-polling-restoration-explicit-react18|pending轮询、generation|经验来源U2同源显式变体，只作开发诊断|
|2|audit-commit-attribution-vanilla|Promise、入口快照、审计/UI归属|未参与E1提炼；旧六槽全过，保留容易任务|
|3|transfer-progress-composition-v4-vanilla|监听注册、异步decode、重入cleanup|未参与E1提炼；历史困难/不稳定|
|4|cached-feed-lifecycle-repair-vanilla|warm feed、异步paint、visit/history|未参与E1提炼；listener同源派生开发任务|
|5|document-submit-snapshot-vanilla|debounce、flush、同步重入、快照|未参与E1提炼；既有维护暴露，与audit有辅助模板关联|
|6|commit-ack-boundary-vanilla|durable commit先后|未参与E1提炼；历史容易任务，观察不适用边界|
|7|upload-finalize-barrier-vanilla|upload barrier|未参与E1提炼；相邻telemetry保留，不预设经验适用|
|8|feature-flag-readiness-vue3|首次readiness|未参与E1提炼；历史容易任务，观察退步|
|9|local-config-readiness-low-cue-vue2|local迁移、组件API readiness|未参与E1提炼；历史失败后也通过|
|10|error-reporting-retired-request-vanilla|timer retry、逻辑活动与UI归属|未参与E1提炼；与audit共享controller/preview模式|

来源案例旧low-cue U2保留在诊断，不是本批独立样本。同源变体1例、其他来源9例分别报告；“其他来源”仅表示未参与E1-v1提炼，不等于历史未见。所有案例均来自已研究暴露题库，不称独立泛化。exposure-index.json记录限定范围的全部命中路径；无法认证旧模型训练或所有外部会话，未知明确保留，不将索引未命中当全新。

四条件共同使用精确原任务、同一冻结candidate（包括README）及共同维护/运行时/交付指令，不交付研究评价。N无Contract；H为有来源的手工整理参考Contract；M为固定K1技能生成的Contract；E与M相同，仅追加E1-v1。H由本次执行Agent人工整理流程辅助形成，明确AI辅助、非独立人类专家撰写或复核，不伪造专家身份。逐例H在维护前冻结；不使用oracle/参考补丁写H，来源见H.provenance.json及source-scope.json。

保留旧M交接包装以隔离变量：只机械截取四栏提取输出的第1栏，完整输出另存；不因维护结果修订或补其他栏目。提取模型gpt-6-sol/low，所有修复条件gpt-5.6-terra/medium，service_tier=priority。本轮全部10例新生成一次，复用0；旧C3可复用但本批统一新生成，不能混成本。重复修复共用同一份冻结M，M/E字节相同。提取只读候选，不挂H、评分、历史、其他运行；提取后全部M及实际修复prompt在第一份维护评分前再次冻结，不依补丁结果修订。K1原文及SHA固定，不改提取器或控制器。

实际CLI版本、二进制/后端摘要、catalog支持的模型effort、研究profile及全局配置前后SHA在frozen-config.json及各receipt。catalog可用不是实际服务成功保证，首个正式请求如拒绝即记录，不换模型。原生Codex exec，code_mode_host/shell_tool；无实验ReAct、网络搜索、插件和multi_agent。服务端tier路由不能独立认证。Node16.20.2；React例用18.17.0。只读挂现有运行时依赖，不安装包。所有研究侧配置独立，不改全局。

### 冻结预算

- 10例×4条件×2重复＝80正式维护槽位。
- 修复阶段经验，最多10次自动提取、每例一次；合计90会话，复用0，反思/judge/模型预跑/自动补跑均0。
- 每会话600秒、12次原生底层请求、最终report最多6000 Unicode字符，沿用已有验证上限。独立meter每槽12次，仅90个唯一ID各启动一次；因此总预留1080请求、54000会话秒（串行硬上限15小时）。不沿用49请求全局门。最终文本上限不是全部推理token/工具输出上限，不冒称另有已验证token硬上限。
- 粗估依据旧同模型U2有效四槽：120–172秒、9–12请求、输入144337–181260（含缓存）、输出5360–7019。提取依据U2 v2 K1：36–41秒、3请求、输入35905–35954、输出1170–1255。机械外推本批约2.8–4.0小时、750–990请求、输入约1190–1487万、输出约44–57万；不同任务、失败和服务负载会超出该观察范围，故按完整硬预留控制，不能将预估当上限。所有失败/停止也计入；缓存和reasoning为子项，不重复相加。
- 没有可靠费率／实际账单，不估货币费用。账号余量不可从本地记录认证；如服务拒绝保留原始错误并按停止规则处理，不默换账号或随机截断组。

schedule.json的种子2026110801只控制调度，不是采样种子。按case/repeat形成20块，各块交错四组，固定80槽完整顺序。可靠性优先串行（并发1，低于上限2）；每槽独立workspace/profile/meter/output，从同一base逐字复制，不共享模型上下文。总调用上限覆盖所有槽；不按质量改变规模。

首个正式维护槽验证真实成功工具输出包含原源码正文及归档完整性，计入80槽，不另加模型预跑。每个提取也存实际正文读取证据。首维护门失败即停；计量缺失或模型配置偏离立即停；连续2次基础设施异常停发新槽；评分异常停发。输出格式/交付失败与服务/工具基础设施失败分别记录；无自动补跑，无替换失败槽位。提取如不能取得全部冻结M，不启动部分不平衡维护批。保留全部部分输出及实际用量，缺失用量报告下界。后续源码与prompt不得看之前评分。

## Task 3：预先固定评价与停止规则

整体通过只取原ungranted verdict，目标行为只取metric-spec.json预选原effect的合取；逐effect及原consumer_outcomes原样保留，不用总分抵消关键退步。与冻结起点及同case/repeat N分别比较原通过项丢失、新增forbidden；区分required真/forbidden假，不能简单把false当失败。不把重复当独立案例。有效、无效、未发起分母分别报告；0有效时比率为不可评价，不能写0%成功。

实际交付报告是否有补丁、改动文件、最终答复、已执行自检、未覆盖范围。H即便PASS也逐份阅读补丁范围：接口/输入字段/token编码、相邻消费者、未决错误传播或返回值、跨活动归属的无依据变化单列，静态风险不冒称动态失败。scope-review.csv记录所有已测/未测范围和证据，不能只有关键词或文件计数。

比较H对N、M对H、E对M，并逐例、逐来源、重复块展示。其他来源9例单独统计，不称独立泛化。明确是否只帮助来源变体、是否伤害无生命周期任务。提取与经验字符/输入增量、成功/失败/停止的输入/缓存/输出/推理token、底层请求/工具/耗时均计成本。无新增LLM judge。若H也不显示增量，报告区分力或执行变化，不能据此认定自动提取成功。

批次只运行一次；全部结果保留。E只增加文字成本而没有行为收益则停止该干预；即使有个别成功也不更新生产经验库，不生成下一版或选赢家。未确认E1时可完成准备，但正式增强会话0；本批暂整体等待，避免提前形成不完整组序。最终产物明确区分准备与实际执行，不虚构轨迹、自动Contract或四组结果。

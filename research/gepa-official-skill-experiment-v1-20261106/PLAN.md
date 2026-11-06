# 官方GEPA受限适配实验（模型调用前冻结）

日期2026-11-06。目标为检验官方GEPA对当前任务分布有无增量，允许零候选接纳、无赢家、退步或执行阻塞。不以手写线性循环代替GEPA，不声称复现论文收益。全部研究内容在独立目录；不改生产prompt、分析器、AST、评分器、原题库或任何历史，不提交。

## 官方来源和方法

上游https://github.com/gepa-ai/gepa，固定commit 8e9ae9ed063f6a0259c93db595b96953fdab0e6d，包metadata版本0.1.4。在本目录.venv中从完整官方checkout构建安装，不改官方源文件，环境/包文件摘要及锁定记录另存。阅读官方论文arXiv:2507.19457v2的核心算法、Pareto选择与merge说明。

使用官方gepa.optimize、GEPAAdapter.evaluate/make_reflective_dataset、EvaluationBatch、GEPAResult与官方callbacks/stop_callbacks接口。唯一候选组件temporal_skill。保留默认官方StatelessReflectionLM、InstructionProposalSignature解析、SingleMutationSampling、AllImprovements和strict_improvement；不提供custom_candidate_proposer或自写搜索循环。pareto候选选择、instance frontier、round_robin单组件、epoch_shuffled、train minibatch=2、full_eval val、skip_perfect_score=True、perfect_score=1。通过官方reflection_prompt_template参数固定技能边界模板（非论文元prompt逐字复制），由官方反思变异器调用现有Codex callable。

merge支持但不启用（use_merge=False），本轮单一文本组件与极小预算不强开。研究档案保留官方pool、Pareto记录、父版本和所有提出但未接纳的proposal；不得因部分样本退步另行删档或替换官方接受/选择。最终K*使用官方result.best_idx：val整任务均值最大，平局取最早pool索引（包含seed K0）。检查项/断言退步与成本独立报告，不作为手写额外候选筛选或用总分掩盖整体失败。

## 固定系统、进化对象与边界

执行模型gpt-6-sol / low，600秒，workspace-write、approval never，沿用最近可信原始IsolatedWorkbench CLI自主路径和bubblewrap边界，不接入react-skill-evolution的controller、状态/修改门/Stop续行。仅加Pre/PostModelRequest被动记账，不读取工具输出、不注入上下文、不改变任务继续规则；所有执行条件相同。原CLI输出设置不新增token硬上限，默认候选Node与可信评分Node版本沿用前轮。

公共材料为原维护任务、冻结候选、同字节源码BM25/top8/12000字符与固定五题/顺序；AST各条件不交付，规则保持不变。BASE.md与END.md固定，完整执行prompt模板为 common + BASE + <temporal-contract-skill>skill</...> + END；只有skill文本可变。END要求实际维护和验证，允许有依据不修改/未完成，不强制diff，辅助问题不能替代维护目标。

K0逐字节沿用上轮初始K0（2836字符），不是未接纳K1。候选上限6000 Unicode字符，必须保持技能作用域。禁止案例ID、文件路径/名、任务程序符号、隐藏断言/oracle标识、原题专用答案及补丁代码、修改固定外围/权限/评分/结束协议。机械检查和研究侧边界复核通过后才允许真实执行；违规候选仍保存并作为无效组件向官方返回0分/0真实metric calls，不偷偷改文本或删档。不以预期效力审查候选，不人工改写。

## 按来源分区（全部已研究暴露，探索性）

train（反思/变异）：
1. transfer-progress-composition-v4-vanilla，unit transfer-retry-abort-handoff；近期诊断自主/证据各0/3，技能实验仍8/10，可信行为失败。
2. download-polling-restoration-low-cue-react18，unit download-polling-restoration；历史等待状态/生命周期失败，最近K0通过、K1退步，观察稳定性。

val（官方pool/最终选择）：
1. document-submit-snapshot-vanilla，unit debounced-submit-flush；持久flush/提交快照/回调重入，历史自主15/20，近期公共辅助+K0稳定通过。
2. feature-flag-readiness-vue3，unit feature-flag-readiness；首次就绪机制，较稳定容易任务用于观察退步。
两val不同机制，但近期均有天花板风险；不为制造赢家换题。

test（选择完成后仅最终评价）：
1. local-config-readiness-low-cue-vue2，unit local-config-readiness；历史自主及RAG条件失败，近轮又通过；困难来源但当前难度不预定。
2. listener-registration-order-vanilla，unit listener-registration-order；历史低强度自主有失败，近期源码辅助通过；事件注册机制。
3. commit-ack-boundary-vanilla，unit commit-ack-boundary；近期自主/RAG均4/4检查通过的容易任务。

核对project/source cluster及independent_unit_id，所有同源变体不跨组，来源分类和历史依据冻结于split.json。不能因为重分区称为独立测试：全部来源已研究暴露，独立泛化案例0。test材料在研究侧准备/无模型校准，但不传给GEPA/反思端；test轨迹与成绩在选择前不存在且从不回流。原任务不增造业务要求。

## 反馈与指标

单任务可信整体PASS=1.0，其他可信行为结果=0.0。执行/验证异常单列且本次不静默补跑，不称为契约失败。保存完整原始score及每次原通过检查/断言得失（条件未发出与明确false区分）、patch、实际prompt、CLI events/工具输出、用量与关联摘要。

make_reflective_dataset只接受train轨迹。反思数据含原任务、实际读取/修改位置与events引用、真实工具输出/候选可见验证、实际patch、是否交付、开发评分揭示的自然语言行为差异及未知。私有映射只在研究侧，将隐藏检查名译为有可见task/source依据的诊断描述；不传隐藏断言名称、原oracle实现/expected测试输入、参考补丁或案例答案。未压缩证据独立保留，给反思端的有界摘录显式记录截断。评分反馈不被当成新增业务规范。反思端仅见官方生成的当前技能+train诊断消息，不挂整个研究目录/val/test。

## 预算语义、缓存与恢复

优化真实维护任务执行最多24次，包含seed val、train父/子和val候选选择；模型冒烟也须计入，本轮不做模型冒烟。gepa.max_metric_calls=24，并在官方stop_callbacks中要求每个新迭代开始时至少剩6次真实任务预算（父train2+子train2+full val2的最坏情况）。evaluate在每个batch及每次真实启动前再硬检查台账；max_reflection底层请求6，test真实任务12独立台账。停止条件取先到者，不为耗尽额度继续搜；保守预留可能留下不足一轮预算。

metric call、evaluate batch次数、样本级评估、真实维护执行、Codex CLI会话、底层模型请求分别计数。EvaluationBatch.num_metric_calls按真实任务计数；拒绝的无效技能0真实执行。正常合法路径seed2，此后每迭代最多6；官方metric计数与台账对账，不靠轮数近似。官方边界检查不能单独充当硬上限。

反思沿用既有可用登录CLI配置gpt-6-sol/low，不购买服务或改付费账号；官方LanguageModel callable将完整反思消息直接交CLI，要求纯文本无工具。PreModelRequest逐底层请求计数（含重试/意外工具续轮），共享上限6；达到上限时由独立进程监督终止后续请求的CLI，而不冒称hook JSON能阻断模型请求。反思CLI调用次数和底层请求分别保存，未调用的反思额度不冒充已用。若现有反思连接实际不可用则保存阻塞/失败，停止而非切换模型。

cache_evaluation=False：任务端随机性下不复用单次分数；实际缓存命中0，所有重复执行均计预算。原始证据无缓存丢弃。官方run_dir checkpoint可恢复；本轮新目录正式运行一次，不自动恢复/补跑。离线用合成适配器验证官方resume和cache语义，任何重启必须显式验证账本/输入/代码/候选哈希，已有未完成启动按已耗额度保留，不重跑。普通本轮不计划重启。

## 最终test、调度和停止

种子2026110604只控制官方选择/抽样和最终调度，不是Codex采样种子。test预定3案例×A(K0)/B(K*)×2重复，最多12。每个rep/case配对交错，第一重复随机A/B，第二反转，案例顺序随机；全部顺序先冻结。每次全新相同起点，公共字节/权限/配置一致。不共享中间结果。

优化结束先保存官方result、完整candidate pool/parents/val向量，再冻结best_idx、K*与A/B实际输入，之后才允许test。若K*=K0，删除预定调度中B，只跑3案例×2次A基线（6次），留存其余6；不得解释同文本重复波动为优化收益。test结束不再改候选或重测。

## 离线核查及交付

模型前验证：安装版本/源哈希、原始执行与评分/归档关联、输出解析、执行失败/超时/预算守卫、候选外围边界、缓存/恢复、train/val/test隔离、公共同起点摘要；7案例原样/参考14次无模型校准。合成GEPA运行明确无真实模型/任务，不计正式预算且不能称实证。反思边界审查只决定安全/合规，不替代官方性能选择。

保存PLAN、环境锁/安装记录、官方完整源、适配器、离线测试、split/来源、K0/所有proposals/official pool/parents/K*、全部prompt/轨迹/patch/可信评分/usage、metric与真实执行台账、开发/val曲线、cache/异常、summary/REPORT及建议commit信息。最终回答：是否真正运行官方候选搜索/反馈优化；在所定分布/预算内是否优于冻结K0及其证据/全成本。小样本和预算不足、val/test天花板、反馈与适配限制均允许未知，不作因果或普遍泛化结论。

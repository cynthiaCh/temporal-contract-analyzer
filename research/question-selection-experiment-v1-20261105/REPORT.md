# 自动选题：减少材料，但未观察到修复收益

24次全部完成，S/F/R整体通过均8/8；原通过项丢失均0/8。**不能据此认定R优于F或S的修复效果。** 本轮全部为探索来源，无认证独立案例；S已达通过上限。

**协议偏差须保留：** 交接案例查询含`package.json`的fixture名称，`reentrancy`贡献了词法得分，违反“不把案例名作为选题依据”的输入卫生要求。调用前检查漏掉该名称变体。保留原prompt、查询、得分与结果，不改检索器、不补跑。事后仅屏蔽包名时003得分由7.716降为5.439，仍过冻结门槛并选中同一题；这不能追认原查询合规。[偏差及完整敏感性记录](protocol-deviation.json)。以下同时保留24次全量与排除此例的18次结果，不能把排除后的3个案例当作独立泛化测试。

全量R相对F：交付题数40→10（-75%），初始prompt UTF-8字节111974→52590（-53.0%），累计输入token 1012016→915990（-9.49%），输出token 10737→10311（-3.97%），累计模型秒 472.579→432.673（-8.44%）。这些是含缓存、多轮读源码的观察用量，不是费用或稳定速度结论。

## 全量24次结果

记录 24/24；可信评分 24。4个案例，每条件2次。独立泛化案例0；不作统计显著性主张。

|条件|整体通过/评分（计划8）|必需检查（辅助）|原通过项丢失的调用|输入token|输出token|模型秒|交付题数|
|---|---:|---:|---:|---:|---:|---:|---:|
|S|8/8|78/78|0/8|978359|11277|474.806|0|
|F|8/8|78/78|0/8|1012016|10737|472.579|40|
|R|8/8|78/78|0/8|915990|10311|432.673|10|

S=同源码RAG；F=S+全部5题；R=S+自动0—2题。token含模型额外读源码的累计输入，不是初始prompt长度或费用。

|案例|S整体；必需项每次|F整体；必需项每次|R整体；必需项每次|R选题|
|---|---|---|---|---|
|listener-registration-order-vanilla|2/2；8/8, 8/8|2/2；8/8, 8/8|2/2；8/8, 8/8|TCQ-001, TCQ-003|
|document-submit-snapshot-vanilla|2/2；20/20, 20/20|2/2；20/20, 20/20|2/2；20/20, 20/20|TCQ-003, TCQ-004|
|handoff-redirect-reentrancy-vanilla|2/2；7/7, 7/7|2/2；7/7, 7/7|2/2；7/7, 7/7|TCQ-003|
|feature-flag-readiness-vue3|2/2；4/4, 4/4|2/2；4/4, 4/4|2/2；4/4, 4/4|0条|

## 检索先验审查

selection-review.json在首个正式调用前冻结。研究Agent审查，不冒称独立人工盲审。监听漏002、草稿漏005；交接003完整，负案例拒绝返回。入选5个题目-案例关系全部判适用（5/5）；适用关系召回5/7；完全覆盖2/4案例（包括负案例）。F无关13/20题目-案例关系，R为0/5；两次重复不重复算新相关性样本。这些标签为研究审查，非普遍真值。

全量分数、贡献、阈值/拒绝原因和查询见每次question-retrieval.json；完整交付prompt、events.jsonl、changes.json和原始评分路径见runs.json、trajectory-evidence.json、raw-vectors.json。

## 解释边界

校准4/4 reference PASS、4/4 unchanged UNDERREACH。运行器mock测试16/16；首次系统Python3.8不符评分测试版本要求的2项失败及修正环境记录于runner-validation.md。执行失败和验证异常独立记录audit.json；不补跑。

源码检索字节复用上一轮研究实现；生产分析器/评分器、原题库、历史档案未改。随机种子2026110502只控制调度，模型无可控采样种子。R返回0时仍收到同一条件声明。workspace-write继承原配置，不是严格读隔离；显式受限路径命令检查不构成无泄漏证明。


## 排除包名偏差案例后的结果

|条件|整体通过|必需项（辅助）|原通过项丢失调用|输入token|输出token|模型秒|交付题数|
|---|---:|---:|---:|---:|---:|---:|---:|
|S|6/6|64/64|0/6|795698|9125|376.068|0|
|F|6/6|64/64|0/6|827451|8609|364.426|30|
|R|6/6|64/64|0/6|748951|8101|338.724|8|

排除后R相对F输入token变化-9.49%，输出-5.9%，模型秒-7.05%，交付题数-73.33%；每组整体仍6/6，无行为增量。选题审查剩余4/4入选关系适用、召回4/6；F无关9/15，R无关0/4。

## 五个分析问题与实际证据

1. **R相对F减少无关题目与材料。** 冻结的先验审查中，全量无关关系13/20→0/5；去除偏差后9/15→0/4。全量累计输入/输出/模型时间均较低，18次子集见上表。运行准备时为可比归档，S/F也计算了题库检索但不使用其选择；不能把这部分记录误算成F必须承担的检索开销。R八份题库查询合计约16.03毫秒，平均约2.00毫秒；源码检索逐次耗时见source-retrieval.json。

2. **R相对S未增加整体成功或降低退步。** 全量8/8对8/8、原通过项丢失0/8对0/8；排除后6/6对6/6。R对S、对F的8个同block配对均为整体平局，不能将8次视作8个新案例。stable_S_check_losses同样为空。S的成功上限使本轮不能辨别潜在修复收益。

3. **漏选监听002、草稿005；未观察到误选题目，但有输入卫生偏差。** 两题在top-k/门槛处落选的完整分数及理由见question-retrieval.json。监听002仅命中2个英文词、得分4.77，未达到3词且5分门槛；草稿005得分10.52，满足门槛但位列003/004之后。监听和草稿实际上各有3题适用，top2上限本身造成必然漏选风险。交接包名影响得分单独披露；不能只凭入选题相关就视检索完全合格。

4. **适用题目收到后确实核查了相关代码，仍没有相对S的通过增量。** 监听R1在轨迹第7行cat全部src，第12行测试同步/延迟首次事件及重入切换，第14行测试旧decode完成；补丁调整注册顺序与panel访问/清理保护，可信评分8/8。它甚至核查了未检索中的002机制，因此不能把漏选直接等同修复失败。监听R2第7/12行有相应读代码及测试，亦8/8。

[prompt](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/jobs/j-001/prompt.md)；[轨迹](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/jobs/j-001/events.jsonl)；[补丁](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/jobs/j-001/changes.json)；[评分](trials/lane0/reports-experiments/e-6bcfa862f92b43aa/evaluations/v-ab32f43af9964344/j-001/oracle/stdout.json)

草稿R1第7/9行读取editor/workspace/trailing-task及README，第16行执行静默期、close/submit结算和回调导航测试；补丁新增flush及visit归属检查，可信评分20/20。草稿R2第7/14行有相应读代码及测试，亦20/20。尽管漏005，两次仍自行实现flush；同block S也都20/20。这是轨迹和补丁事实，不能归因于问句。

[prompt](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/jobs/j-001/prompt.md)；[轨迹](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/jobs/j-001/events.jsonl)；[补丁](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/jobs/j-001/changes.json)；[评分](trials/lane1/reports-experiments/e-0ee7fc5f3bae4217/evaluations/v-3fd78360ea404359/j-001/oracle/stdout.json)

交接R两次均实际rg阅读open/retire/onHandoff，并执行回调内导航/关闭测试，补丁增加请求代际保护，评分各7/7；因包名偏差只作辅助展示。全部6份R适用运行的读取与可执行核查行号见[EVIDENCE.md](EVIDENCE.md)，完整命令输出见[trajectory-evidence.json](trajectory-evidence.json)。

5. **未观察到问题诱导的越界行为变化。** 负案例六份补丁均只改src/temporal-flow.js中的runTarget；runAdjacent源码逐字保留，其他文件未改，评分各4/4且禁止效果0。S/R第一次补丁字节相同；F第一次使用不同的局部变量形式，但同样仅等待loadedFlag，未引入持久化、监听或额外生命周期要求。六次都通过有界oracle不能证明所有可能输入行为等价；这里没有把格式差异称作诱导的业务变更。

负案例F1：[prompt](trials/lane2/reports-experiments/e-33895ad58f154b19/jobs/j-001/prompt.md)；[轨迹](trials/lane2/reports-experiments/e-33895ad58f154b19/jobs/j-001/events.jsonl)；[补丁](trials/lane2/reports-experiments/e-33895ad58f154b19/jobs/j-001/changes.json)；[评分](trials/lane2/reports-experiments/e-33895ad58f154b19/evaluations/v-c5e9ad8e7eac4616/j-001/oracle/stdout.json)

负案例R1：[prompt](trials/lane1/reports-experiments/e-62757bdff6b94ad3/jobs/j-001/prompt.md)；[轨迹](trials/lane1/reports-experiments/e-62757bdff6b94ad3/jobs/j-001/events.jsonl)；[补丁](trials/lane1/reports-experiments/e-62757bdff6b94ad3/jobs/j-001/changes.json)；[评分](trials/lane1/reports-experiments/e-62757bdff6b94ad3/evaluations/v-6af161fdb6a74c1e/j-001/oracle/stdout.json)

上述范围审核及摘要见[evidence-review.json](evidence-review.json)。归档events中的shell启动偶有本机fsl路径缺失提示，相关命令退出码仍为0；不将其当作模型执行失败或可信评分异常。

## Task 1 / 2 / 3 交付与实际工作量

|任务|范围与文件|技术点与验证|实际工作量|
|---|---|---|---|
|Task 1|[PLAN.md](PLAN.md)、[prior-audit.json](prior-audit.json)、protocol.cases、calibration.json|核对上轮脚本/配置/真实prompt；区分自动top2与全量；审查谱系并沿用评分标准|核对上轮24份prompt摘要，其中6份RQ逐条ID；4个入选案例来源审查，4×2=8次无模型校准|
|Task 2|[retriever.py](retriever.py)、[offline_check.py](offline_check.py)、[preflight.py](preflight.py)、[selection-review.json](selection-review.json)、protocol.json|标准库加权BM25，0—2题、解释贡献/拒绝原因；同格式与同源码字节；调用前审查/冻结|6个离线查询（3开发、3合成）；24份prompt/命令检查；16项mock测试通过（首轮2项环境失败另记）；5题索引，无新依赖|
|Task 3|[run.py](run.py)、[analyze.py](analyze.py)、[finalize.py](finalize.py)、runs/results/summary.json、EVIDENCE.md、trials/|同冻结起点、8个交错block、24独立工作区；原始oracle/候选字节审计；轨迹/补丁核对；偏差透明报告|24/24正式运行与24份可信评分；0补跑/0追加；6份R适用轨迹及6份负案例补丁范围核对；1次事后纯离线包名屏蔽敏感性|

## 投入判断

本轮支持“自动选择可压缩交付材料”这一描述，尚不支持“选择问题提升修复能力”。两处漏选、一个输入卫生偏差、S表现饱和及全部探索来源降低了继续投入修复效果优化的依据。本轮不扩大规模、不接入生产、不以成功率证明有效；若以后另行立项，应先解决元数据卫生及独立且未饱和的可信任务来源。

原生产代码、题库和历史冻结材料及上轮24份prompt摘要均复核未变；未创建Git提交。计划、模型与调度配置、完整查询/打分/提示/轨迹/补丁/评分/摘要均在本目录。机械审计通过不等于协议完全合规，见audit.json。

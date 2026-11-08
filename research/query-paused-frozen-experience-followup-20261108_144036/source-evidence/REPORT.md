# 初始暂停查询：同题经验实验 / Terra low

## Task 1：来源、评价和工具预检

本批在用户查阅历史并回复“do”后独立执行。初始HEAD `07b7cdcdec0dd8caf016be8f8d67378c83c53156`，tracked diff为空；此前研究目录已由外部状态纳入新HEAD，本轮不创建提交或改写历史。未发现适用的额外AGENTS.md。

唯一case `query-paused-initial-fetch-10266-vanilla` 从实际cluster登记解析。旧low L/G/C原件分别为25/29、26/29、28/29，都是不同提示条件各一次，不是同条件三次重复。当前4个候选文件、12个oracle文件、任务及manifest与旧批冻结摘要对应；历史仅作选题线索，不给actor、不充当本批基线。

policy-review.md按原任务、README及src/session.js区分首次尚未进入请求的pending+paused、已开始的未消费工作、已消费工作、已有缓存刷新及query/attempt所有权；取消既要阻止无效未来调用，也要结算来源attempt并恢复先前状态。保留原有多观察者、惰性signal读取、network/focus/retry、代际结果及依赖配置。AI辅助核查不伪造人工批准，也不声称整个上游库等价。

M1零模型校准共10项：bounded/expanded两个有效参考均PASS，原始候选与7个退化变体均UNDERREACH，无runtimeError。本例无授权扩展区分，两个参考均通过不视为异常。所有原29项评分及scope-baseline保持不变。固定Python归档运行器15项离线检查、当前JS源码正文读取、只读/可写namespace、host归档隐藏、RPC账本与code_mode_host/shell工具检查通过。评分所用既有esbuild/jsdom及相关锁文件/入口摘要另外冻结，没有安装依赖。

维护所有组gpt-5.6-terra/low，提取gpt-6-sol/low，反思gpt-5.6-terra/medium；实际Node与声明一致为v16.20.2。并发1，每会话600秒，维护24请求、提取/反思12请求，总上限12会话264请求。CLI/config声明effort，hook核对型号及请求，不宣称独立认证服务端路由/effort。业务补丁只在独立工作区发生，归档由Python执行，执行环境不挂评分、历史、参考、其他槽位或host归档目录。

## Task 2：实际执行与经验接纳

停止/完成原因：**一次反思未找到可接纳同题经验**。

- AUTO开发基线：0/2整体通过，另有0无效。
- AUTO_EXP训练回验：1/2整体通过，另有0无效。

自动Contract仅提取一次，按既有栏目机械截取，完整原报告另存；不依据标准手工修正。所有维护会话均从相同原始候选开始，无会话/补丁/工具状态继承。

仅一次Reflection产生NEW_EXPERIENCE.md，原输出及摘要独立保存，不手工润色、不更新生产经验库。反馈仅含本批基线的源绑定差异、保留要求、必要实际结果；完整标准和参考补丁留评价侧。reflection-input与feedback-freeze归档。

经验接纳：**未通过**。接纳依据为反思前PLAN固定的目标关系实际改善、原正确行为保留、无无据策略及实际查证/落实，不以报告长短判定。完整对应重复差异见acceptance.json与experience-evidence.json；无模型采样种子相同的主张。

各组只有是否追加冻结经验这一输入差异；模型/effort、工具、输出、时间与请求预算相同。调度种子20261108只控制交错顺序。正式开始后不再改经验/Contract/评分，结束后统一分析，正式反馈不再用于演化。开发运行不混入正式分母。

本批具体观察：两次AUTO均为26/29行为项通过，均未修复首次暂停收尾，并误挡两项缓存刷新。一次经验的两次回验均修好了这三项预定目标：第一轮27/29，第二轮29/29并整体PASS。因此开发整体通过从0/2变为1/2，确有目标层面的实际补丁改善；没有把这个开发差异当正式验证增益。

未接纳的具体原因：第一轮回验把原来的共享查询级消费记录移到单次attempt上，删除query记录并让旧context的访问仅标记旧attempt，新增cached-prior-consumed-success与retained-context-query-flag两项保留失败。第二轮保留query级记录及原context getter，修复后全过。对应repeat1有明确已过→未过，违反反思前固定的无保留损失条件；不能因repeat2成功而删掉repeat1、放宽条件或追加一轮反思。scope-review与experience-evidence记录了源码位置、原始观察和自验证事件。

这次没有遇到基线天花板；新经验帮助模型修复了原失败关系，但尚未证明在本设置下能无损地使用经验。经验文本对不同生命周期作了区分，第一轮执行仍改变了消费事实的所有权；现有数据不足以把该改动直接归因于某一句经验。下一步若另立协议，可针对共享查询事实与attempt私有状态的归属做更具体的经验表达与保留验证；本批不改写经验或继续运行。

## Task 3：观察结果、成本和限制

首要正式结果：

|组|整体通过|有效|无效|已启动/预留|
|---|---:|---:|---:|---:|
|AUTO|0|0|0|0/3|
|AUTO_EXP|0|0|0|0/3|

逐项行为/断言向量在behavior-vectors.json，完整原始评分在runs/<slot>/archive/score/stdout.json；下表只列未通过行为，不将29个耦合检查当29个独立案例：

|槽位|组|判定|未通过行为|原已过required损失|
|---|---|---|---|---|
|base-1|AUTO|UNDERREACH|offline-nonconsuming-detach, cached-paused-background, cached-later-consumption|cached-paused-background, cached-later-consumption|
|base-2|AUTO|UNDERREACH|offline-nonconsuming-detach, cached-paused-background, cached-later-consumption|cached-paused-background, cached-later-consumption|
|reval-1|AUTO_EXP|UNDERREACH|cached-prior-consumed-success, retained-context-query-flag|cached-prior-consumed-success, retained-context-query-flag|
|reval-2|AUTO_EXP|PASS|||

源码范围、额外文件及经验实际查证记录见scope-review.json。原始缺陷、补丁新增保留项损失与未知政策分开记录；额外文件保留，不按后缀清理。

所有阶段计量如下。input/output含缓存/推理子项，不重复相加；失败与取消请求也计入started，缺失用量为未知，不补零。

|阶段|会话|请求started/completed|工具|会话秒|input tokens|output tokens|
|---|---:|---:|---:|---:|---:|---:|
|M1离线|0模型|0/0|0模型工具|校准9.47秒，其他本地准备未独立计量|0模型|0模型|
|M2_extraction|1|3/3|2|34.19|35569|1420|
|M2_AUTO_development|2|14/14|12|189.80|183529|6725|
|M3_reflection|1|1/1|0|20.87|16056|573|
|M3_revalidation|2|15/15|13|227.65|220115|9069|
|M4_formal|0|0/0|0|0.00|0|0|
|合计|6|33/33|27|472.51|455269|17787|

Cached input=358784；reasoning output=6183；未发送的超限dispatch=0；未知模型用量会话=[]。主聊天准备/分析用量不可从实验hook取得，单列未知；未核验价格，不估货币成本。阶段详情与工具流均可复核。

正式证据未完整形成，不估计正式经验收益，不将未启动槽位记作失败。

边界：训练是经验文本更新，没有模型权重更新，没有官方GEPA或搜索。案例是已暴露合成派生表示；反馈与正式题目相同，存在同题学习信息，不能宣称未见测试。后续若继续须另立协议；本批不补跑、不换case/effort、不二次反思、不恢复旧调度器。

未启动槽位：final-1-AUTO, final-1-AUTO_EXP, final-2-AUTO, final-2-AUTO_EXP, final-3-AUTO_EXP, final-3-AUTO。

完整性记录在integrity-validation.json；输入/实现/评价冻结见protocol.json，所有归档摘要见ARTIFACTS.sha256。历史、生产、原案例及全局配置摘要保持不变；没有创建提交。

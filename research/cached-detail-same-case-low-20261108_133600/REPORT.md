# cached-detail 同题经验实验：Terra low 开发筛查

## Task 1：来源、评价和工具预检

用户在同题开发/冻结后验证方案后授权“do”。本批独立目录，HEAD `40919fb9f33f2336a581c7d013d4d5d888505387`，起始tracked diff为空，保留已有两个未跟踪研究目录。无适用的额外AGENTS.md。

唯一case `cached-detail-activation-vanilla`，从服务器reentrant-lifecycle-handoff/cluster.json的arm.path解析。原任务/候选/manifest/oracle完整复制并SHA冻结。候选可见任务、README及repository注释支持缓存必须在open内显示、当前activation继续network、每次同key打开是新activation、最新导航优先、迟到handle归原activation并在退役时释放，以及compliance/preview不同策略。policy-review.md是AI辅助核查，不伪造人工批准，也不用参考通过反推政策。

原始、bounded、expanded与6个mutants，共9项离线校准符合预期：仅bounded整体PASS，其余正确触发原ungranted规则。校准不计模型修复结果。15项固定Python归档运行器离线测试通过；当前案例5份JS源码正文逐行读取、readonly、host archive/output/meter隐藏、guard RPC、code_mode_host和shell工具可用性检查通过。首次预检的文件数硬编码断言已在首个模型调用前修正为实际清单核对，失败证据保留。

维护配置固定gpt-5.6-terra/low，提取gpt-6-sol/low，一次反思预留gpt-5.6-terra/medium。CLI/config给出effort声明，真实hook核对型号与每次请求；不宣称独立认证服务器effort或路由。声明Node v16.20.2，实际全批统一v18.17.0，两者分开记录。并发1，维护24请求、提取/反思12请求，每会话600秒；最高12会话264底层请求。没有安装依赖、修改全局配置或生产代码，没有创建提交。

## Task 2：实际执行与停止

**执行至M2，停止：AUTO开发基线2/2整体通过，本次未观察到同题经验提升空间。**

一次K1自动Contract有效提取，原报告与栏目1机械交付分别保存，未根据标准答案人工修改。两次AUTO从同一原始候选独立创建工作区，使用相同任务/Contract、low参数、工具和资源上限，没有继承会话或补丁。

|开发槽位|有效性|官方评分|归档|业务改动|额外文件|
|---|---|---|---|---|---|
|base-1|有效|PASS|OK|src/detail-panel.js|无|
|base-2|有效|PASS|OK|src/detail-panel.js|无|

两次都建立/选中activation再调用可能同步回调的prefer-cache订阅，使用对象身份守卫当前发布，并释放归属已退役activation的迟到handle；合规与预览源码未改动。两轮都执行内联断言和语法检查，实际命令与输出见runs各archive。源码审查未发现无据策略扩展；这只是AI辅助核查与当前评分覆盖内结论。

Python独立保存原始/最终快照、实际prompt、事件/工具输出/stderr、raw answer、账本、patch.diff和评分。两轮未创建模型归档副本或patch目录，宿主归档不挂给模型；不据不同case/effort/输入的历史运行推断节省了多少请求。

停止后没有反思、没有新经验、没有训练回验，也没有正式AUTO/AUTO_EXP对照。未启动9个预留槽位：反思1、回验2、正式6。没有补跑、替换案例或改effort继续找结果。

## Task 3：观察结果、成本和限制

首要正式结果：两组均未启动，不能把开发2/2混入正式分母。

|正式组|通过|有效|无效|未启动|
|---|---:|---:|---:|---:|
|AUTO|0|0|0|3|
|AUTO_EXP|0|0|0|3|

本批无可估计的经验增益，也不是经验组失败。它提供的是：该案例在当前固定自动Contract+Terra low条件下，观察到两次完整修复，缺少本轮经验开发所需的失败反馈。小样本不能证明永远没有提升空间，不能推广到其他case或medium设置。

逐项行为向量见behavior-vectors.json，完整断言/轨迹见每轮archive/score/stdout.json。两轮14个required effects全部true，禁止的preview-cache-migrated为false。共同存在的原已过断言没有true→false；部分旧断言只在原始无cache路径的条件分支出现，新正确cache路径不再生成，单列为absent而不伪称行为丢失。这里没有进行经验接纳判断。

|阶段|模型会话|底层请求|工具调用|模型会话秒|input tokens|output tokens|
|---|---:|---:|---:|---:|---:|---:|
|M1离线预检|0|0|0模型工具|非模型校准7.85秒，其余准备时间未独立计量|0模型|0模型|
|M2_extraction|1|3|2|39.59|35578|1931|
|M2_AUTO_development|2|13|11|154.70|167004|5779|
|M3_reflection|0|0|0|0.00|0|0|
|M3_revalidation|0|0|0|0.00|0|0|
|M4_formal|0|0|0|0.00|0|0|
|模型阶段合计|3|16|13|194.29|202582|7710|

全部16次底层请求均有完成hook与用量，无失败/取消/超限调度；permission events=0，完成shell命令11次。Cached input=158976、reasoning output=1686，是各自input/output子项，不重复相加；cache-write=0。未知模型用量会话为空。主聊天准备/分析用量及未测的本地编排时间未知，不补零；未核验单价，不报货币成本。完整分阶段计量见summary.json与各archive/usage.json。

限制与下一步：同题、作者构造且已暴露，未来即便有经验增益也只能称同题开发收益。本次不产生新经验，也不检验跨case或跨语言迁移。若继续研究，需要另立协议选择有集中失败证据的候选，或明确研究其他设置；本批不自动换case、降低effort或追加调用。

完整性验证见integrity-validation.json，冻结协议见protocol.json与protocol.sha256，全部文件摘要见ARTIFACTS.sha256。历史/生产/案例/全局配置的保护摘要均不变。

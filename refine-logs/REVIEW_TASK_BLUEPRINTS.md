# 六个定向审查任务蓝图

状态：计划，未采集回答、未冻结gold。T编号对应中性候选快照；variant来源仅在 `tasks-analyst-only.json` 中供研究者核查，不提供给参与者。

所有条件都获得同样的源码、以下共同要求和情境。它们是**给定要求下的代码审查**，不用于宣称工具自动发现了隐含要求。每题10分钟，每题三个固定情境问题；每个情境作答：当前代码满足/违反/证据不足，关键身份和保护依据在哪里，还缺什么证据。要求政策的复述本身不算充分证据。

## T01：登记、接收与访问归属

共同要求：presence应接收合法bootstrap；metrics保持只计live delta；退休visit不能继续接收新工作；已经接受的异步结果按其消费者要求处理；同步通知可能触发新导航。

1. connect可能同步发bootstrap：presence与metrics是否都保持各自规定的行为？找出登记、触发与消费者调用位置。
2. 在监听仍有效时已开始decode，随后关闭并重用同一channel：旧结果是否可能发布给新visit？哪些身份检查约束它？
3. bootstrap回调内再次select/hide：外层返回后，哪个订阅与cleanup仍被保存？引用重入调用和赋值的关系。

重点源码：`subscription.js`、`presence-panel.js`、`metrics-consumer.js`、`channel.js`、`workspace-navigation.js`。工具不能从“channel相同”自动判定“visit相同”。

## T02：已接受提交与旧访问通知

共同要求：提交保留入口所属文档和文本；同步save回调可以导航；已接受receipt应保留；旧visit的提交展示应抑制；新visit仍可正常操作。

1. submit中flush可能同步导航到另一个文档：receipt捕获的doc/text来自哪里，是否仍符合入口归属？
2. 回调关闭后重新打开同一document：renderSubmission的检查能否区分旧visit与新visit？
3. 若只因访问退休就停止archive.capture，会违反什么要求？现有代码中记录与UI是否受到不同控制？

重点源码：`workspace.js`、`editor.js`、`draft-store.js`、`save-status.js`、`receipt-archive.js`。同一文档key不自动等于同次访问；capture和显示分别分析。

## T03：前台与后台准备

共同要求：前台关闭/重开应使旧前台工作不再更新当前对话框；后台任务由workspace拥有，应按其任务协议继续；pending准备仍需正常重试。

1. 前台请求未完成时close，再reopen复用token：回调中哪些状态仍属于原始工作？现有保护覆盖什么？
2. 对共享逻辑加“关闭即停止所有工作”会不会改变后台消费者？指出前后台的调用入口与所有权证据。
3. 取消timer是否也约束已经开始的请求完成或下一次retry？如果代码/模型无法建立连接，明确指出缺口。

重点源码：`usePreparation.js`、`DownloadDialog.jsx`、`BackgroundExportPanel.jsx`及实际候选中存在的相关模块。React调度不被静态报告自动证明。

## T04：异步迭代的清理完成

共同要求：first_match拥有传入的generator；返回结果或退出前需完成该资源的异步清理，保留原结果/原异常/取消语义。

1. 找到匹配行提前返回：当前路径是否先完成必要关闭？调用close与await其完成有什么区别？
2. predicate抛错或迭代出错：异常离开前的资源路径是否具有足够源码依据？
3. 取消发生时清理可能暂停：当前结构如何约束退出与清理完成？证据不足时不要从finally或close名称推断正确。

重点源码：`src/workflow.py`及任务给定的generator协议。要求来自共同任务；“函数拥有资源”不由工具规则命中自动成立。

## T05：新接收与已接受历史

共同要求：退休visit不得开始接受新progress工作；退休前已接受的工作仍应完成历史记录；旧UI不得更新；更晚的合法visit不受影响。

1. close先发生，新event后到达：是否在decode/record前阻止新接收？引用检查的实际位置。
2. event先接受，decode未完成时close，随后decode完成：record与receive各自应怎样处理，当前代码是否满足？
3. 同一file/feed被重新打开：代码用的identity是否足以区分visit与attempt？若无法恢复，指出缺少的连接。

重点源码：`progress.js`、`panel.js`、`transfer.js`、`workspace.js`与关联调用。**同一个record调用在前两个情境中有不同要求**；不能只按effect给一个continue/stop标签。

## T06：API发布与父组件使用

共同要求：本地配置优化不能丢失parent values；只有实际可用的form API才能被命令式调用，或通过既有声明式hydration保留值；相邻组件不作未授权迁移。

1. 本地配置立即可用，而子组件稍后发布API：父组件的setValue调用是否处在API可用之后？
2. 父组件只额外等待一个Promise microtask：这是否足以建立与实际API发布的关系？哪些候选代码能支持或反驳？
3. form/访问复用：值所属parent与当前API如何关联？原工具parsed且零finding能说明什么、不能说明什么？

重点源码：`PersonnelEditor.vue`、`SchemaForm.vue`和候选提供的相关服务/组件文件。该任务保留模型覆盖不足，不能因为U也困难就结果后删除。

## 统一评分约束

- 上述每个情境形成一个question，共18个question类型；12人每人完成6题是72份task answer，最多216份情境回答，**不是216个独立样本**。
- 主要终点要求正确情境判断与足够源码证据同时成立，不能靠复述共同规范或回答所有unknown拿分。
- 每个question的准确答案、可接受替代证据和确实未知的部分，需两名独立复核者结合完整物化代码及原scorer验证后冻结。当前不生成假gold。
- 不能凭控制版本名宣称某题必过；有些快照只实现部分维护目标，必须限定当前题目的范围并保留不足。
- 参与者提供任何说明性问题的答复必须统一记录，并按事先规则同等提供给其他条件；不能私下给U额外解释。

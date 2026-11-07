你只做一次提取技能的开发期反思，不执行工具，不修改外围任务、权限、输出协议或评价规则。
下面仅提供本批次两份有效基线、冻结评价规则和AI代理差异反馈；不得使用上批无效输出。

<K0>
# Contract 提取技能 K0

从原任务、候选文档和相关源码中寻找行为要求，区分当前实现事实与应满足的义务。
逐条写明适用条件、相关身份或生命周期，以及必须发生、禁止发生或应保留的效果。
引用可检查的来源，说明来源是否足以支持要求；不要把标识符或现有实现自动当成业务规范。
对于证据不足的要求列为候选或待确认，说明缺少什么；不编造协议、额外政策或唯一实现。
建议验证应对准条件和可观察效果，明确仍不能据此确认的事项，不把建议当作已经验证。

</K0>
<evaluation-rules>
item_id,eligibility,source_mapping_id,source,sufficiency,trigger,effect,acceptable_equivalence,unresolved,judgment_rule,dimensions,status_vocabulary
O1,可评价：任务义务,O1,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:69 「| R1 | pending 继续检查，ready 才交付 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/prompts/maintenance-core.md:3 「The preparation service can now report that a file is still pending before it becomes ready.」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/preparation-api.js:10 「function schedulePreparationRetry」,原task直接规定 keeps checking pending preparation；状态具体值未提供。,pending且尚未ready,持续检查至ready,表达同一准备活动可跨多次检查，不能因一次pending结束,状态具体编码、间隔、上限、错误协议未知,不得将假值/字符串/对象形状强行选为唯一；可把缺少重试作为当前实现事实。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足
O2,仅评价可恢复事实和未知；不扣未猜中loading=true,O2,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:70 「| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:78 「loading` 是否必须独自表示整个过程；是否允许由 loading 与 retryScheduled 组合表达等待」,源码把loading写到data-loading，相邻后台pending不清loading；仅是线索，task未定义全区间。标准确认的是等待状态，并明确允许字段组合未知，不能等价为loading唯一表达。,单次请求结束到下一次检查之间,已确认R2等待意图存在；当前输入不足以唯一规定字段期间,追踪loading消费者并区分请求/活动等待；不足时列候选,loading是否必须独自表达整体等待未知，不能把标准R2隐藏输入强加,区分当前回调清loading事实与业务义务。把全程loading=true列确定Contract为无依据新增。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足
O3,可评价：任务义务,O3,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:69 「| R1 | pending 继续检查，ready 才交付 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:70 「| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/prompts/maintenance-core.md:3 「The preparation service can now report that a file is still pending before it becomes ready.」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」,task仅ready后交付直接支持；completed作为项目可见效果，真实文件消费者未提供。,准备尚未ready，包括pending或等待下次检查,禁止交付完成,仅ready后交付；completed是真实可见记录，实际下载消费者未知,状态schema和completed等同真实下载未知,不得把status任意真值当ready规范；检查“only after”方向。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足
O4,单列timer边界：只评价源码关系、条件和未知,O4,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:33 「state.current.visible = false;」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/preparation-api.js:10 「function schedulePreparationRetry」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」,API提供调度/取消，原close只隐藏；没有直接前台取消政策。R3要求明确关闭后续工作，未独立列出已排队timer边界。,假设已排队retry时关闭；明确所属消费者和版本,本轮不规定必须取消；须区分存在性、取消位置、可能继续、接口未知,原前台未接入timer；后台pending排队，close只隐藏，卸载取消；若宿主保持挂载、调度可触发则可能再检查,前台未来轮询关闭政策未知；注入scheduler取消/同步保证未知；不得把条件性场景说成已运行或必然缺陷,T1:是否存在待执行retry及对象；T2:取消入口和实际调用位置；T3:关闭后可能检查的条件；T4:缺失宿主/接口证据。只列close测试不算完整；不要求判必须取消。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足
O5,仅评价事实和未知,O5,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:33 「state.current.visible = false;」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」,原close只隐藏，无guard；可恢复行为风险，不能仅据此确定必须丢弃已接纳结果。标准R3禁止错误影响，但具体关闭政策仍未知。,前台close后旧请求返回,防止错误影响为已确认目标，当前输入未完整定义丢弃政策,指出close只隐藏、原回调无生命周期检查；把必须丢弃所有旧结果列待确认,关闭是否取消活动/已接纳完成政策未知，多请求未定义,不能把原实现无守卫直接写成已确认取消要求，不能套后台政策。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足
O6,仅评价事实和未知,O6,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」,源码reopen更换token并检查，旧回调写共享状态；可发现交错风险，但新代政策未由task明示。同token代隔离不能从token字段猜出。,reopen改token并检查时旧请求未完成,可确认共享状态交错风险，具体新代规范待确认,区分请求捕获token和当前共享状态，旧回调未守卫；代隔离作为候选要求,同token重开、结果归属产品政策未知,不得以变量名推导唯一generation实现，未给定要求不能猜。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足
O7,仅评价当前后台行为与政策来源,O7,research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:36 「| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:90 「| A5 | 区分前台访问、旧回调与后台组件的政策 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/BackgroundExportPanel.jsx:38 「close = () => this.setState({ visible: false });」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:36 「| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」,BackgroundExportPanel源码close只隐藏、卸载才清理，直接支持当前行为应先分开考察；workspace-owned产品定义与授权例外不在候选task/源码中。,后台面板关闭且仍挂载，或卸载,事实：隐藏与停止分开；不把workspace-owned及授权例外要求模型恢复,源码close隐藏，active/取消在卸载；前后台政策各自核对,workspace所有权和授权迁移不是候选输入，完整宿主挂载未知,把当前行为称既定产品必须保留须有任务/文档依据；不得凭后台做法制定前台规范。,覆盖／语义方向／来源准确／无依据新增／未知处理,完整覆盖／部分覆盖／未覆盖／证据不足；正确／错误／不适用；有／无／证据不足

</evaluation-rules>
<baseline-outputs>
{
  "k0-1": "1. 可确认的 Contract\n原任务明确要求：下载对话框在文件准备状态为 pending 时继续检查；只有状态为 ready 后才交付文件。这里的 pending、ready 是原任务给出的语义，候选源码没有定义其具体返回格式。\n\n2. 每条的条件、效果、来源及依据\n- 条件：下载对话框已发起某文件的准备检查，服务报告 pending。效果：继续检查该文件的准备状态，不能因 pending 交付文件。依据：原任务背景直接提出“keeps checking pending preparation”。相关入口为 `DownloadDialog` 使用 `usePreparation(token)` 并暴露其操作：[src/DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:6)、[src/DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:8)；检查调用位于 [src/usePreparation.js](/workspace/src/usePreparation.js:18)。源码仅定位责任位置，不能单独证明该业务要求。\n- 条件：服务报告 ready。效果：此后才交付对应文件。依据：原任务背景直接提出“delivers the file only after a ready status”。当前实现事实：检查结果只按真值写入 `completed`，没有可见的文件交付操作：[src/usePreparation.js](/workspace/src/usePreparation.js:23)、[src/usePreparation.js](/workspace/src/usePreparation.js:25)。`completed` 的业务含义及交付机制未由源码确认。\n\n3. 不能确认的候选要求\n- 状态返回值是否为布尔值、字符串或对象，以及错误状态如何处理：接口仅原样返回传输结果，[src/preparation-api.js](/workspace/src/preparation-api.js:3)。旁侧组件按真假值处理结果只是当前实现事实：[src/BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:22)。\n- 重试间隔、次数、退避策略及是否必须使用现有调度器：源码提供调度和取消接口，[src/preparation-api.js](/workspace/src/preparation-api.js:10)、[src/preparation-api.js](/workspace/src/preparation-api.js:17)；原任务未指定策略。旁侧组件使用调度器只是实现参考：[src/BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:31)。\n- 关闭、重新打开、更换 token 或卸载时，旧请求及重试应如何处置：下载 hook 有 `close`、`reopen` 和 token 状态，[src/usePreparation.js](/workspace/src/usePreparation.js:32)、[src/usePreparation.js](/workspace/src/usePreparation.js:36)；旁侧组件卸载时取消重试，[src/BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:14)。这些不足以确立下载对话框的产品规则。\n- 是否去重交付、如何下载文件、交付成功如何判定：候选源码未提供足够协议或产品说明。\n\n4. 建议验证范围\n建议分别模拟 pending 后 ready、持续 pending，以及不同 token 的检查结果，观察 pending 时继续检查且无交付、ready 后才对相应文件交付。另检查关闭、重新打开和卸载时是否出现旧文件交付或遗留重试；这些生命周期行为仍需产品规则确认。验证建议不代表已运行测试，也不能凭现有源码确认状态格式、调度策略或实际交付方式。",
  "k0-2": "1. 可确认的 Contract\n原任务明确要求：文件下载对话框遇到准备服务返回 pending 时，应继续检查；只有收到 ready 后才交付对应文件。这里的 pending、ready 是任务描述中的状态含义，候选源码未给出其具体数据格式。\n\n2. 每条的条件、效果、来源及依据\n- 条件：下载对话框正在处理某文件，准备检查结果表示 pending。效果：继续发起后续准备检查，且此时不得将该文件视为已可交付。来源：原任务背景的“keeps checking pending preparation and delivers the file only after a ready status”，足以支持行为要求，但不足以规定重试间隔、次数或调度方式。\n- 条件：同一文件的准备检查结果表示 ready。效果：此后才交付该文件。来源：原任务背景的“only after a ready status”，足以支持交付时机，未规定交付的具体机制。\n- 当前实现事实，并非业务规范：[usePreparation.js](/workspace/src/usePreparation.js:23) 对任何真值结果都把请求时的 token 加入 completed，且没有安排后续检查；[DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:6) 使用该 hook，并只渲染 visible/loading 属性。[preparation-api.js](/workspace/src/preparation-api.js:3) 将 token 传给外部 transport；同文件第 10–20 行提供重试调度和取消接口。[BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:19) 展示另一个界面对假值结果安排重试、真值结果记录完成；这是可参考的实现事实，不能直接当作下载对话框的完整规范。\n\n3. 不能确认的候选要求\n- pending/ready 的实际返回值形状，以及是否仍以假值/真值表示：源码只显示现有布尔式判断，缺少新版服务协议。\n- 重试间隔、上限、失败处理，以及关闭、重新打开、更换 token 或卸载时对在途请求和重试的精确规则：现有接口和生命周期代码提供线索，但原任务未指定预期效果。\n- “交付文件”是否等同于写入 completed，或还需触发浏览器下载：候选源码没有文件交付接口或产品说明。\n\n4. 建议验证范围\n建议用明确的 pending、ready 响应序列检查：pending 后会再次检查且不会提前交付；ready 后才交付对应文件。另检查请求与交付所用的文件身份，以及关闭、重开和卸载期间是否发生过期交付或无效重试。上述均为建议验证，尚未执行；即使通过，也不能单独确定服务状态格式、重试政策或真实下载机制。"
}
</baseline-outputs>
<feedback>
{
  "batch": "v2 only",
  "review_mode": "AI executing-agent evaluation; not independent human review",
  "execution_valid": [
    "k0-1",
    "k0-2"
  ],
  "used_v1_outputs": false,
  "genuine_gaps": [
    {
      "items": [
        "O2"
      ],
      "observation": "k0-1未追踪waiting状态消费者，k0-2只提DOM属性；两者未将单次操作结束/后续等待/整体活动分开。",
      "interpretation": "可见事实和待确认字段语义的提取不够具体，不要求给出隐藏loading=true答案。"
    },
    {
      "items": [
        "O4",
        "T1",
        "T2",
        "T3",
        "T4"
      ],
      "observation": "两份均未完整说明已排队retry时close的关系。k0-1提卸载取消，k0-2仅提取消包装；均未串起原前台无timer、后台已有排队、关闭仅隐藏、仍挂载时可能继续。",
      "interpretation": "缺少条件化资源生命周期说明，不是必须取消的产品结论。"
    },
    {
      "items": [
        "O5",
        "O6",
        "O7"
      ],
      "observation": "均合理未知具体产品政策，但没有充分展开可见的close/reopen共享状态交错及后台close与卸载差别。",
      "interpretation": "可确认源码事实不必与待确认规范一起省略。"
    }
  ],
  "preserve": [
    "O1持续检查和O3 only-ready交付已恢复，禁止损失。",
    "两份都未指定状态编码/间隔/取消政策，无已发现无依据产品要求；保持合理未知。",
    "不要把实现事实变为必须保留的业务义务；不指定唯一修复或变量。"
  ],
  "not_skill_defects": [
    "输入未提供loading唯一表达、完整前台取消政策、workspace所有权/授权迁移；未恢复不扣为能力失败。"
  ],
  "evidence_rows": [
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O1",
      "coverage": "完整覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "效果：继续检查该文件的准备状态，不能因 pending 交付文件。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:5",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:69 「| R1 | pending 继续检查，ready 才交付 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/prompts/maintenance-core.md:3 「The preparation service can now report that a file is still pending before it becomes ready.」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/preparation-api.js:10 「function schedulePreparationRetry」",
      "judgment_rule": "不得将假值/字符串/对象形状强行选为唯一；可把缺少重试作为当前实现事实。",
      "reason": "准确恢复任务义务，未指定状态编码或调度策略。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O2",
      "coverage": "未覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "其他政策合理未知；此字段期间未展开",
      "model_quote": "这些不足以确立下载对话框的产品规则。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:11",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:70 「| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:78 「loading` 是否必须独自表示整个过程；是否允许由 loading 与 retryScheduled 组合表达等待」",
      "judgment_rule": "区分当前回调清loading事实与业务义务。把全程loading=true列确定Contract为无依据新增。",
      "reason": "未提loading消费者及单次请求/整体等待区间；不扣未断言loading=true。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O3",
      "coverage": "完整覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "只有状态为 ready 后才交付文件。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:2",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:69 「| R1 | pending 继续检查，ready 才交付 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:70 「| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/prompts/maintenance-core.md:3 「The preparation service can now report that a file is still pending before it becomes ready.」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」",
      "judgment_rule": "不得把status任意真值当ready规范；检查“only after”方向。",
      "reason": "交付方向正确，另说明completed不等于已确认真实下载。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O4",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "旁侧组件卸载时取消重试",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:11",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:33 「state.current.visible = false;」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/preparation-api.js:10 「function schedulePreparationRetry」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」",
      "judgment_rule": "T1:是否存在待执行retry及对象；T2:取消入口和实际调用位置；T3:关闭后可能检查的条件；T4:缺失宿主/接口证据。只列close测试不算完整；不要求判必须取消。",
      "reason": "识别卸载取消，但未解释已排队timer与close隐藏的条件性关系；仅列生命周期待确认不算完整T1-T4。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O5",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "旧请求及重试应如何处置",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:11",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:33 「state.current.visible = false;」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」",
      "judgment_rule": "不能把原实现无守卫直接写成已确认取消要求，不能套后台政策。",
      "reason": "保留前台政策未知合理；未展开close只隐藏和回调无生命周期守卫的事实。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O6",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "关闭、重新打开、更换 token 或卸载时，旧请求及重试应如何处置",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:11",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」",
      "judgment_rule": "不得以变量名推导唯一generation实现，未给定要求不能猜。",
      "reason": "关注身份和生命周期，但没有追踪捕获token/共享loading/completed及旧回调交错。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-1",
      "phase": "K0",
      "item_id": "O7",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "旁侧组件按真假值处理结果只是当前实现事实",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:9",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:36 「| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:90 「| A5 | 区分前台访问、旧回调与后台组件的政策 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/BackgroundExportPanel.jsx:38 「close = () => this.setState({ visible: false });」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:36 「| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」",
      "judgment_rule": "把当前行为称既定产品必须保留须有任务/文档依据；不得凭后台做法制定前台规范。",
      "reason": "相邻实现未当成前台规范，卸载事实已有；未展开后台close只隐藏及挂载时继续的条件。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O1",
      "coverage": "完整覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "效果：继续发起后续准备检查，且此时不得将该文件视为已可交付。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:5",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:69 「| R1 | pending 继续检查，ready 才交付 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/prompts/maintenance-core.md:3 「The preparation service can now report that a file is still pending before it becomes ready.」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/preparation-api.js:10 「function schedulePreparationRetry」",
      "judgment_rule": "不得将假值/字符串/对象形状强行选为唯一；可把缺少重试作为当前实现事实。",
      "reason": "恢复task规范，并明确不规定间隔次数。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O2",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "其他政策合理未知；等待字段期间未展开",
      "model_quote": "只渲染 visible/loading 属性",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:7",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:70 「| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:78 「loading` 是否必须独自表示整个过程；是否允许由 loading 与 retryScheduled 组合表达等待」",
      "judgment_rule": "区分当前回调清loading事实与业务义务。把全程loading=true列确定Contract为无依据新增。",
      "reason": "识别loading消费者，未追踪字段写入和请求结束到下次检查的区间；不要求猜loading全程保持。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O3",
      "coverage": "完整覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "只有收到 ready 后才交付对应文件。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:2",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:69 「| R1 | pending 继续检查，ready 才交付 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:70 「| R2 | 有效前台准备在 pending 后等待 retry 的间隙仍应呈现等待状态 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/prompts/maintenance-core.md:3 「The preparation service can now report that a file is still pending before it becomes ready.」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」",
      "judgment_rule": "不得把status任意真值当ready规范；检查“only after”方向。",
      "reason": "只有ready后交付方向准确，completed/真实下载未知合理。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O4",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "且没有安排后续检查",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:7",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:33 「state.current.visible = false;」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/preparation-api.js:10 「function schedulePreparationRetry」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」",
      "judgment_rule": "T1:是否存在待执行retry及对象；T2:取消入口和实际调用位置；T3:关闭后可能检查的条件；T4:缺失宿主/接口证据。只列close测试不算完整；不要求判必须取消。",
      "reason": "原前台未接后续检查、相邻后台调度已提，但没有已排队→close→可能检查路径和实际取消位置。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O5",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "关闭、重新打开、更换 token 或卸载时对在途请求和重试的精确规则",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:11",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:33 「state.current.visible = false;」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」",
      "judgment_rule": "不能把原实现无守卫直接写成已确认取消要求，不能套后台政策。",
      "reason": "合理未知；未具体说明close当前只隐藏及回调无guard。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O6",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "另检查请求与交付所用的文件身份",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:15",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/usePreparation.js:24 「state.current.loading = false;」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:71 「| R3 | 已关闭或已被新访问替代的旧回调不能错误影响当前前台准备；关闭时等待状态及后续工作如何处理要明确 |」",
      "judgment_rule": "不得以变量名推导唯一generation实现，未给定要求不能猜。",
      "reason": "有身份验证建议，但未解释reopen改当前token与旧请求捕获token的共享状态交错。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    },
    {
      "call_id": "k0-2",
      "phase": "K0",
      "item_id": "O7",
      "coverage": "部分覆盖",
      "semantic_direction": "正确（已表达部分）",
      "source_accuracy": "准确（所引部分；缺失另计覆盖）",
      "unsupported_additions": "无",
      "unknown_handling": "合理保留未知",
      "model_quote": "这是可参考的实现事实，不能直接当作下载对话框的完整规范。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:7",
      "standard_and_source": "research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:36 「| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:90 「| A5 | 区分前台访问、旧回调与后台组件的政策 |」 | /home/sribd/Downloads/wangshu/temporal-contract-bench-git/case-clusters/download-polling-restoration/arms/download-polling-restoration-low-cue-react18/base/src/BackgroundExportPanel.jsx:38 「close = () => this.setState({ visible: false });」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:36 「| S6 | 相邻后台组件 pending 分支调度 retry，不在该分支清 loading；关闭只隐藏，卸载才停活动并取消定时 |」 | research/code-analysis-standard-drafts-v1-20261107/U2-pending-waiting.md:72 「| R4 | 最终交付、重复触发、close/reopen 及相邻后台行为需要分别检查，不能一套取消条件覆盖全部 |」",
      "judgment_rule": "把当前行为称既定产品必须保留须有任务/文档依据；不得凭后台做法制定前台规范。",
      "reason": "前后台规范未混同；未展开后台close与卸载不同边界。",
      "review_mode": "AI executing-agent evaluation; not independent human review",
      "quality_total": null
    }
  ],
  "timer_rows": [
    {
      "call_id": "k0-1",
      "item_id": "O4",
      "subitem": "T1",
      "coverage": "部分覆盖",
      "model_quote": "旁侧组件使用调度器只是实现参考",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:10",
      "reason": "只提后台调度，未明确关闭时timer存在性与原前台尚无重试。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-1",
      "item_id": "O4",
      "subitem": "T2",
      "coverage": "部分覆盖",
      "model_quote": "旁侧组件卸载时取消重试",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:11",
      "reason": "实际取消位置提到；未结合close位置对照。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-1",
      "item_id": "O4",
      "subitem": "T3",
      "coverage": "未覆盖",
      "model_quote": "另检查关闭、重新打开和卸载时是否出现旧文件交付或遗留重试",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:15",
      "reason": "这是检查建议，没有陈述关闭后仍可能执行检查的源码条件。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-1",
      "item_id": "O4",
      "subitem": "T4",
      "coverage": "部分覆盖",
      "model_quote": "这些不足以确立下载对话框的产品规则。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-1/contract.md:11",
      "reason": "产品政策未知保留；scheduler取消/宿主挂载保证未展开。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-2",
      "item_id": "O4",
      "subitem": "T1",
      "coverage": "部分覆盖",
      "model_quote": "且没有安排后续检查",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:7",
      "reason": "辨明前台无后续检查与后台调度，但未专门指出关闭时已排队timer前提。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-2",
      "item_id": "O4",
      "subitem": "T2",
      "coverage": "部分覆盖",
      "model_quote": "同文件第 10–20 行提供重试调度和取消接口",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:7",
      "reason": "只列包装接口，未定位组件卸载调用。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-2",
      "item_id": "O4",
      "subitem": "T3",
      "coverage": "未覆盖",
      "model_quote": "关闭、重开和卸载期间是否发生过期交付或无效重试",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:15",
      "reason": "仅为验证建议，缺少挂载/隐藏/调度触发的关系。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    },
    {
      "call_id": "k0-2",
      "item_id": "O4",
      "subitem": "T4",
      "coverage": "部分覆盖",
      "model_quote": "现有接口和生命周期代码提供线索，但原任务未指定预期效果。",
      "model_reference": "research/contract-extraction-evolution-u2-v2-20261107/runs/k0-2/contract.md:11",
      "reason": "产品政策合理未知；注入接口和宿主保证不足未展开。",
      "normative_must_cancel_required": false,
      "review_mode": "AI executing-agent evaluation; not independent human review"
    }
  ],
  "no_total_score": true
}
</feedback>

只返回JSON：skill为完整候选提取技能文本（最多4000字符），changes为gap/change/expected_action三字段对象数组。每项说明提取缺口、方法变化和希望改变的动作。
候选必须是可复用的证据提取方法，不包含案例名/ID、文件名或路径、源码变量/函数名、隐藏断言、参考修复或本例七条专用答案。不要把未提供的政策改成要求；不要改变可确认义务与合理未知的评价边界。不得将基础设施失败作为技能缺陷。
只在反馈确实支持方法缺口时修订；不要为表现自演化而制造缺点。若没有必要改动，可原样返回K0并令changes为空。候选将原样冻结，不经人工润色；违规、缺失或范围扩大会停止，不能再生成。

1. 可确认的 Contract
原任务明确要求：下载对话框收到“仍在准备”的结果后继续检查；只有收到“已就绪”的结果，才交付对应文件。该要求针对一次持续的准备活动，涵盖首次请求结束后的等待间隙和后续请求。原任务未规定轮询间隔、状态值的具体编码或交付方式。

2. 每条的条件、效果、来源及依据
- 条件：下载对话框发起的准备检查返回 pending。效果：继续安排后续检查；此时不得交付文件。依据：原任务原文“keeps checking pending preparation and delivers the file only after a ready status”，足以支持行为要求，但不足以规定调度机制。[usePreparation.js](/workspace/src/usePreparation.js:18) 至第27行是当前实现事实：每次调用只发起一次请求，回调将 `loading` 置为 false，并按结果真值写入 `completed`；目前没有后续检查。
- 条件：后续某次检查返回 ready。效果：交付与该准备活动对应的文件。依据：原任务原文，足以支持交付时机。当前代码将真值结果对应的请求 token 加入 `completed`（[usePreparation.js](/workspace/src/usePreparation.js:19) 至第26行）；[DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:6) 至第14行只呈现 `visible`、`loading`，没有可见的文件交付调用。因此 `completed` 是否就是交付，以及 pending/ready 是否以假值/真值表示，均不能由源码确认为协议。
- 当前状态和身份事实：[usePreparation.js](/workspace/src/usePreparation.js:18) 至第27行在发请求时捕获 `requestToken`，回调写共享的 `loading`、`completed`；[usePreparation.js](/workspace/src/usePreparation.js:36) 至第40行重开时更换共享 token 并立即发起检查。旧请求若在重开后返回，可与新活动交错；它会改写共享 `loading`，并以旧 token 写入 `completed`。这是有条件的交错可能性，不等于已证实发生错误。`loading` 当前由请求发起和结束写入，不能据此认定它必须独自表示跨等待间隙的整个活动。
- 当前生命周期事实：[usePreparation.js](/workspace/src/usePreparation.js:32) 至第40行关闭仅设 `visible=false`，重开会立即检查；第18至27行没有排队重试或取消调用。[preparation-api.js](/workspace/src/preparation-api.js:10) 至第20行提供调度和取消入口，但没有给出调度、取消或传输的保证。相邻的 [BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:19) 至第35行在未完成时安排重试，并在卸载时尝试取消（第14至17行）；这是相邻组件的当前行为，原任务没有要求下载对话框复制其状态表示或取消方案。

3. 不能确认的候选要求
- pending、ready 的具体返回值和错误状态处理；需要准备服务的接口契约。
- “交付文件”的可观察动作、是否需要去重，以及 `completed` 的业务含义；需要交付流程或产品规格。
- 关闭后是否继续检查、重开是否创建新活动、同一 token 的活动如何区分、卸载时应如何处理在途回调和已排队工作；需要生命周期政策及宿主行为。若未来加入重试且关闭后组件仍挂载、调度仍可触发，后续检查可能继续；若旧回调仍可执行，也可能影响新活动。这些是条件性风险，不能据此指定唯一的取消或隔离方案。
- `loading` 在两次请求之间应显示 true 还是 false，以及重试间隔、次数或退避规则；现有字段和相邻组件不足以确立这些义务。

4. 建议验证范围
用明确的 pending→pending→ready 序列检查：每次 pending 后是否发生后续请求，等待间隙是否尚未交付，ready 后是否交付正确身份的文件。另覆盖关闭、重开并切换 token、卸载时分别存在在途请求或已排队重试的情形，观察后续请求与共享状态变化。验证前仍需确认服务状态编码、交付动作和生命周期政策；上述建议并非已执行的测试。
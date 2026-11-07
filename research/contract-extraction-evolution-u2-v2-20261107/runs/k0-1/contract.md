1. 可确认的 Contract
原任务明确要求：下载对话框在文件准备状态为 pending 时继续检查；只有状态为 ready 后才交付文件。这里的 pending、ready 是原任务给出的语义，候选源码没有定义其具体返回格式。

2. 每条的条件、效果、来源及依据
- 条件：下载对话框已发起某文件的准备检查，服务报告 pending。效果：继续检查该文件的准备状态，不能因 pending 交付文件。依据：原任务背景直接提出“keeps checking pending preparation”。相关入口为 `DownloadDialog` 使用 `usePreparation(token)` 并暴露其操作：[src/DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:6)、[src/DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:8)；检查调用位于 [src/usePreparation.js](/workspace/src/usePreparation.js:18)。源码仅定位责任位置，不能单独证明该业务要求。
- 条件：服务报告 ready。效果：此后才交付对应文件。依据：原任务背景直接提出“delivers the file only after a ready status”。当前实现事实：检查结果只按真值写入 `completed`，没有可见的文件交付操作：[src/usePreparation.js](/workspace/src/usePreparation.js:23)、[src/usePreparation.js](/workspace/src/usePreparation.js:25)。`completed` 的业务含义及交付机制未由源码确认。

3. 不能确认的候选要求
- 状态返回值是否为布尔值、字符串或对象，以及错误状态如何处理：接口仅原样返回传输结果，[src/preparation-api.js](/workspace/src/preparation-api.js:3)。旁侧组件按真假值处理结果只是当前实现事实：[src/BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:22)。
- 重试间隔、次数、退避策略及是否必须使用现有调度器：源码提供调度和取消接口，[src/preparation-api.js](/workspace/src/preparation-api.js:10)、[src/preparation-api.js](/workspace/src/preparation-api.js:17)；原任务未指定策略。旁侧组件使用调度器只是实现参考：[src/BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:31)。
- 关闭、重新打开、更换 token 或卸载时，旧请求及重试应如何处置：下载 hook 有 `close`、`reopen` 和 token 状态，[src/usePreparation.js](/workspace/src/usePreparation.js:32)、[src/usePreparation.js](/workspace/src/usePreparation.js:36)；旁侧组件卸载时取消重试，[src/BackgroundExportPanel.jsx](/workspace/src/BackgroundExportPanel.jsx:14)。这些不足以确立下载对话框的产品规则。
- 是否去重交付、如何下载文件、交付成功如何判定：候选源码未提供足够协议或产品说明。

4. 建议验证范围
建议分别模拟 pending 后 ready、持续 pending，以及不同 token 的检查结果，观察 pending 时继续检查且无交付、ready 后才对相应文件交付。另检查关闭、重新打开和卸载时是否出现旧文件交付或遗留重试；这些生命周期行为仍需产品规则确认。验证建议不代表已运行测试，也不能凭现有源码确认状态格式、调度策略或实际交付方式。
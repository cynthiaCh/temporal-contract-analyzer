1. 可确认的 Contract

准备服务以 false 表示 pending、true 表示 ready。下载弹窗发起检查后，若结果为 pending，应继续检查；只有对应活动收到 ready，才能将文件记为完成并交付。关闭、重开、切换 token 与卸载时，后续检查及回调应按其所属活动处理，避免旧活动的结果影响新活动。

2. 每条的条件、效果、来源及依据

- **状态与完成条件**：每次 `checkPreparation(token)` 返回 false 时，文件仍在准备中；返回 true 时才就绪。`PREPARATION_STATUS` 及其注释明确给出协议（[preparation-api.js](/workspace/src/preparation-api.js:3)）。原任务要求持续检查 pending，并仅在 ready 后交付。当前下载逻辑只在 ready 时把请求捕获的 token 加入 `completed`，这是可观察的完成记录；源码未展示实际文件传输（[usePreparation.js](/workspace/src/usePreparation.js:42)）。
- **一次请求及等待间隙**：`check` 在请求前写入 `loading=true`、增加 `checkCount`；ready 回调写入 `loading=false` 和 `completed`。pending 回调仅触发发布，没有安排下一次检查，因此请求结束后仍显示 `loading=true`，但没有在途请求或已排队重试；这说明当前实现尚未满足持续检查要求（[usePreparation.js](/workspace/src/usePreparation.js:42)）。`DownloadDialog` 将 `visible`、`loading` 暴露为 DOM 属性（[DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:9)）。`loading` 是否应单独表示整个准备活动，来源不足以确定。
- **后续请求与整个活动**：服务提供安排及取消重试的入口（[preparation-api.js](/workspace/src/preparation-api.js:17)）。当前下载 hook 导入取消入口，却未调用安排入口；`retryScheduled` 初始为 false，仅在清理时写为 false（[usePreparation.js](/workspace/src/usePreparation.js:3)、[usePreparation.js](/workspace/src/usePreparation.js:29)）。因此当前活动不会因 pending 自动产生后续请求。实现轮询后，应使后续检查归属触发它的活动，并以 ready 作为完成条件；具体间隔、次数及状态字段分工没有规范依据。
- **关闭、重开和卸载**：下载弹窗传入 `invalidateOnClose: true`（[DownloadDialog.jsx](/workspace/src/DownloadDialog.jsx:6)）。`close` 隐藏弹窗并递增 generation；`reopen(nextToken)` 更新 token、显示弹窗、开启新 generation 和检查；卸载会标记 disposed 并清理（[usePreparation.js](/workspace/src/usePreparation.js:59)）。回调检查 disposed 与 generation，因此在途旧请求于关闭、重开或卸载后返回时，目前不会写入完成记录。当前没有已排队的下载重试；若加入重试，需检查已排队回调在仍挂载且调度器仍触发时是否会继续检查旧活动。源码没有给出调度器取消成功或回调不再触发的保证。
- **身份交错**：每次请求捕获当时的 `requestToken`，回调修改 hook 共享状态；`reopen` 可在旧请求未结束时换 token（[usePreparation.js](/workspace/src/usePreparation.js:42)、[usePreparation.js](/workspace/src/usePreparation.js:74)）。现有 generation 检查阻止旧响应写入新活动。轮询加入后，同样需要核对排队回调与新活动交错的条件及可观察效果；来源未指定唯一的隔离方法。
- **相邻组件边界**：后台面板在非 ready 时安排重试，ready 时记录完成；关闭面板仅隐藏，工作继续（[useBackgroundPreparation.js](/workspace/src/useBackgroundPreparation.js:36)、[useBackgroundPreparation.js](/workspace/src/useBackgroundPreparation.js:63)）。这证明项目中有调度用法，但其关闭行为属于后台工作，不能据此规定下载弹窗关闭后也继续轮询。

3. 不能确认的候选要求

- pending 期间 `loading`、`retryScheduled` 应分别呈现什么值：当前读写可查，但没有字段语义规范。
- 关闭下载弹窗后是否必须取消整个准备活动、是否允许后台继续准备；现有代码会使当前回调失效，但原任务未给出产品政策。
- 重试间隔、上限、错误处理、重复启动策略，以及 ready 后实际文件交付的接口：相关协议与宿主代码均未提供。
- 调度取消是否保证已排队回调不会运行、卸载后的宿主行为：仅有可选取消函数包装，缺少调度器保证。

4. 建议验证范围

按同一 token 的 pending→pending→ready 检查请求次数与 token，并确认 ready 前无完成或交付、ready 后仅完成一次。分别在请求在途和重试已排队时关闭、重开为另一 token、卸载，观察旧回调与排队工作是否影响新活动或继续发请求。核对请求进行中、请求结束等待重试时及整体活动期间的可见状态。这些验证能确认实现效果；仍不能确定未提供的重试政策、字段语义或实际文件交付接口。
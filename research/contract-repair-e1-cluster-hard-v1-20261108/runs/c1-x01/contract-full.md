## 1. 可确认的 Contract

前台准备客户端在一次检查返回 pending（`false`）后，必须继续安排后续检查；重复 pending 时继续检查；只有检查返回 ready（`true`）后，才将该文档包记为已交付，并停止该活动的后续检查。检查与重试均为异步，重试发生在之后的事件轮次，没有规定实时轮询间隔。

## 2. 每条的条件、效果、来源及依据

- **pending 后继续检查。** 条件：前台已打开的文档包发起检查，服务返回 `false`，且该准备活动仍有效。效果：安排后续检查；再次返回 pending 时重复，不能将 pending 当作完成。依据：原任务明确要求持续检查 pending；[README.md](/workspace/README.md:2) 明确服务可重复报告 pending、不会自行重试，回调在之后的事件轮次执行。当前 [DialogResource](/workspace/src/session.js:35) 的 `pending()` 只发布状态，未安排重试，因此不满足该要求。[WorkspaceJob](/workspace/src/session.js:39) 当前会调度重试，但它是独立生命周期的相邻组件，并非前台义务的来源。
- **ready 后交付。** 条件：当前活动的一次检查返回严格的 `true`。效果：把该次请求对应的包加入完成结果，且不再保留该活动的排队重试。依据：原任务要求“only after a ready status”；[session.js](/workspace/src/session.js:17) 当前以 `ready===true` 进入完成分支，取消重试并更新 `completed`。`completed` 是源码中的可观察结果；它是否等同于产品层面的全部“交付”行为，文档未另行定义。
- **请求及间隙中的状态事实。** [session.js](/workspace/src/session.js:14) 在每次请求前写入 `loading=true`、增加 `checkCount` 并发布快照；请求捕获当时的 `token`。当前前台 pending 回调只发布，故请求结束后的等待间隙里 `loading` 仍为 `true`，`retryScheduled` 仍为 `false`，也没有后续检查。相邻任务的 `schedule()` 会写入 `retryScheduled=true` 并排队，回调触发时清除该标志、发起下一次检查。`snapshot()`、宿主 `publish()` 和组件通知会消费这些状态；[Workspace.vue](/workspace/src/Workspace.vue:1) 直接显示 `visible` 与 `loading`。这些是当前状态流事实；来源不足以要求 `loading` 一个字段独自表达整段准备活动。
- **活动身份与生命周期。** `start()` 和 `reopen(token)` 当前先递增 `generation`、取消排队重试，再开始检查；`reopen` 同时替换包身份。检查回调和已排队的重试回调均检查 `disposed` 与 `generation`，旧代回调通过检查后才可改共享状态。[session.js](/workspace/src/session.js:10) [session.js](/workspace/src/session.js:12) [session.js](/workspace/src/session.js:17) [session.js](/workspace/src/session.js:26)。前台 `close()` 当前隐藏资源、使旧代失效并取消排队重试；`dispose()` 同样使回调失效并取消重试。[session.js](/workspace/src/session.js:33) [session.js](/workspace/src/session.js:37)。这是现有边界；若实现前台轮询，须使后续检查归属于仍有效的准备活动，不能让旧包的结果在新活动中交付。原任务和“已打开文档包”的说明支持活动身份边界，但未指定必须采用某一种取消机制。[README.md](/workspace/README.md:6)
- **相邻组件边界。** `WorkspaceJob.close()` 当前只隐藏面板，已排队重试仍可能在组件挂载且调度器触发时执行；`beforeDestroy()` 才调用 `dispose()`。[session.js](/workspace/src/session.js:39) [Workspace.vue](/workspace/src/Workspace.vue:7)。README 明确相邻工作有自己的生命周期、面板只是显示；这不足以要求前台关闭后仍继续检查。[README.md](/workspace/README.md:7)

## 3. 不能确认的候选要求

- pending 等待间隙里 `loading` 应显示 `true` 还是 `false`，以及 `retryScheduled` 应如何对用户呈现：源码给出当前写法，任务未定义字段语义或 UI 文案。
- 关闭前台后是否应保留已开始的服务端准备、重新打开时是否复用进度、以及最终交付除 `completed` 外是否还有动作：缺少宿主协议与产品政策。
- 精确重试次数、延迟、退避、错误处理和 `false`／`true` 之外的响应：README 只说明后续事件轮次、可取消及两种状态；不能据此补造协议。
- 在途请求是否可由宿主取消：源码只展示已排队回调的取消入口，未给出 `host.check()` 的取消保证。旧回调与新活动可能交错完成，但现有代际检查会阻止旧回调改状态；不能把可能的交错直接称为已发生缺陷。

## 4. 建议验证范围

用可控宿主分别验证：同一包连续多次 pending 后 ready 时的检查顺序、仅 ready 后完成记录、每次等待间隙及后续请求的快照；在 pending 后分别 close、reopen 为另一包、再次 start、卸载，并控制在途响应与已排队回调的先后顺序，检查旧活动不会交付到新活动，且有效活动按要求继续检查。另行观察相邻工作关闭面板后的行为，避免误将其生命周期套用于前台。上述验证即使通过，也不能确定未文档化的 UI 字段语义、服务端取消保证或额外交付动作。
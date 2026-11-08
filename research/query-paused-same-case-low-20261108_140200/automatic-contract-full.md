1. 可确认的 Contract

离线期间新建的 `online` 查询若在首次请求开始前失去唯一观察者，重连后不得让该已离开的观察活动以有效信号调用查询函数。此要求独立于 `refetchOnReconnect`。已开始且未消费信号的请求仍可在视图离开后完成并写入缓存；多个观察者共享请求等现有支持行为应保留。

2. 每条的条件、效果、来源及依据

- **离线首次挂载与卸载。** `subscribe` 在离线且为 `online` 模式时创建 attempt，但只把 `fetchStatus` 设为 `paused`，没有调用 `queryFn`；`unsubscribe` 在最后一个观察者离开时，因尚未消费信号，仅设置 `retryCancelled`。随后 `online(true)` 调用 `resume`，其排入 Promise 回调；因首次请求的 `failures` 为 0，回调仍调用 `invoke`。`invoke` 创建未中止的 controller，并把其信号交给 `queryFn`。这条路径与 `refetchOnReconnect` 无关，源码也没有该选项的判断。来源：[session.js](/workspace/src/session.js:2)、[session.js](/workspace/src/session.js:9)、[session.js](/workspace/src/session.js:10)、[session.js](/workspace/src/session.js:11)、[session.js](/workspace/src/session.js:12)、[session.js](/workspace/src/session.js:13)；禁止出现的效果直接来自原任务。
- **请求与缓存行为。** 每次实际读取 `context.signal` 记录消费；每个 attempt 有自己的 controller，完成后异步更新状态。多个观察者共享一次活动请求；已开始但未消费信号的工作可在观察者离开后完成并写入缓存。来源：[README.md](/workspace/README.md:3)；源码在 [session.js](/workspace/src/session.js:9) 与 [session.js](/workspace/src/session.js:11) 支持这些当前行为。README 足以支持将其列为修复时应保留的行为，但不规定本缺陷的唯一修法。
- **取消与生命周期。** 文档要求取消恢复此前数据和状态，并结算原 attempt；迟到的完成不得成为新 attempt 的数据。源码的完成回调用 attempt 身份检查阻止旧结果写入新 attempt；`cancel` 会中止 controller 并恢复状态。来源：[README.md](/workspace/README.md:3)、[session.js](/workspace/src/session.js:7)、[session.js](/workspace/src/session.js:8)、[session.js](/workspace/src/session.js:9)。本缺陷中首次请求尚未发生，故不能仅凭“未消费的工作可完成”推定其重连后必须启动。

3. 不能确认的候选要求

- 文档未规定离线卸载后的 paused attempt 必须采用取消、删除、标记失效或其他特定实现；只可确认题述的后续有效信号调用须消除。
- 源码有 `focus` 与重试调度，但没有 `refetchOnReconnect` 接口或宿主组件实现；无法确认该选项的完整语义，也无法确认宿主在卸载后是否调用 `dispose`。在仍可调度的条件下，上述重连路径成立。
- 若旧 attempt 的异步回调与新订阅交错，当前 `active` 检查会阻止已被替换的 attempt 写入状态；同一 attempt 被重新订阅时如何处理旧观察活动，尚缺产品要求，不能据此指定隔离策略。

4. 建议验证范围

验证离线新建 `online` 查询、卸载最后一个观察者、重连的完整序列，检查 `queryFn` 是否被调用及若被调用时信号状态；分别覆盖 `refetchOnReconnect` 的设置。再检查重新订阅、多个观察者、已启动且未消费信号的请求、已消费信号的取消、排队恢复及重试回调，确认缓存数据和状态没有回退。上述为建议，尚未执行。按本次“只读取、不修改或执行候选程序”的限制，源码未修改，修复尚未实施。
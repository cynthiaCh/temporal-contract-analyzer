**现有实现能确认的条件如下：**

| 顺序 | 事件接纳与历史 | 当前显示 |
|---|---|---|
| `initialPacket()` 先触发导航，随后 `start()` 派发 | 面板监听器在 `start()` 返回后才注册，因此这次初始事件不会进入该监听器的解码，也不会由它写入历史。 | 原访问不会显示这次初始进度。导航中建立的新访问若已监听同一共享 feed，则可能收到这次派发；这需要按具体重入顺序验证。 |
| 事件已进入监听器和解码，随后导航 | 解码完成后仍调用捕获的 `record`，以**原 fileId、attemptId**写入历史；移除监听器不会撤销已开始的 Promise。 | `receive` 只在 `state.current === visit` 时显示。同一文件重新选择会创建新 visit，因此旧结果不会显示在新访问。 |
| 事件已进入解码，随后重试 | 已接纳结果仍记入**旧 attemptId**的历史。 | 重试沿用同一 visit；现有显示判断没有核对 attemptId，因此旧尝试的迟到结果可能显示到重试后的面板。 |

依据是 [progress.js](/workspace/src/progress.js:3) 的监听、解码及 `start()` 顺序，[progress-source.js](/workspace/src/progress-source.js:26) 的同步派发，[queue.js](/workspace/src/queue.js:11) 的两种输出，以及 [panel.js](/workspace/src/panel.js:17) 和 [retry.js](/workspace/src/retry.js:8) 的访问与尝试归属。

**仍需验证的假设：**“进入解码”应作为已接纳事件的边界，历史在之后导航或重试时仍应保留；这与现有实现及 README 对历史和显示的区分一致，但 README 没有逐字规定该边界。修复初始更新时，还需用同步导航、异步乱序解码和同访问重试验证：失效后才派发的旧初始事件不会被误记，已接纳的旧结果保留原尝试历史，而较旧的完整帧不会把当前显示倒退。
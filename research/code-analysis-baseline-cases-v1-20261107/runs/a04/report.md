1. 原任务目标与需要保留的行为
任务背景要求：编辑突发结束、安静 120 ms 后才将该突发的最新文本写入 store；后续突发仍须保存。保留工作区同步 API、关闭或切换文档后可读到最后一次已接受编辑、保存状态、提交收据及通知等既有行为。相邻搜索预览不在维护范围内。[README.md](/workspace/README.md:3)、[README.md](/workspace/README.md:15)、[README.md](/workspace/README.md:26)

2. 关键源码事实及路径、行号
`workspace.edit` 调用 `editor.edit`；后者立即更新 `current.text` 并逐次调用 `store.write`。[workspace.js](/workspace/src/workspace.js:9)、[editor.js](/workspace/src/editor.js:17) `store.write` 先更新记录，再同步通知订阅者。[draft-store.js](/workspace/src/draft-store.js:10) 订阅者包括 `onSaved` 和当前文档的保存状态渲染；`onSaved` 可经工作区 API 再次导航或编辑。[workspace.js](/workspace/src/workspace.js:5)、[save-status.js](/workspace/src/save-status.js:4)、[README.md](/workspace/README.md:9) 现有 `createTrailingTask` 的 `push` 重置计时并保留最新参数，`flush` 先清除待办再调用工作，`cancel` 丢弃待办。[trailing-task.js](/workspace/src/trailing-task.js:5) 搜索预览使用该工具，延迟为 40 ms，隐藏时取消。[search-preview.js](/workspace/src/search-preview.js:3)

3. 相关事件顺序及其依据
当前每次有效编辑均先更新编辑器文本，再写 store，再同步发出保存事件。打开文档先调用 `close`，它先清除当前访问并解除状态订阅，随后读取新文档并渲染。[editor.js](/workspace/src/editor.js:5)、[editor.js](/workspace/src/editor.js:12) 提交先读取当前选择，再捕获收据、渲染通知；当前实现未在捕获前显式冲刷待保存文本。[workspace.js](/workspace/src/workspace.js:11) 若改用延迟任务，编辑与计时回调的先后取决于调用和计时安排；关闭、切换、提交与回调交错时的处理需依据上述同步契约判断，不能仅由延迟工具推定。

4. 不同消费者、阶段或效果是否采用不同条件
store 记录供 `read` 和重开文档使用；保存事件供 `onSaved` 与按文档 ID 过滤的状态渲染使用。[draft-store.js](/workspace/src/draft-store.js:9)、[save-status.js](/workspace/src/save-status.js:5) 提交收据取调用入口所选文档和最新文本，需在归档捕获前持久化；提交通知仅属于接受动作的同一次编辑器访问。[README.md](/workspace/README.md:15)、[README.md](/workspace/README.md:20) `selection` 已返回访问标识，但当前 `submit` 渲染通知时没有检查它。[editor.js](/workspace/src/editor.js:22)、[workspace.js](/workspace/src/workspace.js:12)

5. 能确认的要求、仅有线索的判断及未知项
可确认：120 ms 合并写入来自原任务；关闭或切换返回时的持久化、订阅回调可重入、提交前持久化及访问限定通知来自 README。源码线索显示延迟工具具备合并、立即执行、丢弃三种操作，但具体调用位置与交错处理尚未定义。未知：候选工作区中没有进一步说明计时器对已取消回调的交付保证；不能据此断言所有回调交错顺序。

6. 建议验证的行为范围
建议后续验证连续编辑只写最后文本、安静期后第二突发仍保存；关闭或切换前的待写文本可读且旧状态不再渲染；提交在待写期间捕获已持久化的入口快照，回调中导航或编辑后收据及通知仍符合访问约束；无选择提交返回 null；搜索预览维持 40 ms 与隐藏取消行为。这些是待验证范围，本轮未执行测试。
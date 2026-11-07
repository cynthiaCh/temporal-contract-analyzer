1. 原任务目标与需要保留的行为
原任务要求草稿编辑在安静 120 ms 后才向 store 写入该轮编辑的最新文本，后续编辑轮次仍须保存；相邻搜索预览不在改动范围。README 还要求 open、edit、close、submit 同步；close/open 返回时，离开文档最后接受的编辑已可从 store 读取，并保留工作区及渲染接口（README.md:3-7,26-33）。

2. 关键源码事实及路径、行号
`src/workspace.js:3-19` 将公开操作转交编辑器；store 订阅事件会同步调用 `onSaved(event, navigation)`。`src/editor.js:12-23` 在 open 时读取 store 并建立一次 visit；edit 立即更新内存文本并逐次 `store.write`；selection 返回当前内存文本。close 先清空 current、停止保存状态订阅，再清空文档渲染（`src/editor.js:5-9`）。`src/draft-store.js:10-16` 先写记录，再同步通知订阅者。`src/trailing-task.js:5-27` 的 push 重置计时并保留最新参数，flush 执行待办，cancel 丢弃待办；执行 work 前会清除旧批次状态。搜索预览已使用该工具，延迟 40 ms，hide 时取消（`src/search-preview.js:3-9`）。

3. 相关事件顺序及其依据
当前 edit 中，内存文本更新先于 store 写入；写入先于订阅通知（`src/editor.js:19-20`；`src/draft-store.js:10-15`）。使用 trailing task 时，同一轮多次 push 会取消前次计时，仅最新参数在安静间隔后交给 work；work 内若发生回调并再次 push，新一轮可继续排队（`src/trailing-task.js:8-20`）。README 明确 `onSaved` 可通过工作区 API 导航或编辑，且导航以请求开始顺序决定优先级（README.md:9-13）；因此保存通知与重入的 open、close、edit、submit 的交错顺序是分析重点。源码尚未定义编辑器应在哪个具体调用点 flush 待保存文本。

4. 不同消费者、阶段或效果是否采用不同条件
保存状态订阅仅渲染匹配文档 id 的事件，离开时停止订阅（`src/save-status.js:1-7`）；草稿持久化属于独立效果（同文件第 3 行）。submit 从当前 selection 取 id 和内存文本，随后捕获不可变收据并渲染通知（`src/workspace.js:11-17`；`src/receipt-archive.js:6-9`）。README 要求收据捕获前文本已持久化，通知只属于接受提交的那次编辑 visit（README.md:15-24）。当前源码中的 submit 没有持久化步骤或 visit 校验；这与延迟保存后的要求如何衔接，不能仅凭函数名推断。搜索预览使用相同工具，但其 hide 明确丢弃待发布查询（`src/search-preview.js:4-9`），与草稿离开时须保留最后编辑的要求不同。

5. 能确认的要求、仅有线索的判断及未知项
可确认：120 ms 合并保存及后续轮次继续保存来自原任务；离开时可读、提交前持久化、同步接口和通知归属来自 README。线索：编辑器已接收 `timers`，却未使用（`src/editor.js:3`），现有工具可能用于实现调度。未知：外部传入 timers 的具体调度语义与句柄类型、重入回调时预期的具体实现策略；源码和文档没有规定唯一修复方式。

6. 建议验证的行为范围
建议在后续维护验证中观察：一轮连续 edit 的写入次数、文本和 120 ms 边界；第二轮是否仍保存；close/open、submit、dispose 前待保存文本的 store 可读性及收据内容；同步 onSaved 重入导航或编辑时的目标文档、保存状态和提交通知；搜索预览的 40 ms 发布及 hide 取消行为。这些观察可判断外部效果是否符合任务和 README，但不能单独证明内部采用了哪一种调度实现。本轮未运行验证。
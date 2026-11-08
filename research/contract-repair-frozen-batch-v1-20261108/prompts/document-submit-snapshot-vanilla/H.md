The workspace draft editor currently writes to the store on every keystroke.
Coalesce edits using the existing trailing-task utility: after a 120 ms quiet
interval, write only the latest text in that editing burst. Subsequent bursts
must continue to save. Preserve the editor's other behavior and public interfaces.
The adjacent search preview is outside this maintenance change.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
edit按现有trailing utility在120ms静默后只写该burst最新值，后续burst仍可保存。close/open返回时离开文档最后接纳编辑已持久化；先退休旧badge。保留按请求开始顺序后发导航优先。submit入口确定文档和文本，无selection返回null，否则同步返回恰好一个不可变receipt；capture前先持久化，接纳提交跨后续导航仍存在。notice只属原visit，导航清旧notice，同文档重开也是新visit。保留public API及40ms预览hide丢弃/可复用。


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。

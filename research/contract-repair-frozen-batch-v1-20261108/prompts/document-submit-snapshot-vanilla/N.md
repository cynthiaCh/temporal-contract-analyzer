The workspace draft editor currently writes to the store on every keystroke.
Coalesce edits using the existing trailing-task utility: after a 120 ms quiet
interval, write only the latest text in that editing burst. Subsequent bursts
must continue to save. Preserve the editor's other behavior and public interfaces.
The adjacent search preview is outside this maintenance change.


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。

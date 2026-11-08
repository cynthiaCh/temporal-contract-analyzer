Add one automatic retry to load: if the first request rejects with error.retryable === true, retry once after 20 ms using the supplied timers. Do not retry a second time. Keep the existing public interfaces and behavior outside this retry change. Search preview is outside this change.


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。

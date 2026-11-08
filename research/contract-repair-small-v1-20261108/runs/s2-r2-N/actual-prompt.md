The save service is becoming asynchronous: service.commit(snapshot) now returns a Promise for a receipt, or rejects. Update submit to work with it and return a Promise that settles after handling the outcome. Preserve the editor behavior, public methods and other consumers. Search preview is outside this change.


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

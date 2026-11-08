The save service is becoming asynchronous: service.commit(snapshot) now returns a Promise for a receipt, or rejects. Update submit to work with it and return a Promise that settles after handling the outcome. Preserve the editor behavior, public methods and other consumers. Search preview is outside this change.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
每次submit在入口捕获doc、actor和text。commit成功后按receipt revision只记录一次该快照审计；失败不记录成功审计。已接纳提交跨close/reopen保留，saved/error只属于当前visit最新提交。返回Promise在处理结果后定案。保留40ms预览、hide丢弃待处理查询、后续复用。失败传播值及嵌套可变性未规定。


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。

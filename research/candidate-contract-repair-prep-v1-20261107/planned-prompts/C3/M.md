完成以下原维护任务并实际修改候选代码，交付补丁，不仅解释Contract。仅在/workspace内自主执行，保留公共接口和原任务要求。不得读取标准、评分器、隐藏测试、参考修复、历史研究或其他运行，不使用网络。允许在候选工作区内读取、编辑并做相关自检。JavaScript自检使用统一提供的/runtime/node，并记录版本。不要修改候选之外的文件。最终返回JSON，唯一字段report，最多6000个Unicode字符，简述修改和实际自检；实际补丁由工作区差异另行归档。

原任务：
The save service is becoming asynchronous: service.commit(snapshot) now returns a Promise for a receipt, or rejects. Update submit to work with it and return a Promise that settles after handling the outcome. Preserve the editor behavior, public methods and other consumers. Search preview is outside this change.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
<contract>
原任务要求适配异步保存：service.commit(snapshot) 返回 receipt 的 Promise，或发生拒绝；submit 应返回一个在结果处理完成后才定案的 Promise。每次提交使用调用入口捕获的 doc、actor、text。成功后，以该快照和返回的 revision 恰好写入一条审计记录；失败不得写成功审计。已受理提交在 close 或重新 open 后仍须完成其历史记录处理。saved/error 界面反馈仅属于当前打开活动中的最新提交。保留编辑器公开方法及其他消费者的行为；搜索预览不在本次改动范围。

</contract>

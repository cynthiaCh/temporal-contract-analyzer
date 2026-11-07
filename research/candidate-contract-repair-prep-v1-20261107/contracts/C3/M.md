原任务要求适配异步保存：service.commit(snapshot) 返回 receipt 的 Promise，或发生拒绝；submit 应返回一个在结果处理完成后才定案的 Promise。每次提交使用调用入口捕获的 doc、actor、text。成功后，以该快照和返回的 revision 恰好写入一条审计记录；失败不得写成功审计。已受理提交在 close 或重新 open 后仍须完成其历史记录处理。saved/error 界面反馈仅属于当前打开活动中的最新提交。保留编辑器公开方法及其他消费者的行为；搜索预览不在本次改动范围。


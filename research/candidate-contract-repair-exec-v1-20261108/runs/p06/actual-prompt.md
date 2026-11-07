完成以下原维护任务并实际修改候选代码，交付补丁，不仅解释Contract。仅在/workspace内自主执行，保留公共接口和原任务要求。不得读取标准、评分器、隐藏测试、参考修复、历史研究或其他运行，不使用网络。允许在候选工作区内读取、编辑并做相关自检。JavaScript自检使用统一提供的/runtime/node，并记录版本。不要修改候选之外的文件。最终返回JSON，唯一字段report，最多6000个Unicode字符，简述修改和实际自检；实际补丁由工作区差异另行归档。

原任务：
The save service is becoming asynchronous: service.commit(snapshot) now returns a Promise for a receipt, or rejects. Update submit to work with it and return a Promise that settles after handling the outcome. Preserve the editor behavior, public methods and other consumers. Search preview is outside this change.


以下为辅助材料。辅助材料不能替代原维护任务。依据原任务和项目证据核查其适用性；存在冲突或证据不足时回到源码核查，不要盲目执行。

Contract：
- 每次 submit 在调用入口捕获 doc、actor、text 快照。
- commit 成功后，按入口快照及 receipt revision 恰好记录一次审计；失败不生成成功审计。
- 已接纳提交在 close 或 reopen 后继续处理其历史记录。
- saved/error 反馈只属于当前 visit 的最新提交。
- submit 返回在结果处理完成后定案的 Promise。
- 保留编辑器公开方法及其他消费者行为；搜索预览保持 40 ms、hide 丢弃待处理查询并可复用。

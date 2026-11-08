The save service is becoming asynchronous: service.commit(snapshot) now returns a Promise for a receipt, or rejects. Update submit to work with it and return a Promise that settles after handling the outcome. Preserve the editor behavior, public methods and other consumers. Search preview is outside this change.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

`submit` 要适配 `service.commit(snapshot)` 返回 receipt Promise 或拒绝的接口，并返回一个在相应结果处理完后才敲定的 Promise。每次提交在调用入口固定 doc、actor、text；成功后以该快照和返回的 revision 恰好写一条审计记录，失败不写成功审计。已接受的提交在关闭或重开后仍须完成其审计处理。saved/error 界面反馈只属于当前访问及该访问中最新的提交。保留 `open`、`edit`、`submit`、`close` 等公开方法及编辑器行为。Search preview 不在本次改动范围内。

## 

完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

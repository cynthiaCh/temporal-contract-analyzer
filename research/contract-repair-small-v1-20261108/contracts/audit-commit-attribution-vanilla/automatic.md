
`submit` 要适配 `service.commit(snapshot)` 返回 receipt Promise 或拒绝的接口，并返回一个在相应结果处理完后才敲定的 Promise。每次提交在调用入口固定 doc、actor、text；成功后以该快照和返回的 revision 恰好写一条审计记录，失败不写成功审计。已接受的提交在关闭或重开后仍须完成其审计处理。saved/error 界面反馈只属于当前访问及该访问中最新的提交。保留 `open`、`edit`、`submit`、`close` 等公开方法及编辑器行为。Search preview 不在本次改动范围内。

## 
# Maintenance task

The remote static-configuration endpoint used by the Personnel relationship
editor has been retired. Replace that request with the existing local JSON
configuration and keep the editor's existing behavior unchanged.

Do not migrate the Structure relationship editor.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
Personnel editor改用现有local JSON并保留父身份、声明式rule、option和unit picker行为。SchemaForm的imperative API由mounted后定时发布，rule watcher也支持value；不能把请求延迟当API就绪保证。仅迁移Personnel，不迁移Structure或更改共享接口。具体实现不限于一种。


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器或网络。Node自检使用 /runtime/node，并记录 --version。依赖仅使用已有只读运行时。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。补丁从工作区归档。

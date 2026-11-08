The observatory exposure package service can now report that a package is still pending before it becomes ready. Update the foreground preparation client so it keeps checking pending preparation and delivers the package only after a ready status.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
前台准备客户端面对 `false`（pending）时，应继续检查同一活动的包；只有收到 `true`（ready）后，才将该包标为已完成并对外发布。pending 可以重复出现，传输层不会自行重试。前台资源的公开操作包括 start、close、reopen、snapshot；最终 owner disposal 释放资源。



完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

# Task

The preparation service can now report that a file is still pending before it becomes ready. Update the file download dialog so it keeps checking pending preparation and delivers the file only after a ready status.



以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

准备服务以 false 表示 pending、true 表示 ready。下载弹窗发起检查后，若结果为 pending，应继续检查；只有对应活动收到 ready，才能将文件记为完成并交付。关闭、重开、切换 token 与卸载时，后续检查及回调应按其所属活动处理，避免旧活动的结果影响新活动。



完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

The archaeological excavation atlas service can now report that a package is still pending before it becomes ready. Update the foreground preparation client so it keeps checking pending preparation and delivers the package only after a ready status.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

前台准备客户端在一次检查返回 pending（`false`）后，必须继续安排后续检查；重复 pending 时继续检查；只有检查返回 ready（`true`）后，才将该文档包记为已交付，并停止该活动的后续检查。检查与重试均为异步，重试发生在之后的事件轮次，没有规定实时轮询间隔。

## 

完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

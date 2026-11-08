A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, audit, or queue-record behavior. Full
progress frames may decode out of order; do not allow an older frame to roll the
current display backward. Preserve ordinary streaming, diagnostic telemetry,
and subsequent uses.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
恢复warm source初始进度，保留普通streaming、公共API和相邻telemetry。README定义select创建visit、retry仅替换物理attempt、同文件重选创建新visit，feed对象共享。decode可能异步；不得用较旧帧回退当前显示。保留history与UI各自归属、同步宿主回调、队列记录结构及原导航/取消/cleanup行为；未授权新增byteCount。


完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

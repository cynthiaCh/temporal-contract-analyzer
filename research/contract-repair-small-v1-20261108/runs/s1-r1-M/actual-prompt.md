A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, audit, or queue-record behavior. Full
progress frames may decode out of order; do not allow an older frame to roll the
current display backward. Preserve ordinary streaming, diagnostic telemetry,
and subsequent uses.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

1. 对有进度源的传输，若 `start()` 同步发出缓存的初始包，面板应收到解码后的初始进度；随后到达的进度包仍应正常处理。
2. 完整进度帧的解码可能乱序完成；较旧的帧不得使当前面板显示倒退。
3. 修复须保留公开传输、重试、导航、清理、审计、队列记录及诊断遥测的既有行为。`recordProgress` 的历史记录与 `showProgress` 的面板显示是不同输出。

## 

完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围；补丁从独立工作区归档。

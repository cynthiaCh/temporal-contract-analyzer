A transfer with a warm progress source shows no initial progress until a later
packet arrives. Restore the initial progress update without changing the public
transfer, retry, navigation, cleanup, audit, or queue-record behavior. Full
progress frames may decode out of order; do not allow an older frame to roll the
current display backward. Preserve ordinary streaming, diagnostic telemetry,
and subsequent uses.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。

- 有缓存首包的进度源启动传输时，面板应收到初始进度更新；后续普通进度包仍应正常传递。
- 完整进度帧可乱序完成解码；较旧的帧不得使当前显示的进度倒退。
- 修复须保留公开传输、重试、导航、清理、审计、队列记录和诊断遥测的既有行为。



完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。

原始快照、最终源码、补丁差异、日志及实验结果由外部运行器自动保存。请集中完成业务修复与必要验证，不创建用于实验留档的备份副本、补丁归档目录或结果汇总文件。结束时按现有输出格式简要说明修改与验证结果。

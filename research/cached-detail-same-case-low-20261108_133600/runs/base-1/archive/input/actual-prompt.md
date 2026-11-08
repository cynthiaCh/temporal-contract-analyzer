# Improve warm record-detail activation

The detail workspace still waits for a network observation when a record already
exists in the shared repository cache. Update detail activation to use the
repository's existing cache-preferred watch mode: when cached data is available,
show it within the opening call and continue receiving fresh network updates.
A cold record should continue to work normally. Preserve the workspace's
existing behavior. This task covers the detail panel; keep compliance review and
recent preview behavior unchanged.


以下为辅助材料。依据原任务和项目证据核查其适用性；存在冲突或证据不足时不要盲目执行。
详情面板打开已有缓存的记录时，应在 `open(id)` 返回前交付缓存快照，并继续接收该次订阅的网络更新；无缓存时，仍按正常网络订阅流程工作。每次 `open(id)` 都是新活动，包括重复打开同一 ID。选择状态代表最新请求的目的地，详情记录只在所属活动仍被选中时才有用；离开后不得保留该活动的传输订阅。合规审查继续要求新鲜网络观察，最近预览的呈现行为保持不变。

## 

完成原维护任务，实际修改候选代码并做相关验证。仅在 /workspace 内工作，不查看研究材料、历史、评分器、其他槽位或网络。Node自检使用 /runtime/node，并记录 --version；不安装依赖。最终返回JSON，唯一字段report，最多6000个Unicode字符，报告实际交付、验证与未覆盖范围。

原始快照、最终源码、补丁差异、日志及实验结果由外部运行器自动保存。请集中完成业务修复与必要验证，不创建用于实验留档的备份副本、补丁归档目录或结果汇总文件。结束时按现有输出格式简要说明修改与验证结果。

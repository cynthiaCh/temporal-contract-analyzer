Fix the museum accession activity viewer's startup and navigation lifecycle.

Opening a feed backed by a warm cache sometimes leaves the first batch missing,
although later activity appears. During quick feed changes or closing and
reopening the panel, rows or the count can also appear for a previous visit.

Correct these timing problems while preserving normal live updates, history
recording, public APIs and the existing rendering adapters. The independent
metrics consumer is outside this repair.


以下自动Contract为辅助材料，请依据当前任务和源码核查，不盲从无据政策：
For each panel visit, receive the cached first batch when its feed starts, including when start emits synchronously, and continue receiving live deltas while that visit is selected. After selection changes or the panel hides, prevent rows or counts from a previous visit from becoming visible, including when the same feed object is reused and decode or paint completes later. A count may become visible only after its corresponding rows have finished painting and only if that visit is still current. Preserve history for every batch already received by the panel subscriber once decoding completes, even if the visit has ended; detachment stops new reception but does not revoke accepted work. Preserve public APIs, payloads, host rendering behavior, and the independent metrics consumer’s policy. Account for callbacks that run inline and painting that synchronously navigates or hides; no particular repair strategy is required.

在 /workspace 内自主定位、修复与验证。只修改产品源码；保留接口、依赖和构建/测试配置。不安装依赖，不访问网络或研究材料。JS使用 /runtime/node，Python使用 /usr/bin/python3 -B。
原始快照、最终源码、补丁差异、日志及评分由外部Python自动保存。请只修业务代码并做必要验证，不创建实验备份、归档补丁或结果汇总文件。最终返回唯一字段report的JSON，简短说明实际修改、验证与未覆盖范围，不超过6000个Unicode字符。